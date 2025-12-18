"""Telegram logging utilities for image generation."""

import io
import os
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from telegram import InputMediaPhoto


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
        # Если только сгенерированное изображение, отправляем с промптом в подписи и пометкой об отсутствии оригинала
        await bot.send_photo(
            chat_id=chat_id,
            photo=io.BytesIO(generated_image_bytes),
            caption=f"⚠️ Начальное изображение не задано\n\nПромпт:\n{prompt_text}"
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

