from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_user, redis_client
from app.schemas import ExportStatus
import os
import json
from app.config import get_settings
from fastapi.responses import FileResponse

settings = get_settings()
router = APIRouter(prefix="/exports", tags=["Exports"])

@router.get("/{job_id}/status", response_model=ExportStatus)
async def export_status(job_id: str, user=Depends(get_current_user)):
    raw = redis_client.get(f"export:{job_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="Export job not found")
    data = json.loads(raw)
    url = None
    if data.get("status") == "completed":
        url = f"/api/v1/exports/{job_id}/download"
    return {"job_id": job_id, "status": data["status"], "download_url": url}

@router.get("/{job_id}/download")
async def export_download(job_id: str, user=Depends(get_current_user)):
    raw = redis_client.get(f"export:{job_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="Export job not found")
    data = json.loads(raw)
    if data.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Export not ready")
    filepath = data.get("filepath")
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File expired")
    ext = os.path.splitext(filepath)[1]
    media = {
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".csv": "text/csv",
        ".pdf": "application/pdf"
    }
    return FileResponse(filepath, media_type=media.get(ext, "application/octet-stream"),
                        filename=f"minadoor_export_{job_id}{ext}")
