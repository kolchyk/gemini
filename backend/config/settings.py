import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_IMAGE_MODELS = ("gemini-3.1-flash-image-preview", "gemini-3-pro-image-preview")
IMAGE_MODELS = GEMINI_IMAGE_MODELS
IMAGE_MODEL = "gemini-3-pro-image-preview"

# Image generation defaults
IMAGE_DEFAULT_TEMPERATURE = 1.0
IMAGE_DEFAULT_ASPECT_RATIO = "1:1"
IMAGE_DEFAULT_RESOLUTION = "1K"
IMAGE_DEFAULT_THINKING_LEVEL = "HIGH"
