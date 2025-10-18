"""Mock implementation of the Code Agent for mocking purposes."""

from datetime import datetime
from typing import Any
from loguru import logger


class CodeAgentMock:
    def invoke(
        self, patterns: list[tuple], visual_analysis: dict[str, Any], custom_instructions: str = ""
    ) -> dict[str, Any]:
        """Mock implementation of the Code Agent's invoke method."""
        logger.debug("MockCodeAgent invoked")
        return {
            "html_code": "<html><body><h1>Generated Code Mock</h1></body></html>",
            "generation_metadata": {
                "model_used": "mock-model",
                "patterns_used": len(patterns),
                "visual_components": visual_analysis.get("components", []),
                "custom_instructions": custom_instructions.strip() if custom_instructions else "",
                "timestamp": datetime.now().isoformat(),
            },
            "visual_analysis_summary": {
                "components": visual_analysis.get("components", []),
                "layout": visual_analysis.get("layout", "unknown"),
                "style": visual_analysis.get("style", "modern"),
            },
        }
