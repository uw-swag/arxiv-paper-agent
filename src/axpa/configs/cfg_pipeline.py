from dataclasses import dataclass
from pathlib import Path
import yaml

from .cfg_user import UserConfig
from .cfg_orchestrator import OrchestratorConfig
from .cfg_exporter import ExporterConfig


@dataclass
class PipelineConfig:
    """
    Main configuration that combines user config and orchestrator configs.
    """
    user: UserConfig
    orchestrator_configs: list[OrchestratorConfig]
    additional_html_formatting: bool = False

    def __post_init__(self):
        # Check if additional HTML formatting is needed
        for user_exporter in self.user.summary_exporters:
            if user_exporter.format == "html" and user_exporter.summary_type in ["detailed", "both"]:
                self.additional_html_formatting = True
                break

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> "PipelineConfig":
        """Load configuration from a YAML file."""
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Parse user config
        user_data = data.get("user_config", {})
        user = UserConfig.from_dict(user_data)

        # Parse orchestrator configs (list of configs)
        orchestrator_data = data.get("orchestrator_config", [])
        orchestrator_configs = [
            OrchestratorConfig.from_dict(cfg) for cfg in orchestrator_data
        ]

        return cls(user=user, orchestrator_configs=orchestrator_configs)

    @classmethod
    def from_dict(cls, data: dict) -> "PipelineConfig":
        """Create a PipelineConfig from a dictionary."""
        user_data = data.get("user_config", {})
        user = UserConfig.from_dict(user_data)

        orchestrator_data = data.get("orchestrator_config", [])
        orchestrator_configs = [
            OrchestratorConfig.from_dict(cfg) for cfg in orchestrator_data
        ]

        return cls(user=user, orchestrator_configs=orchestrator_configs)
