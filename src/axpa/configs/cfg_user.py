from dataclasses import dataclass, field
from .cfg_exporter import ExporterConfig


@dataclass
class UserConfig:
    """
    Configuration for user preferences.
    """
    user_name: str
    user_email: str
    # Personalized summary for future use
    personalized_summary: str = ""
    # Summary exporters configuration (applies to all queries)
    summary_exporters: list[ExporterConfig] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "UserConfig":
        """Create a UserConfig from a dictionary."""
        # Parse exporters
        summary_exporters = []
        for exp in data.get("summary_exporters", []):
            summary_exporters.append(ExporterConfig.from_dict(exp))

        return cls(
            user_name=data.get("user_name", ""),
            user_email=data.get("user_email", ""),
            personalized_summary=data.get("personalized_summary", ""),
            summary_exporters=summary_exporters,
        )
