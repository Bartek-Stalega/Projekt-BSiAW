"""Zapisywanie obrazkow z formularzy."""

import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import ALLOWED_IMAGE_TYPES, MAX_UPLOAD_BYTES, UPLOAD_DIR


class UploadError(ValueError):
    pass


def ensure_upload_dir() -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR


def save_image(upload: UploadFile | None) -> str | None:
    """Zapisuje plik; zwraca nazwe do URL /uploads/<name> albo None gdy brak pliku."""
    if upload is None or not upload.filename:
        return None

    content_type = (upload.content_type or "").lower()
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise UploadError("Dozwolone formaty: JPEG, PNG, WebP.")

    data = upload.file.read()
    if not data:
        return None
    if len(data) > MAX_UPLOAD_BYTES:
        raise UploadError(f"Plik jest za duzy (max {MAX_UPLOAD_BYTES // (1024 * 1024)} MB).")

    ensure_upload_dir()
    ext = ALLOWED_IMAGE_TYPES[content_type]
    name = f"{uuid.uuid4().hex}{ext}"
    path = UPLOAD_DIR / name
    path.write_bytes(data)
    return name


def delete_image(name: str | None) -> None:
    if not name:
        return
    # tylko sama nazwa pliku - bez path traversal
    safe = Path(name).name
    path = UPLOAD_DIR / safe
    if path.is_file() and path.resolve().parent == UPLOAD_DIR.resolve():
        path.unlink(missing_ok=True)
