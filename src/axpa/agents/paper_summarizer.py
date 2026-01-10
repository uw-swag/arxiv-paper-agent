from mcp_agent.agents.agent import Agent

# TODO: Build the prompt of how to summarize the paper

def create_paper_summarizer_agent() -> Agent:
    return Agent(
        name="paper_summarizer",
        instruction="""You are a paper summarizer.

        Generate a comprehensive summary with these sections:
        1. **Key Contribution**: 1-2 sentences on main contribution
        2. **Methodology**: 2-3 sentences on approach/methods
        3. **Results**: 2-3 sentences on key findings
        4. **Limitations**: 1-2 sentences on limitations (if mentioned)

        Output as markdown. Be concise but informative.
        Include paper ID and title at the top.
        """,
        server_names=["arxiv"],
    )