from axpa.agents.paper_filter import create_paper_filter_agent
from axpa.outputs.data_models import Paper

from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.parallel.fan_in import FanInInput
from mcp_agent.workflows.parallel.parallel_llm import ParallelLLM

from typing import List
import json


def aggregate_as_markdown(messages: FanInInput) -> str:
    blocks = []
    for source, outputs in messages.items():
        lines = "\n".join(str(item) for item in outputs)
        blocks.append(f"### {source}\n{lines}")
    return "\n\n".join(blocks)



async def filter_papers_stage(
    papers: List[Paper],
    query: str,
    context,
    llm_factory,
) -> List[Paper]:
    """
    Stage 3: Filter papers in parallel.

    Creates one filter agent per paper, runs in parallel.
    Returns only accepted papers.
    """
    # Create filter agents dynamically
    filter_agents = [
        create_paper_filter_agent() for _ in papers
    ]

    # Create aggregator agent
    aggregator = Agent(
        name="filter_aggregator",
        instruction="""Aggregate filter results.
        Return JSON list of accepted papers with reasoning."""
    )

    # TODO: Verify the deterministic_aggregator is correct and implement it
    deterministic_aggregator = aggregate_as_markdown

    # Create parallel workflow
    parallel = ParallelLLM(
        fan_in_agent=aggregator,
        fan_out_agents=filter_agents,
        llm_factory=llm_factory,
    )

    # Prepare messages
    messages = [
        f"Query: {query}\n\nPaper:\n{paper.model_dump_json(indent=2)}"
        for paper in papers
    ]

    # FIXME: Execute those messages in parallel
    result = await parallel.generate_str(messages)

    # Parse and return accepted papers
    accepted_papers = parse_filter_results(result, papers)
    print(f"accepted_papers: {accepted_papers}")
    raise Exception("Stop here")
    return accepted_papers


def parse_filter_results(result: str, papers: List[Paper]) -> List[Paper]:
    """
    Parse the filter results and return the accepted papers.
    """
    accepted_papers = []
    for paper in papers:
        if paper.id in result:
            accepted_papers.append(paper)
    return accepted_papers