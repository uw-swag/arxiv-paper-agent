from __future__ import annotations

from typing import Optional
import asyncio

from axpa.agents.html_converter import create_html_formatter_agent
from axpa.outputs.data_models import WorkflowResult, HTMLFormatResult, PaperSummary
from mcp_agent.workflows.llm.augmented_llm import RequestParams


async def html_formatting_stage(workflow_result: WorkflowResult, context, llm_factory) -> Optional[HTMLFormatResult]:
    logger = context.logger
    logger.info("html_formatting.start", data={"total_summaries": len(workflow_result.summaries)})

    request_params = RequestParams(
        maxTokens=16384,
        temperature=0.2
    )

    formatting_prompts = [
        ("research_gap", "Format the research gap into a HTML section."),
        ("related_studies", "Format the related studies into a HTML section."),
        ("methodology", "Format the methodology into a HTML section."),
        ("experiments", "Format the experiments into a HTML section."),
        ("further_research", "Format the further research into a HTML section."),
        ("overall_summary", "Format the overall summary into a HTML section."),
    ]

    async def format_html_summary(paper_summary: PaperSummary, llm) -> PaperSummary:
        try:
            llm.history.clear()

            logger.info("html_formatting.format_html_start", data={
                "paper_id": paper_summary.score.paper_id,
                "title": paper_summary.score.paper.title[:60],
            })

            html_format_generated = {}
            for field_name, description in formatting_prompts:
                logger.debug("html_formatting.format_html_prompt", data={
                    "paper_id": paper_summary.score.paper_id,
                    "field": field_name,
                })
                
                html_text = await llm.generate_str(
                    message=f"{description}\n\n{getattr(paper_summary, field_name)}", 
                    request_params=request_params
                )

                html_format_generated[field_name] = html_text

                logger.debug("html_formatting.format_html_complete", data={
                    "paper_id": paper_summary.score.paper_id,
                    "field": field_name,
                    "length": len(html_text),
                })
            
            html_format_result = PaperSummary(
                score=paper_summary.score,
                research_gap=html_format_generated["research_gap"],
                related_studies=html_format_generated["related_studies"],
                methodology=html_format_generated["methodology"],
                experiments=html_format_generated["experiments"],
                further_research=html_format_generated["further_research"],
                overall_summary=html_format_generated["overall_summary"],
            )
            
            logger.info("html_formatting.format_html_complete", data={
                "paper_id": paper_summary.score.paper_id,
                "title": paper_summary.score.paper.title[:60],
            })
            
            return html_format_result
        
        except Exception as e:
            logger.error("html_formatting.format_html_error", data={
                "paper_id": paper_summary.score.paper_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "[WARNING]": "Failed to format HTML summary for the paper. Returning the original summary in markdown format.",
            })
            return paper_summary
    
    all_html_format_results = []

    html_formatter_agent = create_html_formatter_agent()
    async with html_formatter_agent as agent_ctx:
        llm = await agent_ctx.attach_llm(llm_factory)

        try:
            all_html_format_results = await asyncio.gather(
                *[format_html_summary(paper_summary, llm)
                  for paper_summary in workflow_result.summaries]
            )

        except Exception as e:
            logger.error("html_formatting.format_html_summary_error", data={"error": str(e)})
            all_html_format_results = workflow_result.summaries

    try:
        html_format_result = HTMLFormatResult(
            **workflow_result.model_dump(),
            html_summaries=all_html_format_results,
        )
    except Exception as e:
        logger.error("html_formatting.format_html_result_error", data={
            "error": str(e),
            "error_type": type(e).__name__,
        })
        return None

    logger.info("html_formatting.format_html_result_complete", data={
        "query": workflow_result.query,
        "html_summaries_count": len(html_format_result.html_summaries),
    })

    return html_format_result
