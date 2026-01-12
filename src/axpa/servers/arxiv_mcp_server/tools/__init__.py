"""Tool definitions for the arXiv MCP server."""

from .search import search_tool, handle_search
from .download import download_tool, handle_download
from .list_papers import list_tool, handle_list_papers


__all__ = [
    "search_tool",
    "download_tool",
    "list_tool",
    "handle_search",
    "handle_download",
    "handle_list_papers",
]
