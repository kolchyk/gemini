import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "6780240224")

DEFAULT_MODEL = "gemini-3.1-pro-preview"
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "gemini-3-pro-image-preview")
IMAGE_MODELS = [
    "gemini-3-pro-image-preview",
    "imagen-4.0-generate-001",
]
