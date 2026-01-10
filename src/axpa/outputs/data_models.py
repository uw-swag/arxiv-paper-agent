from pydantic import BaseModel, Field
from typing import List, Optional

class Paper(BaseModel):
    id: str
    title: str
    authors: List[str]
    abstract: str
    categories: List[str]
    published: str
    pdf_link: str

class FilterResult(BaseModel):
    paper_id: str
    accept: bool
    reasoning: str
    relevance_score: float = Field(ge=0, le=10)

class ScoreResult(BaseModel):
    paper_id: str
    relevance: float = Field(ge=0, le=10)
    novelty: float = Field(ge=0, le=10)
    methodology: float = Field(ge=0, le=10)
    clarity: float = Field(ge=0, le=10)
    overall_score: float = Field(ge=0, le=10)
    justification: str

class PaperSummary(BaseModel):
    paper: Paper
    score: ScoreResult
    summary: str