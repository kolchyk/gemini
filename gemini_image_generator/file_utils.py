"""File handling utilities for uploaded images and metadata extraction."""

import io
import os
import re
import uuid
from PIL import Image as PILImage


def extract_metadata_hints(file_bytes, file_path):
    """
    Extracts path hints from image metadata (best-effort).
    Returns a list of strings resembling Windows paths.
    """
    hints = []

    try:
        img = PILImage.open(io.BytesIO(file_bytes))

        exif_data = img.getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                try:
                    if isinstance(value, str):
                        # Drive letter paths: X:\... or X:/...
                        drive_pattern = r'[A-Za-z]:[\\/][^\\/:*?"<>|\r\n]{0,200}'
                        # UNC paths: \\server\share\...
                        unc_pattern = r'\\\\[^\\/:*?"<>|\r\n]{1,200}(?:\\[^\\/:*?"<>|\r\n]{0,200}){0,10}'

                        matches = re.findall(drive_pattern, value)
                        hints.extend(matches)
                        matches = re.findall(unc_pattern, value)
                        hints.extend(matches)
                except Exception:
                    continue

        # Additional: search raw bytes for ASCII strings resembling Windows paths
        try:
            text_content = file_bytes[:min(50000, len(file_bytes))].decode('ascii', errors='ignore')

            drive_pattern = r'[A-Za-z]:[\\/][^\\/:*?"<>|\r\n]{10,200}'
            unc_pattern = r'\\\\[^\\/:*?"<>|\r\n]{1,50}(?:\\[^\\/:*?"<>|\r\n]{1,50}){1,10}'

            matches = re.findall(drive_pattern, text_content)
            hints.extend(matches)
            matches = re.findall(unc_pattern, text_content)
            hints.extend(matches)
        except Exception:
            pass

    except Exception:
        # If processing as image fails, skip
        pass

    # Deduplicate and limit length
    unique_hints = []
    seen = set()
    for hint in hints:
        normalized = hint.replace('/', '\\').lower()
        if normalized not in seen and len(hint) <= 300:
            seen.add(normalized)
            unique_hints.append(hint)
            if len(unique_hints) >= 5:
                break

    return unique_hints


def save_uploaded_file(uploaded_file):
    """
    Saves an uploaded file to a temporary directory and returns file metadata.
    Returns a dict with keys: original_name, server_abs_path, metadata_hints
    """
    temp_dir = os.path.join(os.path.dirname(__file__), "..", "temp_uploads")
    temp_dir = os.path.abspath(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)

    original_name = uploaded_file.name
    name_base, ext = os.path.splitext(original_name)
    unique_name = f"{name_base}_{uuid.uuid4().hex[:8]}{ext}"
    file_path = os.path.join(temp_dir, unique_name)

    uploaded_file.seek(0)
    file_bytes = uploaded_file.read()

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Extract metadata hints (best-effort)
    metadata_hints = extract_metadata_hints(file_bytes, file_path)

    return {
        'original_name': original_name,
        'server_abs_path': os.path.abspath(file_path),
        'metadata_hints': metadata_hints
    }
