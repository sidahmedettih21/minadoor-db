from datetime import datetime, timedelta
from jose import jwt
import uuid
from app.config import SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from app.dependencies import redis_client

def create_tokens(user_id: int) -> tuple:
    now = datetime.utcnow()
    access_exp = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_exp = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    jti = str(uuid.uuid4())
    access_payload = {
        "sub": user_id,
        "exp": access_exp,
        "type": "access"
    }
    refresh_payload = {
        "sub": user_id,
        "exp": refresh_exp,
        "type": "refresh",
        "jti": jti
    }
    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return access_token, refresh_token

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])

async def rotate_refresh_token(old_refresh_token: str, user_id: int) -> str:
    """Invalidate old refresh token and return new access + refresh"""
    payload = decode_token(old_refresh_token)
    jti = payload.get("jti")
    exp = payload.get("exp")
    # Add old token to blocklist until its original expiry
    ttl = max(0, int(exp - datetime.utcnow().timestamp()))
    if ttl > 0:
        await redis_client.setex(f"bl:{jti}", ttl, "revoked")
    # Create new pair
    access_token, new_refresh_token = create_tokens(user_id)
    return access_token, new_refresh_token

def get_password_hash(password: str) -> str:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(plain_password, hashed_password)
