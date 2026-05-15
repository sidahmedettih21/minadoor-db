from fastapi import APIRouter, Query
from fastapi.responses import FileResponse
import os

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])

@router.get("/{lang}")
async def download_template(lang: str = "en"):
    return {"message": f"Template for {lang}"}
