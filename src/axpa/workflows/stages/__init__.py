from typing import Callable, Coroutine, Any, Optional
import asyncio


from .category_selection import select_categories_stage
from .paper_fetching import fetch_papers_from_categories_stage
from .paper_filtering import filter_papers_stage
from .paper_scoring import score_papers_stage
# from .paper_summarization import summarize_papers_stage

__all__ = [
    "select_categories_stage",
    "fetch_papers_from_categories_stage",
    "filter_papers_stage",
    "score_papers_stage",
    # "summarize_papers_stage",
]




# TODO: Merge this 
async def _retry_async(
    fn: Callable[[], Coroutine[Any, Any, Any]],
    *,
    name: str,
    retries: int = 5,
    delay_time: float = 1
) -> Any:
    last_exc: Optional[BaseException] = None
    for attempt in range(1, retries + 1):
        try:
            return await fn()
        except Exception as e:
            last_exc = e
            if attempt >= retries:
                break
            await asyncio.sleep(delay_time)
    raise RuntimeError(f"{name} failed after {retries} attempts") from last_exc