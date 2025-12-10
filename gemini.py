from google import genai
from google.genai import types
from PIL import Image as PILImage
import io
import base64
import os
import mimetypes
import tkinter as tk
from tkinter import filedialog

client = genai.Client(api_key="GEMINI_API_KEY")

model = "gemini-3-pro-image-preview"  # або ім'я, яке у твоєму SDK відповідає Nano Banana Pro

# Вибір файлу вручну через діалог
root = tk.Tk()
root.withdraw()  # Приховуємо головне вікно

input_file_path = filedialog.askopenfilename(
    title="Виберіть зображення для обробки",
    filetypes=[
        ("Зображення", "*.jpg *.jpeg *.png *.bmp *.gif"),
        ("JPEG", "*.jpg *.jpeg"),
        ("PNG", "*.png"),
        ("Всі файли", "*.*")
    ]
)

root.destroy()  # Закриваємо вікно після вибору

# Завантажуємо файл, якщо він існує
file_parts = []
if input_file_path and os.path.exists(input_file_path):
    # Визначаємо MIME тип на основі розширення файлу
    mime_type, _ = mimetypes.guess_type(input_file_path)
    if not mime_type:
        # Якщо mimetypes не зміг визначити тип, використовуємо за замовчуванням
        ext = os.path.splitext(input_file_path)[1].lower()
        mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp'
        }
        mime_type = mime_map.get(ext, 'image/jpeg')
    
    # Завантажуємо файл
    with open(input_file_path, 'rb') as f:
        uploaded_file = client.files.upload(file=f, config={'mime_type': mime_type})
    # Створюємо частину контенту з файлом
    file_parts.append(types.Part(file_data=types.FileData(file_uri=uploaded_file.uri)))
    print(f"Файл {input_file_path} завантажено успішно")
else:
    if not input_file_path:
        print("Файл не вибрано. Генерація без вхідного зображення.")
    else:
        print(f"Попередження: файл {input_file_path} не знайдено. Генерація без вхідного зображення.")

# Створюємо текстовий промпт
text_prompt = "Keep the facial features of the person in the uploaded image exactly consistent. Dress her in a professional, **fitted black business suit (blazer) with a crisp white blouse**. Background: Place the subject against a clean, solid dark gray studio photography backdrop. The background should have a subtle gradient, slightly lighter behind the subject and darker towards the edges (vignette effect). There should be no other objects. Photography Style: Shot on a Sony A7III with an 85mm f/1.4 lens, creating a flattering portrait compression. Lighting: Use a classic three-point lighting setup. The main key light should create soft, defining shadows on the face. A subtle rim light should separate the subject's shoulders and hair from the dark background. Crucial Details: Render natural skin texture with visible pores, not an airbrushed look. Add natural catchlights to the eyes. The fabric of the suit should show a subtle wool texture. Final image should be an ultra-realistic, 8k professional headshot."

# Створюємо частину з текстом
text_part = types.Part(text=text_prompt)

# Об'єднуємо файли та текст у contents (спочатку файли, потім текст)
contents = file_parts + [text_part]

resp = client.models.generate_content(
    model=model,
    contents=contents,
    config=types.GenerateContentConfig(
        response_modalities=[ "IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio="1:1",  # або "1:1", "9:16" тощо
        ),
    ),
)

# Отримуємо зображення з відповіді
image_bytes = None

# Перевіряємо структуру відповіді
if hasattr(resp, 'parts') and resp.parts:
    for part in resp.parts:
        # Перевіряємо чи є inline_data
        if hasattr(part, 'inline_data') and part.inline_data is not None:
            # Спробуємо отримати зображення через as_image()
            try:
                img = part.as_image()
                if img is not None and isinstance(img, PILImage.Image):
                    # Конвертуємо PIL Image у bytes
                    buf = io.BytesIO()
                    img.save(buf, format='JPEG')
                    image_bytes = buf.getvalue()
                    break
            except Exception as e:
                # Якщо as_image() не працює, спробуємо отримати дані напряму
                pass
            
            # Альтернативний спосіб: отримати дані напряму з inline_data
            if hasattr(part.inline_data, 'data'):
                # Дані можуть бути в base64 або bytes
                data = part.inline_data.data
                if isinstance(data, bytes):
                    image_bytes = data
                    break
                elif isinstance(data, str):
                    # Якщо це base64 рядок
                    image_bytes = base64.b64decode(data)
                    break
# Зберігаємо зображення у файл JPEG
if image_bytes:
    with open("output.jpg", "wb") as f:
        f.write(image_bytes)
    print("Зображення збережено у файл output.jpg")
else:
    print("Помилка: зображення не знайдено у відповіді")
    # Додаткова діагностика
    if hasattr(resp, 'parts'):
        print(f"Кількість parts у відповіді: {len(resp.parts)}")
        for i, part in enumerate(resp.parts):
            print(f"Part {i}: {type(part)}")
            if hasattr(part, 'inline_data'):
                print(f"  inline_data: {part.inline_data}")
