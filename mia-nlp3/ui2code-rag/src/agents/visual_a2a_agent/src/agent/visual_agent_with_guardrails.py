# src/agents/visual_agent/src/agent/visual_agent_with_guardrails.py

"""Proxy para el agente visual que maneja la validación de salidas usando Guardrails."""
import json
from typing import Any, Dict
from guardrails import Guard, OnFailAction
from PIL import Image
from loguru import logger

from guardrails_grhub_valid_json import ValidJson
from ..guardrails.validators.valid_schema_json import ValidSchemaJson
from ..guardrails.schemas.visual_agent_schema import OUTPUT_SCHEMA

from .visual_agent import VisualAgent

class VisualAgentWithGuardrails:
    output_schema = OUTPUT_SCHEMA

    def __init__(self, agent: VisualAgent, on_fail: OnFailAction = OnFailAction.EXCEPTION):
        logger.debug("Inicializando VisualAgentWithGuardrails")
        self.agent = agent
        self.on_fail = on_fail

    def _build_guard(self) -> Guard:
        return Guard.for_string(
            validators=[
                ValidJson(on_fail=OnFailAction.EXCEPTION),
                ValidSchemaJson(json_schema=self.output_schema, on_fail=OnFailAction.EXCEPTION),
            ]
        )

    @staticmethod
    def _normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes keys so that the schema accepts current variants."""
        if not isinstance(raw, dict):
            return raw

        # Ensure analysis_text is present (even if empty)
        raw.setdefault("analysis_text", "")

        # If we only have image_meta {w,h}, optionally materialize image_metadata
        if "image_meta" in raw and "image_metadata" not in raw:
            try:
                w = int(raw["image_meta"]["w"])
                h = int(raw["image_meta"]["h"])
                raw["image_metadata"] = {
                    "dimensions": {"width": w, "height": h, "aspect_ratio": (w / h) if h else 0.0},
                    "dominant_colors": [],   
                    "layout_hints": {},
                    "file_size": 0,
                    "format": "unknown",
                }
            except Exception:
                pass

        return raw

    @staticmethod
    def _coerce_guard_output_to_str(validated_output: Any) -> str:
        """
        Guardrails can return str or ValidationOutcome.
        Extract the JSON string regardless of version.
        """
        if isinstance(validated_output, str):
            return validated_output

        # Duck-typing over typic attributes
        for attr in ("output", "validated_output", "value", "raw_output"):
            s = getattr(validated_output, attr, None)
            if isinstance(s, str):
                return s

        raise TypeError(
            f"Guard.parse() returned {type(validated_output).__name__} and cannot extract JSON."
        )

    def invoke(self, image: Image) -> Dict[str, Any]:
        raw: Dict[str, Any] = self.agent.invoke(image)
        raw = self._normalize(raw)
        try:
            validated = self._build_guard().parse(json.dumps(raw))
            validated_str = self._coerce_guard_output_to_str(validated)
            spec: Dict[str, Any] = json.loads(validated_str)
            return spec

        except Exception as e:
            logger.error(f"Error during Visual Agent validation: {e}")
            if self.on_fail == OnFailAction.EXCEPTION:
                raise
            logger.warning("Returning raw output due to on_fail != EXCEPTION policy.")
            return raw
