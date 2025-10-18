# TODO: Posibles mejoras
# - Tests
# - Los returns tendrían que ser objetos (de Pydantic?), no dicts
import os, json, textwrap
from typing import Any, Dict, List, Set
from datetime import datetime
import openai
from loguru import logger

# Custom dependencies
from ..config import settings
from ..texts.prompts import SYSTEM_PROMPT, GENERATION_PROMPT_TEMPLATE
from ..texts.html_examples import write_examples, FALLBACK_HTML

OPENROUTER_API_KEY = settings.openrouter_api_key
OPENROUTER_BASE_URL = settings.openrouter_base_url
CODE_MODEL = settings.openrouter_code_model
OPENAI_KEY = settings.openai_key
OPENAI_MODEL = settings.openai_code_model
MAX_TOKENS = settings.max_tokens
TEMPERATURE = min(0.2, settings.temperature or 0.2)  # bajar temp por seguridad


class CodeAgent:
    """
    Genera HTML/Tailwind estricto en JSON:
    {
      "status": "OK" | "INSUFFICIENT_EVIDENCE",
      "hash": "<eco del visual_analysis.hash>",
      "used_component_ids": ["..."],
      "missing": ["..."],           # optional when status == "INSUFFICIENT_EVIDENCE"
      "html_code": "<html>...</html>"
    }
    """

    def __init__(self):
        if not (OPENROUTER_API_KEY or OPENAI_KEY):
            raise ValueError("No API key found for available providers. Please set one in the environment.")
        if OPENROUTER_API_KEY:
            self.client = openai.OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)
            self.model = CODE_MODEL
            self.use_openrouter = True
        else:
            if OPENAI_KEY:
                self.client = openai.OpenAI(api_key=OPENAI_KEY)
                self.model = OPENAI_MODEL
                self.use_openrouter = False

    # ------------------------------- PUBLIC -------------------------------

    def invoke_from_prompt(
        self, prompt_text: str, patterns: list[tuple] | None = None, custom_instructions: str = ""
    ) -> dict[str, Any]:
        """Generates an HTML/Tailwind only from a prompt (without visual analysis)."""

        pattern_context = self._format_patterns_for_generation(patterns or [])

        # IMPORTANT: use the HTML-only system prompt (not the JSON one)
        system = self._system_contract_html()

        user_prompt = f"""
    Generate a clean, responsive HTML page using Tailwind CSS based on this UI description.

    Constraints:
    - Tailwind utilities only (no <style>, no inline style).
    - Semantic HTML where possible.
    - Accessible (labels/ARIA when applicable).
    - Keep it minimal and modern.

    UI description:
    {prompt_text}

    Inspiration snippets (do NOT copy tokens blindly):
    {pattern_context}

    Extra requirements:
    {custom_instructions or "(none)"}

    Return ONLY raw HTML (no JSON, no markdown, no backticks).
        """.strip()

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )

        generated = (response.choices[0].message.content or "").strip()

        # NEW: robust extraction of raw HTML from any shape
        html_out = self._extract_html_from_any(generated)
        if not html_out:
            # try old fence cleaner as a fallback
            html_out = self._clean_generated_code(generated)

        if not html_out:
            html_out = self._get_fallback_html()

        # avoid empty minItems/arrays
        visual_components = ["from_prompt"]
        summary_components = [{"id": "prompt_0", "type": "container"}]

        return {
            "html_code": html_out,
            "generation_metadata": {
                "model_used": self.model,
                "patterns_used": len(patterns or []),
                "visual_components": visual_components,
                "custom_instructions": (custom_instructions or "").strip(),
                "timestamp": datetime.now().isoformat(),
            },
            "visual_analysis_summary": {
                "components": summary_components,
                "layout": "from_prompt",
                "style": "modern",
            },
            "status": "OK",
            "hash": "",
            "used_component_ids": [],
            "missing": [],
        }

    def _get_generation_prompt(
        self, visual_analysis: dict[str, Any], pattern_context: str, custom_instructions: str = ""
    ) -> str:
        """Construct the full prompt for code generation"""
        logger.debug(f"Visual analysis for prompt: {visual_analysis}")
        logger.debug(f"Pattern context for prompt: {pattern_context}")
        logger.debug(f"Custom instructions for prompt: {custom_instructions}")

        components = ", ".join(str(c) for c in visual_analysis.get("components", []))
        layout = visual_analysis.get("layout", "modern layout")
        style = visual_analysis.get("style", "clean and modern")
        color_scheme = visual_analysis.get("color_scheme", "neutral colors")

        logger.debug(f"Color scheme for prompt: {color_scheme}")
        logger.debug(f"Layout for prompt: {layout}")
        logger.debug(f"Components for prompt: {components}")
        logger.debug(f"Style for prompt: {style}")

        ci_text = (
            f"\n\nADDITIONAL INSTRUCTIONS:\n{custom_instructions.strip()}"
            if custom_instructions and custom_instructions.strip()
            else ""
        )

        logger.debug(f"Final custom instructions text for prompt: {ci_text}")
        prompt = GENERATION_PROMPT_TEMPLATE.format(
            components=components,
            layout=layout,
            style=style,
            color_scheme=color_scheme,
            pattern_context=pattern_context,
            custom_instructions=ci_text,
        )

        logger.debug(f"Generated prompt text: {prompt}")

        return prompt

    def invoke(
        self, patterns: list[tuple], visual_analysis: dict[str, Any], custom_instructions: str = ""
    ) -> dict[str, Any]:
        try:
            pattern_context = self._format_patterns_for_generation(patterns)
            instructions_context = custom_instructions or "No hay instrucciones adicionales."

            prompt = self._get_generation_prompt(visual_analysis, pattern_context, instructions_context)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
            )

            generated_code = (response.choices[0].message.content or "").strip()
            cleaned_code = self._clean_generated_code(generated_code).strip()

            if not cleaned_code:
                cleaned_code = self._get_fallback_html()

            # Validate that generated HTML matches expected components
            raw_components = visual_analysis.get("components", [])
            validation_result = self._validate_html_components(cleaned_code, raw_components)
            if not validation_result["valid"]:
                logger.warning(f"⚠️⚠️⚠️ HALLUCINATION DETECTED ⚠️⚠️⚠️")
                logger.warning(f"   Message: {validation_result['message']}")
                logger.warning(f"   Expected components: {raw_components}")
                logger.warning(f"   Extra components found: {validation_result['extra_components']}")
                logger.warning(f"   🚨 The model generated sections that were NOT in the visual analysis!")

            if raw_components and isinstance(raw_components[0], dict):
                components_for_metadata = [c.get("type", "") for c in raw_components if isinstance(c, dict)]
            else:
                components_for_metadata = raw_components

            # for summary according to schema
            if not raw_components:
                summary_components = [{"id": "auto_0", "type": "container"}]
            else:
                summary_components = raw_components

            return {
                "html_code": cleaned_code or self._get_fallback_html(),
                "generation_metadata": {
                    "model_used": self.model,
                    "patterns_used": len(patterns),
                    "visual_components": components_for_metadata,
                    "custom_instructions": instructions_context.strip() if instructions_context else "",
                    "timestamp": datetime.now().isoformat(),
                },
                "visual_analysis_summary": {
                    "components": summary_components,
                    "layout": visual_analysis.get("layout", "unknown"),
                    "style": visual_analysis.get("style", "modern"),
                },
            }

        except Exception as e:
            logger.error(f"Code Agent invocation failed: {e}")
            return {
                "html_code": self._get_fallback_html(),
                "generation_metadata": {
                    "model_used": getattr(self, "model", "unknown"),
                    "patterns_used": len(patterns) if patterns else 0,
                    "visual_components": [],
                    "custom_instructions": custom_instructions.strip() if custom_instructions else "",
                    "timestamp": datetime.now().isoformat(),
                    "error": f"{e}",
                },
                "visual_analysis_summary": {
                    "components": visual_analysis.get("components", []),
                    "layout": visual_analysis.get("layout", "unknown"),
                    "style": visual_analysis.get("style", "modern"),
                },
                "status": "FALLBACK_HTML",
            }

    # ------------------------------- HELPERS ------------------------------

    # Add this helper inside CodeAgent
    def _extract_html_from_any(self, content: str) -> str:
        """Try hard to get raw HTML from any model output (JSON wrapper, code fences, plain)."""
        s = (content or "").strip()

        # a) Try JSON like {"html": "..."} or {"html_code": "..."}
        if s.startswith("{"):
            try:
                obj = json.loads(s)
                if isinstance(obj, dict):
                    for key in ("html", "html_code", "content"):
                        val = obj.get(key)
                        if isinstance(val, str) and (
                            "<html" in val or "<!DOCTYPE html" in val or "<nav" in val or "<div" in val
                        ):
                            return val.strip()
            except Exception:
                pass

        # b) Try fenced blocks ```html ... ```
        if "```html" in s:
            start = s.find("```html") + len("```html")
            end = s.find("```", start)
            if end != -1:
                return s[start:end].strip()

        # c) Try generic fences ```
        if "```" in s:
            start = s.find("```") + 3
            end = s.find("```", start)
            if end != -1:
                candidate = s[start:end].strip()
                if "<html" in candidate or "<!DOCTYPE html" in candidate:
                    return candidate

        # d) Try to slice from <!DOCTYPE ...> to </html>
        if "<!DOCTYPE html" in s and "</html>" in s:
            start = s.find("<!DOCTYPE html")
            end = s.rfind("</html>")
            return s[start : end + len("</html>")].strip()

        # e) As a last resort, if we see HTML-ish tags, return as-is
        if "<html" in s or "<!DOCTYPE html" in s or "<nav" in s or "<div" in s:
            return s

        # f) Give up -> empty (caller will fallback)
        return ""

    def create_sample_examples(self, examples_dir):
        """Write HTML/CSS reference examples"""
        write_examples(examples_dir)

    def _system_contract(self) -> str:

        return (
            "You are a deterministic UI-to-HTML code generator. "
            "Output ONLY a single JSON object with the required fields. No prose, no markdown."
        )

    # Add this method inside CodeAgent
    def _system_contract_html(self) -> str:
        """System prompt for prompt-only mode: return raw HTML, never JSON."""
        return (
            "You are a deterministic UI-to-HTML generator. "
            "Return ONLY a complete raw HTML document (with <!DOCTYPE html>). "
            "Do not return JSON. Do not return Markdown fences. "
            "No explanations."
        )

    def _format_patterns_for_generation(self, patterns: List[tuple]) -> str:
        """
        Format RAG patterns with FULL HTML code for the model to use as structural base.
        Patterns come enriched with complete html_code from RAGAgent.
        """
        if not patterns:
            return "No se han encontrado patrones similares. Genera desde cero usando buenas prácticas."

        formatted = []
        for i, (doc_id, chunk, metadata, score) in enumerate(patterns, 1):
            # Extract metadata
            if isinstance(metadata, dict):
                source_name = metadata.get("filename", metadata.get("source", "unknown"))
                description = metadata.get("description", "No description available")
                doc_type = metadata.get("doc_type", "unknown")
                # Get FULL html_code (enriched by RAGAgent)
                html_code = metadata.get("html_code", chunk)
            else:
                source_name = getattr(metadata, "filename", getattr(metadata, "source", "unknown"))
                description = getattr(metadata, "description", "No description available")
                doc_type = getattr(metadata, "doc_type", "unknown")
                html_code = getattr(metadata, "html_code", chunk)

            # Show more code for better context (2000 chars instead of 600)
            code_snippet = html_code[:2000] + ("\n... [truncated]" if len(html_code) > 2000 else "")

            block = textwrap.dedent(
                f"""\
                === Pattern {i} (Relevance: {score:.2f}) ===
                Source: {source_name}
                Type: {doc_type}
                Description: {description}

                HTML Structure (use as STRUCTURAL REFERENCE):
                ```html
                {code_snippet}
                ```

                Key points to adopt:
                - Component hierarchy and organization
                - Tailwind utility class patterns
                - Responsive design approach
                - Layout structure (grid/flex)
                """
            ).strip()
            formatted.append(block)

        return "\n\n".join(formatted)

    def _components_brief(self, visual_analysis: Dict[str, Any]) -> str:
        comps = visual_analysis.get("components", [])
        if not isinstance(comps, list):
            return "[]"
        items = []
        for c in comps:
            if isinstance(c, dict):
                cid = c.get("id", "")
                ctype = c.get("type", "")
                bbox = c.get("bbox", [])
                txt = (c.get("evidence", {}) or {}).get("ocr", "")
                items.append(f"{cid}:{ctype}@{bbox} text='{(txt or '')[:30]}'")
            else:
                items.append(str(c))
        return "[" + "; ".join(items) + "]"

    def _extract_component_ids(self, visual_analysis: Dict[str, Any]) -> List[str]:
        comps = visual_analysis.get("components", [])
        ids = [c.get("id") for c in comps if isinstance(c, dict) and c.get("id")]
        return ids

    def _extract_palette_hex(self, visual_analysis: Dict[str, Any]) -> List[str]:
        pal = visual_analysis.get("palette", [])
        hexes = []
        for p in pal:
            h = (p or {}).get("hex")
            if isinstance(h, str) and h.startswith("#") and len(h) == 7:
                hexes.append(h.lower())
        return hexes or ["#111111", "#ffffff"]

    def _build_strict_json_prompt(
        self,
        analysis_hash: str,
        component_ids: List[str],
        palette_hex: List[str],
        spacing_unit: int,
        visual_analysis: Dict[str, Any],
        pattern_context: str,
        custom_instructions: str,
    ) -> str:
        components_brief = self._components_brief(visual_analysis)
        layout = visual_analysis.get("layout", "unknown")
        style = visual_analysis.get("style", "modern")

        contract = textwrap.dedent(
            f"""\
            Produce ONLY a single JSON object with this exact shape:

            {{
              "status": "OK" | "INSUFFICIENT_EVIDENCE",
              "hash": "{analysis_hash}",
              "used_component_ids": ["..."],
              "missing": ["..."],                       // optional when status == "INSUFFICIENT_EVIDENCE"
              "html_code": "<!DOCTYPE html>...HTML..."
            }}

            HARD RULES:
            - Echo EXACTLY the provided hash in field "hash".
            - You may ONLY use components with ids from this set: {component_ids}.
            - Copy textual content from components' OCR evidence when present (no invented copy).
            - Restricted tokens:
                * Colors: ONLY these hex tokens (Tailwind bracket syntax allowed): {palette_hex}
                  Examples: bg-[#111111], text-[#ffffff], border-[#0ea5e9]
                * Spacing: ONLY multiples of {spacing_unit} px when using bracketed utilities. Example: p-[16px].
            - Do NOT use inline styles or <style> blocks. Tailwind utility classes ONLY.
            - Do NOT invent components, colors, classes or content outside the allowed set.
            - If information is insufficient (e.g., no reliable components), return status="INSUFFICIENT_EVIDENCE" and list "missing".

            CONTEXT:
            - Layout: {layout}
            - Style: {style}
            - Components (brief): {components_brief}

            PATTERN SNIPPETS (for structure inspiration; DO NOT copy styling tokens outside allowed lists):
            {pattern_context}

            USER EXTRA REQUIREMENTS (optional):
            {custom_instructions or "(none)"}
            """
        )
        return contract

    def _parse_json_strict_or_recover(self, content: str, analysis_hash: str) -> Dict[str, Any]:
        """Intenta json.loads; si falla, intenta extraer ```json ...``` o limpia HTML."""
        try:
            obj = json.loads(content)
            # normalization
            obj.setdefault("status", "OK")
            obj.setdefault("hash", analysis_hash)
            obj.setdefault("used_component_ids", [])
            obj.setdefault("html_code", "")
            return obj
        except Exception:
            pass

        # 2) ```json ... ```
        start = content.find("```json")
        if start != -1:
            start += len("```json")
            end = content.find("```", start)
            if end != -1:
                try:
                    obj = json.loads(content[start:end].strip())
                    obj.setdefault("status", "OK")
                    obj.setdefault("hash", analysis_hash)
                    obj.setdefault("used_component_ids", [])
                    obj.setdefault("html_code", "")
                    return obj
                except Exception:
                    pass

        # 3) Last resource: clean HTML
        cleaned = self._clean_generated_code(content)
        return {
            "status": "OK",
            "hash": analysis_hash,
            "used_component_ids": [],
            "html_code": cleaned if cleaned else self._get_fallback_html(),
        }

    def _clean_generated_code(self, code: str) -> str:
        """Quita fences de markdown si vinieran."""
        if "```html" in code:
            start = code.find("```html") + 7
            end = code.find("```", start)
            if end != -1:
                code = code[start:end]
        elif "```" in code:
            start = code.find("```") + 3
            end = code.find("```", start)
            if end != -1:
                code = code[start:end]
        return code.strip()

    def _get_fallback_html(self) -> str:
        return FALLBACK_HTML

    def _validate_html_components(self, html_code: str, expected_components: list) -> dict:
        """
        Validates that generated HTML only contains expected components.
        Returns: {"valid": bool, "extra_components": list, "message": str}
        """
        import re

        # Common sections that shouldn't appear if not in analysis
        common_sections = {
            "header": r"<header[^>]*>",
            "nav": r"<nav[^>]*>",
            "footer": r"<footer[^>]*>",
            "aside": r"<aside[^>]*>",
        }

        # Normalize expected_components to lowercase strings
        expected_lower = []
        for c in expected_components:
            if isinstance(c, dict):
                comp_type = c.get("type", "").lower()
                if comp_type:
                    expected_lower.append(comp_type)
            else:
                expected_lower.append(str(c).lower())

        # Detect components present in HTML
        found_components = []
        for name, pattern in common_sections.items():
            if re.search(pattern, html_code, re.IGNORECASE):
                found_components.append(name)

        # Identify extra components (present but not expected)
        extra = []
        for comp in found_components:
            # Check if component is mentioned in expected_components
            is_expected = any(comp in exp or exp in comp for exp in expected_lower)
            # Also check common aliases
            aliases = {"nav": ["navigation", "navbar", "menu"], "header": ["top", "banner"], "footer": ["bottom"]}
            if not is_expected and comp in aliases:
                is_expected = any(alias in " ".join(expected_lower) for alias in aliases[comp])

            if not is_expected:
                extra.append(comp)

        if extra:
            return {
                "valid": False,
                "extra_components": extra,
                "message": f"Generated HTML contains unexpected sections: {', '.join(extra)}. These were not in the visual analysis.",
            }

        return {"valid": True, "extra_components": [], "message": "HTML components match visual analysis"}
