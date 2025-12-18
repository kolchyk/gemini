"""Gemini API client initialization."""

import os
import streamlit as st
from google import genai


@st.cache_resource
def get_gemini_client():
    """Initialize and return Gemini API client."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("⚠️ GEMINI_API_KEY не встановлено. Будь ласка, встановіть змінну середовища.")
        st.stop()
    return genai.Client(api_key=api_key)

