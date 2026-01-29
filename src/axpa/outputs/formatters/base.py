from abc import ABC, abstractmethod
from axpa.outputs.data_models import WorkflowResult, AggregatedScoreResult, PaperSummary
from axpa.configs import UserConfig

class BaseFormatter(ABC):

    @abstractmethod
    def format_info(self, user: UserConfig, info: list[WorkflowResult]) -> str:
        """Format the information of the report at the beginning."""
        pass

    @abstractmethod
    def format_short_summaries(self, summary: AggregatedScoreResult) -> str:
        """Format a list of short summaries of the papers."""
        pass

    @abstractmethod
    def format_detailed_summary(self, result: PaperSummary) -> str:
        """Format the detailed summary of the papers."""
        pass

    @abstractmethod
    def format_paper_summary(self, summary_type: str, result: WorkflowResult) -> str:
        """Format the summary of the paper based on the summary type."""
        pass

    @abstractmethod
    def prepare_all(self, user: UserConfig, results: list[WorkflowResult]) -> str:
        """Prepare the final report."""
        pass