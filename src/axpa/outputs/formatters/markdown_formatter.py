from __future__ import annotations

from axpa.outputs.formatters.base import BaseFormatter
from axpa.configs import UserConfig
from axpa.outputs.data_models import WorkflowResult, PaperSummary, AggregatedScoreResult


class MarkdownFormatter(BaseFormatter):
    def _adjust_heading_levels(self, text: str) -> str:
        """Adjust heading levels in detailed summary content.

        - #### : if text is already **bold**, keep as **text**; else wrap in **text**
        - ### : if text is **bold**, convert to <u><b>text</b></u>; else convert to <u><b>text</b></u>
        - ## becomes ####
        """
        lines = text.split('\n')
        adjusted_lines = []

        for line in lines:
            if line.startswith('#### '):
                heading_text = line[5:]
                # Check if already surrounded by ** **
                if heading_text.startswith('**') and heading_text.endswith('**'):
                    adjusted_lines.append(heading_text)
                else:
                    adjusted_lines.append(f'**{heading_text}**')
            elif line.startswith('### '):
                heading_text = line[4:]
                # Check if surrounded by ** **
                if heading_text.startswith('**') and heading_text.endswith('**'):
                    # Remove ** ** and convert to <u><b></b></u>
                    inner_text = heading_text[2:-2]
                    adjusted_lines.append(f'<u><b>{inner_text}</b></u>')
                else:
                    # Convert h3 to <u><b>text</b></u>
                    adjusted_lines.append(f'<u><b>{heading_text}</b></u>')
            elif line.startswith('## '):
                # Convert h2 to h4
                heading_text = line[3:]
                adjusted_lines.append(f'#### {heading_text}')
            else:
                adjusted_lines.append(line)

        return '\n'.join(adjusted_lines)

    def format_info(self, user_name: str, info: list[WorkflowResult]) -> str:
        md = "# arXiv Paper Weekly Update\n\n"

        md += f"### Report Summary:\n\n"
        md += f"**For**: {user_name}\n\n"

        for i, result in enumerate(info):
            md += f"**Query {i+1}**: {result.query}\n\n"
            md += f"**Categories**: {', '.join(result.categories)}\n\n"
            md += f"**Total Papers Analyzed**: {result.total_papers}\n\n"
            md += f"**Accepted Papers**: {result.accepted_papers}\n\n"
        
        md += "---\n\n"
        return md

    def format_short_summaries(self, summary: AggregatedScoreResult) -> str:
        md = f"***Brief Summary***: \n {summary.summary}\n\n"
        md += f"***Strengths***: \n {summary.strengths}\n\n"
        md += f"***Weaknesses***: \n {summary.weaknesses}\n\n"
        return md


    def format_detailed_summary(self, summary: PaperSummary) -> str:
        md = f"{self._adjust_heading_levels(summary.research_gap)}\n\n"
        md += f"{self._adjust_heading_levels(summary.related_studies)}\n\n"
        md += f"{self._adjust_heading_levels(summary.methodology)}\n\n"
        md += f"{self._adjust_heading_levels(summary.experiments)}\n\n"
        md += f"{self._adjust_heading_levels(summary.further_research)}\n\n"
        md += f"{self._adjust_heading_levels(summary.overall_summary)}\n\n"
        return md


    def format_paper_summary(self, summary_type: str, result: WorkflowResult) -> str:
        md = f"## Top {len(result.summaries)} papers for the topic: {result.query}\n\n"
        for paper in result.summaries:
            summary = paper.score
            md += f"### [{summary.paper.title}]({summary.paper.pdf_link})\n"
            md += f"arXiv ID: `{summary.paper.id}`\n"
            md += f"Score: {summary.avg_score:.2f}/10\n\n"

            if summary_type in ["short", "both"]:
                md += self.format_short_summaries(summary)

            if summary_type in ["detailed", "both"]:
                md += self.format_detailed_summary(paper)
            
            md += "---\n\n"
        return md


    def prepare_all(self, user_name: str, summary_type: str, results: list[WorkflowResult]) -> str:
        md = self.format_info(user_name, results)

        for result in results:
            md += self.format_paper_summary(summary_type, result)

        return md
            