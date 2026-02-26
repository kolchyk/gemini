import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "6780240224")

GEMINI_IMAGE_MODELS = ("gemini-3.1-flash-image-preview", "gemini-3-pro-image-preview")
IMAGE_MODELS = GEMINI_IMAGE_MODELS
IMAGE_MODEL = "gemini-3-pro-image-preview"  # Pro Banana 2

# Image generation defaults
IMAGE_DEFAULT_TEMPERATURE = 1.0
IMAGE_DEFAULT_ASPECT_RATIO = "1:1"
IMAGE_DEFAULT_RESOLUTION = "2K"
IMAGE_DEFAULT_THINKING_LEVEL = "HIGH"
