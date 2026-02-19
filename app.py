import streamlit as st
import subprocess
import sys

# Import from local modules
from config.styles import CUSTOM_CSS
from components.image_generator import render_image_generator
from components.deep_research import render_deep_research
from components.gemini_chat import render_gemini_chat

# Page configuration
st.set_page_config(
    page_title="Darnytsia Gemini Hub",
    page_icon="🎨",
    layout="wide"
)

# Custom CSS for modern UI
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Create tabs
tab1, tab2, tab3 = st.tabs(["🎨 Генератор зображень", "🔍 Deep Research Agent", "💬 Чат з Gemini 3 Pro"])

with tab1:
    render_image_generator()

with tab2:
    render_deep_research()

with tab3:
    render_gemini_chat()

if __name__ == "__main__":
    try:
        from streamlit.runtime.scriptrunner.script_run_context import get_script_run_ctx
        in_streamlit = get_script_run_ctx() is not None
    except Exception:
        in_streamlit = False

    if not in_streamlit:
        subprocess.run(["streamlit", "run", sys.argv[0]])
