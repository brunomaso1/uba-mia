import streamlit as st
import uuid

_DEFAULTS = {
    "primary": "#8B5CF6", 
    "bg":      "#0B0B10",
    "bg2":     "#151621",
    "text":    "#EDEAF5",
    "accent":  "#7C3AED",
    "font":    "montserrat",  
}

def stable_code_block(code: str, *, language: str="html", key: str|None=None):
    import uuid, streamlit as st
    anchor = key or f"code_{uuid.uuid4().hex[:8]}"
    st.markdown(f'<div id="{anchor}"></div>', unsafe_allow_html=True)
    st.code(code, language=language)
    st.markdown(f"""
    <style>
    div#{anchor} + div, div#{anchor} + div * {{
      opacity: 1 !important; visibility: visible !important;
      filter: none !important; transform: none !important;
      transition: none !important; animation: none !important;
    }}
    div#{anchor} + div pre[height="0"]{{height:auto !important;min-height:120px !important;}}
    /* move copy button, disable wrapper overlay locally */
    div#{anchor} + div > :last-child{{position:static !important;pointer-events:none !important;background:transparent !important;}}
    div#{anchor} + div [data-testid="stCodeCopyButton"]{{position:absolute !important;top:8px !important;right:8px !important;pointer-events:auto !important;z-index:3 !important;}}
    </style>
    """, unsafe_allow_html=True)
    
def set_theme_globals(**overrides):
    if "_theme_defaults" not in st.session_state:
        st.session_state["_theme_defaults"] = dict(_DEFAULTS)
    st.session_state["_theme_defaults"].update({k: v for k, v in overrides.items() if v})

def _cfg():
    cfg = st.session_state.get("_theme_defaults", dict(_DEFAULTS))
    f = (cfg.get("font") or "montserrat").lower()
    if f not in ("montserrat", "roboto"):
        f = "montserrat"
    cfg["font"] = f
    return cfg

def violet_button(label, key, *, on_click=None, disabled=False, help=None, full_width=False, color="var(--primary, #8B5CF6)"):
    """
    Renderiza un st.button y lo fuerza a violeta (mismo del theme),
    usando CSS "scoped" al botón recién pintado.
    """
    anchor_id = f"{key}__anchor"
    st.markdown(f'<div id="{anchor_id}"></div>', unsafe_allow_html=True)

    clicked = st.button(
        label=label,
        key=key,
        disabled=disabled,
        on_click=on_click,
        help=help,
        use_container_width=full_width,
        type="primary",  # aunque Streamlit lo ignore, lo forzamos con CSS
    )

    st.markdown(f"""
    <style>
    /* botón hermano inmediato y también general (por si hay wrappers) */
    div#{anchor_id} + div button,
    div#{anchor_id} + div [data-testid^="baseButton"],
    div#{anchor_id} ~ div button,
    div#{anchor_id} ~ div [data-testid^="baseButton"],
    /* variantes más específicas que suelen ganar al naranja */
    div#{anchor_id} + div div[data-testid="stButton"] > button,
    div#{anchor_id} ~ div div[data-testid="stButton"] > button,
    div#{anchor_id} + div div[data-testid="baseButton-primary"] > button,
    div#{anchor_id} ~ div div[data-testid="baseButton-primary"] > button {{
      background: {color} !important;
      background-color: {color} !important;
      color: #fff !important;
      border-radius: 12px !important;
      border: 1px solid rgba(255,255,255,0.10) !important;
      box-shadow: 0 6px 18px rgba(139, 92, 246, .25) !important; /* 8B5CF6 */
      padding: .6rem 1rem !important;
      font-weight: 600 !important;
      font-family: 'Montserrat','Roboto',sans-serif !important;
      transition: transform .08s ease, filter .08s ease;
    }}
    div#{anchor_id} + div button:hover,
    div#{anchor_id} + div [data-testid^="baseButton"]:hover,
    div#{anchor_id} ~ div button:hover,
    div#{anchor_id} ~ div [data-testid^="baseButton"]:hover {{
      filter: brightness(1.08) !important;
      transform: translateY(-0.5px) !important;
    }}
    div#{anchor_id} + div button:disabled,
    div#{anchor_id} + div [data-testid^="baseButton"][disabled],
    div#{anchor_id} ~ div button:disabled,
    div#{anchor_id} ~ div [data-testid^="baseButton"][disabled] {{
      opacity: .55 !important;
      cursor: not-allowed !important;
      box-shadow: none !important;
    }}
    </style>
    """, unsafe_allow_html=True)
    return clicked

def apply_theme():
    cfg = _cfg()
    primary, bg, bg2, text, accent, font = (
        cfg["primary"], cfg["bg"], cfg["bg2"], cfg["text"], cfg["accent"], cfg["font"]
    )
    from app.ui.header import render_global_header
    render_global_header(
        title="🧠 Multi-Agent UI-to-Code System",
        subtitle="Vision + RAG + Prompt-to-HTML (Tailwind)"
    )
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
    text-transform: capitalize; /* capitaliza cada palabra del link */
    }
    </style>
""", unsafe_allow_html=True)
    st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet"/>
""", unsafe_allow_html=True)

    font_stack = (
        "'Montserrat','Roboto',-apple-system,BlinkMacSystemFont,'Segoe UI','Helvetica Neue',Arial,sans-serif"
        if font == "montserrat"
        else "'Roboto',-apple-system,BlinkMacSystemFont,'Segoe UI','Helvetica Neue',Arial,sans-serif"
    )

    st.markdown(f"""
<style>
  /* ===== Root tokens (para todas las versiones de Streamlit) ===== */
  :root,
  .stApp,
  [data-testid="stAppViewContainer"] {{
    /* tokens nuevos */
    --primary: {primary};
    --accent:  {accent};
    --bg:      {bg};
    --bg2:     {bg2};
    --text:    {text};
    --font-sans: {font_stack};

    /* tokens legacy de Streamlit (¡clave para el naranja!) */
    --primary-color: {primary} !important;
    --secondary-background-color: {bg2} !important;
    --background-color: {bg} !important;
    --text-color: {text} !important;

    /* variantes camelCase usadas en builds recientes */
    --secondaryBackgroundColor: {bg2} !important;
    --backgroundColor: {bg} !important;
    --primaryColor: {primary} !important;
    --textColor: {text} !important;

    /* botones (algunos temas los leen de acá) */
    --button-primary-background-color: {primary} !important;
    --button-primary-text-color: #ffffff !important;
  }}

  /* ===== Tipografía global (incluye widgets) ===== */
  html, body, [class*="css"], .stApp, .main,
  button, input, textarea, select,
  .stButton > button, .stDownloadButton > button, [data-testid^="baseButton"] {{
    font-family: var(--font-sans) !important;
    color: var(--text) !important;
  }}

  /* ===== Fondos ===== */
  .stApp, [data-testid="stAppViewContainer"], .main {{ background: var(--bg) !important; }}
  [data-testid="stHeader"] {{
    background: linear-gradient(180deg, rgba(0,0,0,.35), rgba(0,0,0,0)) !important;
  }}
  section[data-testid="stSidebar"] {{ background: var(--bg2) !important; }}

  /* ===== Menú de Pages en sidebar ===== */
  section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
  section[data-testid="stSidebar"] nav[aria-label="Main"] a {{
    display: block !important;
    color: var(--text) !important;
    text-decoration: none !important;
    border-radius: 12px !important;
    padding: .55rem .75rem !important;
    margin: 2px 4px !important;
    border: 1px solid transparent !important;
  }}
  section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover,
  section[data-testid="stSidebar"] nav[aria-label="Main"] a:hover {{
    background: color-mix(in srgb, {primary} 18%, transparent) !important;
    border-color: color-mix(in srgb, {primary} 45%, transparent) !important;
  }}
  section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"],
  section[data-testid="stSidebar"] nav[aria-label="Main"] a[aria-current="page"] {{
    background: color-mix(in srgb, {primary} 28%, transparent) !important;
    border-color: color-mix(in srgb, {primary} 55%, transparent) !important;
    box-shadow: 0 0 0 1px color-mix(in srgb, {primary} 35%, transparent) inset !important;
  }}

  /* ===== BOTONES (todas las variantes) ===== */
  .stButton > button,
  .stDownloadButton > button,
  [data-testid="stFormSubmitButton"] > button,
  .stForm button[type="submit"] {{
    background: {primary} !important;
    background-color: {primary} !important;  /* por si el build usa background-color */
    color: #fff !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    box-shadow: 0 6px 18px color-mix(in srgb, {primary} 25%, transparent) !important;
    padding: .6rem 1rem !important;
    font-weight: 600 !important;
    transition: transform .08s ease, filter .08s ease;
  }}
  .stButton > button:hover,
  .stDownloadButton > button:hover,
  [data-testid="stFormSubmitButton"] > button:hover,
  .stForm button[type="submit"]:hover {{
    filter: brightness(1.08) !important;
    transform: translateY(-0.5px) !important;
  }}

  [data-testid^="baseButton"],
  div[role="button"][data-testid^="baseButton"] {{
    background: {primary} !important;
    background-color: {primary} !important;
    color: #fff !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    box-shadow: 0 6px 18px color-mix(in srgb, {primary} 25%, transparent) !important;
    padding: .6rem 1rem !important;
    font-weight: 600 !important;
  }}
  [data-testid^="baseButton"]:hover {{
    filter: brightness(1.08) !important;
    transform: translateY(-0.5px) !important;
  }}

  /* Secondary */
  .stButton > button[kind="secondary"],
  [data-testid="baseButton-secondary"] {{
    background: transparent !important;
    color: var(--text) !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
    box-shadow: none !important;
  }}
  .stButton > button[kind="secondary"]:hover,
  [data-testid="baseButton-secondary"]:hover {{
    background: color-mix(in srgb, {primary} 16%, transparent) !important;
    border-color: color-mix(in srgb, {primary} 55%, transparent) !important;
    color: #fff !important;
  }}

  /* ===== Inputs / slider / code ===== */
  .stTextInput input, .stTextArea textarea, .stNumberInput input,
  .stSelectbox > div > div {{
    background: rgba(255,255,255,0.06) !important;
    color: var(--text) !important;
    border-radius: 10px !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
  }}
  .stSlider [data-baseweb="slider"] > div > div > div {{ background: {primary} !important; }}
  pre, code, .stCode > div {{
    background: #0f0f17 !important;
    color: #eae9f1 !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
  }}
</style>
""", unsafe_allow_html=True)
    
 
    st.markdown("""
    <style>
    /* ——— SOLO el contenedor de st.code ——— */
    div[data-testid="stCode"], .stCode {
    position: relative !important;   /* referencia para posicionar el copy */
    }

    /* 1) Matar cualquier efecto de hover dentro del code */
    div[data-testid="stCode"]:hover,
    div[data-testid="stCode"]:hover *,
    .stCode:hover,
    .stCode:hover * {
    opacity: 1 !important;
    visibility: visible !important;
    transform: none !important;
    filter: none !important;
    animation: none !important;
    transition: none !important;
    }

    /* 2) Asegurar que el <pre> nunca colapse (Streamlit a veces lo pone con height="0") */
    div[data-testid="stCode"] pre[height="0"],
    .stCode pre[height="0"] {
    height: auto !important;
    min-height: 120px !important;
    max-height: none !important;
    overflow: auto !important;
    }

    /* 3) El wrapper del botón Copy NO debe cubrir todo el bloque */
    div[data-testid="stCode"] .st-emotion-cache-chk1w8.e1rzn78k3 {
    position: static !important;           /* evita overlay absoluto sobre todo el code */
    width: auto !important;
    height: auto !important;
    background: transparent !important;
    box-shadow: none !important;
    pointer-events: none !important;       /* el wrapper ignora el mouse… */
    }

    /* …y el botón sí capta el click, posicionado en la esquina */
    div[data-testid="stCode"] [data-testid="stCodeCopyButton"]{
    position: absolute !important;
    top: 8px !important;
    right: 8px !important;
    pointer-events: auto !important;
    z-index: 2 !important;
    background: rgba(0,0,0,.35) !important;
    border: 1px solid rgba(255,255,255,.15) !important;
    border-radius: 8px !important;
    }

    /* 4) Mantener el <pre> por debajo del botón pero SIEMPRE visible */
    div[data-testid="stCode"] pre { 
    position: relative !important; 
    z-index: 0 !important; 
    }

    /* 5) Extra por si cambia la clase de Emotion: eliminar cualquier hover que intente ocultar */
    div[data-testid="stCode"] *[class*="st-emotion-cache-"]:hover {
    opacity: 1 !important;
    visibility: visible !important;
    transform: none !important;
    filter: none !important;
    animation: none !important;
    transition: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style id="st-code-hover-fix">
    /* Scope only inside Streamlit code blocks */
    div[data-testid="stCode"]{ position:relative !important; }

    /* 1) The copy-button wrapper (last child) must not overlay the <pre> */
    div[data-testid="stCode"] > :last-child{
    position: static !important;
    width: auto !important;
    height: auto !important;
    background: transparent !important;
    box-shadow: none !important;
    pointer-events: none !important;  /* wrapper ignores mouse */
    transform: none !important;
    opacity: 1 !important;
    visibility: visible !important;
    }

    /* The actual copy button remains clickable and goes to the top-right */
    div[data-testid="stCode"] [data-testid="stCodeCopyButton"]{
    position: absolute !important;
    top: 8px !important;
    right: 8px !important;
    z-index: 3 !important;
    pointer-events: auto !important;
    }

    /* 2) Keep <pre>/<code> ALWAYS visible, regardless of any :hover */
    div[data-testid="stCode"] pre,
    div[data-testid="stCode"] code{
    position: relative !important;
    z-index: 2 !important;
    opacity: 1 !important;
    visibility: visible !important;
    filter: none !important;
    transform: none !important;
    transition: none !important;
    animation: none !important;
    }

    /* Kill any hover-driven effect inside the code block */
    div[data-testid="stCode"]:hover,
    div[data-testid="stCode"]:hover *,
    div[data-testid="stCode"] *:hover{
    opacity: 1 !important;
    visibility: visible !important;
    filter: none !important;
    transform: none !important;
    transition: none !important;
    animation: none !important;
    }

    /* 3) Fix Streamlit occasionally setting <pre height="0"> */
    div[data-testid="stCode"] pre[height="0"]{
    height: auto !important;
    min-height: 120px !important;
    max-height: none !important;
    overflow: auto !important;
    }
    </style>
    """, unsafe_allow_html=True)

