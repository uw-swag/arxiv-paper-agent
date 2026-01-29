from .html_formatter import HtmlFormatter
from .markdown_formatter import MarkdownFormatter
from .base import BaseFormatter

__all__ = [
    "HtmlFormatter",
    "MarkdownFormatter",
]


def load_formatter(format: str) -> BaseFormatter:
    if format == "markdown":
        return MarkdownFormatter()
    elif format == "html":
        return HtmlFormatter()
    else:
        raise ValueError(f"Unsupported format: {format}")