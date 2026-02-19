# Full Project Refactoring Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor the Gemini project into a modular, service-oriented architecture with a clean separation between UI (Streamlit) and business logic.

**Architecture:** Component-based UI with a service layer for API interactions. Centralized configuration for styles, prompts, and settings.

**Tech Stack:** Streamlit, google-genai, python-telegram-bot, pytest.

---

### Task 1: Centralized Configuration

**Files:**
- Create: `config/settings.py`
- Create: `config/styles.py`
- Create: `config/prompts.py`

**Step 1: Create `config/settings.py`**
Extract environment variables and general settings.

```python
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "6780240224")

DEFAULT_MODEL = "gemini-2.0-flash-exp"
IMAGE_MODEL = "imagen-3.0-generate-002"
```

**Step 2: Create `config/styles.py`**
Move `CUSTOM_CSS` from `gemini_image_generator/config.py`.

**Step 3: Create `config/prompts.py`**
Move `PROMPT_WOMEN`, `PROMPT_MEN`, `PROMPT_CUSTOM` from `gemini_image_generator/config.py`.

**Step 4: Commit**
```bash
git add config/
git commit -m "feat: add centralized configuration modules"
```

---

### Task 2: Gemini Client Service

**Files:**
- Create: `services/gemini_client.py`

**Step 1: Write the service**
Wrap the client initialization and caching.

```python
import streamlit as st
from google import genai
from config import settings

@st.cache_resource
def get_gemini_client():
    if not settings.GEMINI_API_KEY:
        st.error("⚠️ GEMINI_API_KEY not found in environment variables.")
        st.stop()
    return genai.Client(api_key=settings.GEMINI_API_KEY)
```

**Step 2: Commit**
```bash
git add services/gemini_client.py
git commit -m "feat: add centralized gemini client service"
```

---

### Task 3: Telegram Service

**Files:**
- Create: `services/telegram_service.py`

**Step 1: Implement async telegram service**
Refactor `gemini_image_generator/telegram_utils.py` to be a cleaner service.

```python
import io
import logging
import asyncio
from telegram import Bot, InputMediaPhoto
from config import settings

logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self):
        self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN) if settings.TELEGRAM_BOT_TOKEN else None
        self.chat_id = settings.TELEGRAM_CHAT_ID

    async def send_image_log(self, original_images, generated_image, prompt):
        if not self.bot: return
        # ... logic from telegram_utils.py ...

    def sync_send_image_log(self, *args, **kwargs):
        if not self.bot: return
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.send_image_log(*args, **kwargs))
        loop.close()

telegram_service = TelegramService()
```

**Step 2: Commit**
```bash
git add services/telegram_service.py
git commit -m "feat: add telegram service"
```

---

### Task 4: Image Generation Service

**Files:**
- Create: `services/image_service.py`

**Step 1: Extract logic from app.py**
Create a service that handles image generation using the Gemini client and Telegram service.

```python
from services.gemini_client import get_gemini_client
from services.telegram_service import telegram_service
from config import settings

class ImageService:
    def __init__(self):
        self.client = get_gemini_client()

    def generate_image(self, prompt, aspect_ratio="1:1", person_images=None):
        # ... implementation from app.py ...
        pass
```

**Step 2: Commit**
```bash
git add services/image_service.py
git commit -m "feat: add image generation service"
```

---

### Task 5: Research and Chat Services

**Files:**
- Create: `services/research_service.py`
- Create: `services/chat_service.py`

**Step 1: Extract Research logic**
Move logic from `gemini_image_generator/research_agent.py` and `app.py`.

**Step 2: Extract Chat logic**
Move logic from `app.py`.

**Step 3: Commit**
```bash
git add services/research_service.py services/chat_service.py
git commit -m "feat: add research and chat services"
```

---

### Task 6: UI Components Refactoring

**Files:**
- Create: `components/image_generator.py`
- Create: `components/deep_research.py`
- Create: `components/gemini_chat.py`

**Step 1: Create `components/image_generator.py`**
Move the UI code for the first tab into this component.

**Step 2: Create `components/deep_research.py`**
Move the UI code for the second tab.

**Step 3: Create `components/gemini_chat.py`**
Move the UI code for the third tab.

**Step 4: Commit**
```bash
git add components/
git commit -m "feat: add UI components for each feature"
```

---

### Task 7: Final app.py Cleanup

**Files:**
- Modify: `app.py`

**Step 1: Refactor app.py**
Remove all business logic and move tab content to components.

```python
import streamlit as st
from config.styles import CUSTOM_CSS
from components.image_generator import render_image_generator
from components.deep_research import render_deep_research
from components.gemini_chat import render_gemini_chat

st.set_page_config(page_title="  Gemini Hub", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🎨 Генератор Фото", "🔍 Дослідження", "💬 Chat Pro"])

with tab1:
    render_image_generator()
# ...
```

**Step 2: Commit**
```bash
git add app.py
git commit -m "refactor: clean up app.py dispatcher"
```

---

### Task 8: Cleanup and Testing

**Files:**
- Delete: `gemini_image_generator/config.py`
- Delete: `gemini_image_generator/telegram_utils.py`
- Delete: `gemini_image_generator/research_agent.py`
- Create: `tests/conftest.py`
- Create: `tests/unit/test_image_service.py`

**Step 1: Remove old files**
```bash
rm gemini_image_generator/config.py gemini_image_generator/telegram_utils.py gemini_image_generator/research_agent.py
```

**Step 2: Setup tests**
Add a basic test for one of the services.

**Step 3: Commit**
```bash
git commit -m "cleanup: remove obsolete files and add basic test structure"
```
