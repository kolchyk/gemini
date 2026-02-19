import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "6780240224")

DEFAULT_MODEL = "gemini-3.1-pro-preview"
 
# Imagen models use generate_images() API; Gemini uses generate_content_stream()
IMAGEN_MODELS = ("imagen-4.0-generate-001",  "gemini-3-pro-image-preview", "imagen-4.0-ultra-generate-001")
IMAGE_MODELS = IMAGEN_MODELS
IMAGE_MODEL = "gemini-3-pro-image-preview"
