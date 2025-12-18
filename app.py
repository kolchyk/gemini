import streamlit as st
from google.genai import types
import base64
import os
import mimetypes
import time

# Import from local modules
from gemini_image_generator.config import CUSTOM_CSS, PROMPT_WOMEN, PROMPT_MEN
from gemini_image_generator.client import get_gemini_client
from gemini_image_generator.file_utils import save_uploaded_file
from gemini_image_generator.telegram_utils import send_telegram_log
from gemini_image_generator.research_agent import start_research, check_research_status

# Page configuration
st.set_page_config(
    page_title="NanaBanana for Darnytsia",
    page_icon="🎨",
    layout="wide"
)

# Custom CSS for modern UI
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Header container
with st.container():
    st.markdown('<div class="main-title">', unsafe_allow_html=True)
    st.title("🍌 NanaBanana for Darnytsia")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Завантажте одне або кілька референсних зображень та введіть промпт для генерації нового зображення</p>', unsafe_allow_html=True)


# Initialize session state for research agent
if 'research_interaction_id' not in st.session_state:
    st.session_state['research_interaction_id'] = None
if 'research_query' not in st.session_state:
    st.session_state['research_query'] = None
if 'research_status' not in st.session_state:
    st.session_state['research_status'] = None
if 'research_auto_polling' not in st.session_state:
    st.session_state['research_auto_polling'] = False
if 'research_result' not in st.session_state:
    st.session_state['research_result'] = None
if 'research_error' not in st.session_state:
    st.session_state['research_error'] = None


# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Параметри генерації")
    
    aspect_ratio = st.selectbox(
        "Співвідношення сторін:",
        options=["1:1", "16:9", "9:16", "4:3", "3:4"],
        index=0,
        help="Виберіть співвідношення сторін для згенерованого зображення"
    )
    
    resolution = st.selectbox(
        "Роздільна здатність:",
        options=["1K", "2K", "4K"],
        index=0,
        help="Виберіть роздільну здатність зображення (вища = краща якість, але довше генерація)"
    )
    
    temperature = st.slider(
        "Temperature:",
        min_value=0.0,
        max_value=1.0,
        value=1.0,
        step=0.05,
        help="Контролює випадковість генерації (0.0 = детерміновано, 1.0 = більше варіацій)"
    )
    
    st.divider()
    
    with st.expander("ℹ️ Про додаток"):
        st.markdown("""
        **NanaBanana for Darnytsia** — це веб-додаток для створення професійних зображень 
        за допомогою Google Gemini API.
        
        Використовуйте референсні зображення та детальні промпти для отримання 
        найкращих результатів.
        """)
    
    with st.expander("💡 Підказки"):
        st.markdown("""
        **Для максимальної схожості:**
        - Додайте *keep facial features exactly consistent*
        - Опишіть ракурс (front/3-4 view)
        
        **Для бізнес-портрета:**
        - Уточніть *studio backdrop*
        - Додайте *three-point lighting*
        - Вкажіть *85mm lens*
        
        **Щоб прибрати артефакти:**
        - Додайте *no extra people, no text, no watermark*
        
        **Якщо фон "брудний":**
        - Вкажіть *clean solid background, subtle gradient, no objects*
        """)
    
    st.markdown("---")
    st.caption("Версія 0.1.0")

# Create tabs
tab1, tab2 = st.tabs(["🎨 Генератор зображень", "🔍 Deep Research Agent"])

# Default settings
model_name = "gemini-3-pro-image-preview"

# ========== TAB 1: IMAGE GENERATOR ==========
with tab1:
    # Quick start guide
    with st.expander("📖 Швидкий старт", expanded=False):
        st.markdown("""
        **Як користуватись:**
        1. **Завантажте референси** (краще 1–3 фото обличчя, схожий ракурс/світло)
        2. **Оберіть шаблон** (Жінки/Чоловіки) і **відредагуйте промпт** під задачу
        3. Натисніть **«Згенерувати зображення»** → потім **«Завантажити»**
        
        **Порада:** якщо результат не влучив — спробуйте уточнити одяг/фон/світло або додайте ще один референс.
        """)
    
    st.markdown("---")
    
    # Section 1: Reference image upload (top)
    st.subheader("📤 Крок 1: Референсні зображення")
    uploaded_files = st.file_uploader(
        "Завантажте одне або кілька референсних зображень (опціонально)",
        type=['jpg', 'jpeg', 'png', 'bmp', 'gif'],
        accept_multiple_files=True,
        help=(
            "Рекомендовано: 1–3 референси з обличчям/портретом. "
            "Чим ближче ракурс і освітлення до бажаного результату — тим краще. "
            "Можна генерувати без референсів, але промпт обов'язковий."
        ),
        key="reference_images"
    )
    st.caption(
        "💡 Підказка: якщо референсів немає — генерація можлива, але схожість/стабільність результату може бути гіршою."
    )
    
    # Display uploaded reference images immediately
    if uploaded_files:
        num_files = len(uploaded_files)
        st.markdown("---")
        if num_files == 1:
            st.caption(f"✅ Завантажено 1 референсне зображення")
            st.image(uploaded_files[0], caption="Референсне зображення", use_container_width=True)
        else:
            st.caption(f"✅ Завантажено {num_files} референсних зображень")
            # Display images in columns for better layout
            cols = st.columns(min(3, num_files))
            for idx, uploaded_file in enumerate(uploaded_files):
                with cols[idx % len(cols)]:
                    st.image(uploaded_file, caption=f"Референс {idx + 1}: {uploaded_file.name}", use_container_width=True)
    
    st.markdown("---")

    # Section 2: Prompt input (middle)
    st.subheader("✍️ Крок 2: Промпт")
    
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
    
    st.markdown("---")
    
    # Generate button - more prominent placement
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_button = st.button("🚀 Згенерувати зображення", type="primary", use_container_width=True)

    # Generate image when button is clicked
    if generate_button:
        # Validation - prompt is mandatory
        if not prompt or not prompt.strip():
            st.error("⚠️ Будь ласка, введіть промпт. Промпт є обов'язковим для генерації зображення.")
            st.stop()
        
        # Source images are optional - just show info if provided
        if uploaded_files and len(uploaded_files) > 0:
            st.info(f"ℹ️ Буде використано {len(uploaded_files)} референсних зображень")
        
        st.markdown("---")
        
        # Section 3: Result display (bottom)
        st.subheader("🎨 Результат генерації")
        
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
            
            # Create parts list (files + text)
            parts_list = file_parts.copy()
            parts_list.append(types.Part.from_text(text=prompt))
            
            # Create Content object matching the example format
            contents = [
                types.Content(
                    role="user",
                    parts=parts_list,
                ),
            ]
            
            status_text.text("🎨 Генерація зображення...")
            progress_bar.progress(50)
            
            # Prepare tools (GoogleSearch)
            tools = [
                types.Tool(googleSearch=types.GoogleSearch()),
            ]
            
            # Generate content with streaming
            generate_content_config = types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
                temperature=temperature,
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    image_size=resolution,
                ),
                tools=tools,
            )
            
            # Process streaming response
            image_bytes = None
            text_output = []
            file_index = 0
            
            # Create a placeholder for text output
            text_placeholder = st.empty()
            
            status_text.text("📥 Обробка відповіді (streaming)...")
            progress_bar.progress(60)
            
            for chunk in client.models.generate_content_stream(
                model=model_name,
                contents=contents,
                config=generate_content_config,
            ):
                if (
                    chunk.candidates is None
                    or chunk.candidates[0].content is None
                    or chunk.candidates[0].content.parts is None
                ):
                    continue
                
                # Check for image data
                if (chunk.candidates[0].content.parts[0].inline_data 
                    and chunk.candidates[0].content.parts[0].inline_data.data):
                    inline_data = chunk.candidates[0].content.parts[0].inline_data
                    data_buffer = inline_data.data
                    
                    # Convert string to bytes if needed
                    if isinstance(data_buffer, str):
                        data_buffer = base64.b64decode(data_buffer)
                    
                    if data_buffer:
                        image_bytes = data_buffer
                        file_index += 1
                        progress_bar.progress(90)
                        status_text.text("✅ Зображення отримано!")
                else:
                    # Check for text output (matching example format)
                    if hasattr(chunk, 'text') and chunk.text:
                        text_output.append(chunk.text)
                        # Display accumulated text
                        if text_output:
                            text_placeholder.text("".join(text_output))
            
            progress_bar.progress(100)
            status_text.text("✅ Готово!")
            
            # Display text output if available
            if text_output:
                full_text = "".join(text_output)
                if full_text.strip():
                    with st.expander("📝 Текстова відповідь", expanded=False):
                        st.markdown(full_text)
            
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
                st.image(image_bytes, caption="Згенероване зображення", use_container_width=True)
                
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
            elif not text_output:
                st.error("❌ Помилка: зображення не знайдено у відповіді")
        
        except Exception as e:
            st.error(f"❌ Помилка: {str(e)}")
            st.exception(e)
        finally:
            progress_bar.empty()
            status_text.empty()

    # Display previously generated image if exists
    if 'generated_image' in st.session_state and not generate_button:
        st.markdown("---")
        st.subheader("📸 Останнє згенероване зображення")
        st.image(st.session_state['generated_image'], caption="Останнє згенероване зображення", use_container_width=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.download_button(
                label="💾 Завантажити останнє зображення",
                data=st.session_state['generated_image'],
                file_name="generated_image.jpg",
                mime="image/jpeg",
                use_container_width=True
            )

# ========== TAB 2: DEEP RESEARCH AGENT ==========
with tab2:
    st.subheader("🔍 Deep Research Agent")
    st.markdown("Використовуйте Deep Research Agent для глибокого дослідження тем з автоматичним збором та аналізом інформації")
    
    with st.expander("📖 Як користуватись", expanded=False):
        st.markdown("""
        **Інструкція:**
        1. **Введіть запит** для дослідження (наприклад, про історію технологій, події, аналіз даних)
        2. Натисніть **«Почати дослідження»** — агент почне роботу у фоновому режимі
        3. **Моніторинг статусу** — система автоматично перевіряє прогрес кожні 10 секунд
        4. Коли дослідження завершиться, ви побачите **фінальний звіт** з результатами
        """)
    
    st.markdown("---")
    
    # Input section
    st.subheader("📝 Запит для дослідження")
    research_query = st.text_area(
        "Введіть тему або питання для дослідження:",
        value=st.session_state['research_query'] if st.session_state['research_query'] else "",
        height=150,
        placeholder="Наприклад: Research the history of the Google TPUs with a focus on 2025 and 2026.",
        help="Опишіть тему дослідження детально для кращих результатів.",
        key="research_query_input"
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        start_research_button = st.button("🚀 Почати дослідження", type="primary", use_container_width=True)
    
    # Handle start research button
    if start_research_button:
        if not research_query or not research_query.strip():
            st.error("⚠️ Будь ласка, введіть запит для дослідження")
        else:
            try:
                client = get_gemini_client()
                interaction_id, status = start_research(research_query.strip(), client)
                st.session_state['research_interaction_id'] = interaction_id
                st.session_state['research_query'] = research_query.strip()
                st.session_state['research_status'] = status
                st.session_state['research_auto_polling'] = True
                st.session_state['research_result'] = None
                st.session_state['research_error'] = None
                st.session_state['research_last_poll_time'] = 0  # Reset poll timer
                st.success(f"✅ Дослідження розпочато! Interaction ID: {interaction_id}")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Помилка: {str(e)}")
    
    st.markdown("---")
    
    # Status and results section
    if st.session_state['research_interaction_id']:
        st.subheader("📊 Статус дослідження")
        
        interaction_id = st.session_state['research_interaction_id']
        current_status = st.session_state['research_status']
        
        # Display interaction ID
        st.caption(f"**Interaction ID:** `{interaction_id}`")
        
        # Status display with better visual indicators
        status_col1, status_col2 = st.columns([2, 1])
        with status_col1:
            if current_status == "pending":
                st.info("⏳ **Статус:** Очікування...")
            elif current_status == "processing":
                st.info("🔄 **Статус:** Обробка...")
            elif current_status == "completed":
                st.success("✅ **Статус:** Завершено!")
            elif current_status in ["failed", "cancelled"]:
                st.error(f"❌ **Статус:** {current_status.capitalize()}")
            else:
                st.info(f"ℹ️ **Статус:** {current_status}")
        
        with status_col2:
            if st.session_state['research_auto_polling']:
                st.caption("🔄 **Автоматичне оновлення:** Увімкнено")
            else:
                st.caption("⏸️ **Автоматичне оновлення:** Вимкнено")
            
        # Control buttons
        control_col1, control_col2, control_col3 = st.columns([1, 1, 1])
        with control_col1:
            if st.button("🔄 Оновити статус", use_container_width=True):
                try:
                    client = get_gemini_client()
                    status, result, error = check_research_status(interaction_id, client)
                    st.session_state['research_status'] = status
                    if result:
                        st.session_state['research_result'] = result
                    if error:
                        st.session_state['research_error'] = error
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Помилка: {str(e)}")
        
        with control_col2:
            if st.button("⏹️ Зупинити моніторинг", use_container_width=True):
                st.session_state['research_auto_polling'] = False
                st.rerun()
        
        with control_col3:
            if st.button("🔄 Відновити моніторинг", use_container_width=True):
                st.session_state['research_auto_polling'] = True
                st.rerun()
            
        # Auto-polling logic
        if st.session_state['research_auto_polling'] and current_status not in ["completed", "failed", "cancelled"]:
            # Initialize last poll time if not exists
            if 'research_last_poll_time' not in st.session_state:
                st.session_state['research_last_poll_time'] = 0
            
            current_time = time.time()
            time_since_last_poll = current_time - st.session_state['research_last_poll_time']
            
            # Poll if 10 seconds have passed since last poll or if this is the first poll
            if time_since_last_poll >= 10 or st.session_state['research_last_poll_time'] == 0:
                try:
                    client = get_gemini_client()
                    status, result, error = check_research_status(interaction_id, client)
                    st.session_state['research_last_poll_time'] = current_time
                    
                    if status != current_status:
                        st.session_state['research_status'] = status
                        if result:
                            st.session_state['research_result'] = result
                        if error:
                            st.session_state['research_error'] = error
                        st.rerun()
                    elif result and not st.session_state['research_result']:
                        # Status same but we got a result we didn't have before
                        st.session_state['research_result'] = result
                        st.rerun()
                    elif error and not st.session_state['research_error']:
                        # Status same but we got an error we didn't have before
                        st.session_state['research_error'] = error
                        st.rerun()
                    else:
                        # Status unchanged, schedule auto-refresh using JavaScript
                        st.markdown(
                            f"""
                            <script>
                                setTimeout(function() {{
                                    window.location.reload();
                                }}, 10000);
                            </script>
                            """,
                            unsafe_allow_html=True
                        )
                        st.caption("⏱️ Автоматичне оновлення через 10 секунд...")
                except Exception as e:
                    st.warning(f"⚠️ Помилка при перевірці статусу: {str(e)}")
                    st.session_state['research_auto_polling'] = False
            else:
                # Show countdown until next poll
                seconds_until_next = int(10 - time_since_last_poll)
                st.markdown(
                    f"""
                    <script>
                        setTimeout(function() {{
                            window.location.reload();
                        }}, {seconds_until_next * 1000});
                    </script>
                    """,
                    unsafe_allow_html=True
                )
                st.caption(f"⏱️ Наступна перевірка через {seconds_until_next} секунд...")
        
        st.markdown("---")
        
        # Results display
        if st.session_state['research_result']:
            st.subheader("📄 Фінальний звіт")
            
            result_text = st.session_state['research_result']
            
            # Display result in expandable section
            with st.expander("🔍 Переглянути звіт", expanded=True):
                st.markdown(result_text)
            
            # Download button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    label="💾 Завантажити звіт",
                    data=result_text.encode('utf-8'),
                    file_name=f"research_report_{interaction_id[:8]}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
        
        elif current_status in ["failed", "cancelled"]:
            st.warning("⚠️ Дослідження завершилося з помилкою або було скасовано.")
            if st.session_state['research_error']:
                st.error(f"**Деталі помилки:** {st.session_state['research_error']}")
        
        elif current_status == "completed" and not st.session_state['research_result']:
            st.info("ℹ️ Дослідження завершено, але результат ще не отримано. Натисніть «Оновити статус».")
    
    else:
        st.info("💡 Введіть запит вище та натисніть «Почати дослідження», щоб розпочати роботу з Deep Research Agent.")

