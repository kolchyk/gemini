from functools import lru_cache
from google import genai
from backend.config import settings


@lru_cache(maxsize=1)
def get_gemini_client():
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not found in environment variables.")
    return genai.Client(api_key=settings.GEMINI_API_KEY)
