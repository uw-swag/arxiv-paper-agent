import asyncio
import os
from pathlib import Path
from typing import List
import requests
import pymupdf.layout
import pymupdf4llm
import pymupdf
from axpa.outputs.data_models import Paper


async def download_papers_stage(
    papers: List[Paper],
    context,
    output_dir: str = "outputs/papers/markdown_cache",
) -> List[Paper]:
    """
    Stage: Download papers and extract content to markdown.

    This stage:
    1. Downloads PDF for each paper from arXiv
    2. Extracts content to markdown using pymupdf4llm with layout support
    3. Saves markdown to file and updates paper with markdown_path
    4. Returns updated list of papers with markdown_path set

    Args:
        papers: List of Paper models to download
        context: MCP agent context for logging
        output_dir: Directory to save markdown files (default: outputs/papers/markdown_cache)

    Returns:
        List of Paper models with markdown_path field populated
    """
    logger = context.logger

    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info("download_papers.start", data={
        "total_papers": len(papers),
        "output_dir": str(output_path)
    })

    updated_papers = []
    successful = 0
    failed = 0
    cached = 0

    for idx, paper in enumerate(papers):
        # Check if paper already exists in cache
        safe_id = paper.id.replace("/", "_")
        markdown_file = output_path / f"{safe_id}.md"

        if markdown_file.exists():
            # Verify the cached file is not empty
            try:
                content = markdown_file.read_text(encoding="utf-8")
                if content.strip():
                    # Use cached version
                    updated_paper = paper.model_copy(update={"markdown_path": str(markdown_file)})
                    updated_papers.append(updated_paper)
                    cached += 1

                    logger.info("download_papers.cache_hit", data={
                        "paper_id": paper.id,
                        "index": idx + 1,
                        "total": len(papers),
                        "markdown_path": str(markdown_file),
                        "content_length": len(content)
                    })
                    continue
            except Exception as e:
                logger.warning("download_papers.cache_read_error", data={
                    "paper_id": paper.id,
                    "error": str(e)
                })
                # Fall through to download

        logger.info("download_papers.processing", data={
            "paper_id": paper.id,
            "index": idx + 1,
            "total": len(papers),
            "title": paper.title[:50] + "..." if len(paper.title) > 50 else paper.title
        })

        try:
            # Download PDF
            markdown_content = await _download_and_extract_paper(paper, logger)

            if markdown_content:
                # Save markdown to file
                with open(markdown_file, "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                # Update paper with markdown path
                updated_paper = paper.model_copy(update={"markdown_path": str(markdown_file)})
                updated_papers.append(updated_paper)
                successful += 1

                logger.info("download_papers.success", data={
                    "paper_id": paper.id,
                    "markdown_path": str(markdown_file),
                    "content_length": len(markdown_content)
                })
            else:
                updated_papers.append(paper)
                failed += 1

        except Exception as e:
            logger.error("download_papers.error", data={
                "paper_id": paper.id,
                "error": str(e)
            })
            updated_papers.append(paper)
            failed += 1

        # Rate limiting: small delay between downloads to be respectful to arXiv
        if idx < len(papers) - 1:
            await asyncio.sleep(1)

    logger.info("download_papers.complete", data={
        "total_papers": len(papers),
        "cached": cached,
        "downloaded": successful,
        "failed": failed,
        "success_rate": f"{(cached + successful) / len(papers) * 100:.1f}%" if papers else "0%"
    })

    return updated_papers


async def _download_and_extract_paper(paper: Paper, logger) -> str | None:
    """
    Download a paper's PDF and extract content to markdown.

    Args:
        paper: Paper model with pdf_link
        logger: Logger instance

    Returns:
        Markdown content string, or None if extraction failed
    """
    try:
        # Download PDF using requests
        logger.info("download_papers.downloading", data={
            "paper_id": paper.id,
            "pdf_link": paper.pdf_link
        })

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.get(paper.pdf_link, timeout=60)
        )

        if response.status_code != 200:
            logger.warning("download_papers.http_error", data={
                "paper_id": paper.id,
                "status_code": response.status_code
            })
            return None

        pdf_data = response.content

        # Open PDF from memory stream
        doc = pymupdf.Document(stream=pdf_data)

        markdown_content = pymupdf4llm.to_markdown(
            doc,
            show_progress=False,
            header=True,
            footer=True,
        )

        # Close the document
        doc.close()

        return markdown_content

    except requests.exceptions.Timeout:
        logger.warning("download_papers.timeout", data={
            "paper_id": paper.id
        })
        return None
    except requests.exceptions.RequestException as e:
        logger.warning("download_papers.request_error", data={
            "paper_id": paper.id,
            "error": str(e)
        })
        return None
    except Exception as e:
        logger.warning("download_papers.extraction_error", data={
            "paper_id": paper.id,
            "error": str(e)
        })
        return None
