

def format_as_markdown(results: dict) -> str:
    """Format results as human-readable markdown."""
    md = f"# arXiv Paper Analysis: {results['query']}\n\n"
    md += f"**Categories**: {', '.join(results['categories'])}\n\n"
    md += f"**Total Papers Analyzed**: {results['total_papers']}\n\n"
    md += f"**Top {len(results['summaries'])} Papers**\n\n"

    for i, paper in enumerate(results['summaries'], 1):
        md += f"## {i}. {paper['title']}\n\n"
        md += f"**arXiv ID**: {paper['id']}\n"
        md += f"**Score**: {paper['score']:.2f}/10\n"
        md += f"**PDF**: {paper['pdf_link']}\n\n"
        md += f"{paper['summary']}\n\n"
        md += "---\n\n"

    return md