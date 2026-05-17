import json
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.dependencies import get_current_active_user, redis_client
from app.schemas import ExportStatus

router = APIRouter(prefix="/api/v1/exports", tags=["exports"])


@router.get("/{job_id}/status", response_model=ExportStatus)
async def export_status(
    job_id: str,
    current_user=Depends(get_current_active_user),
):
    # Actually read from Redis (was always returning "completed" before)
    raw = await redis_client.get(f"export:{job_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="Export job not found")
    data = json.loads(raw)
    return ExportStatus(
        job_id=job_id,
        status=data.get("status", "unknown"),
        error=data.get("error"),
        download_url=f"/api/v1/exports/{job_id}/download" if data.get("status") == "completed" else None,
    )


@router.get("/{job_id}/download")
async def export_download(
    job_id: str,
    current_user=Depends(get_current_active_user),
):
    raw = await redis_client.get(f"export:{job_id}")
    if not raw:
        raise HTTPException(status_code=404, detail="Export job not found")
    data = json.loads(raw)
    if data.get("status") != "completed":
        raise HTTPException(status_code=425, detail=f"Export not ready: {data.get('status')}")
    filepath = data.get("filepath", "")
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Export file not found on disk")
    fmt = data.get("format", "xlsx")
    media_types = {
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "csv": "text/csv",
        "pdf": "application/pdf",
    }
    return FileResponse(
        path=filepath,
        media_type=media_types.get(fmt, "application/octet-stream"),
        filename=f"clients_export.{fmt}",
    )
