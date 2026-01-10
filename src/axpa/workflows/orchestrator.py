from mcp_agent.app import MCPApp
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from .stages import *
from datetime import datetime, timedelta
# from axpa.workflows.stages.paper_fetching import fetch_papers_stage_debug


async def run_arxiv_analysis_workflow(
    query: str,
    top_k: int = 10,
    search_limit: int = 2000,
    output_format: str = "markdown",
    paper_start_time: datetime = None,
    paper_end_time: datetime = None,
) -> dict:
    """
    Main orchestrator for multi-agent arXiv analysis.
    """
    app = MCPApp(name="arxiv_analysis")

    async with app.run() as agent_app:
        context = agent_app.context
        print(f"context: {context}")
        llm_factory = OpenAIAugmentedLLM

        # Stage 1: Select categories
        categories = await select_categories_stage(
            query=query,
            context=context,
            llm_factory=llm_factory,
        )

        # Stage 2: Fetch papers
        paper_start_time = datetime.now() - timedelta(days=7) if not paper_start_time else paper_start_time
        paper_end_time = datetime.now() if not paper_end_time else paper_end_time
        
        papers = await fetch_papers_from_categories_stage(
            categories=categories,
            limit=search_limit,
            context=context,
            paper_start_time=paper_start_time,
            paper_end_time=paper_end_time,
        )

        # Stage 3: Filter papers
        filtered_papers = await filter_papers_stage(
            papers=papers,
            query=query,
            context=context,
            llm_factory=llm_factory,
        )
        raise Exception("Stop here")

        # Stage 4: Score papers (2 rounds)
        scored_papers = await score_papers_stage(
            papers=filtered_papers,
            query=query,
            context=context,
            llm_factory=llm_factory,
        )

        # Stage 5: Select top-k and summarize
        top_papers = sorted(scored_papers, key=lambda p: p['avg_score'], reverse=True)[:top_k]
        summaries = await summarize_papers_stage(
            papers=top_papers,
            context=context,
            llm_factory=llm_factory,
        )

        # Format and return results
        return format_results(summaries, output_format)