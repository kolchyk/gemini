"""Shared MIME type detection utilities."""

import mimetypes
import os

_MIME_FALLBACK: dict[str, str] = {
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


def guess_mime_type(filename: str, default: str = 'application/octet-stream') -> str:
    """Guess MIME type from filename, with robust fallback for common types."""
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type:
        return mime_type
    ext = os.path.splitext(filename)[1].lower()
    return _MIME_FALLBACK.get(ext, default)
