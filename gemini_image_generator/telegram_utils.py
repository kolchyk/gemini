"""Telegram logging utilities for image generation."""

import io
import os
import asyncio
from telegram import Bot
from telegram import InputMediaPhoto


async def _send_telegram_log_async(original_images_bytes_list, generated_image_bytes, prompt_text, file_metadata_list=None):
    """Асинхронная функция для отправки логов в Telegram."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        return
    
    chat_id = "6780240224"
    bot = Bot(token=bot_token)
    
    media_group = []
    
    if original_images_bytes_list:
        for idx, img_bytes in enumerate(original_images_bytes_list):
            caption = None
            if idx == 0:
                caption = "📸 Исходные изображения"
                if file_metadata_list:
                    for m_idx, metadata in enumerate(file_metadata_list):
                        caption += f"\n- {metadata.get('original_name', 'unknown')}"
            
            media_group.append(InputMediaPhoto(
                media=io.BytesIO(img_bytes),
                caption=caption
            ))
    
    gen_caption = f"🎨 Згенероване зображення\n\nПромпт:\n{prompt_text}"
    if not original_images_bytes_list:
        gen_caption = f"⚠️ Без референсів\n\n{gen_caption}"
    
    media_group.append(InputMediaPhoto(
        media=io.BytesIO(generated_image_bytes),
        caption=gen_caption
    ))
    
    try:
        if len(media_group) > 1:
            # Ограничение Telegram на media group - до 10 элементов
            await bot.send_media_group(chat_id=chat_id, media=media_group[:10])
        else:
            await bot.send_photo(
                chat_id=chat_id,
                photo=io.BytesIO(generated_image_bytes),
                caption=gen_caption
            )
    except Exception:
        pass


async def _send_telegram_text_async(text, title=None):
    """Асинхронная функция для отправки текста в Telegram."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        return
    
    chat_id = "6780240224"
    bot = Bot(token=bot_token)
    
    message = ""
    if title:
        message += f"<b>{title}</b>\n\n"
    message += text
    
    # Ограничение Telegram на длину сообщения (4096 символов)
    if len(message) > 4000:
        message = message[:3997] + "..."
    
    await bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')


def send_telegram_log(original_images_bytes_list, generated_image_bytes, prompt_text, file_metadata_list=None):
    """Отправляет логи в Telegram: исходные фото, обработанное фото и промпт."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_send_telegram_log_async(original_images_bytes_list, generated_image_bytes, prompt_text, file_metadata_list))
        loop.close()
    except Exception:
        pass


def send_telegram_text_log(text, title=None):
    """
    Отправляет текстовый лог в Telegram.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_send_telegram_text_async(text, title))
        loop.close()
    except Exception:
        pass

