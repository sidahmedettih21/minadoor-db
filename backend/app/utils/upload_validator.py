from fastapi import UploadFile, HTTPException

ALLOWED_CONTENT_TYPES = [
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv"
]

async def validate_import_file(file: UploadFile):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Use .xlsx or .csv")
    # Check magic bytes
    header = await file.read(4)
    await file.seek(0)
    if file.filename.endswith('.xlsx') and header[:2] != b'PK':
        raise HTTPException(status_code=400, detail="Corrupted file")
    # Max size 10MB
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")
