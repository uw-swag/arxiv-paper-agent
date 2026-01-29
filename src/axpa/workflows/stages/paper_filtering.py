from axpa.agents.paper_filter import create_paper_filter_agent
from axpa.outputs.data_models import Paper, FilterResult
from mcp_agent.workflows.llm.augmented_llm import RequestParams

from typing import List
import asyncio


async def filter_papers_stage(
    papers: List[Paper],
    query: str,
    context,
    llm_factory,
) -> List[Paper]:
    """
    Stage 3: Filter papers in parallel using asyncio.gather.

    Creates one filter agent instance and calls it for each paper in parallel.
    Returns only accepted papers.
    """
    logger = context.logger
    logger.info("filter_papers.start", data={"total_papers": len(papers), "query": query})

    # Create a single filter agent
    filter_agent = create_paper_filter_agent()

    # Attach LLM to the agent
    async with filter_agent as agent_ctx:
        llm = await agent_ctx.attach_llm(llm_factory)

        # Request parameters for filtering
        request_params = RequestParams(
            maxTokens=16384,
            temperature=0.3
        )

        # Create filtering tasks for each paper
        async def filter_single_paper(paper: Paper) -> tuple[Paper, FilterResult | None]:
            """Filter a single paper and return (paper, result)."""
            try:
                message = f"Query: {query}\n\nPaper:\n{paper.model_dump_json(indent=2)}"

                # Use structured generation - much cleaner!
                filter_result = await llm.generate_structured(
                    message=message,
                    response_model=FilterResult,
                    request_params=request_params
                )

                # Add paper_id to the result
                filter_result.paper_id = paper.id

                return (paper, filter_result)

            except Exception as e:
                logger.error("filter_papers.paper_error", data={
                    "paper_id": paper.id,
                    "error": str(e)
                })
                return (paper, None)

        # Run all filtering tasks in parallel
        logger.info("filter_papers.parallel_start", data={"count": len(papers)})

        try:
            results = await asyncio.gather(
                *[filter_single_paper(paper) for paper in papers],
                return_exceptions=True
            )
            logger.info("filter_papers.parallel_complete", data={"results_count": len(results)})
        except Exception as e:
            logger.error("filter_papers.parallel_error", data={"error": str(e)})
            raise

        # Aggregate results
        accepted_papers = []
        rejected_papers = []
        error_count = 0

        logger.info("filter_papers.aggregating", data={"results_to_process": len(results)})

        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning("filter_papers.result_exception", data={
                    "index": idx,
                    "error": str(result)
                })
                error_count += 1
                continue

            try:
                paper, filter_result = result
            except Exception as e:
                logger.error("filter_papers.unpack_error", data={
                    "index": idx,
                    "result_type": type(result).__name__,
                    "error": str(e)
                })
                error_count += 1
                continue

            if filter_result and filter_result.accept:
                accepted_papers.append(paper)
                logger.debug("filter_papers.accepted", data={
                    "paper_id": paper.id,
                    "title": paper.title[:60],
                    "score": filter_result.relevance_score
                })
            elif filter_result:
                rejected_papers.append(paper)
                logger.debug("filter_papers.rejected", data={
                    "paper_id": paper.id,
                    "title": paper.title[:60],
                    "score": filter_result.relevance_score
                })
            else:
                error_count += 1

        # Log summary
        logger.info("filter_papers.complete", data={
            "total_papers": len(papers),
            "accepted": len(accepted_papers),
            "rejected": len(rejected_papers),
            "errors": error_count
        })

        return accepted_papers