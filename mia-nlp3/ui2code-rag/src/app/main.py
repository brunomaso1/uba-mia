# --- PATH FIX (dejar arriba de todo) ---
import os, sys, pathlib
FILE = pathlib.Path(__file__).resolve()
APP_DIR = FILE.parent
SRC_DIR = APP_DIR.parent
for p in (str(SRC_DIR), str(APP_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)
# ---------------------------------------
from src.config import create_all_directories
create_all_directories()

from app.ui.preloader import show_preloader, hide_preloader

import streamlit as st

# ⚠️ Seteamos el tema *antes* de cualquier UI:
st._config.set_option("theme.base", "dark")
st._config.set_option("theme.primaryColor", "#8B5CF6")          # ← violeta
st._config.set_option("theme.textColor", "#EDEAF5")
st._config.set_option("theme.backgroundColor", "#0B0B10")
st._config.set_option("theme.secondaryBackgroundColor", "#151621")

st.set_page_config(
    page_title="Multi-Agent UI-to-Code System",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

show_preloader(color="#8B5CF6", bg="#000000", message="Inicializando…")

import nest_asyncio
from loguru import logger

from app.ui.theme import set_theme_globals, apply_theme, violet_button
from app.services.agents import get_rag_agent
from app.services.rag_pipeline import get_legacy_pdf_pipeline
from src.config import project_dir

set_theme_globals(primary="#8B5CF6", font="montserrat")
apply_theme()

st.markdown("""
<style>
:root, .stApp, [data-testid="stAppViewContainer"]{
  --primary: #8B5CF6 !important;
  --primary-color: #8B5CF6 !important;
  --primaryColor:  #8B5CF6 !important;
  --button-primary-background-color: #8B5CF6 !important;
  --button-primary-text-color: #ffffff !important;
  --text-color: #EDEAF5 !important;
}
/* tipografía sí, color NO (no pongas violeta acá o pisás el blanco del botón) */
button, [data-testid^="baseButton"]{
  font-family: 'Montserrat','Roboto',sans-serif !important;
}
</style>
""", unsafe_allow_html=True)


nest_asyncio.apply()

# ========================= NAV (sidebar) =========================
# === Sidebar menu (Home + pages) ===
import re
from pathlib import Path
import streamlit as st

def pretty_label(path: str) -> str:
    """
    Convierte 'pages/01_query_interface.py' -> 'Query Interface'
    """
    name = Path(path).stem                # 01_query_interface
    name = re.sub(r"^\d+[_-]*", "", name) # query_interface
    name = name.replace("_", " ").replace("-", " ").strip()  # query interface
    return name.title()                   # Query Interface


def initialize_state():
    if "download_websight" not in st.session_state:
        st.session_state.download_websight = False
    if "rag_ready" not in st.session_state:
        st.session_state.rag_ready = False

def handle_download_websight_click():
    rag_agent = get_rag_agent()
    if not rag_agent:
        st.error("RAG agent no disponible.")
        return
    with st.spinner("Descargando e inicializando WebSight…"):
        try:
            ok = rag_agent.initialize_websight_rag_pipeline()
            if ok:
                st.session_state.download_websight = True
                st.success("✅ WebSight listo e indexado.")
            else:
                st.error("❌ Falló la inicialización de WebSight (ver logs).")
        except Exception as e:
            logger.exception(e)
            st.error(f"Error inicializando WebSight: {e}")

def print_rag_summary_status(rag_status: dict):
    total_docs = rag_status.get("total_documents", 0)
    total_chunks = rag_status.get("total_chunks", 0)
    st.success(f"✅ Corpus HTML/CSS: {total_docs} documentos ({total_chunks} patrones) listos")


def ensure_rag_ready():
    rag_agent = get_rag_agent()
    if not rag_agent:
        st.error("❌ No se pudo crear RAGAgent.")
        return None, {}

    rag_status = rag_agent.get_rag_status()
    if rag_status.get("status") == "ready":
        st.session_state.rag_ready = True
        st.session_state.download_websight = True
        return rag_agent, rag_status

    with st.spinner("Inicializando RAG del corpus local…"):
        try:
            ok = rag_agent.initialize_corpus_rag_pipeline()
        except Exception as e:
            logger.exception(e)
            ok = False

    if ok:
        rag_status = rag_agent.get_rag_status()
        st.session_state.rag_ready = True
        st.session_state.download_websight = True
        return rag_agent, rag_status

    st.session_state.rag_ready = False
    st.warning(
        "⚠️ El corpus de patrones HTML/CSS no está listo.\n"
        "- Podés depositar plantillas HTML propias en el corpus del proyecto.\n"
        "- O cargar el dataset de ejemplos **WebSight** para pruebas."
    )

    # Botón WebSight (forzado a violeta)
    if violet_button(
        "📦 Descargar dataset WebSight",
        key="ws_download",
        disabled=st.session_state.download_websight,
        on_click=handle_download_websight_click,
        help="Baja ejemplos HTML/CSS y los indexa para recuperación semántica.",
        full_width=False,
        color="var(--primary, #8B5CF6)",  # el mismo violeta del theme
    ):
        pass

    return rag_agent, rag_status

def main():
    initialize_state()
    _ = get_legacy_pdf_pipeline()  # precalentar PDF legacy
    rag_agent, rag_status = ensure_rag_ready()

    st.session_state["app_ready"] = True
    hide_preloader()

    st.title("🏠 Home")
    st.caption("Vision + RAG + Prompt-to-HTML (Tailwind) — con evaluaciones de retrieval")

    if rag_agent:
        if rag_status.get("status") == "ready":
            print_rag_summary_status(rag_status)
        else:
            st.info("Usá el menú **Menu** (izquierda) para ir a 'System Status' y ver más detalles.")

    st.markdown("---")
    st.subheader("Navegación rápida")
    st.info(
        "• **Query Interface**: búsqueda de patrones o Prompt→HTML\n"
        "• **UI to Code**: subir imagen y generar HTML/Tailwind\n"
        "• **Evaluaciones**: métricas de retrieval (MRR, nDCG, P@k, R@k)\n"
        "• **System Status** y **Corpus Information**"
    )

    from src.config import corpus_dir
    st.caption(f"Project root: `{project_dir()}`")
    st.caption(f"Corpus dir: `{corpus_dir()}`")

if __name__ == "__main__":
    main()
