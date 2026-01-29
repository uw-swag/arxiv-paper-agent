"""Tests for the arXiv Paper MCP server."""

import json
import os
from pathlib import Path
import pytest
from axpa.servers.arxiv_paper_mcp.main import (
    fetch_arxiv_papers,
    _get_cache_path,
    _load_from_cache,
    _save_to_cache,
    _extract_pages_content,
)


# Test paper ID provided by user
TEST_PAPER_ID = "2503.09573"

# Test cache directory
TEST_CACHE_DIR = "./outputs/papers/test_json_cache"


class TestFetchArxivPapers:
    """Tests for the fetch_arxiv_papers function."""

    async def test_fetch_papers_returns_list(self, aiohttp_session):
        """Test that fetch_arxiv_papers returns a list of papers."""
        papers = await fetch_arxiv_papers(aiohttp_session, "machine learning", limit=2)

        assert isinstance(papers, list)
        assert len(papers) <= 2

    async def test_fetch_papers_has_required_fields(self, aiohttp_session):
        """Test that each paper has all required fields."""
        papers = await fetch_arxiv_papers(aiohttp_session, "neural network", limit=1)

        assert len(papers) > 0
        paper = papers[0]

        required_fields = ["id", "title", "authors", "summary", "published", "updated", "link", "pdf_link", "categories"]
        for field in required_fields:
            assert field in paper, f"Missing field: {field}"

    async def test_fetch_specific_paper_by_title(self, aiohttp_session):
        """Test fetching a specific paper by title keywords."""
        # Use a unique title keyword from the test paper instead of ID search
        papers = await fetch_arxiv_papers(aiohttp_session, "MCP-Zero", limit=5)

        assert len(papers) > 0
        # Check that we got some results with reasonable structure
        assert "id" in papers[0]

    async def test_fetch_papers_empty_query(self, aiohttp_session):
        """Test that an empty or very specific query might return no results."""
        # Using a very specific nonsense query that should return no results
        papers = await fetch_arxiv_papers(aiohttp_session, "xyzabc123nonsensequery456", limit=1)

        assert isinstance(papers, list)


class TestGetPaperContentDirect:
    """Tests for getting paper content directly (without MCP context)."""

    async def test_download_and_extract_paper(self, aiohttp_session):
        """Test downloading and extracting a paper's content."""
        import pymupdf
        import pymupdf4llm
        import aiohttp

        pdf_url = f"http://arxiv.org/pdf/{TEST_PAPER_ID}"

        async with aiohttp_session.get(pdf_url, timeout=aiohttp.ClientTimeout(total=120)) as response:
            assert response.status == 200, f"Failed to fetch PDF: HTTP {response.status}"
            pdf_data = await response.read()

        # Open PDF from memory stream
        doc = pymupdf.Document(stream=pdf_data)

        # Extract markdown
        markdown_content = pymupdf4llm.to_markdown(
            doc,
            pages=[0],  # Just first page for speed
            show_progress=False,
        )

        doc.close()

        assert isinstance(markdown_content, str)
        assert len(markdown_content) > 0

    async def test_extract_specific_pages(self, aiohttp_session):
        """Test extracting specific pages from a paper."""
        import pymupdf
        import pymupdf4llm
        import aiohttp

        pdf_url = f"http://arxiv.org/pdf/{TEST_PAPER_ID}"

        async with aiohttp_session.get(pdf_url, timeout=aiohttp.ClientTimeout(total=120)) as response:
            pdf_data = await response.read()

        doc = pymupdf.Document(stream=pdf_data)

        # Extract first two pages
        markdown_content = pymupdf4llm.to_markdown(
            doc,
            pages=[0, 1],
            show_progress=False,
        )

        doc.close()

        assert isinstance(markdown_content, str)
        assert len(markdown_content) > 0

    async def test_extract_all_pages(self, aiohttp_session):
        """Test extracting all pages from a paper."""
        import pymupdf
        import pymupdf4llm
        import aiohttp

        pdf_url = f"http://arxiv.org/pdf/{TEST_PAPER_ID}"

        async with aiohttp_session.get(pdf_url, timeout=aiohttp.ClientTimeout(total=120)) as response:
            pdf_data = await response.read()

        doc = pymupdf.Document(stream=pdf_data)

        # Extract all pages (pages=None)
        markdown_content = pymupdf4llm.to_markdown(
            doc,
            pages=None,
            show_progress=False,
        )

        doc.close()

        assert isinstance(markdown_content, str)
        assert len(markdown_content) > 100  # Should have substantial content


class TestSearchArxivIntegration:
    """Integration tests for search functionality."""

    async def test_search_returns_valid_json(self, aiohttp_session):
        """Test that search returns valid JSON."""
        papers = await fetch_arxiv_papers(aiohttp_session, "transformer attention", limit=3)

        # Simulate what search_arxiv does
        result = json.dumps(papers, indent=2)

        # Should be valid JSON
        parsed = json.loads(result)
        assert isinstance(parsed, list)

    async def test_search_respects_limit(self, aiohttp_session):
        """Test that search respects the limit parameter."""
        limit = 3
        papers = await fetch_arxiv_papers(aiohttp_session, "deep learning", limit=limit)

        assert len(papers) <= limit


class TestPaperMetadata:
    """Tests for paper metadata structure."""

    async def test_paper_id_format(self, aiohttp_session):
        """Test that paper IDs are in expected format."""
        papers = await fetch_arxiv_papers(aiohttp_session, "large language model", limit=1)

        assert len(papers) > 0
        paper_id = papers[0]["id"]
        # arXiv IDs are typically in format YYMM.NNNNN or category/YYMMNNN
        assert len(paper_id) > 0
        # Should contain digits
        assert any(c.isdigit() for c in paper_id)

    async def test_pdf_link_format(self, aiohttp_session):
        """Test that PDF links are properly formatted."""
        papers = await fetch_arxiv_papers(aiohttp_session, "neural network", limit=1)

        assert len(papers) > 0
        pdf_link = papers[0]["pdf_link"]
        assert pdf_link.startswith("http://arxiv.org/pdf/")

    async def test_authors_is_list(self, aiohttp_session):
        """Test that authors field is a list."""
        papers = await fetch_arxiv_papers(aiohttp_session, "reinforcement learning", limit=1)

        if papers:
            authors = papers[0]["authors"]
            assert isinstance(authors, list)

    async def test_categories_is_list(self, aiohttp_session):
        """Test that categories field is a list."""
        papers = await fetch_arxiv_papers(aiohttp_session, "computer vision", limit=1)

        if papers:
            categories = papers[0]["categories"]
            assert isinstance(categories, list)


class TestCacheHelperFunctions:
    """Tests for caching helper functions."""

    def test_get_cache_path_creates_directory(self):
        """Test that _get_cache_path creates the cache directory."""
        cache_path = _get_cache_path(TEST_PAPER_ID, TEST_CACHE_DIR)

        assert cache_path.parent.exists()
        assert cache_path.name == f"{TEST_PAPER_ID}.json"

    def test_get_cache_path_handles_slash_in_id(self):
        """Test that _get_cache_path handles paper IDs with slashes."""
        paper_id_with_slash = "cs.AI/0001001"
        cache_path = _get_cache_path(paper_id_with_slash, TEST_CACHE_DIR)

        # Slash should be replaced with underscore
        assert "/" not in cache_path.name
        assert cache_path.name == "cs.AI_0001001.json"

    def test_save_and_load_cache(self):
        """Test saving and loading page chunks from cache."""
        # Create test page chunks
        test_chunks = [
            {"text": "Page 1 content", "metadata": {"page_number": 1}},
            {"text": "Page 2 content", "metadata": {"page_number": 2}},
            {"text": "Page 3 content", "metadata": {"page_number": 3}},
        ]

        cache_file = _get_cache_path("test_paper_cache", TEST_CACHE_DIR)

        # Save to cache
        _save_to_cache(cache_file, test_chunks)

        # Verify file exists
        assert cache_file.exists()

        # Load from cache
        loaded_chunks = _load_from_cache(cache_file)

        assert loaded_chunks is not None
        assert len(loaded_chunks) == 3
        assert loaded_chunks[0]["text"] == "Page 1 content"
        assert loaded_chunks[2]["text"] == "Page 3 content"

    def test_load_from_cache_returns_none_for_missing_file(self):
        """Test that _load_from_cache returns None for non-existent file."""
        cache_file = Path(TEST_CACHE_DIR) / "nonexistent_paper.json"

        result = _load_from_cache(cache_file)

        assert result is None

    def test_extract_pages_content_all_pages(self):
        """Test extracting all pages content."""
        test_chunks = [
            {"text": "Page 1 content"},
            {"text": "Page 2 content"},
            {"text": "Page 3 content"},
        ]

        result = _extract_pages_content(test_chunks, None)

        assert "Page 1 content" in result
        assert "Page 2 content" in result
        assert "Page 3 content" in result

    def test_extract_pages_content_specific_pages(self):
        """Test extracting specific pages content."""
        test_chunks = [
            {"text": "Page 1 content"},
            {"text": "Page 2 content"},
            {"text": "Page 3 content"},
        ]

        # Extract only pages 0 and 2 (first and third)
        result = _extract_pages_content(test_chunks, [0, 2])

        assert "Page 1 content" in result
        assert "Page 2 content" not in result
        assert "Page 3 content" in result

    def test_extract_pages_content_out_of_range(self):
        """Test extracting pages with out-of-range indices."""
        test_chunks = [
            {"text": "Page 1 content"},
            {"text": "Page 2 content"},
        ]

        # Request page 10 which doesn't exist
        result = _extract_pages_content(test_chunks, [0, 10])

        assert "Page 1 content" in result
        # Should not crash, just skip the invalid page


class TestCachingIntegration:
    """Integration tests for caching with real paper downloads."""

    async def test_download_and_cache_paper(self, aiohttp_session):
        """Test downloading a paper and caching it as JSON page chunks."""
        import pymupdf
        import pymupdf4llm
        import aiohttp

        pdf_url = f"http://arxiv.org/pdf/{TEST_PAPER_ID}"

        async with aiohttp_session.get(pdf_url, timeout=aiohttp.ClientTimeout(total=120)) as response:
            assert response.status == 200
            pdf_data = await response.read()

        # Open PDF from memory stream
        doc = pymupdf.Document(stream=pdf_data)

        # Extract with page_chunks=True
        page_chunks = pymupdf4llm.to_markdown(
            doc,
            page_chunks=True,
            show_progress=False,
        )

        doc.close()

        # Verify page_chunks structure
        assert isinstance(page_chunks, list)
        assert len(page_chunks) > 0

        # Each chunk should have 'text' key
        for chunk in page_chunks:
            assert "text" in chunk
            assert isinstance(chunk["text"], str)

        # Save to cache
        cache_file = _get_cache_path(TEST_PAPER_ID, TEST_CACHE_DIR)
        _save_to_cache(cache_file, page_chunks)

        # Verify cache file exists and is valid JSON
        assert cache_file.exists()

        with open(cache_file, "r", encoding="utf-8") as f:
            cached_data = json.load(f)

        assert isinstance(cached_data, list)
        assert len(cached_data) == len(page_chunks)

        print(f"\nCache file created at: {cache_file}")
        print(f"Total pages cached: {len(page_chunks)}")
        print(f"Cache file size: {cache_file.stat().st_size} bytes")

    async def test_load_cached_paper_and_extract_pages(self, aiohttp_session):
        """Test loading a cached paper and extracting specific pages."""
        cache_file = _get_cache_path(TEST_PAPER_ID, TEST_CACHE_DIR)

        # This test depends on test_download_and_cache_paper running first
        # If cache doesn't exist, download it first
        if not cache_file.exists():
            import pymupdf
            import pymupdf4llm
            import aiohttp

            pdf_url = f"http://arxiv.org/pdf/{TEST_PAPER_ID}"

            async with aiohttp_session.get(pdf_url, timeout=aiohttp.ClientTimeout(total=120)) as response:
                pdf_data = await response.read()

            doc = pymupdf.Document(stream=pdf_data)
            page_chunks = pymupdf4llm.to_markdown(doc, page_chunks=True, show_progress=False)
            doc.close()
            _save_to_cache(cache_file, page_chunks)

        # Load from cache
        page_chunks = _load_from_cache(cache_file)
        assert page_chunks is not None

        # Extract first page only
        first_page_content = _extract_pages_content(page_chunks, [0])
        assert len(first_page_content) > 0

        # Extract first 3 pages
        first_three_pages = _extract_pages_content(page_chunks, [0, 1, 2])
        assert len(first_three_pages) > len(first_page_content)

        # Extract all pages
        all_pages = _extract_pages_content(page_chunks, None)
        assert len(all_pages) >= len(first_three_pages)

        print(f"\nFirst page content length: {len(first_page_content)}")
        print(f"First 3 pages content length: {len(first_three_pages)}")
        print(f"All pages content length: {len(all_pages)}")

    async def test_page_chunks_metadata_structure(self, aiohttp_session):
        """Test that page chunks have the expected metadata structure."""
        cache_file = _get_cache_path(TEST_PAPER_ID, TEST_CACHE_DIR)

        # Ensure cache exists
        if not cache_file.exists():
            import pymupdf
            import pymupdf4llm
            import aiohttp

            pdf_url = f"http://arxiv.org/pdf/{TEST_PAPER_ID}"

            async with aiohttp_session.get(pdf_url, timeout=aiohttp.ClientTimeout(total=120)) as response:
                pdf_data = await response.read()

            doc = pymupdf.Document(stream=pdf_data)
            page_chunks = pymupdf4llm.to_markdown(doc, page_chunks=True, show_progress=False)
            doc.close()
            _save_to_cache(cache_file, page_chunks)

        # Load and inspect structure
        page_chunks = _load_from_cache(cache_file)
        assert page_chunks is not None

        # Check first page chunk structure
        first_chunk = page_chunks[0]

        print(f"\nPage chunk keys: {list(first_chunk.keys())}")

        # Required key
        assert "text" in first_chunk

        # Optional keys that may be present with page_chunks=True
        optional_keys = ["metadata", "toc_items", "tables", "images", "graphics"]
        present_keys = [k for k in optional_keys if k in first_chunk]
        print(f"Optional keys present: {present_keys}")

        # If metadata exists, check its structure
        if "metadata" in first_chunk:
            metadata = first_chunk["metadata"]
            print(f"Metadata keys: {list(metadata.keys())}")
