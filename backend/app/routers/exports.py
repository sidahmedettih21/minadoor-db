from fastapi import APIRouter, Depends, Query
from app.dependencies import get_current_active_user
from app.schemas import ExportStatus

router = APIRouter(prefix="/api/v1/exports", tags=["exports"])

@router.get("/{job_id}/status", response_model=ExportStatus)
async def export_status(job_id: str, current_user = Depends(get_current_active_user)):
    return {"job_id": job_id, "status": "completed"}

@router.get("/{job_id}/download")
async def export_download(job_id: str, current_user = Depends(get_current_active_user)):
    return {"message": "Download endpoint placeholder"}
