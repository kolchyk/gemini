import streamlit as st
import time
import concurrent.futures
from services.image_service import ImageService
from services.error_utils import format_error_with_retry
from config import settings, prompts


def render_image_sidebar():
    """Renders the sidebar for image generator."""
    with st.sidebar:
        # Dynamic badge based on selected mode
        mode = st.session_state.get('image_generation_mode', 'Pro')
        badge_text = f"🍌 Nano Banana 2 {mode}" if mode != "Обидві" else "🍌 Nano Banana 2 (Dual)"
        st.markdown(f'<div class="model-badge">{badge_text}</div>', unsafe_allow_html=True)

        image_generation_mode = st.selectbox(
            "Режим генерації:",
            options=["Flash", "Pro", "Обидві"],
            index=["Flash", "Pro", "Обидві"].index(mode),
            key="image_generation_mode_selector"
        )
        st.session_state['image_generation_mode'] = image_generation_mode

        # Update underlying image_model for backward compatibility if needed
        if image_generation_mode == "Flash":
            st.session_state['image_model'] = settings.GEMINI_IMAGE_MODELS[0]
        elif image_generation_mode == "Pro":
            st.session_state['image_model'] = settings.GEMINI_IMAGE_MODELS[1]
        # For "Обидві", we'll handle it in the generation button logic

        st.markdown('<div class="sidebar-section-label">Параметри</div>', unsafe_allow_html=True)

        aspect_ratio = st.selectbox(
            "Співвідношення:",
            options=["1:1", "16:9", "9:16", "4:3", "3:4"],
            index=["1:1", "16:9", "9:16", "4:3", "3:4"].index(
                st.session_state.get('image_aspect_ratio', settings.IMAGE_DEFAULT_ASPECT_RATIO)
            ),
            key="image_aspect_ratio_selector"
        )
        st.session_state['image_aspect_ratio'] = aspect_ratio

        resolution = st.selectbox(
            "Роздільність:",
            options=["1K", "2K", "4K"],
            index=["1K", "2K", "4K"].index(
                st.session_state.get('image_resolution', settings.IMAGE_DEFAULT_RESOLUTION)
            ),
            key="image_resolution_selector"
        )
        st.session_state['image_resolution'] = resolution

        temperature = st.slider(
            "Temperature:",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.get('image_temperature', settings.IMAGE_DEFAULT_TEMPERATURE),
            step=0.05,
            key="image_temperature_slider"
        )
        st.session_state['image_temperature'] = temperature

        if image_generation_mode in ("Pro", "Обидві"):
            st.markdown('<div class="sidebar-section-label">Розширені</div>', unsafe_allow_html=True)
            thinking_level = st.selectbox(
                "Thinking:",
                options=["MINIMAL", "LOW", "MEDIUM", "HIGH"],
                index=["MINIMAL", "LOW", "MEDIUM", "HIGH"].index(
                    st.session_state.get('image_thinking_level', settings.IMAGE_DEFAULT_THINKING_LEVEL)
                ),
                key="image_thinking_level_selector"
            )
            st.session_state['image_thinking_level'] = thinking_level

        st.divider()
        if st.button("🧹 Очистити результат", use_container_width=True, type="secondary"):
            st.session_state.pop('generated_image', None)
            st.session_state.pop('generated_text', None)
            st.session_state.pop('generated_results', None)
            st.rerun()

        st.markdown('<div class="sidebar-section-label">Документація</div>', unsafe_allow_html=True)
        st.markdown("""
        - [Imagen 4 Guide](https://ai.google.dev/gemini-api/docs/imagen)
        - [Prompt Engineering](https://ai.google.dev/gemini-api/docs/prompting-strategies)

        *Nano Banana 2 — високоякісна генерація зображень.*
        """, unsafe_allow_html=True)


def _init_session_state():
    """Initialize session state defaults for image generator."""
    defaults = {
        'image_model': settings.IMAGE_MODEL if settings.IMAGE_MODEL in settings.IMAGE_MODELS else settings.IMAGE_MODELS[0],
        'image_aspect_ratio': settings.IMAGE_DEFAULT_ASPECT_RATIO,
        'image_resolution': settings.IMAGE_DEFAULT_RESOLUTION,
        'image_temperature': settings.IMAGE_DEFAULT_TEMPERATURE,
        'image_thinking_level': settings.IMAGE_DEFAULT_THINKING_LEVEL,
        'image_person_generation': settings.IMAGE_DEFAULT_PERSON_GENERATION,
        'image_generation_mode': 'Pro',  # 'Flash' | 'Pro' | 'Обидві'
        'prompt_type': 'custom',
        'edited_prompt_women': None,
        'edited_prompt_men': None,
        'edited_prompt_custom': None,
        'generated_results': {},  # Map of model_name -> result_dict
    }
    for key, default_val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_val


def _render_reference_upload():
    """Step 1: Reference image upload section. Returns uploaded files."""
    st.subheader("📤 Крок 1: Референсні зображення")
    uploaded_files = st.file_uploader(
        "Референсні зображення (опціонально)",
        type=['jpg', 'jpeg', 'png', 'bmp', 'gif'],
        accept_multiple_files=True,
        help="Для режиму 'З нуля' — опціонально. Для 'Жінки'/'Чоловіки' — рекомендовано 1–3 референси.",
        key="reference_images"
    )

    current_image_model = st.session_state.get('image_model', settings.IMAGE_MODEL)
    # Gemini models and Nano Banana 2 use native Gemini API (generate_content)
    is_imagen = "imagen" in current_image_model.lower() or current_image_model in getattr(settings, 'IMAGEN_MODELS', ())
    is_gemini_image = "gemini" in current_image_model.lower() or current_image_model in getattr(settings, 'GEMINI_IMAGE_MODELS', ())
    
    if is_gemini_image:
        is_imagen = False
        
    if uploaded_files and is_imagen:
        st.info("ℹ️ Модель Imagen генерує зображення лише за текстовим описом. Референсні зображення ігноруються.")

    if uploaded_files:
        num_files = len(uploaded_files)
        cols = st.columns(min(6, num_files))
        for idx, uploaded_file in enumerate(uploaded_files):
            with cols[idx % len(cols)]:
                st.image(uploaded_file, caption=f"Реф. {idx + 1}", use_container_width=True)

    return uploaded_files


def _render_prompt_section():
    """Step 2: Prompt type selector and text area. Returns the prompt text."""
    st.subheader("✍️ Крок 2: Промпт")

    prompt_type_options = ["З нуля (Власний промпт)", "Жінки", "Чоловіки"]
    prompt_type_index_map = {'custom': 0, 'women': 1, 'men': 2}
    current_index = prompt_type_index_map.get(st.session_state['prompt_type'], 0)

    prompt_type = st.radio(
        "Режим генерації:",
        prompt_type_options,
        index=current_index,
        horizontal=True,
        help="Оберіть режим генерації. 'З нуля' — для створення зображень з нуля, 'Жінки'/'Чоловіки' — для редагування фото.",
        key="prompt_type_selector"
    )

    type_map = {
        "З нуля (Власний промпт)": 'custom',
        "Жінки": 'women',
        "Чоловіки": 'men'
    }
    current_prompt_type = type_map[prompt_type]

    if current_prompt_type != st.session_state['prompt_type']:
        old_prompt_key = f"prompt_text_area_{st.session_state['prompt_type']}"
        if old_prompt_key in st.session_state:
            st.session_state[f'edited_prompt_{st.session_state["prompt_type"]}'] = st.session_state[old_prompt_key]
        st.session_state['prompt_type'] = current_prompt_type

    # Determine prompt
    prompt_map = {
        'women': (prompts.PROMPT_WOMEN, st.session_state['edited_prompt_women']),
        'men': (prompts.PROMPT_MEN, st.session_state['edited_prompt_men']),
        'custom': (prompts.PROMPT_CUSTOM, st.session_state['edited_prompt_custom']),
    }
    base_prompt, edited_prompt = prompt_map[st.session_state['prompt_type']]
    current_prompt_value = edited_prompt if edited_prompt is not None else base_prompt

    prompt_key = f"prompt_text_area_{st.session_state['prompt_type']}"
    prompt = st.text_area(
        "Промпт:",
        value=current_prompt_value,
        height=150,
        placeholder="Опишіть що згенерувати...",
        key=prompt_key
    )

    col_reset, _ = st.columns([1, 2])
    with col_reset:
        if st.button("↩️ Скинути промпт", use_container_width=True):
            st.session_state[f'edited_prompt_{st.session_state["prompt_type"]}'] = base_prompt
            st.rerun()

    st.session_state[f'edited_prompt_{st.session_state["prompt_type"]}'] = prompt
    return prompt


def _render_generate_button(image_service, prompt, uploaded_files):
    """Generate button and execution logic."""
    st.markdown('<div class="spacer-lg"></div>', unsafe_allow_html=True)
    
    mode = st.session_state.get('image_generation_mode', 'Pro')
    button_label = "🚀 Згенерувати зображення"
    if mode == "Обидві":
        button_label += " (паралельно)"
    
    if st.button(button_label, type="primary", use_container_width=True):
        if not prompt:
            st.error("Будь ласка, введіть промпт!")
        else:
            spinner_text = f"✨ Генеруємо ваш шедевр ({mode})..."
            if mode == "Обидві":
                spinner_text = "✨ Генеруємо ваш шедевр у двох моделях паралельно..."
                
            with st.spinner(spinner_text):
                try:
                    # Determine target models based on generation mode
                    flash_model = settings.GEMINI_IMAGE_MODELS[0]
                    pro_model = settings.GEMINI_IMAGE_MODELS[1]
                    
                    if mode == "Flash":
                        target_models = [flash_model]
                    elif mode == "Pro":
                        target_models = [pro_model]
                    else:  # "Обидві"
                        target_models = [flash_model, pro_model]

                    # Capture session state values in main thread; worker threads cannot
                    # access st.session_state (KeyError / wrong context on Heroku etc.)
                    aspect_ratio = st.session_state.get('image_aspect_ratio', settings.IMAGE_DEFAULT_ASPECT_RATIO)
                    resolution = st.session_state.get('image_resolution', settings.IMAGE_DEFAULT_RESOLUTION)
                    temperature = st.session_state.get('image_temperature', settings.IMAGE_DEFAULT_TEMPERATURE)
                    thinking_level = st.session_state.get('image_thinking_level', settings.IMAGE_DEFAULT_THINKING_LEVEL)

                    def generate_with_model(model_name):
                        model_thinking = None if "pro" not in model_name.lower() else thinking_level
                        return model_name, image_service.generate_image(
                            prompt=prompt,
                            aspect_ratio=aspect_ratio,
                            person_images=uploaded_files,
                            resolution=resolution,
                            temperature=temperature,
                            model=model_name,
                            thinking_level=model_thinking,
                        )

                    results = {}
                    with concurrent.futures.ThreadPoolExecutor(max_workers=len(target_models)) as executor:
                        future_to_model = {executor.submit(generate_with_model, m): m for m in target_models}
                        for future in concurrent.futures.as_completed(future_to_model):
                            model_name, result = future.result()
                            results[model_name] = result

                    st.session_state['generated_results'] = results
                    
                    # Backwards compatibility for single image if needed elsewhere
                    first_model = target_models[0]
                    if results.get(first_model, {}).get('image_bytes'):
                        st.session_state['generated_image'] = results[first_model]['image_bytes']
                        if results[first_model].get('text_output'):
                            st.session_state['generated_text'] = results[first_model]['text_output']

                    st.success(f"🎉 Зображення згенеровано ({', '.join(target_models)})!")
                    st.rerun()
                except Exception as e:
                    st.error(format_error_with_retry(e, "генерацію зображення"))
                    with st.expander("Технічні деталі"):
                        st.exception(e)


def _render_result_section():
    """Step 3: Result display with side-by-side models."""
    results = st.session_state.get('generated_results', {})
    
    if results:
        st.subheader("🖼️ Результати")
        
        model_names = list(results.keys())
        num_models = len(model_names)
        
        if num_models > 0:
            cols = st.columns(num_models)
            for idx, model_name in enumerate(model_names):
                with cols[idx]:
                    result = results[model_name]
                    st.markdown(f"**Модель: `{model_name}`**")
                    if result.get('image_bytes'):
                        st.image(result['image_bytes'], use_container_width=True)
                        st.download_button(
                            label=f"📥 Завантажити ({model_name})",
                            data=result['image_bytes'],
                            file_name=f"generated_{model_name}_{int(time.time())}.png",
                            mime="image/png",
                            use_container_width=True,
                            key=f"download_{model_name}_{idx}"
                        )
                        if result.get('text_output'):
                            with st.expander(f"Опис від {model_name}"):
                                st.write(result['text_output'])
                    else:
                        st.warning(f"Модель `{model_name}` не повернула зображення.")
    elif 'generated_image' in st.session_state:
        # Fallback for old sessions or single results
        st.subheader("🖼️ Результат")
        st.image(st.session_state['generated_image'], use_container_width=True)
        st.download_button(
            label="📥 Завантажити зображення",
            data=st.session_state['generated_image'],
            file_name=f"generated_image_{int(time.time())}.png",
            mime="image/png",
            use_container_width=True
        )
    else:
        st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">🍌</div>
                <h3>Результат з'явиться тут</h3>
                <p>Налаштуйте промпт та натисніть "Згенерувати зображення"</p>
            </div>
        """, unsafe_allow_html=True)


def render_image_generator():
    """Renders the image generator UI component."""
    _init_session_state()
    image_service = ImageService()

    uploaded_files = _render_reference_upload()
    prompt = _render_prompt_section()
    _render_generate_button(image_service, prompt, uploaded_files)
    _render_result_section()
