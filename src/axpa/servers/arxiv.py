from mcp.server.fastmcp import Context, FastMCP
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from dotenv import load_dotenv
import feedparser
import aiohttp
import asyncio
import json
import os
import io
import pypdf
from datetime import datetime, timezone, timedelta
from axpa.category_prompt import ArxivCategoryInfo
from axpa.category_prompt import ArxivCategory

load_dotenv()

# Default number of results to return
DEFAULT_RESULT_LIMIT = 100

@dataclass
class ArxivContext:
    """Context for the arXiv MCP server."""
    session: aiohttp.ClientSession

@asynccontextmanager
async def arxiv_lifespan(server: FastMCP) -> AsyncIterator[ArxivContext]:
    """
    Manages the arXiv client lifecycle.
    
    Args:
        server: The FastMCP server instance
        
    Yields:
        ArxivContext: The context containing the aiohttp session
    """
    # Create aiohttp session
    session = aiohttp.ClientSession()   
    
    try:
        yield ArxivContext(session=session)
    finally:
        # Close the session when done
        await session.close()

# Initialize FastMCP server with the arXiv context
mcp = FastMCP(
    "arxiv-mcp",
    # description="MCP server for retrieving papers from arXiv based on keywords",
    lifespan=arxiv_lifespan,
    host=os.getenv("HOST", "0.0.0.0"),
    port=os.getenv("PORT", "8060")
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
    # Format the query for arXiv API
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

def _parse_arxiv_datetime(dt_str: str) -> datetime | None:
    """
    Parse arXiv Atom datetime strings like:
      - "2025-01-06T12:34:56Z"
      - "2025-01-06T12:34:56+00:00"
    """
    if not dt_str:
        return None
    try:
        # Normalize trailing Z
        if dt_str.endswith("Z"):
            dt_str = dt_str[:-1] + "+00:00"
        return datetime.fromisoformat(dt_str)
    except Exception:
        return None
    
async def fetch_arxiv_papers_last_week_with_categories(
    session: aiohttp.ClientSession,
    query: str,
    category_filters: list[str],
    limit: int = DEFAULT_RESULT_LIMIT,
    use_updated_time: bool = False,
    fetch_multiplier: int = 10,
) -> list[dict]:
    """
    Fetch arXiv papers matching `query` that are within the past 7 days, and optionally
    filtered by arXiv category codes.

    IMPORTANT:
    - category_filters: list of category codes like ["cs.CR", "cs.SE"]
      If empty, category filtering is disabled.
    - Past week filtering is applied based on:
        - entry.published (default), OR
        - entry.updated if use_updated_time=True

    Because the arXiv API endpoint doesn't provide a strict "last 7 days" server-side filter
    for the Atom API results, we fetch more items and filter client-side.

    Returns:
        Up to `limit` paper dicts.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=7)

    prefetch = max(limit, 1) * max(fetch_multiplier, 1)

    formatted_query = query.replace(" ", "+")
    url = (
        "http://export.arxiv.org/api/query"
        f"?search_query={formatted_query}"
        f"&start=0&max_results={prefetch}"
        "&sortBy=submittedDate&sortOrder=descending"
    )

    async with session.get(url) as response:
        if response.status != 200:
            raise Exception(f"Failed to fetch papers: HTTP {response.status}")

        content = await response.text()
        feed = feedparser.parse(content)

        papers: list[dict] = []

        for entry in feed.entries:
            paper_id = entry.id.split("/abs/")[-1]
            authors = [author.name for author in entry.authors]
            entry_categories = [tag.term for tag in entry.tags] if hasattr(entry, "tags") else []

            dt_str = entry.updated if use_updated_time else entry.published
            dt = _parse_arxiv_datetime(dt_str)
            if dt is None:
                continue
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            if dt < cutoff:
                if not use_updated_time:
                    break
                continue

            if category_filters:
                if not any(cat in entry_categories for cat in category_filters):
                    continue

            paper = {
                "id": paper_id,
                "title": entry.title,
                "authors": authors,
                "summary": entry.summary,
                "published": entry.published,
                "updated": entry.updated,
                "link": entry.link,
                "pdf_link": f"http://arxiv.org/pdf/{paper_id}",
                "categories": entry_categories,
            }

            papers.append(paper)
            if len(papers) >= limit:
                break

        return papers
    
def get_category_by_code(code: str) -> ArxivCategoryInfo | None:
    for cat in ArxivCategory:
        if cat.value.code == code:
            return cat.value
    return None

async def fetch_paper_content(session: aiohttp.ClientSession, paper_id: str) -> str:
    """
    Attempt to fetch and extract the content of a paper.
    
    Args:
        session: The aiohttp session
        paper_id: The arXiv paper ID
        
    Returns:
        Extracted text from the paper or error message
    """
    try:
        pdf_url = f"http://arxiv.org/pdf/{paper_id}"
        
        async with session.get(pdf_url) as response:
            if response.status != 200:
                return f"Failed to fetch PDF: HTTP {response.status}"
            
            # Read PDF content
            pdf_content = await response.read()
            
            # Use PyPDF2 to extract text
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = pypdf.PdfReader(pdf_file)
            
            # Extract text from first few pages (full extraction could be too large)
            max_pages = min(5, len(pdf_reader.pages))
            text = ""
            
            for i in range(max_pages):
                page = pdf_reader.pages[i]
                text += page.extract_text()
            
            # Truncate if too long
            if len(text) > 5000:
                text = text[:5000] + "... [truncated]"
            
            return text
    except Exception as e:
        return f"Error extracting paper content: {str(e)}"

def format_paper_to_markdown(paper: dict, content: str = None) -> str:
    """
    Format paper metadata and content to Markdown.
    
    Args:
        paper: Paper metadata
        content: Paper content (if available)
        
    Returns:
        Markdown formatted string
    """
    md = f"# {paper['title']}\n\n"
    
    # Authors
    md += "## Authors\n"
    md += ", ".join(paper['authors']) + "\n\n"
    
    # Publication info
    md += f"**Published:** {paper['published']}\n"
    md += f"**Last Updated:** {paper['updated']}\n"
    md += f"**arXiv ID:** {paper['id']}\n"
    md += f"**Categories:** {', '.join(paper['categories'])}\n\n"
    
    # Links
    md += f"**Paper Link:** [{paper['link']}]({paper['link']})\n"
    md += f"**PDF Link:** [{paper['pdf_link']}]({paper['pdf_link']})\n\n"
    
    # Summary
    md += "## Abstract\n"
    md += paper['summary'] + "\n\n"
    
    # Content (if available)
    if content and content.startswith("Error") is False:
        md += "## Content Preview\n"
        md += "```\n" + content + "\n```\n\n"
    
    return md

@mcp.tool()
async def search_arxiv(ctx: Context, query: str, categories: list[str] = [], limit: int = DEFAULT_RESULT_LIMIT) -> str:
    """Search for papers on arXiv based on keywords.
    
    This tool searches arXiv for papers matching the provided keywords and returns
    the top results with their metadata in a structured format.
    
    Args:
        ctx: The MCP server provided context
        query: Search keywords or phrases
        limit: Maximum number of results to return (default: 100)
    """
    try:
        session = ctx.request_context.lifespan_context.session
        papers = await fetch_arxiv_papers_last_week_with_categories(
            session=session,
            query=f"all:{query}",
            category_filters=categories,
            limit=limit,
            use_updated_time=False,
        )
        
        if not papers:
            return "No papers found matching your query."
        
        # Format results as JSON
        return json.dumps(papers, indent=2)
    except Exception as e:
        return f"Error searching arXiv: {str(e)}"

@mcp.tool()
async def get_paper_details(ctx: Context, paper_id: str, include_content: bool = False) -> str:
    """Get detailed information about a specific arXiv paper.
    
    This tool retrieves detailed metadata for a specific paper and optionally
    attempts to extract its content.
    
    Args:
        ctx: The MCP server provided context
        paper_id: The arXiv paper ID (e.g., "2104.08653")
        include_content: Whether to attempt to extract paper content (default: False)
    """
    try:
        session = ctx.request_context.lifespan_context.session
        
        # Fetch paper metadata
        query = f"id:{paper_id}"
        papers = await fetch_arxiv_papers(session, query, 1)
        
        if not papers:
            return f"Paper with ID {paper_id} not found."
        
        paper = papers[0]
        
        # Fetch content if requested
        content = None
        if include_content:
            content = await fetch_paper_content(session, paper_id)
        
        # Format as Markdown
        markdown_output = format_paper_to_markdown(paper, content)
        return markdown_output
    except Exception as e:
        return f"Error retrieving paper details: {str(e)}"

@mcp.tool()
async def search_and_summarize(ctx: Context, query: str, categories: list[str] = [], limit: int = DEFAULT_RESULT_LIMIT) -> str:
    """Search arXiv and provide a comprehensive summary of the top papers.
    
    This tool searches arXiv for papers matching the provided keywords, fetches
    their metadata and content, and returns a comprehensive summary in Markdown format.
    
    Args:
        ctx: The MCP server provided context
        query: Search keywords or phrases
        limit: Maximum number of results to return (default: 5)
    """
    try:
        session = ctx.request_context.lifespan_context.session

        papers = await fetch_arxiv_papers_last_week_with_categories(
            session=session,
            query=f"all:{query}",
            category_filters=categories,
            limit=limit,
            use_updated_time=False,
        )
        
        if not papers:
            return "No papers found matching your query."
        
        # Compile results
        results = f"# arXiv Search Results for: {query}\n\n"
        results += f"Found {len(papers)} papers matching your query.\n\n"
        
        # Process each paper
        for i, paper in enumerate(papers):
            results += f"## {i+1}. {paper['title']}\n\n"
            
            # Authors
            results += "### Authors\n"
            results += ", ".join(paper['authors']) + "\n\n"
            
            # Publication info
            results += f"**Published:** {paper['published']}\n"
            results += f"**arXiv ID:** {paper['id']}\n"
            results += f"**Categories:** {', '.join(paper['categories'])}\n\n"
            
            # Links
            results += f"**Paper Link:** [{paper['link']}]({paper['link']})\n"
            results += f"**PDF Link:** [{paper['pdf_link']}]({paper['pdf_link']})\n\n"
            
            # Abstract
            results += "### Abstract\n"
            results += paper['summary'] + "\n\n"
            
            # Add separator between papers
            if i < len(papers) - 1:
                results += "---\n\n"
        
        return results
    except Exception as e:
        return f"Error searching and summarizing arXiv papers: {str(e)}"

@mcp.tool()
async def describe_arxiv_categories(
    ctx: Context,
    categories: list[str],
) -> str:
    """Get detailed descriptions of arXiv category codes.

    This tool retrieves the full name and description for specified arXiv
    category codes (e.g., cs.SE, cs.CR, cs.AI).

    Args:
        ctx: The MCP server provided context
        categories: List of arXiv category codes to look up

    Returns:
        JSON with category details including code, name, and description
    """
    results = []
    unknown = []

    for code in categories:
        info = get_category_by_code(code)
        if info:
            results.append(
                {
                    "code": info.code,
                    "name": info.name,
                    "description": info.description,
                }
            )
        else:
            unknown.append(code)

    output = {"categories": results}
    if unknown:
        output["unknown"] = unknown

    return json.dumps(output, indent=2)


async def main():
    transport = os.getenv("TRANSPORT", "stdio")
    if transport == 'sse':
        # Run the MCP server with sse transport
        await mcp.run_sse_async()
    else:
        # Run the MCP server with stdio transport
        await mcp.run_stdio_async()


if __name__ == "__main__":
    asyncio.run(main())