from mcp_agent.agents.agent import Agent


def create_paper_filter_agent() -> Agent:
    return Agent(
        name="paper_filter",
        instruction="""You are a paper quality filter.

        Given a paper information (title, abstract, metadata) and a research query:

        1. Evaluate relevance to the research query:
           - Does the paper directly address the query topic?
           - Are the key concepts and terminology aligned?

        2. Check paper quality:
           - Is the abstract substantive (>100 words)?
           - Does it describe clear methodology?
           - Does it present concrete results/contributions?
           - Is it a complete research paper (not just a position paper or abstract)?

        3. Provide your decision:
           - accept: true if the paper is both relevant AND high-quality
           - reasoning: Brief 1-2 sentence explanation of your decision
           - relevance_score: Score from 0-10 indicating relevance to the query

        Be selective. Only accept papers that are clearly relevant and of high quality.
        Try to make your decision based on the paper information and the query.
        But you can use any tools to help you only when you feel the current context is not enough to make a decision.
        """,
        server_names=["arxiv-mcp-server"],
    )