"""Download functionality for the arXiv MCP server."""

import arxiv
import json
from pathlib import Path
from typing import Dict, Any, List
import mcp.types as types
from ..config import Settings
import logging

logger = logging.getLogger("arxiv-mcp-server")
settings = Settings()


download_tool = types.Tool(
    name="download_paper",
    description="Download a paper PDF from arXiv. After download, use pdf-reader-mcp tools to read the PDF content.",
    inputSchema={
        "type": "object",
        "properties": {
            "paper_id": {
                "type": "string",
                "description": "The arXiv ID of the paper to download",
            },
        },
        "required": ["paper_id"],
    },
)


def get_paper_path(paper_id: str, suffix: str = ".pdf") -> Path:
    """Get the absolute file path for a paper with given suffix."""
    storage_path = Path(settings.STORAGE_PATH)
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path / f"{paper_id}{suffix}"


async def handle_download(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle paper download requests."""
    try:
        paper_id = arguments["paper_id"]
        pdf_path = get_paper_path(paper_id, ".pdf")

        # Check if paper is already downloaded
        if pdf_path.exists():
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "status": "success",
                            "message": "Paper already downloaded",
                            "pdf_path": str(pdf_path),
                        }
                    ),
                )
            ]

        # Download PDF
        logger.info(f"Downloading paper {paper_id}")
        client = arxiv.Client()
        paper = next(client.results(arxiv.Search(id_list=[paper_id])))
        paper.download_pdf(dirpath=pdf_path.parent, filename=pdf_path.name)

        logger.info(f"Download completed for {paper_id}")
        return [
            types.TextContent(
                type="text",
                text=json.dumps(
                    {
                        "status": "success",
                        "message": "Paper downloaded successfully",
                        "pdf_path": str(pdf_path),
                    }
                ),
            )
        ]

    except StopIteration:
        return [
            types.TextContent(
                type="text",
                text=json.dumps(
                    {
                        "status": "error",
                        "message": f"Paper {paper_id} not found on arXiv",
                    }
                ),
            )
        ]
    except Exception as e:
        logger.error(f"Download failed for {paper_id}: {str(e)}")
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"status": "error", "message": f"Error: {str(e)}"}),
            )
        ]
