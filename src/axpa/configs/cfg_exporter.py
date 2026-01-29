from dataclasses import dataclass
from typing import Literal


ExportDestination = Literal["email", "local", "notion"]
ExportFormat = Literal["html", "markdown"]
SummaryType = Literal["short", "detailed", "both"]


@dataclass
class ExporterConfig:
    """Configuration for an exporter."""
    destination: ExportDestination
    format: ExportFormat
    summary_type: SummaryType

    @classmethod
    def from_dict(cls, data: dict) -> "ExporterConfig":
        """Create an ExporterConfig from a dict like {'email': ['html', 'detailed']}."""
        if isinstance(data, dict):
            for dest, fmt_summary_type in data.items():
                fmt = fmt_summary_type[0]
                summary_type = fmt_summary_type[1]
                return cls(destination=dest, format=fmt, summary_type=summary_type)
        raise ValueError(f"Invalid exporter config: {data}")