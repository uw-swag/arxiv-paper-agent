from mcp_agent.agents.agent import Agent


def create_paper_filter_agent() -> Agent:
    return Agent(
        name="paper_filter",
        instruction="""You are a paper quality filter.

        Given a paper (title, abstract, metadata):
        1. Evaluate relevance to the research query
        2. Check paper quality:
           - Is abstract substantive (>100 words)?
           - Does it describe clear methodology?
           - Does it present results/contributions?
        3. Return JSON: {
             "accept": true/false,
             "reasoning": "brief explanation",
             "relevance_score": 0-10
           }

        Be selective. Only accept high-quality, clearly relevant papers.
        """,
        server_names=["arxiv"],
    )