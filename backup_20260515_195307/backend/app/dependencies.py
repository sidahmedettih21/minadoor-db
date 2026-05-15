from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import get_token_payload
from app.models import User
from sqlalchemy import select
import redis
from app.config import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    payload = get_token_payload(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    # Check blocklist
    jti = payload.get("jti")
    if jti and redis_client.get(f"blocklist:{jti}"):
        raise HTTPException(status_code=401, detail="Token revoked")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user

async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin required")
    return user

def rate_limit(key_prefix: str, max_requests: int, window_seconds: int):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            client_ip = request.client.host if request else "unknown"
            key = f"rate:{key_prefix}:{client_ip}"
            current = redis_client.get(key)
            if current and int(current) >= max_requests:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            pipe = redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            pipe.execute()
            return await func(*args, **kwargs)
        return wrapper
    return decorator
