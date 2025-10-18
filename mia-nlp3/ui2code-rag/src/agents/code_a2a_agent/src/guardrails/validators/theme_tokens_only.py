import json, re
from typing import Dict, Any, Set, List, Optional
from bs4 import BeautifulSoup
from guardrails import OnFailAction
from loguru import logger

_COLOR_BRACKET_RE = re.compile(r"(?:^|\s)(?:bg|text|border)-\[\#([0-9a-fA-F]{6})\](?:\s|$)")
_SPACING_BRACKET_RE = re.compile(
    r"(?:^|\s)(?:p|px|py|pt|pb|pl|pr|m|mx|my|mt|mb|ml|mr|gap)-\[(\d+)px\](?:\s|$)"
)

class ThemeTokensOnly:
    """
    - Prohíbe 'style=' inline.
    - Colors bg/text/border-[#XXXXXX] should be from the palette.
    - Spacing arbitrarios p-[16px] etc. should be multiples of spacing_unit.
    """
    rail_alias = "theme_tokens_only"
    name = "theme_tokens_only"

    def __init__(self, allowed_palette_hex: Set[str], spacing_unit: int, on_fail: OnFailAction = OnFailAction.EXCEPTION):
        self.allowed = {h.lower() for h in allowed_palette_hex}
        self.spacing_unit = int(spacing_unit)
        self.on_fail = on_fail

    def _fail(self, msg: str):
        if self.on_fail == OnFailAction.EXCEPTION:
            raise ValueError(msg)
        logger.warning(msg)

    def validate(self, value: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        try:
            result = json.loads(value)
            html_code = result.get("html_code", "")
        except Exception:
            self._fail("[ThemeTokensOnly] Result not parseable or missing 'html_code'.")
            return value

        soup = BeautifulSoup(html_code, "html.parser")

        for tag in soup.find_all(True):
            # 1) Sin estilos inline
            if tag.has_attr("style"):
                self._fail("[ThemeTokensOnly] style= inline no permitted.")
            # 2) Validaciones por clases
            cls: List[str] = []
            if tag.has_attr("class"):
                cls = tag["class"] if isinstance(tag["class"], list) else str(tag["class"]).split()
                class_str = " ".join(cls)

                for m in _COLOR_BRACKET_RE.finditer(class_str):
                    hexv = m.group(1).lower()
                    if hexv not in self.allowed:
                        self._fail(f"[ThemeTokensOnly] Color {hexv} not in allowed palette {self.allowed}.")

                for m in _SPACING_BRACKET_RE.finditer(class_str):
                    px = int(m.group(1))
                    if px % self.spacing_unit != 0:
                        self._fail(f"[ThemeTokensOnly] Spacing {px}px not multiple of spacing_unit={self.spacing_unit}.")

        return value
