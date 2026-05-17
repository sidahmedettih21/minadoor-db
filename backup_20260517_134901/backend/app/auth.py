from datetime import datetime, timedelta, timezone
from jose import jwt
import uuid
from passlib.context import CryptContext
from app.config import get_settings

_settings = get_settings()

# Module-level singleton – bcrypt work factor loaded once, not per-call
_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return _pwd_ctx.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_tokens(user_id: int) -> tuple[str, str]:
    now = _now()
    access_payload = {
        "sub": str(user_id),
        "exp": now + timedelta(minutes=_settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",
        "iat": now,
    }
    jti = str(uuid.uuid4())
    refresh_payload = {
        "sub": str(user_id),
        "exp": now + timedelta(days=_settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "type": "refresh",
        "jti": jti,
        "iat": now,
    }
    access_token = jwt.encode(access_payload, _settings.SECRET_KEY, algorithm=_settings.JWT_ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, _settings.SECRET_KEY, algorithm=_settings.JWT_ALGORITHM)
    return access_token, refresh_token


def decode_token(token: str) -> dict:
    return jwt.decode(token, _settings.SECRET_KEY, algorithms=[_settings.JWT_ALGORITHM])


async def rotate_refresh_token(
    old_refresh_token: str,
    user_id: int,
    redis_client,
) -> tuple[str, str]:
    payload = decode_token(old_refresh_token)
    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti and exp:
        ttl = max(0, int(exp - _now().timestamp()))
        if ttl > 0:
            await redis_client.setex(f"bl:{jti}", ttl, "revoked")
    return create_tokens(user_id)
