from __future__ import annotations
from typing import Callable, Coroutine, Any, Optional, Type
import asyncio
import tenacity

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
    delay_time: float = 1.0,
    retry_on: Type[BaseException] | tuple[Type[BaseException], ...] = Exception,
) -> Any:

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(retry_on),
        wait=tenacity.wait_fixed(delay_time),
        stop=tenacity.stop_after_attempt(retries),
        reraise=True,
    )
    async def _wrapped() -> Any:
        return await fn()

    try:
        return await _wrapped()
    except Exception as e:
        raise RuntimeError(f"{name} failed after {retries} attempts") from e