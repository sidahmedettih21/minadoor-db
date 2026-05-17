from fastapi import UploadFile, HTTPException
from app.config import get_settings

settings = get_settings()

ALLOWED_EXTENSIONS = {".xlsx", ".csv"}
XLSX_MAGIC = b"PK"  # ZIP header
MAX_BYTES = settings.MAX_UPLOAD_MB * 1024 * 1024


async def validate_import_file(file: UploadFile) -> None:
    filename = file.filename or ""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only .xlsx and .csv files are accepted")

    # Read header bytes for magic number check
    header = await file.read(4)
    await file.seek(0)

    if ext == ".xlsx" and not header.startswith(XLSX_MAGIC):
        raise HTTPException(status_code=400, detail="File is not a valid XLSX (corrupted or renamed)")

    # Content-Length based size check (fast path)
    if file.size is not None and file.size > MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_MB} MB limit")
