import streamlit as st

from config.styles import CUSTOM_CSS
from components.image_generator import render_image_generator

# Page configuration
st.set_page_config(
    page_title="Nano Banana 2 — Image Generator",
    page_icon="🍌",
    layout="wide"
)

# Custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="app-header">
        <span class="app-logo">🍌</span>
        <span class="app-title">Nano Banana 2</span>
        <span class="app-subtitle">Image Generator</span>
    </div>
""", unsafe_allow_html=True)

render_image_generator()



#good
