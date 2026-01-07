from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any

from mcp_agent.app import MCPApp
from mcp_agent.mcp.gen_client import gen_client

from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM


def _extract_text_content(result: Any) -> str:
    parts: list[str] = []
    for c in getattr(result, "content", []) or []:
        t = getattr(c, "text", None)
        if isinstance(t, str) and t.strip():
            parts.append(t)
    return "\n".join(parts).strip()


def _loads_json(s: str) -> Any:
    try:
        return json.loads(s)
    except Exception:
        return None


def _parse_csv_list(s: str) -> list[str]:
    s = (s or "").strip()
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x.strip()]

async def agent_llm_flow(
    server_name: str,
    query: str,
    categories: list[str],
    limit: int,
) -> None:
    """
    LLM-powered agent:
      - LLM decides how to use tools, but you explicitly have:
          search_arxiv(query, categories, limit)
          get_paper_details(paper_id, include_content)
          search_and_summarize(query, categories, limit)
    """
    app = MCPApp(name="agent_arxiv_llm")

    async with app.run():
        agent = Agent(
            name="agent_arxiv_researcher",
            instruction=(
                "You are a research assistant.\n"
                "Use the available MCP tools to find and analyze papers.\n"
                "Your tools:\n"
                "  - search_arxiv(query, categories, limit): returns JSON list of recent papers (past week)\n"
                "  - get_paper_details(paper_id, include_content): returns Markdown for a specific paper\n"
                "  - search_and_summarize(query, categories, limit): returns Markdown list\n"
                "When given a task:\n"
                "  1) call search_arxiv first\n"
                "  2) pick the best papers and call get_paper_details on 1-3 of them\n"
                "  3) write a concise report with IDs and why relevant\n"
            ),
            server_names=[server_name],
        )

        async with agent:
            llm = await agent.attach_llm(OpenAIAugmentedLLM)

            prompt = (
                f"Find up to {limit} papers from the last week for query: {query!r}.\n"
                f"Filter categories: {categories if categories else 'ANY'}.\n"
                "For each selected paper:\n"
                "  - arXiv id\n"
                "  - title\n"
                "  - one-sentence contribution (based on abstract)\n"
                "  - why it’s relevant to the query\n"
                "Then recommend 3 follow-up reading directions.\n"
                "Use tools; do not guess arXiv IDs.\n"
            )

            answer = await llm.generate_str(prompt)
            print(answer)


async def main() -> None:
    ap = argparse.ArgumentParser(description="mcp-agent client for your FastMCP arXiv server")
    ap.add_argument(
        "--server-name",
        default="arxiv",
        help="Server name as registered in mcp_agent.config.yaml (default: arxiv)",
    )
    ap.add_argument(
        "--mode",
        choices=["tools_only", "agent_llm"],
        default="tools_only",
        help="tools_only requires no LLM; agent_llm uses OpenAIAugmentedLLM",
    )
    ap.add_argument("--query", default="LLM-generated code security", help="Search query string")
    ap.add_argument(
        "--categories",
        default="cs.CR,cs.SE",
        help="Comma-separated arXiv category codes (e.g., cs.CR,cs.SE). Empty means no filter.",
    )
    ap.add_argument("--limit", type=int, default=5, help="How many papers to return")
    ap.add_argument(
        "--include-content",
        action="store_true",
        help="Whether to include PDF text preview for get_paper_details (slower).",
    )
    args = ap.parse_args()

    categories = _parse_csv_list(args.categories)

    if args.mode == "tools_only":
        await tools_only_flow(
            server_name=args.server_name,
            query=args.query,
            categories=categories,
            limit=args.limit,
            include_content=args.include_content,
        )
    else:
        await agent_llm_flow(
            server_name=args.server_name,
            query=args.query,
            categories=categories,
            limit=args.limit,
        )


if __name__ == "__main__":
    asyncio.run(main())
