import streamlit as st
from app.services.agents import get_orchestrator, get_rag_agent
from app.ui.components.code_preview import html_preview
from app.ui.theme import stable_code_block

# 👇 Agregar esto arriba del archivo
import re

_HIDE_TOKENS = [
    r"hover:hidden", r"group-hover:hidden",
    r"hover:opacity-0", r"group-hover:opacity-0",
    r"hover:invisible", r"group-hover:invisible",
    r"hover:collapse", r"group-hover:collapse",
    r"hover:scale-0", r"group-hover:scale-0",
]
_TAG_RE = re.compile(r"<(div|section|main|article|header|footer|body)\b[^>]*>", re.I)

def neutralize_root_hover_hide(html: str) -> str:
    """Quita tokens 'hover:*' que ocultarían TODO el preview al pasar el mouse."""
    if not html:
        return html
    m = _TAG_RE.search(html)
    if not m:
        return html
    tag = m.group(0)

    def _fix_classes(mm: re.Match) -> str:
        classes = mm.group(1)
        for tok in _HIDE_TOKENS:
            classes = re.sub(rf"(?<!\S){tok}(?!\S)", "", classes, flags=re.I)
        classes = re.sub(r"\s+", " ", classes).strip()
        return f'class="{classes}"'

    new_tag = re.sub(r'class\s*=\s*"(.*?)"', _fix_classes, tag, count=1, flags=re.I)
    if new_tag == tag:
        return html

    start, end = m.span()
    return html[:start] + new_tag + html[end:]


import streamlit as st
import uuid


def render():
    st.header("🔎 Query Interface")
    mode = st.radio(
        "Modo",
        ["RAG Search (HTML Patterns)", "Prompt → HTML"],
        horizontal=True
    )

    c1, c2 = st.columns([3,1])
    with c1:
        query = st.text_area(
            "Ingresá tu consulta o prompt de UI",
            placeholder="• RAG: 'dashboard con sidebar y cards'\n• Prompt → HTML: 'dark dashboard con sidebar, cards y header'",
            height=120
        )
    with c2:
        if mode == "RAG Search (HTML Patterns)":
            top_k = st.slider("Top resultados", 1, 10, 5)
            custom = ""
        else:
            custom = st.text_area("Instrucciones opcionales", height=120, placeholder="Tailwind, glassmorphism, mobile-first…")
            save = st.checkbox("Guardar código generado", value=True)

    if mode == "RAG Search (HTML Patterns)":
        if st.button("🚀 Buscar patrones", type="primary", disabled=not query.strip()):
            rag = get_rag_agent()
            if not rag:
                st.error("RAG agent no disponible.")
                return
            with st.spinner("Buscando patrones HTML/CSS…"):
                visual_analysis = {"analysis_text": query.strip(), "components": [], "layout": "unknown", "style": "modern"}
                patterns = rag.invoke(visual_analysis, top_k=top_k)

            if patterns:
                st.subheader(f"🔍 {len(patterns)} patrones similares")
                for i, (doc_id, chunk, meta, score) in enumerate(patterns, 1):
                    with st.expander(f"Pattern #{i} — {meta.get('filename', doc_id)} (score {score:.3f})"):
                        st.markdown(f"**Tipo:** {meta.get('doc_type','?')} — **Desc.:** {meta.get('description','—')}")
                        html_code = meta.get("html_code", chunk)
                        stable_code_block(html_code[:1500] + ("..." if len(html_code)>1500 else ""), language="html")
                        with st.popover("👁️ Previsualizar"):
                             safe_html = neutralize_root_hover_hide(html_code)
                             html_preview(safe_html)
            else:
                st.warning("Sin resultados, probá otra descripción.")
    else:
        if st.button("🚀 Generar desde Prompt", type="primary", disabled=not query.strip()):
            orch = get_orchestrator()
            if not orch:
                st.error("Orchestrator no disponible.")
                return
            with st.spinner("Generando HTML/Tailwind…"):
                import asyncio
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(
                    orch.send_prompt_to_code_agent(prompt_text=query.strip(), patterns=[], custom_instructions=custom.strip())
                )
            if "error" in result and not result.get("html_code"):
                st.error(f"Falló la generación: {result['error']}")
                return
            html_code = result.get("html_code", "")

            st.subheader("💻 Código generado")
            render_code = html_code or "<!-- empty -->"

            stable_code_block(render_code, language="html", key="gen_code_block")
            
            with st.expander("🛠️ Detalles"):
                st.json(result.get("generation_metadata", {}))
                st.json(result.get("visual_analysis_summary", {}))
            st.subheader("🌐 Preview")
            safe_html = neutralize_root_hover_hide(html_code)
            html_preview(safe_html)
            if html_code and st.checkbox("Guardar resultado (artifacts)"):
                from src.agents.orchestator_agent.utils import save_generated_code
                try:
                    p = save_generated_code(result)
                    st.success(f"Guardado en: {p}")
                except Exception as e:
                    st.warning(f"No se pudo guardar: {e}")
