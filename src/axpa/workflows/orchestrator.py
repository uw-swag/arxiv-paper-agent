from mcp_agent.app import MCPApp
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from .stages import *
from datetime import datetime, timedelta
# from axpa.workflows.stages.paper_fetching import fetch_papers_stage_debug
# from mcp_agent.mcp.gen_client import gen_client


async def run_arxiv_analysis_workflow(
    query: str,
    top_k: int = 10,
    search_limit: int = 2000,
    output_format: str = "markdown",
    paper_start_time: datetime = None,
    paper_end_time: datetime = None,
):
    """
    Main orchestrator for multi-agent arXiv analysis.
    """
    app = MCPApp(name="arxiv_analysis")

    async with app.run() as agent_app:
        context = agent_app.context
        logger = context.logger

        # async with gen_client(
        #     server_name="arxiv",
        #     server_registry=app.server_registry,
        #     context=app.context,
        # ) as session:
        #     tools = await session.list_tools()
        #     print("Fetch tools:", [tool.name for tool in tools.tools])

        logger.info("orchestrator.start", data={
            "query": query,
            "top_k": top_k,
            "search_limit": search_limit,
            "output_format": output_format
        })

        llm_factory = OpenAIAugmentedLLM

        # Stage 1: Select categories
        logger.info("orchestrator.stage1_start", data={"stage": "category_selection"})
        categories = await select_categories_stage(
            query=query,
            context=context,
            llm_factory=llm_factory,
        )
        logger.info("orchestrator.stage1_complete", data={"categories": categories})

        # Stage 2: Fetch papers
        paper_start_time = datetime.now() - timedelta(days=7) if not paper_start_time else paper_start_time
        paper_end_time = datetime.now() if not paper_end_time else paper_end_time

        logger.info("orchestrator.stage2_start", data={"stage": "paper_fetching"})
        papers = await fetch_papers_from_categories_stage(
            categories=categories,
            limit=search_limit,
            context=context,
            paper_start_time=paper_start_time,
            paper_end_time=paper_end_time,
        )
        logger.info("orchestrator.stage2_complete", data={"total_papers": len(papers)})

        # Stage 3: Filter papers
        logger.info("orchestrator.stage3_start", data={"stage": "paper_filtering"})
        filtered_papers = await filter_papers_stage(
            papers=papers,
            query=query,
            context=context,
            llm_factory=llm_factory,
        )
        logger.info("orchestrator.stage3_complete", data={
            "filtered_papers": len(filtered_papers),
            "total_papers": len(papers),
            "filter_rate": f"{len(filtered_papers) / len(papers) * 100:.1f}%" if papers else "0%"
        })

        # Stage 4: Score papers (2 rounds)
        logger.info("orchestrator.stage4_start", data={"stage": "paper_scoring"})
        scored_papers = await score_papers_stage(
            papers=filtered_papers,
            query=query,
            context=context,
            llm_factory=llm_factory,
        )
        logger.info("orchestrator.stage4_complete", data={
            "scored_papers": len(scored_papers),
            "filtered_papers": len(filtered_papers),
            "avg_score_mean": sum(sp["avg_score"] for sp in scored_papers) / len(scored_papers) if scored_papers else 0
        })

        # Stage 5: Select top-k and summarize
        top_papers = sorted(scored_papers, key=lambda p: p['avg_score'], reverse=True)[:top_k]
        print(top_papers)
        raise Exception("Debug stop: Scoring complete")
        # summaries = await summarize_papers_stage(
        #     papers=top_papers,
        #     context=context,
        #     llm_factory=llm_factory,
        # )

        # # Format and return results
        # formatted_results = format_results(summaries, output_format)

        # Stage 6: Store results and report