from __future__ import annotations

import html


def format_as_html(results: dict) -> str:
    """
    Format results as a human-readable HTML page, analogous to format_as_markdown().

    Notes:
    - Escapes all user/content fields for safety.
    - Uses a simple, clean document structure suitable for email/web viewing.
    """
    query = html.escape(str(results.get("query", "")), quote=True)
    categories = results.get("categories", []) or []
    categories_text = ", ".join(html.escape(str(c), quote=True) for c in categories)

    total_papers = html.escape(str(results.get("total_papers", "")), quote=True)

    summaries = results.get("summaries", []) or []
    top_n = len(summaries)

    parts: list[str] = []
    parts.append("<!doctype html>")
    parts.append('<html lang="en">')
    parts.append("<head>")
    parts.append('  <meta charset="utf-8" />')
    parts.append('  <meta name="viewport" content="width=device-width, initial-scale=1" />')
    parts.append(f"  <title>arXiv Paper Analysis: {query}</title>")
    parts.append("  <style>")
    parts.append("    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; line-height: 1.5; margin: 24px; }")
    parts.append("    h1 { margin: 0 0 12px 0; }")
    parts.append("    .meta { margin: 0 0 18px 0; }")
    parts.append("    .meta p { margin: 6px 0; }")
    parts.append("    .paper { padding: 14px 0; }")
    parts.append("    .paper h2 { margin: 0 0 10px 0; font-size: 1.15rem; }")
    parts.append("    .kv { margin: 0 0 10px 0; }")
    parts.append("    .kv div { margin: 3px 0; }")
    parts.append("    .kv b { display: inline-block; min-width: 88px; }")
    parts.append("    .summary { white-space: pre-wrap; margin: 10px 0 0 0; }")
    parts.append("    hr { border: 0; border-top: 1px solid #ddd; margin: 14px 0; }")
    parts.append("    a { word-break: break-all; }")
    parts.append("    code { background: #f6f8fa; padding: 2px 4px; border-radius: 4px; }")
    parts.append("  </style>")
    parts.append("</head>")
    parts.append("<body>")

    parts.append(f"<h1>arXiv Paper Analysis: {query}</h1>")

    parts.append('<div class="meta">')
    parts.append(f"<p><b>Categories</b>: {categories_text}</p>")
    parts.append(f"<p><b>Total Papers Analyzed</b>: {total_papers}</p>")
    parts.append(f"<p><b>Top {top_n} Papers</b></p>")
    parts.append("</div>")

    for i, paper in enumerate(summaries, 1):
        title = html.escape(str(paper.get("title", "")), quote=True)
        arxiv_id = html.escape(str(paper.get("id", "")), quote=True)

        score_val = paper.get("score", "")
        try:
            score_str = f"{float(score_val):.2f}/10"
        except Exception:
            score_str = html.escape(str(score_val), quote=True)

        pdf_link_raw = str(paper.get("pdf_link", "") or "")
        pdf_link_escaped = html.escape(pdf_link_raw, quote=True)

        summary_text = html.escape(str(paper.get("summary", "")), quote=True)

        parts.append('<div class="paper">')
        parts.append(f"<h2>{i}. {title}</h2>")
        parts.append('<div class="kv">')
        parts.append(f"<div><b>arXiv ID</b>: <code>{arxiv_id}</code></div>")
        parts.append(f"<div><b>Score</b>: {html.escape(score_str, quote=True)}</div>")

        if pdf_link_raw:
            parts.append(
                f'<div><b>PDF</b>: <a href="{pdf_link_escaped}" target="_blank" rel="noopener noreferrer">{pdf_link_escaped}</a></div>'
            )
        else:
            parts.append("<div><b>PDF</b>: </div>")

        parts.append("</div>")

        parts.append(f'<div class="summary">{summary_text}</div>')
        parts.append("</div>")
        parts.append("<hr />")

    parts.append("</body>")
    parts.append("</html>")

    return "\n".join(parts)

