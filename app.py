import streamlit as st
from google import genai
from google.genai import types
from PIL import Image as PILImage
import io
import base64
import os
import mimetypes

# Page configuration
st.set_page_config(
    page_title="Gemini Image Generator",
    page_icon="🎨",
    layout="wide"
)

st.title("🎨 Gemini Image Generator")
st.markdown("Завантажте зображення та введіть промпт для генерації нового зображення")

# Initialize Gemini client
@st.cache_resource
def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("⚠️ GEMINI_API_KEY не встановлено. Будь ласка, встановіть змінну середовища.")
        st.stop()
    return genai.Client(api_key=api_key)

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Налаштування")
    aspect_ratio = st.selectbox(
        "Співвідношення сторін",
        ["1:1", "16:9", "9:16", "4:3", "3:4"],
        index=0
    )
    model_name = st.selectbox(
        "Модель",
        ["gemini-3-pro-image-preview"],
        index=0
    )

# Main content area
col1, col2 = st.columns(2)

with col1:
    st.subheader("📤 Завантажте зображення")
    uploaded_file1 = st.file_uploader(
        "Зображення 1 (опціонально)",
        type=['jpg', 'jpeg', 'png', 'bmp', 'gif'],
        key="image1"
    )
    
    uploaded_file2 = st.file_uploader(
        "Зображення 2 (опціонально)",
        type=['jpg', 'jpeg', 'png', 'bmp', 'gif'],
        key="image2"
    )
    
    # Display uploaded images
    if uploaded_file1:
        st.image(uploaded_file1, caption="Зображення 1", use_container_width=True)
    
    if uploaded_file2:
        st.image(uploaded_file2, caption="Зображення 2", use_container_width=True)

with col2:
    st.subheader("✍️ Введіть промпт")
    prompt = st.text_area(
        "Опишіть, що ви хочете згенерувати:",
        height=200,
        placeholder="Наприклад: Keep the facial features of the person in the uploaded image exactly consistent. Dress her in a professional, fitted black business suit..."
    )
    
    generate_button = st.button("🚀 Згенерувати зображення", type="primary", use_container_width=True)

# Generate image when button is clicked
if generate_button:
    # Validation
    if not prompt or not prompt.strip():
        st.error("⚠️ Будь ласка, введіть промпт")
        st.stop()
    
    if not uploaded_file1 and not uploaded_file2:
        st.warning("⚠️ Рекомендується завантажити принаймні одне зображення")
    
    # Show progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("🔄 Ініціалізація клієнта Gemini...")
        progress_bar.progress(10)
        client = get_gemini_client()
        
        # Prepare file parts
        file_parts = []
        
        status_text.text("📤 Завантаження зображень...")
        progress_bar.progress(30)
        
        for idx, uploaded_file in enumerate([uploaded_file1, uploaded_file2], 1):
            if uploaded_file is not None:
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
            st.image(image_bytes, caption="Згенероване зображення", use_container_width=True)
            
            # Download button
            st.download_button(
                label="💾 Завантажити зображення",
                data=image_bytes,
                file_name="generated_image.jpg",
                mime="image/jpeg",
                use_container_width=True
            )
            
            # Store in session state for persistence
            st.session_state['generated_image'] = image_bytes
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
if 'generated_image' in st.session_state:
    st.divider()
    st.subheader("📸 Останнє згенероване зображення")
    st.image(st.session_state['generated_image'], caption="Останнє згенероване зображення", use_container_width=True)
    st.download_button(
        label="💾 Завантажити останнє зображення",
        data=st.session_state['generated_image'],
        file_name="generated_image.jpg",
        mime="image/jpeg",
        use_container_width=True
    )

