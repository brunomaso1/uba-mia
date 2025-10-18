import json
import re
from typing import Any, Dict
from guardrails import Guard, OnFailAction
from guardrails_grhub_valid_json import ValidJson
from guardrails_grhub_web_sanitization import WebSanitization
from loguru import logger
import html
from .code_agent import CodeAgent
from ..guardrails.schemas.code_agent_schema import OUTPUT_SCHEMA
from ..guardrails.validators.valid_html import IsHTMLField
from ..guardrails.validators.valid_schema_json import ValidSchemaJson


class CodeAgentWithGuardrails:
    """Wraps CodeAgent with schema + HTML validation and aggressive de-risking."""

    output_schema = OUTPUT_SCHEMA

    def __init__(self, agent: CodeAgent):
        logger.debug("Initializing CodeAgentWithGuardrails")
        self.agent = agent

        # Validate JSON-ness, then JSON Schema, then that html_code looks like HTML.
        self.output_guard = Guard.for_string(
            validators=[
                ValidJson(on_fail=OnFailAction.NOOP),
                ValidSchemaJson(json_schema=self.output_schema, on_fail=OnFailAction.EXCEPTION),
                IsHTMLField(on_fail=OnFailAction.EXCEPTION, property="html_code"),
            ]
        )

        # Final web sanitization (after we pre-strip dangerous bits).
        self.sanitization_guard = Guard().use(WebSanitization, on_fail="exception")

    # ----------------------------- helpers -----------------------------

    def _ensure_schema_minimums(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure required fields exist and satisfy minItems, types, etc."""
        out = dict(payload or {})

        # generation_metadata
        gm = dict(out.get("generation_metadata") or {})
        if not isinstance(gm.get("model_used"), str):
            gm["model_used"] = getattr(self.agent, "model", "unknown")
        if not isinstance(gm.get("patterns_used"), int):
            gm["patterns_used"] = 0
        vc = gm.get("visual_components")
        if not isinstance(vc, list) or len(vc) == 0:
            gm["visual_components"] = ["from_prompt"]  # minItems=1
        if not isinstance(gm.get("custom_instructions"), str):
            gm["custom_instructions"] = ""
        if not isinstance(gm.get("timestamp"), str) or not gm["timestamp"]:
            from datetime import datetime

            gm["timestamp"] = datetime.now().isoformat()
        out["generation_metadata"] = gm

        # visual_analysis_summary
        vas = dict(out.get("visual_analysis_summary") or {})
        comps = vas.get("components")
        if not isinstance(comps, list) or len(comps) == 0:
            vas["components"] = [{"id": "auto_0", "type": "container"}]
        if not isinstance(vas.get("layout"), str) or not vas.get("layout"):
            vas["layout"] = "unknown"
        if not isinstance(vas.get("style"), str) or not vas.get("style"):
            vas["style"] = "modern"
        out["visual_analysis_summary"] = vas

        # outer fields
        if not isinstance(out.get("html_code"), str):
            out["html_code"] = ""
        if not isinstance(out.get("status"), str):
            out["status"] = "OK"
        if not isinstance(out.get("used_component_ids"), list):
            out["used_component_ids"] = []
        if not isinstance(out.get("missing"), list):
            out["missing"] = []
        if not isinstance(out.get("hash"), str):
            out["hash"] = ""

        return out

    def _parse_guardrails_to_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Run Guard.parse and always return a Python dict (supports ValidationOutcome)."""
        outcome = self.output_guard.parse(json.dumps(data))

        # Newer Guardrails returns ValidationOutcome
        if hasattr(outcome, "validated_output"):
            vo = outcome.validated_output
            if isinstance(vo, str):
                return json.loads(vo)
            if isinstance(vo, (dict, list)):
                return vo
            return json.loads(str(vo))

        # Older versions could return a JSON string
        if isinstance(outcome, str):
            return json.loads(outcome)

        # Last resort
        return json.loads(str(outcome))

    def _validate_and_sanitize(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce schema, strip risky HTML, validate, then run final sanitization."""
        prepared = self._ensure_schema_minimums(payload)

        # Pre-strip anything that would trip the web sanitizer
        html_code = prepared.get("html_code", "") or ""
        prepared["html_code"] = html_code

        # Schema + "looks like HTML" validation
        validated = self._parse_guardrails_to_dict(prepared)

        # Final sanitization (guardrails plugin). If this fails, swap to fallback HTML.
        try:
            encoded_html = html.escape(html_code)
            self.sanitization_guard.validate(encoded_html)
        except Exception as e:
            logger.error("Web sanitization failed: {}", e, exc_info=True)
            validated["html_code"] = self.agent._get_fallback_html()
            validated["status"] = "FALLBACK_HTML"
            gm = dict(validated.get("generation_metadata") or {})
            gm["error"] = f"Sanitization failed: {e}"
            validated["generation_metadata"] = gm

        return validated

    # ------------------------------ public ------------------------------

    def invoke_from_prompt(self, prompt_text: str, patterns=None, custom_instructions: str = "") -> dict:
        """Generate from natural-language prompt (no visual analysis)."""
        patterns = patterns or []
        result = self.agent.invoke_from_prompt(prompt_text, patterns, custom_instructions)
        return self._validate_and_sanitize(result)

    def invoke(self, patterns, visual_analysis, custom_instructions=""):
        va = dict(visual_analysis or {})
        va.setdefault("components", [])
        va.setdefault("layout", "unknown")
        va.setdefault("style", "modern")

        result = self.agent.invoke(patterns or [], va, custom_instructions or "")
        return self._validate_and_sanitize(result)
