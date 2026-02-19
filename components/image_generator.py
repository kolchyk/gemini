import streamlit as st
import time
from services.image_service import ImageService
from config import settings, styles, prompts

def render_image_generator():
    """Renders the image generator UI component."""
    image_service = ImageService()

    # Initialize session state for image generator settings
    if 'image_aspect_ratio' not in st.session_state:
        st.session_state['image_aspect_ratio'] = "1:1"
    if 'image_resolution' not in st.session_state:
        st.session_state['image_resolution'] = "1K"
    if 'image_temperature' not in st.session_state:
        st.session_state['image_temperature'] = 1.0
    if 'prompt_type' not in st.session_state:
        st.session_state['prompt_type'] = 'custom'
    if 'edited_prompt_women' not in st.session_state:
        st.session_state['edited_prompt_women'] = None
    if 'edited_prompt_men' not in st.session_state:
        st.session_state['edited_prompt_men'] = None
    if 'edited_prompt_custom' not in st.session_state:
        st.session_state['edited_prompt_custom'] = None

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
            base_prompt = prompts.PROMPT_WOMEN
            edited_prompt = st.session_state['edited_prompt_women']
        elif st.session_state['prompt_type'] == 'men':
            base_prompt = prompts.PROMPT_MEN
            edited_prompt = st.session_state['edited_prompt_men']
        else:  # custom
            base_prompt = prompts.PROMPT_CUSTOM
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
            if st.button("↩️ Скинути промпт до шаблону", use_container_width=True):
                if st.session_state['prompt_type'] == 'women':
                    st.session_state['edited_prompt_women'] = prompts.PROMPT_WOMEN
                elif st.session_state['prompt_type'] == 'men':
                    st.session_state['edited_prompt_men'] = prompts.PROMPT_MEN
                else:  # custom
                    st.session_state['edited_prompt_custom'] = prompts.PROMPT_CUSTOM
                st.rerun()
        with col_b:
            if st.button("🧹 Очистити останній результат", use_container_width=True):
                st.session_state.pop('generated_image', None)
                st.rerun()
    
        # Save edited prompt when user edits
        if st.session_state['prompt_type'] == 'women':
            st.session_state['edited_prompt_women'] = prompt
        elif st.session_state['prompt_type'] == 'men':
            st.session_state['edited_prompt_men'] = prompt
        else:  # custom
            st.session_state['edited_prompt_custom'] = prompt
        
        # Generate button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            generate_button = st.button("🚀 Згенерувати зображення", type="primary", use_container_width=True)
            
        if generate_button:
            if not prompt:
                st.error("Будь ласка, введіть промпт!")
            else:
                with st.spinner("✨ Генеруємо ваш шедевр..."):
                    try:
                        result = image_service.generate_image(
                            prompt=prompt,
                            aspect_ratio=st.session_state['image_aspect_ratio'],
                            person_images=uploaded_files,
                            resolution=st.session_state['image_resolution'],
                            temperature=st.session_state['image_temperature']
                        )
                        
                        if result['image_bytes']:
                            st.session_state['generated_image'] = result['image_bytes']
                            if result['text_output']:
                                st.session_state['generated_text'] = result['text_output']
                            st.success("🎉 Зображення успішно згенеровано!")
                        else:
                            st.warning("Модель не повернула зображення. Спробуйте інший промпт.")
                    except Exception as e:
                        st.error(f"❌ Виникла помилка: {str(e)}")
                        st.exception(e)

        # Section 3: Result display (bottom)
        if 'generated_image' in st.session_state:
            st.subheader("🖼️ Результат")
            st.image(st.session_state['generated_image'], use_container_width=True)
            
            # Download button
            st.download_button(
                label="📥 Завантажити зображення",
                data=st.session_state['generated_image'],
                file_name=f"generated_image_{int(time.time())}.png",
                mime="image/png",
                use_container_width=True
            )
            
            if 'generated_text' in st.session_state:
                with st.expander("Опис від моделі"):
                    st.write(st.session_state['generated_text'])

    # Right settings panel
    with col_settings:
        st.markdown(f'<div class="model-label">Модель:</div><div class="model-badge">🎨 {settings.IMAGE_MODEL}</div>', unsafe_allow_html=True)
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

