import streamlit as st
import subprocess
import sys

# Import from local modules
from config.styles import CUSTOM_CSS
from components.image_generator import render_image_generator, render_image_sidebar
from components.deep_research import render_deep_research, render_research_sidebar
from components.gemini_chat import render_gemini_chat, render_chat_sidebar

# Page configuration
st.set_page_config(
    page_title="  Gemini Hub",
    page_icon="🎨",
    layout="wide"
)

# Custom CSS for modern UI
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Navigation
tabs = {
    "🎨 Генератор": "image",
    "🔍 Deep Research": "research",
    "💬 Чат з Gemini": "chat"
}

# Horizontal tab selector at the top
selected_tab_label = st.radio(
    "Navigation",
    options=list(tabs.keys()),
    horizontal=True,
    label_visibility="collapsed"
)
active_tab = tabs[selected_tab_label]

# Render Sidebar and Component based on active tab
if active_tab == "image":
    render_image_sidebar()
    render_image_generator()
elif active_tab == "research":
    render_research_sidebar()
    render_deep_research()
elif active_tab == "chat":
    render_chat_sidebar()
    render_gemini_chat()
