from mcp_agent.workflows.llm.augmented_llm import RequestParams
from axpa.agents.category_selector import create_category_selector_agent
from axpa.agents.prompts import validate_category_codes
from axpa.outputs.data_models import SelectedCategories
import json

async def select_categories_stage(
    query: str,
    context,
    llm_factory,
) -> list[str]:
    """
    Stage 1: Select categories.
    """

    request_params = RequestParams(
        maxTokens=4096,
        temperature=0.2
    )

    select_agent = create_category_selector_agent()
    llm = await select_agent.attach_llm(llm_factory)

    response = await llm.generate_structured(
        message=f"QUERY:\n{query}\n\n",
        response_model=SelectedCategories,
        request_params=request_params,
    )
    # print(f"response: {response}")
    logger = context.logger
    logger.info("category_selection.response", data={"response": response})

    # Remove <think>...</think> if exists
    if "<think>" in response:
        response = response.split("</think>")[1].strip()

    try:
        selected_categories = response.categories
    except Exception:
        logger.error("category_selection.error", data={"error": "Failed to parse selected categories"})
        selected_categories = []

    categories = [c.strip() for c in selected_categories if isinstance(c, str) and c.strip()]

    valid, _ = validate_category_codes(categories)
    if not valid:
        logger.warning("category_selection.invalid_categories", data={"categories": categories})
        valid = ["cs.SE", "cs.AI"]
        valid, _ = validate_category_codes(valid)

    return valid[:6]