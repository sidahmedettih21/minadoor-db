from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, RefreshRequest, Token, UserOut
from app.auth import verify_password, create_access_token, create_refresh_token, get_token_payload
from app.dependencies import get_current_user, redis_client
from app.utils.i18n import api_error

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=Token)
async def login(req: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    # Rate limit check via Redis
    ip = request.client.host
    key = f"rate:login:{ip}"
    current = redis_client.get(key)
    if current and int(current) >= 5:
        raise HTTPException(status_code=429, detail="Too many login attempts")
    redis_client.incr(key)
    redis_client.expire(key, 60)

    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail=api_error("auth_failed", "en"))
    if not user.is_active:
        raise HTTPException(status_code=401, detail=api_error("auth_failed", "en"))

    data = {"sub": str(user.id), "role": user.role, "lang": user.preferred_lang}
    access = create_access_token(data)
    refresh = create_refresh_token(data)
    return {"access_token": access, "refresh_token": refresh, "expires_in": 15 * 60}

@router.post("/refresh", response_model=Token)
async def refresh(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = get_token_payload(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    jti = payload.get("jti")
    if jti and redis_client.get(f"blocklist:{jti}"):
        raise HTTPException(status_code=401, detail="Token revoked")
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    # Block old refresh token
    if jti:
        redis_client.setex(f"blocklist:{jti}", 7 * 86400, "1")
    data = {"sub": str(user.id), "role": user.role, "lang": user.preferred_lang}
    access = create_access_token(data)
    refresh = create_refresh_token(data)
    return {"access_token": access, "refresh_token": refresh, "expires_in": 15 * 60}

@router.post("/logout")
async def logout(req: RefreshRequest):
    payload = get_token_payload(req.refresh_token)
    if payload:
        jti = payload.get("jti")
        if jti:
            redis_client.setex(f"blocklist:{jti}", 7 * 86400, "1")
    return {"detail": "Logged out"}

@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user
