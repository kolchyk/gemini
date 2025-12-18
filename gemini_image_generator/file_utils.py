"""File handling utilities for uploaded images and metadata extraction."""

import io
import os
import re
import uuid
from PIL import Image as PILImage


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


def save_uploaded_file(uploaded_file):
    """
    Сохраняет загруженный файл во временную директорию и возвращает метаданные файла.
    Возвращает словарь с ключами: original_name, server_abs_path, metadata_hints
    """
    # Создаем директорию temp_uploads в корне проекта, если не существует
    temp_dir = os.path.join(os.path.dirname(__file__), "..", "temp_uploads")
    temp_dir = os.path.abspath(temp_dir)
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

