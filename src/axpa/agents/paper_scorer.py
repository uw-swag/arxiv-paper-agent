from mcp_agent.agents.agent import Agent


# TODO: Build the prompt of paper scorer agent based on the conference paper evaluation criteria
def create_paper_scorer_agent(round_num: int = 1) -> Agent:
    return Agent(
        name=f"paper_scorer_round{round_num}",
        instruction=f"""You are a paper reviewer (Round {round_num}).

        Score the paper on these dimensions (0-10 scale):
        1. **Relevance**: How relevant to the research query?
        2. **Novelty**: How novel/original is the contribution?
        3. **Methodology**: How sound is the methodology?
        4. **Clarity**: How clear is the presentation?

        Return JSON: {{
          "scores": {{
            "relevance": 8,
            "novelty": 7,
            "methodology": 9,
            "clarity": 8
          }},
          "overall_score": 8.0,
          "justification": "Brief explanation..."
        }}

        Be objective and consistent. Judge based on the paper.
        """,
        server_names=["arxiv"],
    )