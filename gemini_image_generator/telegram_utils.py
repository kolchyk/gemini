"""Telegram logging utilities for image generation."""

import io
import os
import asyncio
import logging
from telegram import Bot
from telegram import InputMediaPhoto

logger = logging.getLogger(__name__)


def _truncate_caption(text, limit=1024):
    """Обрезает подписи для Telegram, оставляя место под многоточие."""
    if text is None:
        return None
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)] + "..."


async def _send_telegram_log_async(original_images_bytes_list, generated_image_bytes, prompt_text, file_metadata_list=None):
    """Асинхронная функция для отправки логов в Telegram."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN не установлен, пропуск отправки в Telegram")
        return
    
    # Проверка данных перед отправкой
    if not generated_image_bytes:
        logger.error("generated_image_bytes пустой, невозможно отправить изображение")
        return
    
    if not isinstance(generated_image_bytes, (bytes, bytearray)):
        logger.error(f"generated_image_bytes имеет неверный тип: {type(generated_image_bytes)}")
        return
    
    chat_id = "6780240224"
    bot = Bot(token=bot_token)
    
    media_group = []
    
    if original_images_bytes_list:
        for idx, img_bytes in enumerate(original_images_bytes_list):
            if not img_bytes or not isinstance(img_bytes, (bytes, bytearray)):
                logger.warning(f"Пропуск некорректного исходного изображения {idx}")
                continue
            
            caption = None
            if idx == 0:
                caption = "📸 Исходные изображения"
                if file_metadata_list:
                    for m_idx, metadata in enumerate(file_metadata_list):
                        caption += f"\n- {metadata.get('original_name', 'unknown')}"
                caption = _truncate_caption(caption)
            
            img_io = io.BytesIO(img_bytes)
            img_io.seek(0)
            media_group.append(InputMediaPhoto(
                media=img_io,
                caption=caption
            ))
    
    gen_caption = f"🎨 Згенероване зображення\n\nПромпт:\n{prompt_text}"
    if not original_images_bytes_list:
        gen_caption = f"⚠️ Без референсів\n\n{gen_caption}"
    gen_caption = _truncate_caption(gen_caption)
    
    gen_img_io = io.BytesIO(generated_image_bytes)
    gen_img_io.seek(0)
    media_group.append(InputMediaPhoto(
        media=gen_img_io,
        caption=gen_caption
    ))
    
    try:
        if len(media_group) > 1:
            # Ограничение Telegram на media group - до 10 элементов
            await bot.send_media_group(chat_id=chat_id, media=media_group[:10])
            logger.info(f"Успешно отправлено {len(media_group[:10])} изображений в Telegram")
        else:
            photo_io = io.BytesIO(generated_image_bytes)
            photo_io.seek(0)
            await bot.send_photo(
                chat_id=chat_id,
                photo=photo_io,
                caption=gen_caption
            )
            logger.info("Успешно отправлено изображение в Telegram")
    except Exception as e:
        logger.error(f"Ошибка при отправке изображений в Telegram: {str(e)}", exc_info=True)


async def _send_telegram_text_async(text, title=None):
    """Асинхронная функция для отправки текста в Telegram."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN не установлен, пропуск отправки текста в Telegram")
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
    
    try:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
        logger.info("Успешно отправлено текстовое сообщение в Telegram")
    except Exception as e:
        logger.error(f"Ошибка при отправке текста в Telegram: {str(e)}", exc_info=True)


def send_telegram_log(original_images_bytes_list, generated_image_bytes, prompt_text, file_metadata_list=None):
    """Отправляет логи в Telegram: исходные фото, обработанное фото и промпт."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_send_telegram_log_async(original_images_bytes_list, generated_image_bytes, prompt_text, file_metadata_list))
        loop.close()
    except Exception as e:
        logger.error(f"Ошибка при создании event loop или выполнении асинхронной отправки в Telegram: {str(e)}", exc_info=True)


def send_telegram_text_log(text, title=None):
    """
    Отправляет текстовый лог в Telegram.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_send_telegram_text_async(text, title))
        loop.close()
    except Exception as e:
        logger.error(f"Ошибка при создании event loop или выполнении асинхронной отправки текста в Telegram: {str(e)}", exc_info=True)
