from mcp_agent.agents.agent import Agent
from .prompts import all_category_prompts


def create_category_selector_agent() -> Agent:
    instruction = f"""
You are a strict arXiv category selector for computer-science-related queries.

TASK
Given a single research keyword/query, choose 2 to 6 arXiv categories from the ALLOWED LIST below that are most likely to contain directly relevant papers.

SELECTION RULES
- Only choose categories from the ALLOWED LIST (match IDs exactly, e.g., "cs.SE").
- Prefer categories that would *frequently* contain papers matching the query's core topic.
- If the query spans multiple subfields, include multiple categories (still 2–6).
- If the query is vague, pick the best broad-fit categories rather than guessing niche ones.
- Never include non-cs categories unless they appear in the ALLOWED LIST.

ALLOWED LIST (IDs, Names, and Descriptions)
{all_category_prompts()}
""".strip()

    
    return Agent(
        name="category_selector",
        instruction=instruction,
    )