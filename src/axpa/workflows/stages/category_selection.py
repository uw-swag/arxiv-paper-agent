from axpa.agents.category_selector import create_category_selector_agent
from axpa.agents.prompts import validate_category_codes
import json

async def select_categories_stage(
    query: str,
    context,
    llm_factory,
) -> list[str]:
    """
    Stage 1: Select categories.
    """

    select_agent = create_category_selector_agent()
    llm = await select_agent.attach_llm(llm_factory)

    response = await llm.generate_str(f"QUERY:\n{query}\n\n")
    # print(f"response: {response}")

    # Remove <think>...</think> if exists
    if "<think>" in response:
        response = response.split("</think>")[1].strip()

    try:
        selected_categories = json.loads(response)
    except Exception:
        selected_categories = []

    categories = selected_categories.get("categories", [])
    if not isinstance(categories, list):
        categories = []

    categories = [c.strip() for c in categories if isinstance(c, str) and c.strip()]

    valid, _ = validate_category_codes(categories)
    if not valid:
        # logger.warning(f"Invalid category codes: {categories}")
        print(f"Invalid category codes: {categories}")
        valid = ["cs.SE", "cs.AI"]
        valid, _ = validate_category_codes(valid)
    
    # print(f"valid: {valid}")

    return valid[:6]