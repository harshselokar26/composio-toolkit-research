import streamlit as st
import pathlib
from streamlit.components.v1 import html as st_html

st.set_page_config(page_title="Composio — 100 Apps Case Study", layout="wide")

ROOT = pathlib.Path(__file__).resolve().parent
HTML_PATH = ROOT / "html" / "assets" / "case_study.html"

st.sidebar.title("Composio — Case Study")
st.sidebar.markdown("View the generated case study for the 100-app research set.")
st.sidebar.markdown("---")

st.title("Composio Toolkit Parity — Case Study")

if not HTML_PATH.exists():
    st.error(f"Case study HTML not found at: {HTML_PATH}")
    st.stop()

html_text = HTML_PATH.read_text(encoding='utf-8')

# Embed the full HTML using an iframe via components.html. Set a generous height.
st_html(html_text, height=1400, scrolling=True)
