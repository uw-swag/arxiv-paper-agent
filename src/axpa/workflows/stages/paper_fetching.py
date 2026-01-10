import aiohttp
import asyncio
import feedparser
from datetime import datetime, timezone, timedelta
from typing import List
from axpa.outputs.data_models import Paper


def _parse_arxiv_datetime(dt_str: str) -> datetime | None:
    """Parse arXiv datetime strings."""
    if not dt_str:
        return None
    try:
        # Normalize trailing Z
        if dt_str.endswith("Z"):
            dt_str = dt_str[:-1] + "+00:00"
        return datetime.fromisoformat(dt_str)
    except Exception:
        return None


async def fetch_papers_from_categories_stage(
    categories: List[str],
    limit: int,
    context,
    paper_start_time: datetime,
    paper_end_time: datetime,
) -> List[Paper]:
    """
    Stage 2: Fetch papers from specified categories within a time range.

    This stage:
    1. Fetches papers from each category using arXiv API
    2. Filters papers by the specified time range (paper_start_time to paper_end_time)
    3. Deduplicates papers (papers can appear in multiple categories)
    4. Returns aggregated list of unique papers

    Args:
        categories: List of arXiv category codes (e.g., ["cs.SE", "cs.AI"])
        limit: Maximum total number of papers to return
        context: MCP agent context (not used, kept for consistency)
        paper_start_time: Start of time range (inclusive)
        paper_end_time: End of time range (inclusive)

    Returns:
        List of Paper models, deduplicated and sorted by published date (newest first)
    """
    session = aiohttp.ClientSession()

    try:
        all_papers = []
        seen_ids = set()

        # Ensure timezone aware
        if paper_start_time.tzinfo is None:
            paper_start_time = paper_start_time.replace(tzinfo=timezone.utc)
        if paper_end_time.tzinfo is None:
            paper_end_time = paper_end_time.replace(tzinfo=timezone.utc)
        
        limit_per_category = 2000

        for category in categories:
            try:
                # Build arXiv API query for this category
                # Use cat:category_code to search by category
                query = f"cat:{category}"
                url = (
                    "http://export.arxiv.org/api/query"
                    f"?search_query={query}"
                    f"&start=0&max_results={limit_per_category}"
                    "&sortBy=submittedDate&sortOrder=descending"
                )

                # Fetch from arXiv API
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"Failed to fetch papers for category {category}: HTTP {response.status}")
                        continue

                    content = await response.text()
                    feed = feedparser.parse(content)

                    # Process each entry
                    for entry in feed.entries:
                        paper_id = entry.id.split("/abs/")[-1]

                        # Skip if already seen (deduplication)
                        if paper_id in seen_ids:
                            continue

                        # Parse published date
                        published_dt = _parse_arxiv_datetime(entry.published)
                        if published_dt is None:
                            continue

                        # Ensure timezone aware
                        if published_dt.tzinfo is None:
                            published_dt = published_dt.replace(tzinfo=timezone.utc)

                        # Filter by time range
                        if published_dt < paper_start_time or published_dt > paper_end_time:
                            continue

                        # Extract paper metadata
                        authors = [author.name for author in entry.authors]
                        entry_categories = [tag.term for tag in entry.tags] if hasattr(entry, "tags") else []

                        # Create Paper model instance
                        paper = Paper(
                            id=paper_id,
                            title=entry.title,
                            authors=authors,
                            abstract=entry.summary,  # arXiv calls it "summary", our model uses "abstract"
                            categories=entry_categories,
                            published=entry.published,
                            pdf_link=f"http://arxiv.org/pdf/{paper_id}",
                        )

                        all_papers.append(paper)
                        seen_ids.add(paper_id)

                        # Stop if we've reached the limit
                        if len(all_papers) >= limit:
                            break

                # Stop if we've reached the limit
                if len(all_papers) >= limit:
                    break

            except Exception as e:
                # Log error but continue with other categories
                print(f"Error fetching papers for category {category}: {str(e)}")
                continue

        # Sort by published date (newest first)
        all_papers.sort(
            key=lambda p: _parse_arxiv_datetime(p.published) or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True
        )

        # Return up to limit papers
        return all_papers[:limit]

    finally:
        await session.close()


async def fetch_papers_stage_debug(
    categories: List[str],
    limit: int,
    context,
    paper_start_time: datetime,
    paper_end_time: datetime,
) -> dict:
    """
    Debug stage: Fetch papers from categories to analyze recent 7-day activity.

    This stage fetches up to 3000 papers per category and shows statistics
    about how many papers were published in the last 7 days for each category.

    Args:
        categories: List of arXiv category codes (e.g., ["cs.SE", "cs.AI"])
        context: MCP agent context (not used, kept for consistency)

    Returns:
        Dict with statistics:
        {
            "total_papers": int,
            "categories": {
                "cs.SE": {"count": 123, "papers": [...]},
                "cs.AI": {"count": 456, "papers": [...]},
            },
            "time_range": {"start": "...", "end": "..."}
        }
    """
    session = aiohttp.ClientSession()

    try:
        # Calculate last 7 days
        now = datetime.now(timezone.utc)
        seven_days_ago = now - timedelta(days=7)

        results = {
            "total_papers": 0,
            "categories": {},
            "time_range": {
                "start": seven_days_ago.isoformat(),
                "end": now.isoformat(),
            }
        }

        limit_per_category = 2000

        for idx, category in enumerate(categories):
            # Add 3-second delay between requests to avoid rate limiting (except for first request)
            if idx > 0:
                print(f"   Waiting 3 seconds before next request...")
                await asyncio.sleep(3)
            try:
                print(f"\n{'='*60}")
                print(f"Fetching papers for category: {category}")
                print(f"{'='*60}")

                # Build arXiv API query for this category
                query = f"cat:{category}"
                url = (
                    "http://export.arxiv.org/api/query"
                    f"?search_query={query}"
                    f"&start=0&max_results={limit_per_category}"
                    "&sortBy=submittedDate&sortOrder=descending"
                )

                # Fetch from arXiv API
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"❌ Failed to fetch papers for category {category}: HTTP {response.status}")
                        results["categories"][category] = {
                            "count": 0,
                            "papers": [],
                            "error": f"HTTP {response.status}"
                        }
                        continue

                    content = await response.text()
                    feed = feedparser.parse(content)

                    category_papers = []
                    seen_ids = set()

                    # Process each entry
                    for entry in feed.entries:
                        paper_id = entry.id.split("/abs/")[-1]

                        # Skip duplicates
                        if paper_id in seen_ids:
                            continue

                        # Parse published date
                        published_dt = _parse_arxiv_datetime(entry.published)
                        if published_dt is None:
                            continue

                        # Ensure timezone aware
                        if published_dt.tzinfo is None:
                            published_dt = published_dt.replace(tzinfo=timezone.utc)

                        # Filter by last 7 days
                        if published_dt < seven_days_ago:
                            continue

                        # Extract paper metadata
                        authors = [author.name for author in entry.authors]
                        entry_categories = [tag.term for tag in entry.tags] if hasattr(entry, "tags") else []

                        # Create Paper model instance
                        paper = Paper(
                            id=paper_id,
                            title=entry.title,
                            authors=authors,
                            abstract=entry.summary,
                            categories=entry_categories,
                            published=entry.published,
                            pdf_link=f"http://arxiv.org/pdf/{paper_id}",
                        )

                        category_papers.append(paper)
                        seen_ids.add(paper_id)

                    # Store results for this category
                    results["categories"][category] = {
                        "count": len(category_papers),
                        "papers": category_papers,
                    }

                    results["total_papers"] += len(category_papers)

                    # Print statistics
                    print(f"✅ Category: {category}")
                    print(f"   Papers found (last 7 days): {len(category_papers)}")
                    print(f"   Total entries fetched: {len(feed.entries)}")

                    if category_papers:
                        newest = _parse_arxiv_datetime(category_papers[0].published)
                        oldest = _parse_arxiv_datetime(category_papers[-1].published)
                        print(f"   Newest paper: {newest.strftime('%Y-%m-%d %H:%M:%S') if newest else 'N/A'}")
                        print(f"   Oldest paper: {oldest.strftime('%Y-%m-%d %H:%M:%S') if oldest else 'N/A'}")

            except Exception as e:
                print(f"❌ Error fetching papers for category {category}: {str(e)}")
                results["categories"][category] = {
                    "count": 0,
                    "papers": [],
                    "error": str(e)
                }
                continue

        # Print summary
        print(f"\n{'='*60}")
        print(f"SUMMARY - Last 7 Days Paper Statistics")
        print(f"{'='*60}")
        print(f"Time Range: {seven_days_ago.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}")
        print(f"Total Papers Across All Categories: {results['total_papers']}")
        print(f"\nBreakdown by Category:")
        for cat, data in results["categories"].items():
            print(f"  {cat:15s}: {data['count']:4d} papers")
        print(f"{'='*60}\n")

        return results

    finally:
        await session.close()