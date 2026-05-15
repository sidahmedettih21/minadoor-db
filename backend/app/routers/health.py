from fastapi import APIRouter
from sqlalchemy import text
from app.database import AsyncSessionLocal
from app.dependencies import redis_client
from app.schemas import HealthCheck

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthCheck)
async def health():
    db_status = "ok"
    redis_status = "ok"
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
    try:
        redis_client.ping()
    except Exception:
        redis_status = "error"
    overall = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"
    return {"status": overall, "db": db_status, "redis": redis_status}
