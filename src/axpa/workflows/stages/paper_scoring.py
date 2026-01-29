import traceback
from pathlib import Path
from axpa.agents.paper_scorer import create_paper_scorer_agent
from axpa.outputs.data_models import Paper, ScoreResult, AggregatedScoreResult
from mcp_agent.workflows.llm.augmented_llm import RequestParams

from typing import List
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


async def score_papers_stage(
    papers: List[Paper],
    query: str,
    context,
    llm_factory,
) -> List[AggregatedScoreResult]:
    """
    Stage 5: Score papers in two independent rounds.

    This implements a double-blind review process:
    - Round 1: First independent scoring of all papers
    - Round 2: Second independent scoring of all papers (no knowledge of Round 1)
    - Aggregation: Average scores from both rounds
    - overall_recommendation: "Accept" if accept_rate >= 0.5, else "Reject"

    Implementation pattern:
    - Papers are grouped by whether they have pre-downloaded markdown content
    - Papers with markdown: content is provided directly in the message
    - Papers without markdown: agent uses tools to download and read the paper
    - Two-step approach per paper:
      1. generate_str() - agent evaluates paper and creates evaluation text
      2. generate_structured() - format text as ScoreResult JSON

    Returns:
        List of AggregatedScoreResult objects with paper, scores, and acceptance decision
    """
    logger = context.logger
    logger.info("score_papers.start", data={
        "total_papers": len(papers),
        "query": query
    })

    # Separate papers by markdown availability
    papers_with_markdown = [(p, load_markdown_content(p.markdown_path))
                            for p in papers if p.markdown_path]
    papers_with_markdown = [(p, content) for p, content in papers_with_markdown if content]
    papers_without_markdown = [p for p in papers if not p.markdown_path or
                               p not in [pw[0] for pw in papers_with_markdown]]

    logger.info("score_papers.paper_groups", data={
        "with_markdown": len(papers_with_markdown),
        "without_markdown": len(papers_without_markdown)
    })

    # Request parameters for scoring
    request_params = RequestParams(
        maxTokens=8192,
        temperature=0.4,
        max_iterations=50
    )

    async def score_paper_with_markdown(
        paper: Paper,
        markdown_content: str,
        round_num: int,
        llm
    ) -> tuple[Paper, ScoreResult | None]:
        """Score a paper that has pre-downloaded markdown content."""
        try:
            message = f"""Review the following paper for the research query: {query}

Paper metadata:
- Paper ID: {paper.id}
- Title: {paper.title}
- Authors: {', '.join(paper.authors)}
- Categories: {', '.join(paper.categories)}
- Published: {paper.published}

## Paper Content (Markdown)

{markdown_content}

---

Task: Evaluate this paper according to your scoring criteria. If there are unclear mathematical formulas, you can use the arxiv-latex-mcp tool to get the LaTeX source. Provide a complete evaluation with all scores and assessments."""

            # Step 1: Get the text evaluation
            text_response = await llm.generate_str(
                message=message,
                request_params=request_params
            )

            logger.debug(f"score_papers.round{round_num}_text_response", data={
                "paper_id": paper.id,
                "response_length": len(text_response),
                "has_markdown": True
            })

            # Step 2: Format the text evaluation as structured ScoreResult
            format_prompt = f"""Based on the following paper evaluation, provide a response in JSON format matching the ScoreResult schema.

Evaluation:
{text_response}

Return ONLY valid JSON. All score fields (relevance, novelty, soundness, clarity, significance, overall_score) must be numbers between 0-10. All text fields (summary, strengths, weaknesses, recommendation) must be non-empty strings."""

            score_result = await llm.generate_structured(
                message=format_prompt,
                response_model=ScoreResult,
                request_params=RequestParams(
                    maxTokens=16384,
                    temperature=0.1,
                    use_history=False
                )
            )

            score_result.paper_id = paper.id

            logger.debug(f"score_papers.round{round_num}_scored", data={
                "paper_id": paper.id,
                "overall_score": score_result.overall_score,
                "has_markdown": True
            })

            return (paper, score_result)

        except Exception as e:
            logger.error(f"score_papers.round{round_num}_error", data={
                "paper_id": paper.id,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "has_markdown": True
            })
            return (paper, None)

    async def score_paper_without_markdown(
        paper: Paper,
        round_num: int,
        llm
    ) -> tuple[Paper, ScoreResult | None]:
        """Score a paper that needs to be downloaded by the agent."""
        try:
            message = f"""Review paper ID: {paper.id} for the research query: {query}

Paper metadata:
- Title: {paper.title}
- Authors: {', '.join(paper.authors)}
- Categories: {', '.join(paper.categories)}
- Published: {paper.published}

Task: Use the arxiv MCP server tools to download and read the paper content, then evaluate it according to your scoring criteria. Provide a complete evaluation with all scores and assessments."""

            # Step 1: Get the text evaluation
            text_response = await llm.generate_str(
                message=message,
                request_params=request_params
            )

            logger.debug(f"score_papers.round{round_num}_text_response", data={
                "paper_id": paper.id,
                "response_length": len(text_response),
                "has_markdown": False
            })

            # Step 2: Format the text evaluation as structured ScoreResult
            format_prompt = f"""Based on the following paper evaluation, provide a response in JSON format matching the ScoreResult schema.

Evaluation:
{text_response}

Return ONLY valid JSON. All score fields (relevance, novelty, soundness, clarity, significance, overall_score) must be numbers between 0-10. All text fields (summary, strengths, weaknesses, recommendation) must be non-empty strings."""

            score_result = await llm.generate_structured(
                message=format_prompt,
                response_model=ScoreResult,
                request_params=RequestParams(
                    maxTokens=16384,
                    temperature=0.1,
                    use_history=False
                )
            )

            score_result.paper_id = paper.id

            logger.debug(f"score_papers.round{round_num}_scored", data={
                "paper_id": paper.id,
                "overall_score": score_result.overall_score,
                "has_markdown": False
            })

            return (paper, score_result)

        except Exception as e:
            logger.error(f"score_papers.round{round_num}_error", data={
                "paper_id": paper.id,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "has_markdown": False
            })
            return (paper, None)

    async def run_scoring_round(round_num: int) -> List[tuple[Paper, ScoreResult | None]]:
        """Run a single round of scoring for all papers."""
        logger.info(f"score_papers.round{round_num}_start", data={"round": round_num})

        all_results = []

        # Score papers with markdown (using simplified agent)
        if papers_with_markdown:
            logger.info(f"score_papers.round{round_num}_markdown_start", data={
                "count": len(papers_with_markdown)
            })

            scorer_agent_markdown = create_paper_scorer_agent(round_num=round_num, has_markdown=True)

            async with scorer_agent_markdown as agent_ctx:
                llm = await agent_ctx.attach_llm(llm_factory)
                llm.history.clear()

                try:
                    results = await asyncio.gather(
                        *[score_paper_with_markdown(paper, content, round_num, llm)
                          for paper, content in papers_with_markdown],
                        return_exceptions=True
                    )

                    for idx, result in enumerate(results):
                        if isinstance(result, Exception):
                            logger.warning(f"score_papers.round{round_num}_markdown_exception", data={
                                "index": idx,
                                "error": str(result)
                            })
                        else:
                            all_results.append(result)

                except Exception as e:
                    logger.error(f"score_papers.round{round_num}_markdown_error", data={
                        "error": str(e)
                    })

            logger.info(f"score_papers.round{round_num}_markdown_complete", data={
                "scored": len([r for r in all_results if r[1] is not None])
            })

        # Score papers without markdown (using full agent with tools)
        if papers_without_markdown:
            logger.info(f"score_papers.round{round_num}_download_start", data={
                "count": len(papers_without_markdown)
            })

            scorer_agent_download = create_paper_scorer_agent(round_num=round_num, has_markdown=False)

            async with scorer_agent_download as agent_ctx:
                llm = await agent_ctx.attach_llm(llm_factory)
                llm.history.clear()

                try:
                    results = await asyncio.gather(
                        *[score_paper_without_markdown(paper, round_num, llm)
                          for paper in papers_without_markdown],
                        return_exceptions=True
                    )

                    for idx, result in enumerate(results):
                        if isinstance(result, Exception):
                            logger.warning(f"score_papers.round{round_num}_download_exception", data={
                                "index": idx,
                                "error": str(result)
                            })
                        else:
                            all_results.append(result)

                except Exception as e:
                    logger.error(f"score_papers.round{round_num}_download_error", data={
                        "error": str(e)
                    })

            logger.info(f"score_papers.round{round_num}_download_complete", data={
                "scored": len([r for r in all_results if r[1] is not None])
            })

        # Filter out failed results
        round_results = [(paper, score) for paper, score in all_results if score is not None]

        logger.info(f"score_papers.round{round_num}_complete", data={
            "scored": len(round_results),
            "errors": len(all_results) - len(round_results)
        })

        return round_results

    # Run both rounds sequentially
    logger.info("score_papers.running_rounds", data={"total_rounds": 2})

    round1_results = await run_scoring_round(round_num=1)
    round2_results = await run_scoring_round(round_num=2)

    logger.info("score_papers.aggregating", data={
        "round1_count": len(round1_results),
        "round2_count": len(round2_results)
    })

    # Create a mapping of paper_id to scores
    round1_map = {score.paper_id: (paper, score) for paper, score in round1_results}
    round2_map = {score.paper_id: (paper, score) for paper, score in round2_results}

    # Find papers that have scores in BOTH rounds
    common_paper_ids = set(round1_map.keys()) & set(round2_map.keys())

    scored_papers = []

    for paper_id in common_paper_ids:
        paper1, score1 = round1_map[paper_id]
        paper2, score2 = round2_map[paper_id]

        # Calculate average scores across dimensions
        avg_dimensions = {
            "relevance": (score1.relevance + score2.relevance) / 2,
            "novelty": (score1.novelty + score2.novelty) / 2,
            "soundness": (score1.soundness + score2.soundness) / 2,
            "clarity": (score1.clarity + score2.clarity) / 2,
            "significance": (score1.significance + score2.significance) / 2,
        }

        # Calculate average overall score
        avg_overall_score = (score1.overall_score + score2.overall_score) / 2

        # Calculate accept rate from recommendations
        # Parse recommendation strings to check if they start with "Accept"
        round1_accept = score1.recommendation.strip().lower().startswith("accept")
        round2_accept = score2.recommendation.strip().lower().startswith("accept")
        accept_count = sum([round1_accept, round2_accept])
        accept_rate = accept_count / 2.0

        # Determine overall recommendation based on accept rate >= 0.5
        overall_recommendation = "Accept" if accept_rate >= 0.5 else "Reject"

        # Create AggregatedScoreResult object
        scored_paper = AggregatedScoreResult(
            paper_id=paper_id,
            paper=paper1,
            round_scores=[score1, score2],
            avg_score=avg_overall_score,
            avg_dimensions=avg_dimensions,
            overall_recommendation=overall_recommendation,
            summary=score1.summary,
            strengths=score1.strengths,
            weaknesses=score1.weaknesses,
        )

        scored_papers.append(scored_paper)

        logger.debug("score_papers.aggregated", data={
            "paper_id": paper_id,
            "round1_score": score1.overall_score,
            "round2_score": score2.overall_score,
            "avg_score": avg_overall_score,
            "accept_rate": accept_rate,
            "overall_recommendation": overall_recommendation
        })

    # Log summary with acceptance statistics
    accepted_papers = [sp for sp in scored_papers if sp.overall_recommendation == "Accept"]
    logger.info("score_papers.complete", data={
        "total_papers": len(papers),
        "scored_papers": len(scored_papers),
        "dropped_papers": len(papers) - len(scored_papers),
        "accepted_papers": len(accepted_papers),
        "rejected_papers": len(scored_papers) - len(accepted_papers),
        "acceptance_rate": f"{len(accepted_papers) / len(scored_papers) * 100:.1f}%" if scored_papers else "0%",
        "avg_score_mean": sum(sp.avg_score for sp in scored_papers) / len(scored_papers) if scored_papers else 0
    })

    return scored_papers
