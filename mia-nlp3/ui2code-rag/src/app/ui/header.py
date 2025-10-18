# src/app/ui/header.py
import streamlit as st

def render_global_header(
    title: str = "Multi-Agent UI-to-Code System",
    subtitle: str | None = "Vision + RAG + Prompt-to-HTML (Tailwind)",
    *,
    max_width: int = 1200,      # ancho máximo del contenido del header
    height_px: int = 76,        # alto mínimo del header (ajusta a gusto)
    sidebar_aware: bool = True, # si True, el header se desplaza según el ancho del sidebar
):
    """
    Header fijo y centrado, con H1 y subtítulo. Llamarlo al inicio de cada página
    (p.ej. desde apply_theme()).

    - Centrado y con ancho limitado.
    - No se tapa con el sidebar (usa una CSS var --sbw).
    - Añade padding-top al body para no solaparse con el contenido.
    """
    # Inyectar CSS una sola vez por sesión
    if not st.session_state.get("_global_header_css_injected", False):
        st.session_state["_global_header_css_injected"] = True

        st.markdown(f"""
<style>
  :root {{
    --app-header-height: {height_px}px;
    --app-header-maxw: {max_width}px;
    --sbw: 0px; /* sidebar width dinámico (lo setea el script) */
  }}

  /* Empuje para que el contenido no quede debajo del header */
  [data-testid="stAppViewContainer"] .main .block-container {{
    padding-top: calc(var(--app-header-height) + 16px) !important;
  }}

  /* Header fijo, centrado, con borde inferior sutil */
  #app-global-header {{
    position: fixed;
    top: 0;
    left: {'var(--sbw)' if sidebar_aware else '0'};
    right: 0;
    z-index: 1002;
    min-height: var(--app-header-height);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 10px 16px;
    background: var(--bg2, #151621);
    color: var(--text, #EDEAF5);
    border-bottom: 1px solid rgba(255,255,255,.08);
    backdrop-filter: saturate(1.2) blur(10px);
  }}

  /* Contenedor interno con ancho máximo */
  #app-global-header .wrap {{
    width: 100%;
    max-width: var(--app-header-maxw);
    margin: 0 auto;
    text-align: center;
  }}

  /* Título (H1) centrado */
  #app-global-header h1 {{
    margin: 0;
    font-family: var(--font-sans, 'Montserrat','Roboto',sans-serif);
    font-size: clamp(20px, 2.4vw, 28px);
    font-weight: 800;
    letter-spacing: .2px;
    line-height: 1.2;
  }}

  /* Subtítulo */
  #app-global-header .subtitle {{
    margin-top: 4px;
    font-size: 13px;
    opacity: .85;
    font-weight: 500;
  }}

  /* Header nativo de Streamlit más transparente (opcional) */
  [data-testid="stHeader"] {{
    background: linear-gradient(180deg, rgba(0,0,0,.25), rgba(0,0,0,0)) !important;
  }}
</style>
        """, unsafe_allow_html=True)

        # Script que mide el ancho real del sidebar y lo expone en --sbw
        st.markdown("""
<script>
(function(){
  const root = document.documentElement;
  function setSBW(){
    const sb = document.querySelector('section[data-testid="stSidebar"]');
    const w = sb ? sb.offsetWidth : 0;
    root.style.setProperty('--sbw', w + 'px');
  }
  setSBW();
  const sb = document.querySelector('section[data-testid="stSidebar"]');
  if (sb && 'ResizeObserver' in window) {
    new ResizeObserver(setSBW).observe(sb);
  } else {
    window.addEventListener('resize', setSBW);
  }
})();
</script>
        """, unsafe_allow_html=True)

    # HTML del header (sin widgets → no dispara reruns visibles)
    st.markdown(f"""
<div id="app-global-header">
  <div class="wrap">
    <h1>{title}</h1>
    {f'<div class="subtitle">{subtitle}</div>' if subtitle else ''}
  </div>
</div>
    """, unsafe_allow_html=True)
