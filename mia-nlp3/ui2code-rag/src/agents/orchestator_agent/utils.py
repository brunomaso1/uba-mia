"""Utility functions for the Orchestrator Agent."""

from datetime import datetime
import json
from typing import Any

# Local dependencies
from src.config import temp_images_dir
from src.config import generated_code_dir


def save_analysis_result(analysis_result: dict[str, Any], filename: str = None) -> str:
    """
    Save analysis result to temporary directory

    Args:
        analysis_result: Analysis result dictionary
        filename: Optional filename, auto-generated if not provided

    Returns:
        Path to saved file
    """
    try:
        # Ensure temp directory exists
        temp_dir = temp_images_dir()
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename if not provided
        if filename is None:
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_{timestamp}.json"

        # Save to file
        output_path = temp_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False)

        return str(output_path)

    except Exception as e:
        raise ValueError(f"Failed to save analysis result: {str(e)}")


def save_generated_code(code_result: dict[str, Any], filename: str = None) -> str:
    """
    Save generated code to file

    Args:
        code_result: Generated code result
        filename: Optional filename

    Returns:
        Path to saved file
    """
    try:
        # Ensure output directory exists
        output_dir = generated_code_dir()
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_{timestamp}.html"

        if not filename.endswith(".html"):
            filename += ".html"

        # Save HTML file
        output_path = output_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(code_result.get("html_code", ""))

        # Save metadata
        metadata_path = output_path.with_suffix(".json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "generation_metadata": code_result.get("generation_metadata", {}),
                    "visual_analysis_summary": code_result.get("visual_analysis_summary", {}),
                    "html_file": filename,
                    "created_at": datetime.now().isoformat(),
                },
                f,
                indent=2,
            )

        return str(output_path)

    except Exception as e:
        raise ValueError(f"Failed to save generated code: {str(e)}")
