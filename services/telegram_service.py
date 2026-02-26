import io
import logging
import asyncio
from telegram import Bot, InputMediaPhoto
from config import settings

logger = logging.getLogger(__name__)


class TelegramService:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID

    def _truncate_caption(self, text, limit=1024):
        """Truncates captions for Telegram, leaving room for ellipsis."""
        if text is None:
            return None
        if len(text) <= limit:
            return text
        return text[: max(0, limit - 3)] + "..."

    def _run_async(self, coro):
        """Run an async coroutine synchronously using asyncio.run for proper cleanup."""
        try:
            asyncio.run(coro)
        except Exception as e:
            logger.error(f"Telegram sync wrapper error: {e}", exc_info=True)

    async def send_image_log(self, original_images_bytes_list, generated_image_bytes, prompt_text, file_metadata_list=None):
        """Sends image generation logs to Telegram as a media group."""
        if not self.token:
            logger.warning("TELEGRAM_BOT_TOKEN not set, skipping Telegram send")
            return

        if not generated_image_bytes:
            logger.error("generated_image_bytes is empty, cannot send image")
            return

        if not isinstance(generated_image_bytes, (bytes, bytearray)):
            logger.error(f"generated_image_bytes has invalid type: {type(generated_image_bytes)}")
            return

        media_group = []

        if original_images_bytes_list:
            for idx, img_bytes in enumerate(original_images_bytes_list):
                if not img_bytes or not isinstance(img_bytes, (bytes, bytearray)):
                    logger.warning(f"Skipping invalid source image {idx}")
                    continue

                caption = None
                if idx == 0:
                    caption = "📸 Source images"
                    if file_metadata_list:
                        for metadata in file_metadata_list:
                            caption += f"\n- {metadata.get('original_name', 'unknown')}"
                    caption = self._truncate_caption(caption)

                img_io = io.BytesIO(img_bytes)
                img_io.seek(0)
                media_group.append(InputMediaPhoto(
                    media=img_io,
                    caption=caption
                ))

        gen_caption = f"🎨 Generated image\n\nPrompt:\n{prompt_text}"
        if not original_images_bytes_list:
            gen_caption = f"⚠️ No references\n\n{gen_caption}"
        gen_caption = self._truncate_caption(gen_caption)

        gen_img_io = io.BytesIO(generated_image_bytes)
        gen_img_io.seek(0)

        try:
            async with Bot(token=self.token) as bot:
                if len(media_group) > 0:
                    media_group.append(InputMediaPhoto(
                        media=gen_img_io,
                        caption=gen_caption
                    ))
                    # Telegram media group limit: 10 items
                    await bot.send_media_group(chat_id=self.chat_id, media=media_group[:10])
                    logger.info(f"Successfully sent {len(media_group[:10])} images to Telegram")
                else:
                    await bot.send_photo(
                        chat_id=self.chat_id,
                        photo=gen_img_io,
                        caption=gen_caption
                    )
                    logger.info("Successfully sent image to Telegram")
        except Exception as e:
            logger.error(f"Error sending images to Telegram: {e}", exc_info=True)

    async def send_text_log(self, text, title=None):
        """Sends text message to Telegram."""
        if not self.token:
            logger.warning("TELEGRAM_BOT_TOKEN not set, skipping Telegram text send")
            return

        message = ""
        if title:
            message += f"<b>{title}</b>\n\n"
        message += text

        # Telegram message length limit: 4096 chars
        if len(message) > 4000:
            message = message[:3997] + "..."

        try:
            async with Bot(token=self.token) as bot:
                await bot.send_message(chat_id=self.chat_id, text=message, parse_mode='HTML')
            logger.info("Successfully sent text message to Telegram")
        except Exception as e:
            logger.error(f"Error sending text to Telegram: {e}", exc_info=True)

    def sync_send_image_log(self, *args, **kwargs):
        """Synchronous wrapper for send_image_log."""
        self._run_async(self.send_image_log(*args, **kwargs))

    def sync_send_text_log(self, *args, **kwargs):
        """Synchronous wrapper for send_text_log."""
        self._run_async(self.send_text_log(*args, **kwargs))


telegram_service = TelegramService()
