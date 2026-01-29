import os
os.environ["TESSDATA_PREFIX"] = "./tessdata/best"

from mcp_agent.app import MCPApp
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from .stages import *
from datetime import datetime, timedelta
from axpa.outputs.data_models import WorkflowResult
from axpa.configs import OrchestratorConfig


async def run_arxiv_analysis_workflow(
    config: OrchestratorConfig,
    additional_html_formatting: bool = False,
) -> WorkflowResult:
    """
    Main orchestrator for multi-agent arXiv analysis.

    Args:
        config: OrchestratorConfig containing query and other parameters

    Returns:
        WorkflowResult containing categories, paper counts, and summaries
    """
    app = MCPApp(name="arxiv_analysis")

    async with app.run() as agent_app:
        context = agent_app.context
        logger = context.logger

        logger.info("orchestrator.start", data={
            "query": config.query,
            "top_k": config.top_k,
            "search_limit": config.search_limit,
            "output_format": config.output_format
        })

        llm_factory = OpenAIAugmentedLLM

        # Stage 1: Select categories
        logger.info("orchestrator.stage1_start", data={"stage": "category_selection"})
        categories = await select_categories_stage(
            query=config.query,
            context=context,
            llm_factory=llm_factory,
        )
        logger.info("orchestrator.stage1_complete", data={"categories": categories})

        # Stage 2: Fetch papers
        paper_start_time = config.paper_start_time
        paper_end_time = config.paper_end_time

        logger.info("orchestrator.stage2_start", data={"stage": "paper_fetching"})
        papers = await fetch_papers_from_categories_stage(
            categories=categories,
            limit=config.search_limit,
            context=context,
            paper_start_time=paper_start_time,
            paper_end_time=paper_end_time,
        )
        logger.info("orchestrator.stage2_complete", data={"total_papers": len(papers)})

        # Stage 3: Filter papers
        logger.info("orchestrator.stage3_start", data={"stage": "paper_filtering"})
        filtered_papers = await filter_papers_stage(
            papers=papers,
            query=config.query,
            context=context,
            llm_factory=llm_factory,
        )
        logger.info("orchestrator.stage3_complete", data={
            "filtered_papers": len(filtered_papers),
            "total_papers": len(papers),
            "filter_rate": f"{len(filtered_papers) / len(papers) * 100:.1f}%" if papers else "0%"
        })

        # Stage 4: Download papers and extract to markdown
        logger.info("orchestrator.stage4_start", data={"stage": "paper_downloading"})
        downloaded_papers = await download_papers_stage(
            papers=filtered_papers,
            context=context,
        )
        logger.info("orchestrator.stage4_complete", data={
            "total_papers": len(downloaded_papers),
            "with_markdown": len([p for p in downloaded_papers if p.markdown_path])
        })

        # Stage 5: Score papers (2 rounds)
        logger.info("orchestrator.stage5_start", data={"stage": "paper_scoring"})
        scored_papers = await score_papers_stage(
            papers=downloaded_papers,
            query=config.query,
            context=context,
            llm_factory=llm_factory,
        )
        logger.info("orchestrator.stage5_complete", data={
            "scored_papers": len(scored_papers),
            "downloaded_papers": len(downloaded_papers),
            "avg_score_mean": sum(sp.avg_score for sp in scored_papers) / len(scored_papers) if scored_papers else 0,
            "accepted_papers": len([sp for sp in scored_papers if sp.overall_recommendation == "Accept"]),
        })

        # Stage 6: Select top-k accepted papers and summarize
        # Filter by acceptance first, then sort by score
        accepted_papers = [sp for sp in scored_papers if sp.overall_recommendation == "Accept"]
        top_papers = sorted(accepted_papers, key=lambda p: p.avg_score, reverse=True)[:config.top_k]

        logger.info("orchestrator.stage6_start", data={"stage": "paper_summarization"})
        summaries = await summarize_papers_stage(
            papers=top_papers,
            context=context,
            llm_factory=llm_factory,
        )
        logger.info("orchestrator.stage6_complete", data={"summaries_count": len(summaries)})

        # Create and return result
        result = WorkflowResult(
            query=config.query,
            categories=categories,
            total_papers=len(papers),
            filtered_papers=len(filtered_papers),
            scored_papers=len(scored_papers),
            accepted_papers=len(accepted_papers),
            summaries=summaries,
        )

        if additional_html_formatting:
            logger.info("orchestrator.stage7_start", data={"stage": "additional_html_formatting"})
            html_format_result = await html_formatting_stage(result, context, llm_factory)
            if html_format_result:
                result = html_format_result
            logger.info("orchestrator.stage7_complete", data={"stage": "additional_html_formatting"})

        logger.info("orchestrator.complete", data={
            "query": config.query,
            "summaries": len(summaries)
        })

        return result
