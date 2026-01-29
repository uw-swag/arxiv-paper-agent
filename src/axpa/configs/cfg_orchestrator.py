from dataclasses import dataclass, field
from datetime import datetime, timedelta

@dataclass
class OrchestratorConfig:
    """
    Configuration for the orchestrator (per-query settings).
    """
    query: str
    # Top k papers to return
    top_k: int = 10
    # Search limit
    search_limit: int = 2000
    # Score rounds
    score_rounds: int = 2
    # Paper start time
    paper_start_time: datetime | None = None
    # Paper end time
    paper_end_time: datetime | None = None
    # Time duration in days
    time_duration: int = 7
    # Output format (default for local exports)
    output_format: str = "markdown"

    def __post_init__(self):
        if self.paper_end_time is None:
            self.paper_end_time = datetime.now()
        if self.paper_start_time is None:
            self.paper_start_time = self.paper_end_time - timedelta(days=self.time_duration)

    @classmethod
    def from_dict(cls, data: dict) -> "OrchestratorConfig":
        """Create an OrchestratorConfig from a dictionary."""
        return cls(
            query=data["query"],
            top_k=data.get("top_k", 10),
            search_limit=data.get("search_limit", 2000),
            score_rounds=data.get("score_rounds", 2),
            time_duration=data.get("time_duration", 7),
            output_format=data.get("output_format", "markdown"),
        )
