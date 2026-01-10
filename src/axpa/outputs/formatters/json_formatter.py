import json


def format_as_json(results: dict) -> str:
    """Format results as structured JSON."""
    return json.dumps(results, indent=2, ensure_ascii=False)