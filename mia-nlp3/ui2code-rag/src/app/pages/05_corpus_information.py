import os, sys, pathlib
FILE = pathlib.Path(__file__).resolve()
APP_DIR = FILE.parent.parent
SRC_DIR = APP_DIR.parent
for p in (str(SRC_DIR), str(APP_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import streamlit as st
st.set_page_config(page_title="Corpus Information", page_icon="📚", layout="wide")
st.markdown("""
<style>
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a { text-transform: capitalize; }
button, [data-testid^="baseButton"] { font-family: 'Montserrat','Roboto',sans-serif !important; }
</style>
""", unsafe_allow_html=True)
from app.ui.theme import apply_theme
from app.views.corpus_info import render


apply_theme()
render()
