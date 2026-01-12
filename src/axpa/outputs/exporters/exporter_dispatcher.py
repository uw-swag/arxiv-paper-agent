from typing import Literal
from .base import BaseExporter
from .email_exporter import EmailExporter

ExportPreference = Literal["email"]

class ExporterDispatcher:
    def __init__(self):
        self._exporters: dict[ExportPreference, BaseExporter] = {
            "email": EmailExporter(),
        }
    
    async def export(self, result: dict, destination: str, preference: ExportPreference) -> dict:
        exporter = self._exporters.get(preference)
        if not exporter:
            raise ValueError(f"Unsupported export preference: {preference}")
        return await exporter.export(result, destination)