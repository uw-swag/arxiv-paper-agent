from pathlib import Path
from axpa.outputs.data_models import AggregatedScoreResult, PaperSummary
from mcp_agent.workflows.llm.augmented_llm import RequestParams
from axpa.agents.paper_summarizer import create_paper_summarizer_agent
from typing import List, Optional
import asyncio


def load_markdown_content(markdown_path: str) -> str | None:
    """Load markdown content from file path."""
    try:
        path = Path(markdown_path)
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None
    except Exception:
        return None


async def summarize_papers_stage(
    papers: List[AggregatedScoreResult],
    context,
    llm_factory,
) -> List[PaperSummary]:
    """
    Stage 6: Summarize the papers across 6 key dimensions.

    For each paper, sequentially calls the LLM 6 times to generate:
    1. Research gap
    2. Related studies
    3. Methodology
    4. Experiments
    5. Further research
    6. Overall summary

    Implementation pattern:
    - Papers are grouped by whether they have pre-downloaded markdown content
    - Papers with markdown: content is provided directly, uses arxiv-paper-mcp for related work search
    - Papers without markdown: agent uses tools to download and read the paper
    - History is preserved between calls so the LLM has context of previous responses
    - Papers are processed in parallel, but each paper's 6 summaries are generated sequentially

    Returns:
        List of PaperSummary objects
    """
    logger = context.logger
    logger.info("summarize_papers.start", data={"total_papers": len(papers)})

    # Separate papers by markdown availability
    papers_with_markdown = []
    papers_without_markdown = []

    for paper in papers:
        markdown_path = paper.paper.markdown_path
        if markdown_path:
            content = load_markdown_content(markdown_path)
            if content:
                papers_with_markdown.append((paper, content))
            else:
                papers_without_markdown.append(paper)
        else:
            papers_without_markdown.append(paper)

    logger.info("summarize_papers.paper_groups", data={
        "with_markdown": len(papers_with_markdown),
        "without_markdown": len(papers_without_markdown)
    })

    request_params = RequestParams(
        maxTokens=16384,
        temperature=0.3
    )

    # Define the 6 summary prompts in order
    summary_prompts = [
        ("research_gap", "What problem or gap in existing knowledge is this paper trying to address? Provide a 2-5 sentence explanation."),
        ("related_studies", "What existing studies or prior work are related to this problem? You may search for related papers using the available tools if needed. Provide a 2-5 sentence summary."),
        ("methodology", "How does this paper tackle the issue? What approaches, methods, or techniques are used? Provide a detailed explanation of the methodology."),
        ("experiments", "What kind of experiments were conducted in the paper? What datasets, benchmarks, or evaluations were used? Provide a detailed summary of the experiments and results."),
        ("further_research", "What areas could be explored further? What are the limitations or open questions? You may search for recent work using the available tools if relevant. Provide a 5-10 points list discussion."),
        ("overall_summary", "Provide a comprehensive summary of the paper covering all key aspects: problem, methods, experiments, results, and contributions. This should be 5-10 sentences.")
    ]

    async def summarize_paper_with_markdown(
        paper: AggregatedScoreResult,
        markdown_content: str,
        llm
    ) -> Optional[PaperSummary]:
        """Summarize a paper that has pre-downloaded markdown content."""
        try:
            # Clear history for clean slate for this paper
            llm.history.clear()

            logger.info("summarize_papers.paper_start", data={
                "paper_id": paper.paper_id,
                "title": paper.paper.title[:60],
                "has_markdown": True
            })

            # Initial context message with the paper content
            initial_message = f"""I need you to summarize this paper in detail.

Paper ID: {paper.paper_id}
Title: {paper.paper.title}
Authors: {', '.join(paper.paper.authors[:5])}{'...' if len(paper.paper.authors) > 5 else ''}
Published: {paper.paper.published}

## Paper Content (Markdown)

{markdown_content}

---

I will ask you to provide summaries for 6 different aspects of this paper. If there are unclear mathematical formulas, you can use the arxiv-latex-mcp tool to get the LaTeX source. For searching related papers, use the arxiv-paper-mcp tools. I'll provide you the prompts for each aspect step by step."""

            # Send initial context
            await llm.generate_str(
                message=initial_message,
                request_params=request_params
            )

            # Sequentially generate each summary aspect
            summaries = {}
            for field_name, prompt in summary_prompts:
                logger.debug("summarize_papers.generating", data={
                    "paper_id": paper.paper_id,
                    "field": field_name,
                    "has_markdown": True
                })

                summary_text = await llm.generate_str(
                    message=prompt,
                    request_params=request_params
                )

                summaries[field_name] = summary_text.strip()

                logger.debug("summarize_papers.field_complete", data={
                    "paper_id": paper.paper_id,
                    "field": field_name,
                    "length": len(summary_text),
                    "has_markdown": True
                })

            # Create PaperSummary object
            paper_summary = PaperSummary(
                score=paper,
                research_gap=summaries["research_gap"],
                related_studies=summaries["related_studies"],
                methodology=summaries["methodology"],
                experiments=summaries["experiments"],
                further_research=summaries["further_research"],
                overall_summary=summaries["overall_summary"]
            )

            logger.info("summarize_papers.paper_complete", data={
                "paper_id": paper.paper_id,
                "title": paper.paper.title[:60],
                "has_markdown": True
            })

            return paper_summary

        except Exception as e:
            logger.error("summarize_papers.paper_error", data={
                "paper_id": paper.paper_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "has_markdown": True
            })
            return None

    async def summarize_paper_without_markdown(
        paper: AggregatedScoreResult,
        llm
    ) -> Optional[PaperSummary]:
        """Summarize a paper that needs to be downloaded by the agent."""
        try:
            # Clear history for clean slate for this paper
            llm.history.clear()

            logger.info("summarize_papers.paper_start", data={
                "paper_id": paper.paper_id,
                "title": paper.paper.title[:60],
                "has_markdown": False
            })

            # Initial context message about the paper
            initial_message = f"""I need you to summarize this paper in detail.

Paper ID: {paper.paper_id}
Title: {paper.paper.title}
Authors: {', '.join(paper.paper.authors[:5])}{'...' if len(paper.paper.authors) > 5 else ''}
Published: {paper.paper.published}

I will ask you to provide summaries for 6 different aspects of this paper. You may use `arxiv-latex-mcp` to read the paper at this step. I'll provide you the prompts for each aspect later step by step."""

            # Send initial context (no response needed, just setting context)
            await llm.generate_str(
                message=initial_message,
                request_params=request_params
            )

            # Sequentially generate each summary aspect
            summaries = {}
            for field_name, prompt in summary_prompts:
                logger.debug("summarize_papers.generating", data={
                    "paper_id": paper.paper_id,
                    "field": field_name,
                    "has_markdown": False
                })

                summary_text = await llm.generate_str(
                    message=prompt,
                    request_params=request_params
                )

                summaries[field_name] = summary_text.strip()

                logger.debug("summarize_papers.field_complete", data={
                    "paper_id": paper.paper_id,
                    "field": field_name,
                    "length": len(summary_text),
                    "has_markdown": False
                })

            # Create PaperSummary object
            paper_summary = PaperSummary(
                score=paper,
                research_gap=summaries["research_gap"],
                related_studies=summaries["related_studies"],
                methodology=summaries["methodology"],
                experiments=summaries["experiments"],
                further_research=summaries["further_research"],
                overall_summary=summaries["overall_summary"]
            )

            logger.info("summarize_papers.paper_complete", data={
                "paper_id": paper.paper_id,
                "title": paper.paper.title[:60],
                "has_markdown": False
            })

            return paper_summary

        except Exception as e:
            logger.error("summarize_papers.paper_error", data={
                "paper_id": paper.paper_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "has_markdown": False
            })
            return None

    all_summaries = []

    # Process papers with markdown (using simplified agent)
    if papers_with_markdown:
        logger.info("summarize_papers.markdown_start", data={
            "count": len(papers_with_markdown)
        })

        summarizer_agent_markdown = create_paper_summarizer_agent(has_markdown=True)

        async with summarizer_agent_markdown as agent_ctx:
            llm = await agent_ctx.attach_llm(llm_factory)

            try:
                results = await asyncio.gather(
                    *[summarize_paper_with_markdown(paper, content, llm)
                      for paper, content in papers_with_markdown],
                    return_exceptions=True
                )

                for idx, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.warning("summarize_papers.markdown_exception", data={
                            "index": idx,
                            "error": str(result)
                        })
                    elif result is not None:
                        all_summaries.append(result)

            except Exception as e:
                logger.error("summarize_papers.markdown_error", data={
                    "error": str(e)
                })

        logger.info("summarize_papers.markdown_complete", data={
            "successful": len([s for s in all_summaries])
        })

    # Process papers without markdown (using full agent with tools)
    if papers_without_markdown:
        logger.info("summarize_papers.download_start", data={
            "count": len(papers_without_markdown)
        })

        summarizer_agent_download = create_paper_summarizer_agent(has_markdown=False)

        async with summarizer_agent_download as agent_ctx:
            llm = await agent_ctx.attach_llm(llm_factory)

            try:
                results = await asyncio.gather(
                    *[summarize_paper_without_markdown(paper, llm)
                      for paper in papers_without_markdown],
                    return_exceptions=True
                )

                for idx, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.warning("summarize_papers.download_exception", data={
                            "index": idx,
                            "error": str(result)
                        })
                    elif result is not None:
                        all_summaries.append(result)

            except Exception as e:
                logger.error("summarize_papers.download_error", data={
                    "error": str(e)
                })

        logger.info("summarize_papers.download_complete", data={
            "successful": len(all_summaries) - len(papers_with_markdown)
        })

    # Log summary
    logger.info("summarize_papers.complete", data={
        "total_papers": len(papers),
        "successful_summaries": len(all_summaries),
        "errors": len(papers) - len(all_summaries)
    })

    return all_summaries
