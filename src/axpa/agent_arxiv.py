from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any, Callable, Coroutine, Optional

from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

from axpa.category_prompt import validate_category_codes, all_category_codes

def _loads_json(s: str) -> Any:
    try:
        return json.loads(s)
    except Exception:
        return None


async def _retry_async(
    fn: Callable[[], Coroutine[Any, Any, Any]],
    *,
    name: str,
    retries: int = 5,
    delay_time: float = 1
) -> Any:
    last_exc: Optional[BaseException] = None
    for attempt in range(1, retries + 1):
        try:
            return await fn()
        except Exception as e:
            last_exc = e
            if attempt >= retries:
                break
            await asyncio.sleep(delay_time)
    raise RuntimeError(f"{name} failed after {retries} attempts") from last_exc


async def _llm_choose_categories(llm: OpenAIAugmentedLLM, query: str) -> list[str]:
    allowed = all_category_codes()
    example_json = '{"categories":["cs.SE","cs.CR"]}'

    prompt = (
        "You are selecting arXiv category codes for a search.\n\n"
        "YOU MUST USE TOOLS:\n"
        "  - First, propose 4-8 candidate category codes from ALLOWED_CODES.\n"
        "  - Then CALL the tool `describe_arxiv_categories` with those codes to read names/descriptions.\n"
        "  - Then choose the best set of codes and return ONLY JSON.\n\n"
        "Output rules:\n"
        "  - Return ONLY valid JSON.\n"
        "  - Output must be exactly: {\"categories\": [\"cs.SE\", \"cs.CR\"]}\n"
        "  - No extra keys. No explanations. No markdown.\n\n"
        f"QUERY:\n{query}\n\n"
        f"ALLOWED_CODES (must pick from these only):\n{allowed}\n\n"
        f"EXAMPLE:\n{example_json}\n"
    )

    raw = await llm.generate_str(prompt)

    data = _loads_json(raw) or {}
    cats = data.get("categories", [])
    if not isinstance(cats, list):
        cats = []

    proposed = [c.strip() for c in cats if isinstance(c, str) and c.strip()]

    valid, _ = validate_category_codes(proposed)

    if not valid:
        default = ["cs.SE", "cs.CR", "cs.AI", "cs.LG"]
        valid, _ = validate_category_codes(default)

    return valid[:6]


def _build_final_report_prompt(
    query: str,
    categories: list[str],
    search_limit: int,
    details_top_k: int,
    include_content: bool,
) -> str:
    return (
        f"Task: Find recent arXiv papers from the last week relevant to this query:\n"
        f"  QUERY: {query}\n"
        f"  CATEGORIES (filter): {categories if categories else 'ANY'}\n\n"
        f"Steps you MUST follow:\n"
        f"  1) Call search_arxiv(query={query!r}, categories={categories}, limit={search_limit}).\n"
        f"  2) From the returned JSON list, pick the best {details_top_k} papers for the query.\n"
        f"  3) Call get_paper_details(paper_id=..., include_content={include_content}) for each selected paper.\n"
        f"  4) Produce a concise report:\n"
        f"     - 1 short intro sentence\n"
        f"     - Then a numbered list of the {details_top_k} papers with:\n"
        f"         * arXiv id\n"
        f"         * title\n"
        f"         * 1-sentence contribution (based on abstract)\n"
        f"         * 1-sentence methodology (based on content)\n\n"
        f"Rules:\n"
        f"  - Do NOT guess arXiv IDs; always get them from tool outputs.\n"
        f"  - Keep it concise.\n"
        f"  - If a tool call fails, retry the tool call.\n"
    )

async def agent_llm_flow(
    server_name: str,
    query: str,
    search_limit: int,
    details_top_k: int,
    include_content: bool,
    retries: int = 5,
) -> None:

    app = MCPApp(name="agent_arxiv_llm")

    async with app.run() as agent_app:
        # context = agent_app.context
        # print(context.config)
        
        agent = Agent(
            name="arxiv_paper_agent",
            instruction=(
                "You are a research assistant.\n"
                "Use MCP tools to find and analyze papers.\n\n"
                "Available tools:\n"
                "  - search_arxiv(query: str, categories: list[str] = [], limit: int)\n"
                "  - get_paper_details(paper_id: str, include_content: bool = False)\n"
                "  - search_and_summarize(query: str, categories: list[str] = [], limit: int)\n"
                "  - describe_arxiv_categories(categories: list[str])\n\n"
                "Rules:\n"
                "  - Do not guess arXiv IDs; always get them from tools.\n"
                "  - Keep the final report concise.\n"
                "  - If a tool call fails, retry.\n"
            ),
            server_names=[server_name],
        )

        async with agent:

            llm: OpenAIAugmentedLLM = await _retry_async(
                lambda: agent.attach_llm(OpenAIAugmentedLLM),
                name="attach_llm(OpenAIAugmentedLLM)",
                retries=retries,
            )

            categories: list[str] = await _retry_async(
                lambda: _llm_choose_categories(llm, query),
                name="_llm_choose_categories",
                retries=retries,
            )

            final_prompt = _build_final_report_prompt(
                query=query,
                categories=categories,
                search_limit=search_limit,
                details_top_k=details_top_k,
                include_content=include_content,
            )

            answer: str = await _retry_async(
                lambda: llm.generate_str(final_prompt),
                name="llm.generate_str(final_prompt)",
                retries=retries,
            )

            print("\n" + "="*80)
            print("FINAL REPORT:")
            print("="*80 + "\n")
            print(answer)

async def main() -> None:
    ap = argparse.ArgumentParser(description="arXiv MCP agent client")
    ap.add_argument(
        "--server-name",
        default="arxiv",
        help="Server name is in mcp_agent.config.yaml (default: arxiv)",
    )
    ap.add_argument(
        "--query",
        default="LLM-generated code security",
        help="Search query string",
    )
    ap.add_argument(
        "--search-limit",
        type=int,
        default=100,
        help="How many papers to fetch from search_arxiv",
    )
    ap.add_argument(
        "--details-top-k",
        type=int,
        default=20,
        help="How many top papers to fetch details for",
    )
    ap.add_argument(
        "--include-content",
        action="store_true",
        help="Include PDF text preview in get_paper_details (slower).",
    )
    ap.add_argument(
        "--retries",
        type=int,
        default=5,
        help="Max retries for failing steps (default: 5)",
    )
    args = ap.parse_args()

    await agent_llm_flow(
        server_name=args.server_name,
        query=args.query,
        search_limit=args.search_limit,
        details_top_k=args.details_top_k,
        include_content=args.include_content,
        retries=args.retries,
    )


if __name__ == "__main__":
    asyncio.run(main())
