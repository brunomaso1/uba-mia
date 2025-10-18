# src/app/ui/preloader.py
import streamlit as st

_HTML = """
<style>
  #app-preloader {{
    position: fixed; inset: 0;
    background: {bg};
    display: flex; align-items: center; justify-content: center;
    z-index: 99999;
  }}
  #app-preloader .wrap {{ display:flex; flex-direction:column; align-items:center; gap:14px; }}
  #app-preloader .spinner {{
    width: 56px; height: 56px; box-sizing: border-box;
    border: 4px solid rgba(255,255,255,.18);
    border-top-color: {color};
    border-radius: 50%;
    animation: appspin .9s linear infinite;
  }}
  #app-preloader .msg {{
    color: rgba(255,255,255,.85);
    font-family: 'Montserrat','Roboto',sans-serif;
    font-size: 14px; letter-spacing:.2px;
  }}
  @keyframes appspin {{ to {{ transform: rotate(360deg); }} }}
</style>
<div id="app-preloader">
  <div class="wrap">
    <div class="spinner"></div>
    <div class="msg">{message}</div>
  </div>
</div>
"""

def show_preloader(color="#8B5CF6", bg="#000000", message="Cargando…"):
    """Pinta un overlay en un placeholder que luego podemos vaciar."""
    slot = st.session_state.get("_preloader_slot")
    if slot is None:
        slot = st.empty()
        st.session_state["_preloader_slot"] = slot
    slot.markdown(_HTML.format(color=color, bg=bg, message=message), unsafe_allow_html=True)

def hide_preloader():
    """Vacía el placeholder y elimina el overlay sin depender de JS."""
    slot = st.session_state.get("_preloader_slot")
    if slot is not None:
        slot.empty()
        st.session_state["_preloader_slot"] = None
