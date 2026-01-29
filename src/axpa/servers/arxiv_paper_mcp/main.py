import asyncio
import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP, Context
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from dotenv import load_dotenv
import feedparser
import aiohttp
import json
import pymupdf.layout
import pymupdf
import pymupdf4llm

load_dotenv()

# Default number of results to return
DEFAULT_RESULT_LIMIT = 5

# Default cache directory for JSON page chunks
DEFAULT_JSON_CACHE_DIR = "./outputs/papers/json_cache"


@dataclass
class ArxivPaperContext:
    """Context for the arXiv Paper MCP server."""
    session: aiohttp.ClientSession


@asynccontextmanager
async def arxiv_paper_lifespan(server: FastMCP) -> AsyncIterator[ArxivPaperContext]:
    """
    Manages the arXiv paper client lifecycle.

    Args:
        server: The FastMCP server instance

    Yields:
        ArxivPaperContext: The context containing the aiohttp session
    """
    session = aiohttp.ClientSession()

    try:
        yield ArxivPaperContext(session=session)
    finally:
        await session.close()


# Initialize FastMCP server with the arXiv paper context
mcp = FastMCP(
    "arxiv-paper-mcp",
    lifespan=arxiv_paper_lifespan,
)


async def fetch_arxiv_papers(session: aiohttp.ClientSession, query: str, limit: int = DEFAULT_RESULT_LIMIT) -> list:
    """
    Fetch papers from arXiv based on the query.

    Args:
        session: The aiohttp session
        query: The search query
        limit: Maximum number of results to return

    Returns:
        List of paper metadata
    """
    formatted_query = query.replace(' ', '+')
    url = f"http://export.arxiv.org/api/query?search_query=all:{formatted_query}&start=0&max_results={limit}"

    async with session.get(url) as response:
        if response.status != 200:
            raise Exception(f"Failed to fetch papers: HTTP {response.status}")

        content = await response.text()
        feed = feedparser.parse(content)

        papers = []
        for entry in feed.entries:
            # Extract paper ID from the URL
            paper_id = entry.id.split('/abs/')[-1]

            # Format authors
            authors = [author.name for author in entry.authors]

            # Extract categories
            categories = [tag.term for tag in entry.tags] if hasattr(entry, 'tags') else []

            # Create paper metadata
            paper = {
                "id": paper_id,
                "title": entry.title,
                "authors": authors,
                "summary": entry.summary,
                "published": entry.published,
                "updated": entry.updated,
                "link": entry.link,
                "pdf_link": f"http://arxiv.org/pdf/{paper_id}",
                "categories": categories
            }

            papers.append(paper)

        return papers


def _get_cache_path(paper_id: str, cache_dir: str) -> Path:
    """Get the cache file path for a paper."""
    safe_id = paper_id.replace("/", "_")
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    return cache_path / f"{safe_id}.json"


def _load_from_cache(cache_file: Path) -> list[dict] | None:
    """Load page chunks from cache file if it exists and is valid."""
    if not cache_file.exists():
        return None

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Verify it's a list of page chunks
            if isinstance(data, list) and len(data) > 0:
                return data
    except (json.JSONDecodeError, IOError):
        pass

    return None


def _save_to_cache(cache_file: Path, page_chunks: list[dict]) -> None:
    """Save page chunks to cache file."""
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(page_chunks, f, ensure_ascii=False, indent=2)


def _extract_pages_content(page_chunks: list[dict], pages: list[int] | None) -> str:
    """
    Extract markdown content from page chunks for the specified pages.

    Args:
        page_chunks: List of page chunk dictionaries from pymupdf4llm
        pages: Optional list of 0-based page numbers. If None, returns all pages.

    Returns:
        Combined markdown content for the requested pages.
    """
    if pages is None:
        # Return all pages
        return "\n\n".join(chunk.get("text", "") for chunk in page_chunks)

    # Filter to requested pages (0-based index)
    content_parts = []
    for page_num in pages:
        if 0 <= page_num < len(page_chunks):
            content_parts.append(page_chunks[page_num].get("text", ""))

    return "\n\n".join(content_parts)


@mcp.tool()
async def search_arxiv(ctx: Context, query: str, limit: int = DEFAULT_RESULT_LIMIT) -> str:
    """Search for papers on arXiv based on keywords.

    This tool searches arXiv for papers matching the provided keywords and returns
    the top results with their metadata in a structured format.

    Args:
        ctx: The MCP server provided context
        query: Search keywords or phrases
        limit: Maximum number of results to return (default: 5)
    """
    try:
        session = ctx.request_context.lifespan_context.session
        papers = await fetch_arxiv_papers(session, query, limit)

        if not papers:
            return "No papers found matching your query."

        return json.dumps(papers, indent=2)
    except Exception as e:
        return f"Error searching arXiv: {str(e)}"


@mcp.tool()
async def get_paper_content(
    ctx: Context,
    paper_id: str,
    pages: list[int] | None = None,
) -> str:
    """Get the markdown content of a specific arXiv paper.

    This tool fetches the PDF of a paper from arXiv and extracts its content
    to markdown format using pymupdf4llm for high-quality text extraction.
    Results are cached as JSON page chunks for efficient subsequent access.

    Args:
        ctx: The MCP server provided context
        paper_id: The arXiv paper ID (e.g., "2104.08653")
        pages: Optional list of 0-based page numbers to extract. If None, extracts all pages.
    """
    try:
        cache_dir = os.getenv("JSON_CACHE_DIR", DEFAULT_JSON_CACHE_DIR)
        cache_file = _get_cache_path(paper_id, cache_dir)

        # Try to load from cache first
        page_chunks = _load_from_cache(cache_file)

        if page_chunks is not None:
            # Cache hit - extract requested pages
            return _extract_pages_content(page_chunks, pages)

        # Cache miss - download and process PDF
        session = ctx.request_context.lifespan_context.session
        pdf_url = f"http://arxiv.org/pdf/{paper_id}"

        async with session.get(pdf_url, timeout=aiohttp.ClientTimeout(total=120)) as response:
            if response.status != 200:
                return f"Failed to fetch PDF: HTTP {response.status}"

            pdf_data = await response.read()

        # Open PDF from memory stream
        doc = pymupdf.Document(stream=pdf_data)

        # Extract markdown with page_chunks=True for caching
        page_chunks = pymupdf4llm.to_markdown(
            doc,
            page_chunks=True,
            show_progress=False,
        )

        # Close the document
        doc.close()

        # Save to cache
        _save_to_cache(cache_file, page_chunks)

        # Extract and return requested pages
        return _extract_pages_content(page_chunks, pages)

    except asyncio.TimeoutError:
        return f"Error: Timeout while fetching paper {paper_id}"
    except Exception as e:
        return f"Error extracting paper content: {str(e)}"


@mcp.tool()
async def get_paper_page_count(
    ctx: Context,
    paper_id: str,
) -> str:
    """Get the page count of a specific arXiv paper.

    This tool returns the total number of pages in the paper.
    Useful for planning which pages to read.

    Args:
        ctx: The MCP server provided context
        paper_id: The arXiv paper ID (e.g., "2104.08653")
    """
    try:
        cache_dir = os.getenv("JSON_CACHE_DIR", DEFAULT_JSON_CACHE_DIR)
        cache_file = _get_cache_path(paper_id, cache_dir)

        # Try to load from cache first
        page_chunks = _load_from_cache(cache_file)

        if page_chunks is not None:
            return json.dumps({
                "paper_id": paper_id,
                "page_count": len(page_chunks),
                "cached": True
            })

        # Cache miss - need to download to get page count
        session = ctx.request_context.lifespan_context.session
        pdf_url = f"http://arxiv.org/pdf/{paper_id}"

        async with session.get(pdf_url, timeout=aiohttp.ClientTimeout(total=120)) as response:
            if response.status != 200:
                return f"Failed to fetch PDF: HTTP {response.status}"

            pdf_data = await response.read()

        # Open PDF from memory stream
        doc = pymupdf.Document(stream=pdf_data)

        # Extract markdown with page_chunks=True for caching
        page_chunks = pymupdf4llm.to_markdown(
            doc,
            page_chunks=True,
            show_progress=False,
        )

        page_count = doc.page_count
        doc.close()

        # Save to cache for future use
        _save_to_cache(cache_file, page_chunks)

        return json.dumps({
            "paper_id": paper_id,
            "page_count": page_count,
            "cached": False
        })

    except asyncio.TimeoutError:
        return f"Error: Timeout while fetching paper {paper_id}"
    except Exception as e:
        return f"Error getting page count: {str(e)}"


async def main():
    await mcp.run_stdio_async()


if __name__ == "__main__":
    asyncio.run(main())
