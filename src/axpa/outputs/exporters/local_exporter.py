from pathlib import Path
from datetime import datetime
from .base import BaseExporter


class LocalExporter(BaseExporter):
    """Export results to local files."""

    def __init__(self, output_dir: str = "./outputs/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def export(self, content: str, destination: str, format: str = "markdown") -> dict:
        """
        Export results to a local file.

        Args:
            content: The content to export
            destination: Directory name
            format: Output format - "markdown" or "html"

        Returns:
            Dict with status and file path
        """
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extension = "md" if format == "markdown" else "html"
            filename = f"report_{timestamp}.{extension}"
            filepath = self.output_dir / Path(destination) / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)

            content = content.strip()

            # Write to file
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            return {
                "status": "success",
                "message": f"Report saved to {filepath}",
                "filepath": str(filepath)
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
