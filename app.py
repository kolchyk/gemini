import streamlit as st
from google.genai import types
import base64
import os
import mimetypes
import re
import time

# Import from local modules
from gemini_image_generator.config import CUSTOM_CSS, PROMPT_WOMEN, PROMPT_MEN, PROMPT_CUSTOM
from gemini_image_generator.client import get_gemini_client
from gemini_image_generator.file_utils import save_uploaded_file
from gemini_image_generator.telegram_utils import send_telegram_log, send_telegram_text_log

# Page configuration
st.set_page_config(
    page_title="Darnytsia Gemini Hub",
    page_icon="🎨",
    layout="wide"
)

# Custom CSS for modern UI
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def get_text(outputs):
    return "\n".join(
        output.text for output in (outputs or []) if hasattr(output, 'text') and output.text
    ) or ""


def parse_tasks(text):
    return [
        {"num": match.group(1), "text": match.group(2).strip().replace('\n', ' ')}
        for match in re.finditer(
            r'^(\d+)[\.\)\-]\s*(.+?)(?=\n\d+[\.\)\-]|\n\n|\Z)',
            text,
            re.MULTILINE | re.DOTALL
        )
    ]


def wait_for_completion(client, interaction_id, timeout=300):
    progress, status, elapsed = st.progress(0), st.empty(), 0
    while elapsed < timeout:
        interaction = client.interactions.get(interaction_id)
        if interaction.status != "in_progress":
            progress.progress(100)
            return interaction
        elapsed += 3
        progress.progress(min(90, int(elapsed / timeout * 100)))
        status.text(f"⏳ {elapsed}s...")
        time.sleep(3)
    return client.interactions.get(interaction_id)


# Initialize session state for research planner
for key in [
    "plan_id",
    "plan_text",
    "tasks",
    "research_id",
    "research_text",
    "synthesis_text",
    "infographic",
]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "tasks" else None

# Initialize session state for Gemini 3 Pro chat
if 'gemini_chat_history' not in st.session_state:
    st.session_state['gemini_chat_history'] = []
if 'chat_thinking_level' not in st.session_state:
    st.session_state['chat_thinking_level'] = 'low'
if 'chat_temperature' not in st.session_state:
    st.session_state['chat_temperature'] = 0.7

# Initialize session state for image generator settings
if 'image_aspect_ratio' not in st.session_state:
    st.session_state['image_aspect_ratio'] = "1:1"
if 'image_resolution' not in st.session_state:
    st.session_state['image_resolution'] = "1K"
if 'image_temperature' not in st.session_state:
    st.session_state['image_temperature'] = 1.0

# Create tabs
tab1, tab2, tab3 = st.tabs(["🎨 Генератор зображень", "🔍 Deep Research Agent", "💬 Чат з Gemini 3 Pro"])

# Default settings
model_name = "gemini-3-pro-image-preview"

# ========== TAB 1: IMAGE GENERATOR ==========
with tab1:
    # Create two-column layout: main content (3) and settings panel (1)
    col_main, col_settings = st.columns([3, 1])
    
    with col_main:
        
        # Section 1: Reference image upload (top)
        st.subheader("📤 Крок 1: Референсні зображення")
        uploaded_files = st.file_uploader(
            "Референсні зображення (опціонально)",
            type=['jpg', 'jpeg', 'png', 'bmp', 'gif'],
            accept_multiple_files=True,
            help="Для режиму 'З нуля' - опціонально. Для режимів 'Жінки'/'Чоловіки' - рекомендовано 1–3 референси з обличчям. Промпт обов'язковий.",
            key="reference_images"
        )
        
        # Display uploaded reference images immediately (as thumbnails)
        if uploaded_files:
            num_files = len(uploaded_files)
            cols = st.columns(min(4, num_files))
            for idx, uploaded_file in enumerate(uploaded_files):
                with cols[idx % len(cols)]:
                    st.image(uploaded_file, caption=f"Реф. {idx + 1}", use_container_width=True)

        # Section 2: Prompt input (middle)
        st.subheader("✍️ Крок 2: Промпт")
        
        # Initialize session state for prompt management
        if 'prompt_type' not in st.session_state:
            st.session_state['prompt_type'] = 'custom'
        if 'edited_prompt_women' not in st.session_state:
            st.session_state['edited_prompt_women'] = None
        if 'edited_prompt_men' not in st.session_state:
            st.session_state['edited_prompt_men'] = None
        if 'edited_prompt_custom' not in st.session_state:
            st.session_state['edited_prompt_custom'] = None
        
        # Prompt type selector
        prompt_type_options = ["З нуля (Власний промпт)", "Жінки", "Чоловіки"]
        prompt_type_index_map = {'custom': 0, 'women': 1, 'men': 2}
        current_index = prompt_type_index_map.get(st.session_state['prompt_type'], 0)
        
        prompt_type = st.radio(
            "Режим генерації:",
            prompt_type_options,
            index=current_index,
            horizontal=True,
            help="Оберіть режим генерації. 'З нуля' - для створення зображень з нуля, 'Жінки'/'Чоловіки' - для редагування фото. Ваші правки збережуться окремо для кожного режиму.",
            key="prompt_type_selector"
        )
        
        # Update session state when selection changes
        type_map = {
            "З нуля (Власний промпт)": 'custom',
            "Жінки": 'women',
            "Чоловіки": 'men'
        }
        current_prompt_type = type_map[prompt_type]
        
        if current_prompt_type != st.session_state['prompt_type']:
            # Save current edited prompt before switching
            old_prompt_key = f"prompt_text_area_{st.session_state['prompt_type']}"
            if old_prompt_key in st.session_state:
                if st.session_state['prompt_type'] == 'women':
                    st.session_state['edited_prompt_women'] = st.session_state[old_prompt_key]
                elif st.session_state['prompt_type'] == 'men':
                    st.session_state['edited_prompt_men'] = st.session_state[old_prompt_key]
                elif st.session_state['prompt_type'] == 'custom':
                    st.session_state['edited_prompt_custom'] = st.session_state[old_prompt_key]
            
            st.session_state['prompt_type'] = current_prompt_type
        
        # Determine which prompt to use
        if st.session_state['prompt_type'] == 'women':
            base_prompt = PROMPT_WOMEN
            edited_prompt = st.session_state['edited_prompt_women']
        elif st.session_state['prompt_type'] == 'men':
            base_prompt = PROMPT_MEN
            edited_prompt = st.session_state['edited_prompt_men']
        else:  # custom
            base_prompt = PROMPT_CUSTOM
            edited_prompt = st.session_state['edited_prompt_custom']
        
        # Use edited prompt if available, otherwise use base prompt
        current_prompt_value = edited_prompt if edited_prompt is not None else base_prompt
        
        # Text area for prompt editing - use dynamic key based on prompt type
        prompt_key = f"prompt_text_area_{st.session_state['prompt_type']}"
        prompt = st.text_area(
            "Промпт:",
            value=current_prompt_value,
            height=200,
            placeholder="Опишіть що згенерувати...",
            key=prompt_key
        )

        col_a, col_b = st.columns([1, 1])
        with col_a:
            if st.button("↩️ Скинути промпт до шаблону", width='stretch'):
                if st.session_state['prompt_type'] == 'women':
                    st.session_state['edited_prompt_women'] = PROMPT_WOMEN
                elif st.session_state['prompt_type'] == 'men':
                    st.session_state['edited_prompt_men'] = PROMPT_MEN
                else:  # custom
                    st.session_state['edited_prompt_custom'] = PROMPT_CUSTOM
                st.rerun()
        with col_b:
            if st.button("🧹 Очистити останній результат", width='stretch'):
                st.session_state.pop('generated_image', None)
                st.rerun()
    
        # Save edited prompt when user edits (update session state after text_area is rendered)
        if st.session_state['prompt_type'] == 'women':
            st.session_state['edited_prompt_women'] = prompt
        elif st.session_state['prompt_type'] == 'men':
            st.session_state['edited_prompt_men'] = prompt
        else:  # custom
            st.session_state['edited_prompt_custom'] = prompt
        
        # Generate button - more prominent placement
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            generate_button = st.button("🚀 Згенерувати зображення", type="primary", width='stretch')
    
    # Right settings panel
    with col_settings:
        st.markdown("### Параметри")
        
        aspect_ratio = st.selectbox(
            "Співвідношення:",
            options=["1:1", "16:9", "9:16", "4:3", "3:4"],
            index=["1:1", "16:9", "9:16", "4:3", "3:4"].index(st.session_state['image_aspect_ratio']),
            key="image_aspect_ratio_selector"
        )
        st.session_state['image_aspect_ratio'] = aspect_ratio
        
        resolution = st.selectbox(
            "Роздільність:",
            options=["1K", "2K", "4K"],
            index=["1K", "2K", "4K"].index(st.session_state['image_resolution']),
            key="image_resolution_selector"
        )
        st.session_state['image_resolution'] = resolution
        
        temperature = st.slider(
            "Temperature:",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state['image_temperature'],
            step=0.05,
            key="image_temperature_slider"
        )
        st.session_state['image_temperature'] = temperature
        
    # Generate image when button is clicked
    if generate_button:
        # Use settings from session state
        aspect_ratio = st.session_state['image_aspect_ratio']
        resolution = st.session_state['image_resolution']
        temperature = st.session_state['image_temperature']
        
        with col_main:
            # Validation - prompt is mandatory
            if not prompt or not prompt.strip():
                st.error("⚠️ Будь ласка, введіть промпт. Промпт є обов'язковим для генерації зображення.")
                st.stop()
            
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
                        
                        try:
                            file_metadata = save_uploaded_file(uploaded_file)
                            saved_file_metadata.append(file_metadata)
                        except Exception:
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
                    st.image(image_bytes, caption="Згенероване зображення", width='stretch')
                    
                    # Download button
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.download_button(
                            label="💾 Завантажити зображення",
                            data=image_bytes,
                            file_name="generated_image.jpg",
                            mime="image/jpeg",
                            width='stretch'
                        )
                    
                    # Store in session state for persistence
                    st.session_state['generated_image'] = image_bytes
                    
                    try:
                        original_images_bytes = []
                        if uploaded_files:
                            for uploaded_file in uploaded_files:
                                uploaded_file.seek(0)
                                original_images_bytes.append(uploaded_file.read())
                        
                        send_telegram_log(original_images_bytes, image_bytes, prompt, saved_file_metadata if saved_file_metadata else None)
                    except Exception:
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
    with col_main:
        if 'generated_image' in st.session_state and not generate_button:
            st.subheader("📸 Останнє згенероване зображення")
            st.image(st.session_state['generated_image'], caption="Останнє згенероване зображення", width='stretch')
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    label="💾 Завантажити останнє зображення",
                    data=st.session_state['generated_image'],
                    file_name="generated_image.jpg",
                    mime="image/jpeg",
                    width='stretch'
                )

# ========== TAB 2: DEEP RESEARCH AGENT ==========
with tab2:
    col_main, col_settings = st.columns([3, 1])

    with col_main:
        st.subheader("🔍 Deep Research Planner")

        # Phase 1: Plan
        research_goal = st.text_area(
            "📝 Research Goal",
            placeholder="e.g., Research B2B HR SaaS market in Germany",
            key="research_goal_input"
        )
        if st.button("📋 Generate Plan", disabled=not research_goal, type="primary"):
            with st.spinner("Planning..."):
                try:
                    client = get_gemini_client()
                    interaction = client.interactions.create(
                        model="gemini-3-flash-preview",
                        input=(
                            f"Create a numbered research plan for: {research_goal}\n\n"
                            "Format: 1. [Task] - [Details]\n\nInclude 5-8 specific tasks."
                        ),
                        tools=[{"type": "google_search"}],
                        store=True,
                    )
                    plan_text = get_text(interaction.outputs)
                    st.session_state.plan_id = interaction.id
                    st.session_state.plan_text = plan_text
                    st.session_state.tasks = parse_tasks(plan_text)
                    st.session_state.research_id = None
                    st.session_state.research_text = None
                    st.session_state.synthesis_text = None
                    st.session_state.infographic = None
                except Exception as e:
                    st.error(f"Error: {e}")

        # Phase 2: Select & Research
        if st.session_state.plan_text:
            st.divider()
            st.subheader("🔍 Select Tasks & Research")
            selected = [
                f"{task['num']}. {task['text']}"
                for task in st.session_state.tasks
                if st.checkbox(
                    f"**{task['num']}.** {task['text']}",
                    True,
                    key=f"task_{task['num']}",
                )
            ]
            st.caption(f"✅ {len(selected)}/{len(st.session_state.tasks)} selected")

            if st.button("🚀 Start Deep Research", type="primary", disabled=not selected):
                with st.spinner("Researching (2-5 min)..."):
                    try:
                        client = get_gemini_client()
                        interaction = client.interactions.create(
                            agent="deep-research-pro-preview-12-2025",
                            input=(
                                "Research these tasks thoroughly with sources:\n\n"
                                + "\n\n".join(selected)
                            ),
                            previous_interaction_id=st.session_state.plan_id,
                            background=True,
                            store=True,
                        )
                        interaction = wait_for_completion(client, interaction.id)
                        st.session_state.research_id = interaction.id
                        st.session_state.research_text = get_text(interaction.outputs) or (
                            f"Status: {interaction.status}"
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        if st.session_state.research_text:
            st.divider()
            st.subheader("📄 Research Results")
            st.markdown(st.session_state.research_text)

        # Phase 3: Synthesis + Infographic
        if st.session_state.research_id:
            if st.button("📊 Generate Executive Report", type="primary"):
                with st.spinner("Synthesizing report..."):
                    try:
                        client = get_gemini_client()
                        interaction = client.interactions.create(
                            model="gemini-3.1-pro-preview",
                            input=(
                                "Create executive report with Summary, Findings, "
                                "Recommendations, Risks:\n\n"
                                f"{st.session_state.research_text}"
                            ),
                            previous_interaction_id=st.session_state.research_id,
                            store=True,
                        )
                        st.session_state.synthesis_text = get_text(interaction.outputs)
                    except Exception as e:
                        st.error(f"Error: {e}")
                        st.stop()

                with st.spinner("Creating TL;DR infographic..."):
                    try:
                        response = client.models.generate_content(
                            model="gemini-3-pro-image-preview",
                            contents=(
                                "Create a whiteboard summary infographic for the following: "
                                f"{st.session_state.synthesis_text}"
                            ),
                        )
                        for part in response.candidates[0].content.parts:
                            if hasattr(part, 'inline_data') and part.inline_data:
                                st.session_state.infographic = part.inline_data.data
                                break
                    except Exception as e:
                        st.warning(f"Infographic error: {e}")
                st.rerun()

        if st.session_state.synthesis_text:
            st.divider()
            st.markdown("## 📊 Executive Report")

            if st.session_state.infographic:
                st.markdown("### 🎨 TL;DR")
                st.image(st.session_state.infographic, use_container_width=True)
                st.divider()

            st.markdown(st.session_state.synthesis_text)
            st.download_button(
                "📥 Download Report",
                st.session_state.synthesis_text,
                "research_report.md",
                "text/markdown",
            )

        st.divider()
        st.caption("[Gemini Interactions API](https://ai.google.dev/gemini-api/docs/interactions)")

    with col_settings:
        st.markdown("### How It Works")
        st.markdown(
            """
            1. **Plan** → Gemini 3 Flash creates research tasks
            2. **Select** → Choose which tasks to research
            3. **Research** → Deep Research Agent investigates
            4. **Synthesize** → Gemini 3 Pro writes report + TL;DR infographic

            Each phase chains via `previous_interaction_id` for context.
            """
        )
        if st.button("Reset", width='stretch', use_container_width=True):
            for key in [
                "plan_id",
                "plan_text",
                "tasks",
                "research_id",
                "research_text",
                "synthesis_text",
                "infographic",
            ]:
                st.session_state[key] = [] if key == "tasks" else None
            st.rerun()
        
# ========== TAB 3: GEMINI 3 PRO CHAT ==========
with tab3:
    # Create two-column layout: main content (3) and settings panel (1)
    col_main, col_settings = st.columns([3, 1])
    
    with col_main:
        st.subheader("💬 Чат з Gemini 3 Pro")
        
        
        # Create scrollable container for chat messages
        chat_messages_container = st.container()
        with chat_messages_container:
            st.markdown('<div class="chat-messages-scrollable">', unsafe_allow_html=True)
            # Display chat history
            for message in st.session_state['gemini_chat_history']:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Chat input (will be rendered at bottom by Streamlit, CSS will keep it fixed)
        if prompt := st.chat_input("Введіть ваше повідомлення..."):
            # Add user message to history
            st.session_state['gemini_chat_history'].append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                try:
                    client = get_gemini_client()
                    
                    # Prepare contents from chat history
                    contents = []
                    for msg in st.session_state['gemini_chat_history']:
                        contents.append(
                            types.Content(
                                role=msg["role"],
                                parts=[types.Part.from_text(text=msg["content"])]
                            )
                        )
                    
                    # Generate content config with thinking_config
                    generate_content_config = types.GenerateContentConfig(
                        temperature=st.session_state['chat_temperature'],
                        max_output_tokens=8192,
                        thinking_config=types.ThinkingConfig(
                            thinking_level=st.session_state['chat_thinking_level']
                        ),
                    )
                    
                    # Stream response
                    for chunk in client.models.generate_content_stream(
                        model="gemini-3.1-pro-preview",
                        contents=contents,
                        config=generate_content_config,
                    ):
                        if (
                            chunk.candidates is None
                            or chunk.candidates[0].content is None
                            or chunk.candidates[0].content.parts is None
                        ):
                            continue
                        
                        # Extract text from chunk
                        chunk_text = ""
                        for part in chunk.candidates[0].content.parts:
                            if hasattr(part, 'text') and part.text:
                                chunk_text += part.text
                        
                        if chunk_text:
                            full_response += chunk_text
                            message_placeholder.markdown(full_response + "▌")
                    
                    # Final update without cursor
                    message_placeholder.markdown(full_response)
                    
                    # Add assistant response to history
                    st.session_state['gemini_chat_history'].append({"role": "assistant", "content": full_response})
                    
                    try:
                        chat_log_text = f"User: {prompt}\n\nAssistant: {full_response}"
                        send_telegram_text_log(chat_log_text, title="💬 Gemini 3 Pro Chat")
                    except Exception:
                        pass
                        
                except Exception as e:
                    error_message = f"❌ Помилка: {str(e)}"
                    message_placeholder.error(error_message)
                    st.exception(e)
    
    # Right settings panel
    with col_settings:
        st.markdown("### Налаштування")
        
        thinking_level = st.selectbox(
            "Мислення:",
            options=["low", "high"],
            index=0 if st.session_state['chat_thinking_level'] == 'low' else 1,
            key="thinking_level_selector"
        )
        st.session_state['chat_thinking_level'] = thinking_level
        
        temperature = st.slider(
            "Temperature:",
            min_value=0.0,
            max_value=2.0,
            value=st.session_state['chat_temperature'],
            step=0.1,
            key="chat_temperature_slider"
        )
        st.session_state['chat_temperature'] = temperature
        
        if st.button("🧹 Очистити чат", width='stretch', use_container_width=True):
            st.session_state['gemini_chat_history'] = []
            st.rerun()
