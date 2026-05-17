from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, ExpiredSignatureError
from functools import wraps
import redis.asyncio as aioredis
from sqlalchemy import select
from typing import Optional, Annotated
from app.config import get_settings
from app.database import get_db
from app.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from app.logger import logger

_settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

# Single shared Redis connection pool
redis_client = aioredis.from_url(
    _settings.REDIS_URL,
    decode_responses=True,
    max_connections=20,
)


def rate_limit(max_requests: int, window: int):
    """Sliding-window rate limiter per (IP, endpoint)."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            if not request:
                raise HTTPException(status_code=500, detail="No request object")
            client_ip = (
                request.headers.get("X-Forwarded-For", request.client.host).split(",")[0].strip()
            )
            key = f"rl:{func.__name__}:{client_ip}"
            pipe = redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window)
            results = await pipe.execute()
            if results[0] > max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Try again later.",
                    headers={"Retry-After": str(window)},
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


async def get_current_user(
    token: Annotated[Optional[str], Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate JWT access token and return the corresponding User."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exc

    try:
        from app.auth import decode_token
        payload = decode_token(token)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as exc:
        logger.warning("JWT decode error: %s", exc)
        raise credentials_exc

    if payload.get("type") != "access":
        raise credentials_exc

    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise credentials_exc

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user: Optional[User] = result.scalar_one_or_none()
    if user is None:
        raise credentials_exc

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_admin_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def get_refresh_token_user(
    token: Annotated[Optional[str], Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate JWT refresh token, checking Redis blacklist."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exc

    try:
        from app.auth import decode_token
        payload = decode_token(token)
    except (JWTError, ExpiredSignatureError) as exc:
        logger.warning("Refresh token error: %s", exc)
        raise credentials_exc

    if payload.get("type") != "refresh":
        raise credentials_exc

    jti = payload.get("jti")
    if jti and await redis_client.get(f"bl:{jti}"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise credentials_exc

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user: Optional[User] = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise credentials_exc

    return user
