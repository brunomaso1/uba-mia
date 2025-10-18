import re
import streamlit as st
import streamlit.components.v1 as components

_TAG_RE = re.compile(r"<(html|body|main|section|article|header|footer|div)\b[^>]*>", re.I)

# Elimina del primer contenedor tokens hover destructivos (ya lo tenías)
def _neutralize_root_hover_hide(html: str) -> str:
    if not html:
        return html
    m = _TAG_RE.search(html)
    if not m:
        return html
    tag = m.group(0)

    HIDE_RE = re.compile(
        r"(?<!\S)(?:(?:motion-\w+:)?(?:xs:|sm:|md:|lg:|xl:|2xl:)?(?:hover:|group-hover:))"
        r"(?:hidden|opacity-0(?:/\d+)?|invisible|collapse|scale-0)(?!\S)", re.I
    )
    strip_group = "group-hover:" in html

    def _fix_classes(mm: re.Match) -> str:
        classes = mm.group(1)
        classes = HIDE_RE.sub("", classes)
        if strip_group:
            classes = re.sub(r"(?<!\S)group(?!\S)", "", classes, flags=re.I)
        classes = re.sub(r"\s+", " ", classes).strip()
        return f'class="{classes}"'

    new_tag = re.sub(r'class\s*=\s*"(.*?)"', _fix_classes, tag, count=1, flags=re.I)
    if new_tag == tag:
        return html
    start, end = m.span()
    return html[:start] + new_tag + html[end:]


# Inyecta CSS que neutraliza hover utilities que oculten cosas (incluye group-hover y variantes responsive)
def _inject_hover_safety_css(html: str) -> str:
    style = """
<style id="hover-safety">
/* Neutralize Tailwind hover utilities that hide/collapse on hover, including responsive/group variants */
[class*="hover:hidden"]:hover,
.group:hover [class*="group-hover:hidden"] {
  display: revert !important;
  visibility: visible !important;
  opacity: 1 !important;
  pointer-events: auto !important;
}

[class*="hover:opacity-0"]:hover,
.group:hover [class*="group-hover:opacity-0"] {
  opacity: 1 !important;
  pointer-events: auto !important;
}

[class*="hover:invisible"]:hover,
.group:hover [class*="group-hover:invisible"] {
  visibility: visible !important;
  pointer-events: auto !important;
}

[class*="hover:collapse"]:hover,
.group:hover [class*="group-hover:collapse"] {
  display: revert !important;
  visibility: visible !important;
  pointer-events: auto !important;
}

/* Scale tricks that ‘vanish’ content */
[class*="hover:scale-0"]:hover,
.group:hover [class*="group-hover:scale-0"] {
  transform: none !important;
}

/* Safety: don't let a root-level hover apply global filters/animations */
:where(html, body):hover {
  filter: none !important;
}
</style>
""".strip()

    # Insert before </head>, otherwise before </body>, otherwise prepend
    if re.search(r"</head>", html, flags=re.I):
        return re.sub(r"</head>", style + "\n</head>", html, count=1, flags=re.I)
    if re.search(r"</body>", html, flags=re.I):
        return re.sub(r"</body>", style + "\n</body>", html, count=1, flags=re.I)
    return style + "\n" + html


def html_preview(html_code: str, height: int = 520):
    safe_html = _neutralize_root_hover_hide(html_code)
    safe_html = _inject_hover_safety_css(safe_html)
    components.html(html=safe_html, height=height, scrolling=True)
