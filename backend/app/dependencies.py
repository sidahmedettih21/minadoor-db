from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.config import SECRET_KEY, JWT_ALGORITHM
from app.database import get_db
from app.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from functools import wraps
import redis.asyncio as redis
import os
from datetime import datetime

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
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_admin_user(
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

async def get_refresh_token_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Validate refresh token, check blocklist, return user."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        jti = payload.get("jti")
        if not jti:
            raise HTTPException(status_code=401, detail="Missing JTI")
        # Check Redis blocklist
        if await redis_client.exists(f"bl:{jti}"):
            raise HTTPException(status_code=401, detail="Token revoked")
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    return user
