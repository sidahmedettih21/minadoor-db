from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from functools import wraps
import redis.asyncio as redis
import os
from sqlalchemy import select
from app.config import get_settings
from app.database import get_db
from app.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

_settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)

def rate_limit(max_requests: int, window: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            if not request:
                raise HTTPException(status_code=500, detail="No request object")
            client_ip = request.client.host
            key = f"ratelimit:{client_ip}:{func.__name__}"
            current = await redis_client.get(key)
            if current and int(current) >= max_requests:
                raise HTTPException(status_code=429, detail="Too many requests")
            pipe = redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window)
            await pipe.execute()
            return await func(*args, **kwargs)
        return wrapper
    return decorator

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    # AUTH DISABLED – returns admin for every request
    from app.models import User as U
    return U(id=1, email="admin@minadoor.com", role="admin", is_active=True)

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user

async def get_admin_user(current_user: User = Depends(get_current_active_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

async def get_refresh_token_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    from app.models import User as U
    return U(id=1, email="admin@minadoor.com", role="admin", is_active=True)
