import io
import logging
import asyncio
from telegram import Bot, InputMediaPhoto
from config import settings

logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self):
        self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN) if settings.TELEGRAM_BOT_TOKEN else None
        self.chat_id = settings.TELEGRAM_CHAT_ID

    def _truncate_caption(self, text, limit=1024):
        """Обрезает подписи для Telegram, оставляя место под многоточие."""
        if text is None:
            return None
        if len(text) <= limit:
            return text
        return text[: max(0, limit - 3)] + "..."

    async def send_image_log(self, original_images_bytes_list, generated_image_bytes, prompt_text, file_metadata_list=None):
        """Асинхронная функция для отправки логов в Telegram."""
        if not self.bot:
            logger.warning("TELEGRAM_BOT_TOKEN не установлен, пропуск отправки в Telegram")
            return
        
        # Проверка данных перед отправкой
        if not generated_image_bytes:
            logger.error("generated_image_bytes пустой, невозможно отправить изображение")
            return
        
        if not isinstance(generated_image_bytes, (bytes, bytearray)):
            logger.error(f"generated_image_bytes имеет неверный тип: {type(generated_image_bytes)}")
            return
        
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
                    caption = self._truncate_caption(caption)
                
                img_io = io.BytesIO(img_bytes)
                img_io.seek(0)
                media_group.append(InputMediaPhoto(
                    media=img_io,
                    caption=caption
                ))
        
        gen_caption = f"🎨 Згенероване зображення\n\nПромпт:\n{prompt_text}"
        if not original_images_bytes_list:
            gen_caption = f"⚠️ Без референсів\n\n{gen_caption}"
        gen_caption = self._truncate_caption(gen_caption)
        
        gen_img_io = io.BytesIO(generated_image_bytes)
        gen_img_io.seek(0)
        
        try:
            if len(media_group) > 0:
                # Добавляем сгенерированное изображение к группе
                media_group.append(InputMediaPhoto(
                    media=gen_img_io,
                    caption=gen_caption
                ))
                # Ограничение Telegram на media group - до 10 элементов
                await self.bot.send_media_group(chat_id=self.chat_id, media=media_group[:10])
                logger.info(f"Успешно отправлено {len(media_group[:10])} изображений в Telegram")
            else:
                await self.bot.send_photo(
                    chat_id=self.chat_id,
                    photo=gen_img_io,
                    caption=gen_caption
                )
                logger.info("Успешно отправлено изображение в Telegram")
        except Exception as e:
            logger.error(f"Ошибка при отправке изображений в Telegram: {str(e)}", exc_info=True)

    async def send_text_log(self, text, title=None):
        """Асинхронная функция для отправки текста в Telegram."""
        if not self.bot:
            logger.warning("TELEGRAM_BOT_TOKEN не установлен, пропуск отправки текста в Telegram")
            return
        
        message = ""
        if title:
            message += f"<b>{title}</b>\n\n"
        message += text
        
        # Ограничение Telegram на длину сообщения (4096 символов)
        if len(message) > 4000:
            message = message[:3997] + "..."
        
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message, parse_mode='HTML')
            logger.info("Успешно отправлено текстовое сообщение в Telegram")
        except Exception as e:
            logger.error(f"Ошибка при отправке текста в Telegram: {str(e)}", exc_info=True)

    def sync_send_image_log(self, *args, **kwargs):
        """Синхронная обертка для send_image_log."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.send_image_log(*args, **kwargs))
            loop.close()
        except Exception as e:
            logger.error(f"Ошибка при синхронной отправке изображений в Telegram: {str(e)}", exc_info=True)

    def sync_send_text_log(self, *args, **kwargs):
        """Синхронная обертка для send_text_log."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.send_text_log(*args, **kwargs))
            loop.close()
        except Exception as e:
            logger.error(f"Ошибка при синхронной отправке текста в Telegram: {str(e)}", exc_info=True)

telegram_service = TelegramService()
