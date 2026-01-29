from typing import Literal
from .base import BaseExporter
from .email_exporter import EmailExporter
from .local_exporter import LocalExporter

ExportDestination = Literal["email", "local"]
ExportFormat = Literal["html", "markdown"]


class ExporterDispatcher:
    def __init__(self):
        self._exporters: dict[ExportDestination, BaseExporter] = {
            "email": EmailExporter(),
            "local": LocalExporter(),
        }

    async def export(
        self,
        content: str,
        destination: str,
        export_destination: ExportDestination,
        export_format: ExportFormat = "html"
    ) -> dict:
        """
        Export results using the specified exporter.

        Args:
            content: The content to export
            destination: Where to send (email address or filename base)
            export_destination: The export destination type ("email" or "local")
            export_format: The format to use ("html" or "markdown")

        Returns:
            Dict with status and message
        """
        exporter = self._exporters.get(export_destination)
        if not exporter:
            raise ValueError(f"Unsupported export destination: {export_destination}")
        return await exporter.export(content, destination, format=export_format)
