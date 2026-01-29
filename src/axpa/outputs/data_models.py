from pydantic import BaseModel, Field
from typing import List, Optional

class SelectedCategories(BaseModel):
    categories: List[str]

class Paper(BaseModel):
    id: str
    title: str
    authors: List[str]
    abstract: str
    categories: List[str]
    published: str
    pdf_link: str
    markdown_path: Optional[str] = None

class FilterResult(BaseModel):
    paper_id: Optional[str] = None  # Set after LLM generation
    accept: bool
    reasoning: str
    relevance_score: float = Field(ge=0, le=10)

class ScoreResult(BaseModel):
    """
    Paper evaluation scores based on ICLR review criteria.
    All scores are on a 0-10 scale.
    """
    paper_id: Optional[str] = None  # Set after LLM generation

    # Core evaluation dimensions (aligned with ICLR criteria)
    relevance: float = Field(ge=0, le=10, description="Relevance to the research query/topic")
    novelty: float = Field(ge=0, le=10, description="Originality and novelty of contribution")
    soundness: float = Field(ge=0, le=10, description="Technical correctness and methodological rigor")
    clarity: float = Field(ge=0, le=10, description="Presentation quality and reproducibility")
    significance: float = Field(ge=0, le=10, description="Impact and value to the research community")

    # Overall assessment
    overall_score: float = Field(ge=0, le=10, description="Overall weighted score")

    # Detailed justification
    summary: str = Field(description="1-2 sentence summary of what the paper claims to contribute")
    strengths: str = Field(description="Key strong points of the paper")
    weaknesses: str = Field(description="Key weak points or limitations")
    recommendation: str = Field(description="Accept/Reject recommendation with brief reasoning")

class AggregatedScoreResult(BaseModel):
    paper_id: Optional[str] = None
    paper: Paper
    round_scores: List[ScoreResult]
    avg_score: float = Field(ge=0, le=10, description="Overall weighted score")
    avg_dimensions: dict = Field(description="Average scores across dimensions")
    overall_recommendation: str = Field(description="Overall recommendation (Accept/Reject)")

    # Detailed justification
    summary: str = Field(description="1-2 sentence summary of what the paper claims to contribute")
    strengths: str = Field(description="Key strong points of the paper")
    weaknesses: str = Field(description="Key weak points or limitations")

class PaperSummary(BaseModel):
    score: AggregatedScoreResult
    research_gap: str = Field(description="What problem is the paper trying to address?")
    related_studies: str = Field(description="What studies are related to this problem?")
    methodology: str = Field(description="How does this paper tackle the issue?")
    experiments: str = Field(description="What kind of experiments were conducted in the paper?")
    further_research: str = Field(description="What areas could be explored further?")
    overall_summary: str = Field(description="Give a summary of the paper.")

class WorkflowResult(BaseModel):
    """Result from running the arxiv analysis workflow."""
    query: str
    categories: list[str]
    total_papers: int
    filtered_papers: int
    scored_papers: int
    accepted_papers: int
    summaries: list[PaperSummary]

class HTMLFormatResult(WorkflowResult):
    html_summaries: list[PaperSummary]