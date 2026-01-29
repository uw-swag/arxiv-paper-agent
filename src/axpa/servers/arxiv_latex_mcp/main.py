import asyncio
from mcp.server.fastmcp import FastMCP
import json
import os
from arxiv_to_prompt import process_latex_source


mcp = FastMCP(
    "arxiv-latex-mcp",
)


@mcp.tool()
async def get_paper_details(paper_id: str, keep_comments: bool = False, include_appendix: bool = True) -> str:
    """Get the LaTeX code of a specific arXiv paper.
    
    This tool get a flattened LaTeX code of a paper from arXiv ID for precise interpretation of mathematical expressions.
    
    Args:
        paper_id: The arXiv ID of the paper
        keep_comments: Whether to keep the comments in the LaTeX code
        include_appendix: Whether to include the appendix of the paper
    """
    try:
        cache_dir = os.getenv("PAPER_CACHE_DIR", "./outputs/papers/latex_cache")
        prompt = process_latex_source(paper_id, keep_comments=keep_comments, remove_appendix_section=not include_appendix, cache_dir=cache_dir)
        instructions = """

IMPORTANT INSTRUCTIONS FOR RENDERING:
When discussing this paper, please use dollar sign notation ($...$) for inline equations and double dollar signs ($$...$$) for display equations when providing responses that include LaTeX mathematical expressions.
"""

        response = {
            "status": "success",
            "result": prompt + instructions
        }

        # Format the result as JSON
        return json.dumps(response, indent=2)
    except Exception as e:
        response = {
            "status": "error",
            "result": f"Error getting the LaTeX code of the paper: {str(e)}, please try to download the paper using the `arxiv-mcp-server_download_paper` tool, and then use pdf-reader-mcp tools to read the paper content.",
        }

        # Format the result as JSON
        return json.dumps(response, indent=2)

async def main():
    await mcp.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())