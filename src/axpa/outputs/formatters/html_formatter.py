from __future__ import annotations

import html
from axpa.outputs.formatters.base import BaseFormatter
from axpa.outputs.data_models import WorkflowResult, PaperSummary, AggregatedScoreResult, HTMLFormatResult

class HtmlFormatter(BaseFormatter):

    def _adjust_heading_levels(self, text: str) -> str:
        """Adjust heading levels in detailed summary content.

        - <h4> : if text is already <b>bold</b>, keep as <b>text</b>; else wrap in <b>text</b>
        - <h3> : if text is <b>bold</b>, convert to <u><b>text</b></u>; else convert to <u><b>text</b></u>
        - <h2> becomes <h4>
        """
        import re

        # Handle <h4>: convert to <b>
        def replace_h4(match):
            content = match.group(1)
            # Check if already wrapped in <b>
            b_match = re.match(r'^<b>(.*)</b>$', content, re.DOTALL)
            if b_match:
                return f'<b>{b_match.group(1)}</b>'
            else:
                return f'<b>{content}</b>'

        # Handle <h3>: convert to <u><b>
        def replace_h3(match):
            content = match.group(1)
            # Check if wrapped in <b>
            b_match = re.match(r'^<b>(.*)</b>$', content, re.DOTALL)
            if b_match:
                return f'<u><b>{b_match.group(1)}</b></u>'
            else:
                return f'<u><b>{content}</b></u>'

        # Handle <h2>: convert to <h4>
        def replace_h2(match):
            content = match.group(1)
            return f'<h4>{content}</h4>'

        # Apply replacements in order (h4 first to avoid conflicts)
        text = re.sub(r'<h4>(.*?)</h4>', replace_h4, text, flags=re.DOTALL)
        text = re.sub(r'<h3>(.*?)</h3>', replace_h3, text, flags=re.DOTALL)
        text = re.sub(r'<h2>(.*?)</h2>', replace_h2, text, flags=re.DOTALL)

        return text

    def _css(self) -> str:
        return (
            "body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; line-height: 1.6; margin: 24px; max-width: 900px; }\n"
            "h1 { margin: 0 0 12px 0; color: #333; }\n"
            "h2 { margin: 24px 0 12px 0; color: #444; border-bottom: 2px solid #eee; padding-bottom: 8px; }\n"
            "h3 { margin: 16px 0 8px 0; color: #555; }\n"
            "h4 { margin: 12px 0 6px 0; color: #666; }\n"
            ".meta { margin: 0 0 18px 0; background: #f9f9f9; padding: 12px; border-radius: 6px; }\n"
            ".meta p { margin: 6px 0; }\n"
            ".paper { padding: 14px 0; }\n"
            ".kv { margin: 0 0 10px 0; }\n"
            ".kv div { margin: 3px 0; }\n"
            ".kv b { display: inline-block; min-width: 88px; }\n"
            ".section { margin: 12px 0; }\n"
            ".section p { margin: 6px 0; white-space: pre-wrap; }\n"
            "hr { border: 0; border-top: 1px solid #ddd; margin: 14px 0; }\n"
            "a { color: #0066cc; word-break: break-all; }\n"
            "code { background: #f6f8fa; padding: 2px 4px; border-radius: 4px; font-family: monospace; }\n"
            ".query-section { margin-bottom: 40px; }\n"
        )

    def format_info(self, user_name: str, info: list[WorkflowResult]) -> str:
        parts: list[str] = []
        parts.append("<h3>Report Summary:</h3>")
        parts.append(f'<div class="meta-info">')
        parts.append(f"<div><b>For</b>: {html.escape(user_name)}</div>")

        for i, result in enumerate(info):
            parts.append(f'<div style="margin-top: 10px;">') 
            parts.append(f"<div><b>Query {i + 1}</b>: {html.escape(result.query)}</div>")
            categories_text = ", ".join(html.escape(c) for c in result.categories)
            parts.append(f"<div><b>Categories</b>: {categories_text}</div>")
            parts.append(f"<div><b>Total Papers Analyzed</b>: {result.total_papers}</div>")
            parts.append(f"<div><b>Accepted Papers</b>: {result.accepted_papers}</div>")
            parts.append(f"</div>")

        parts.append("</div>")
        parts.append("<hr />")
        return "\n".join(parts)

    def format_short_summaries(self, summary: AggregatedScoreResult) -> str:
        parts: list[str] = []
        parts.append(f'<div class="section"><b><u>Brief Summary</u></b>:\n<p>{html.escape(summary.summary)}</p></div>')
        parts.append(f'<div class="section"><b><u>Strengths</u></b>:\n<p>{html.escape(summary.strengths)}</p></div>')
        parts.append(f'<div class="section"><b><u>Weaknesses</u></b>:\n<p>{html.escape(summary.weaknesses)}</p></div>')
        return "\n".join(parts)

    def format_detailed_summary(self, summary: PaperSummary) -> str:
        parts: list[str] = []
        parts.append(f'{self._adjust_heading_levels(summary.research_gap)}')
        parts.append(f'{self._adjust_heading_levels(summary.related_studies)}')
        parts.append(f'{self._adjust_heading_levels(summary.methodology)}')
        parts.append(f'{self._adjust_heading_levels(summary.experiments)}')
        parts.append(f'{self._adjust_heading_levels(summary.further_research)}')
        parts.append(f'{self._adjust_heading_levels(summary.overall_summary)}')
        return "\n".join(parts)

    def format_paper_summary(self, summary_type: str, result: HTMLFormatResult) -> str:
        parts: list[str] = []
        parts.append('<div class="query-section">')
        parts.append(f"<h2>Top {len(result.html_summaries)} papers for the topic: {html.escape(result.query)}</h2>")

        for paper in result.html_summaries:
            summary = paper.score
            pdf_link = html.escape(summary.paper.pdf_link, quote=True)

            parts.append('<div class="paper">')
            parts.append(
                f'<h3><a href="{pdf_link}" target="_blank" rel="noopener noreferrer">'
                f'{html.escape(summary.paper.title)}</a></h3>'
            )
            parts.append('<div class="kv">')
            parts.append(f"<div><b>arXiv ID</b>: <code>{html.escape(summary.paper.id)}</code></div>")
            parts.append(f"<div><b>Score</b>: {summary.avg_score:.2f}/10</div>")
            parts.append("</div>")

            if summary_type in ["short", "both"]:
                parts.append(self.format_short_summaries(summary))

            if summary_type in ["detailed", "both"]:
                parts.append(self.format_detailed_summary(paper))
            parts.append("</div>")
            parts.append("<hr />")

        parts.append("</div>")
        return "\n".join(parts)

    def prepare_all(self, user_name: str, summary_type: str, results: list[WorkflowResult]) -> str:
        parts: list[str] = []
        parts.append("<!doctype html>")
        parts.append('<html lang="en">')
        parts.append("<head>")
        parts.append('  <meta charset="utf-8" />')
        parts.append('  <meta name="viewport" content="width=device-width, initial-scale=1" />')
        parts.append("  <title>arXiv Paper Weekly Update</title>")
        parts.append('  <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@4/tex-mml-chtml.js"></script>')
        parts.append(f"  <style>\n{self._css()}  </style>")
        parts.append("</head>")
        parts.append("<body>")

        parts.append(self.format_info(user_name, results))

        for result in results:
            parts.append(self.format_paper_summary(summary_type, result))

        parts.append("</body>")
        parts.append("</html>")
        return "\n".join(parts)