import os
import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.config import get_settings

settings = get_settings()

ALLOWED_EXTENSIONS = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument"
    ".wordprocessingml.document": "docx",
}

# Also allow by extension in case content-type is wrong
ALLOWED_SUFFIXES = {".pdf", ".docx"}


def get_upload_dir(tenant_id: str) -> Path:
    """Return (and create) a per-tenant upload directory."""
    path = Path(settings.upload_dir) / str(tenant_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def validate_file(file: UploadFile) -> str:
    """
    Validate content-type and extension.
    Returns the normalised file type string ('pdf' or 'docx').
    Raises HTTPException 400 on failure.
    """
    suffix = Path(file.filename or "").suffix.lower()
    content_type = file.content_type or ""

    file_type = ALLOWED_EXTENSIONS.get(content_type)
    if not file_type:
        # Fall back to extension check
        if suffix not in ALLOWED_SUFFIXES:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported file type '{content_type}'. "
                    "Only PDF and DOCX are accepted."
                ),
            )
        file_type = suffix.lstrip(".")

    return file_type


async def save_upload(
    file: UploadFile,
    tenant_id: str,
) -> tuple[str, str, int]:
    """
    Stream-save the upload to disk.
    Returns (storage_path, safe_filename, file_size_bytes).
    Raises HTTPException 413 if file exceeds MAX_FILE_SIZE_MB.
    """
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    upload_dir = get_upload_dir(tenant_id)

    # Build a collision-safe filename
    ext = Path(file.filename or "file").suffix.lower()
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = upload_dir / safe_name

    total_bytes = 0
    chunk_size = 1024 * 256  # 256 KB chunks

    try:
        async with aiofiles.open(dest_path, "wb") as out:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    await out.close()
                    os.remove(dest_path)
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            f"File exceeds maximum size of "
                            f"{settings.max_file_size_mb} MB."
                        ),
                    )
                await out.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        if dest_path.exists():
            os.remove(dest_path)
        raise HTTPException(
            status_code=500,
            detail=f"File save failed: {str(e)}",
        )

    return str(dest_path), safe_name, total_bytes
