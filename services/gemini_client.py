import streamlit as st
from google import genai
from config import settings

@st.cache_resource
def get_gemini_client():
    if not settings.GEMINI_API_KEY:
        st.error("⚠️ GEMINI_API_KEY not found in environment variables.")
        st.stop()
    return genai.Client(api_key=settings.GEMINI_API_KEY)
