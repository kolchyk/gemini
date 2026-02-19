import mimetypes
import os
import streamlit as st
from google.genai import types
from services.gemini_client import get_gemini_client
from services.telegram_service import telegram_service
from config import settings

class ChatService:
    def __init__(self):
        self.client = get_gemini_client()
        self._mime_fallback = {
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
            '.png': 'image/png', '.gif': 'image/gif',
            '.bmp': 'image/bmp', '.webp': 'image/webp',
            '.pdf': 'application/pdf',
            '.txt': 'text/plain', '.md': 'text/plain',
            '.py': 'text/plain', '.js': 'text/plain',
            '.ts': 'text/plain', '.html': 'text/html',
            '.css': 'text/css', '.json': 'application/json',
            '.csv': 'text/csv', '.xml': 'application/xml',
        }

    def upload_file(self, uploaded_file):
        """Uploads a file to Gemini and returns attachment metadata."""
        try:
            mime_type, _ = mimetypes.guess_type(uploaded_file.name)
            if not mime_type:
                ext = os.path.splitext(uploaded_file.name)[1].lower()
                mime_type = self._mime_fallback.get(ext, 'application/octet-stream')

            uploaded_file.seek(0)
            file_bytes = uploaded_file.read()
            uploaded_file.seek(0)

            gemini_file = self.client.files.upload(
                file=uploaded_file,
                config={'mime_type': mime_type}
            )

            att = {
                "name": uploaded_file.name,
                "uri": gemini_file.uri,
                "mime_type": mime_type,
            }
            # Store image bytes for thumbnail display (<= 5 MB)
            if mime_type.startswith("image/") and len(file_bytes) <= 5 * 1024 * 1024:
                att["bytes"] = file_bytes
            return att
        except Exception as e:
            raise Exception(f"❌ Помилка завантаження файлу: {str(e)}")

    def generate_response_stream(self, history, thinking_level='low', temperature=0.7):
        """Generates a streaming response from Gemini based on chat history."""
        try:
            # Prepare contents from chat history
            contents = []
            for msg in history:
                parts = []
                for att in msg.get("attachments", []):
                    parts.append(
                        types.Part(file_data=types.FileData(
                            file_uri=att["uri"],
                            mime_type=att["mime_type"],
                        ))
                    )
                parts.append(types.Part.from_text(text=msg["content"]))
                contents.append(types.Content(role=msg["role"], parts=parts))

            # Generate content config
            generate_content_config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=8192,
                thinking_config=types.ThinkingConfig(
                    thinking_level=thinking_level
                ),
            )

            # Stream response
            for chunk in self.client.models.generate_content_stream(
                model="gemini-3.1-pro-preview",
                contents=contents,
                config=generate_content_config,
            ):
                if (
                    chunk.candidates is None
                    or chunk.candidates[0].content is None
                    or chunk.candidates[0].content.parts is None
                ):
                    continue

                chunk_text = ""
                for part in chunk.candidates[0].content.parts:
                    if hasattr(part, 'text') and part.text:
                        chunk_text += part.text
                
                if chunk_text:
                    yield chunk_text

        except Exception as e:
            raise Exception(f"❌ Помилка генерації: {str(e)}")

    def log_chat(self, prompt, full_response):
        """Logs chat interaction to Telegram."""
        try:
            chat_log_text = f"User: {prompt}\n\nAssistant: {full_response}"
            telegram_service.sync_send_text_log(chat_log_text, title="💬 Gemini 3 Pro Chat")
        except Exception:
            pass

chat_service = ChatService()
