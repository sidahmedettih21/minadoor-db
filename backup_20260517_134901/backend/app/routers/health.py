from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.dependencies import redis_client

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Deep health check: DB + Redis connectivity."""
    db_ok = False
    redis_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass
    try:
        await redis_client.ping()
        redis_ok = True
    except Exception:
        pass

    status = "ok" if (db_ok and redis_ok) else "degraded"
    return {
        "status": status,
        "db": "ok" if db_ok else "error",
        "redis": "ok" if redis_ok else "error",
    }
