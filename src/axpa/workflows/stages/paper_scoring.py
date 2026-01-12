import traceback
from axpa.agents.paper_scorer import create_paper_scorer_agent
from axpa.outputs.data_models import Paper, ScoreResult
from mcp_agent.workflows.llm.augmented_llm import RequestParams

from typing import List
import asyncio


async def score_papers_stage(
    papers: List[Paper],
    query: str,
    context,
    llm_factory,
) -> List[dict]:
    """
    Stage 4: Score papers in two independent rounds.

    This implements a double-blind review process:
    - Round 1: First independent scoring of all papers
    - Round 2: Second independent scoring of all papers (no knowledge of Round 1)
    - Aggregation: Average scores from both rounds

    Implementation pattern:
    - Single agent per round
    - Parallel scoring using asyncio.gather
    - Two-step approach per paper:
      1. generate_str() - agent uses tools (download_paper, read_paper) to get evaluation text
      2. generate_structured() - format text as ScoreResult JSON
    - This two-step pattern is required because OpenAI API doesn't support both
      tools and response_format (structured output) in the same call

    Returns:
        List of dicts with paper and averaged scores
    """
    logger = context.logger
    logger.info("score_papers.start", data={
        "total_papers": len(papers),
        "query": query
    })

    # Request parameters for scoring
    request_params = RequestParams(
        maxTokens=8192,
        temperature=0.4,
        max_iterations=50
    )

    async def run_scoring_round(round_num: int) -> List[tuple[Paper, ScoreResult | None]]:
        """Run a single round of scoring for all papers using structured generation."""
        logger.info(f"score_papers.round{round_num}_start", data={"round": round_num})
        scorer_agent = create_paper_scorer_agent(round_num=round_num)

        async with scorer_agent as agent_ctx:
            llm = await agent_ctx.attach_llm(llm_factory)
            llm.history.clear()

            async def score_single_paper(paper: Paper) -> tuple[Paper, ScoreResult | None]:
                """
                Score a single paper using two-step approach (required for tool use + structured output):
                1. generate_str() - agent uses tools to download/read paper and create evaluation
                2. generate_structured() - format the evaluation as ScoreResult JSON

                This pattern matches LMStudioAugmentedLLM.generate_structured() implementation.
                OpenAI API doesn't support both tools and response_format in the same call.
                """
                try:
                    message = f"""Review paper ID: {paper.id} for the research query: {query}

Paper metadata:
- Title: {paper.title}
- Authors: {', '.join(paper.authors)}
- Categories: {', '.join(paper.categories)}
- Published: {paper.published}

Task: Use the arxiv MCP server tools to download and read the paper content, then evaluate it according to your scoring criteria. Provide a complete evaluation with all scores and assessments."""

                    # Step 1: Get the text evaluation
                    text_response = await llm.generate_str(
                        message=message,
                        request_params=request_params
                    )

                    logger.debug(f"score_papers.round{round_num}_text_response", data={
                        "paper_id": paper.id,
                        "response_length": len(text_response),
                    })

                    # Step 2: Format the text evaluation as structured ScoreResult
                    format_prompt = f"""Based on the following paper evaluation, provide a response in JSON format matching the ScoreResult schema.

Evaluation:
{text_response}

Return ONLY valid JSON. All score fields (relevance, novelty, soundness, clarity, significance, overall_score) must be numbers between 0-10. All text fields (summary, strengths, weaknesses, recommendation) must be non-empty strings."""

                    score_result = await llm.generate_structured(
                        message=format_prompt,
                        response_model=ScoreResult,
                        request_params=RequestParams(
                            maxTokens=16384,
                            temperature=0.1,
                            use_history=False
                        )
                    )

                    # Add paper_id to the result
                    score_result.paper_id = paper.id

                    logger.debug(f"score_papers.round{round_num}_scored", data={
                        "paper_id": paper.id,
                        "overall_score": score_result.overall_score,
                    })

                    return (paper, score_result)

                except Exception as e:
                    logger.error(f"score_papers.round{round_num}_error", data={
                        "paper_id": paper.id,
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    })
                    return (paper, None)

            # Run scoring tasks in parallel using asyncio.gather
            logger.info(f"score_papers.round{round_num}_parallel_start", data={"count": len(papers)})

            try:
                results = await asyncio.gather(
                    *[score_single_paper(paper) for paper in papers],
                    return_exceptions=True
                )
                logger.info(f"score_papers.round{round_num}_parallel_complete", data={
                    "results_count": len(results)
                })
            except Exception as e:
                logger.error(f"score_papers.round{round_num}_parallel_error", data={"error": str(e)})
                raise

            # Process results
            round_results = []
            error_count = 0

            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"score_papers.round{round_num}_result_exception", data={
                        "index": idx,
                        "error": str(result)
                    })
                    error_count += 1
                    continue

                try:
                    paper, score_result = result
                    if score_result:
                        round_results.append((paper, score_result))
                    else:
                        error_count += 1
                except Exception as e:
                    logger.error(f"score_papers.round{round_num}_unpack_error", data={
                        "index": idx,
                        "error": str(e)
                    })
                    error_count += 1

            logger.info(f"score_papers.round{round_num}_complete", data={
                "scored": len(round_results),
                "errors": error_count
            })

            return round_results

    # Run both rounds sequentially
    logger.info("score_papers.running_rounds", data={"total_rounds": 2})

    round1_results = await run_scoring_round(round_num=1)
    round2_results = await run_scoring_round(round_num=2)

    logger.info("score_papers.aggregating", data={
        "round1_count": len(round1_results),
        "round2_count": len(round2_results)
    })

    # Create a mapping of paper_id to scores
    round1_map = {score.paper_id: (paper, score) for paper, score in round1_results}
    round2_map = {score.paper_id: (paper, score) for paper, score in round2_results}

    # Find papers that have scores in BOTH rounds
    common_paper_ids = set(round1_map.keys()) & set(round2_map.keys())

    scored_papers = []

    for paper_id in common_paper_ids:
        paper1, score1 = round1_map[paper_id]
        paper2, score2 = round2_map[paper_id]

        # Calculate average scores across dimensions
        avg_dimensions = {
            "relevance": (score1.relevance + score2.relevance) / 2,
            "novelty": (score1.novelty + score2.novelty) / 2,
            "soundness": (score1.soundness + score2.soundness) / 2,
            "clarity": (score1.clarity + score2.clarity) / 2,
            "significance": (score1.significance + score2.significance) / 2,
        }

        # Calculate average overall score
        avg_overall_score = (score1.overall_score + score2.overall_score) / 2

        scored_paper = {
            "paper": paper1,
            "round1_score": score1,
            "round2_score": score2,
            "avg_score": avg_overall_score,
            "avg_dimensions": avg_dimensions,
        }

        scored_papers.append(scored_paper)

        logger.debug("score_papers.aggregated", data={
            "paper_id": paper_id,
            "round1_score": score1.overall_score,
            "round2_score": score2.overall_score,
            "avg_score": avg_overall_score
        })

    # Log summary
    logger.info("score_papers.complete", data={
        "total_papers": len(papers),
        "scored_papers": len(scored_papers),
        "dropped_papers": len(papers) - len(scored_papers),
        "avg_score_mean": sum(sp["avg_score"] for sp in scored_papers) / len(scored_papers) if scored_papers else 0
    })

    return scored_papers
