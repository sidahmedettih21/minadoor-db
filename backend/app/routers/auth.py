from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User
from app.schemas import Token, UserResponse
from app.auth import create_tokens, rotate_refresh_token, verify_password
from app.dependencies import get_refresh_token_user, rate_limit, oauth2_scheme, get_current_active_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/login", response_model=Token)
@rate_limit(max_requests=5, window=60)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    access, refresh = create_tokens(user.id)
    return {"access_token": access, "refresh_token": refresh}

@router.post("/refresh", response_model=Token)
@rate_limit(max_requests=10, window=60)
async def refresh_token(
    request: Request,
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_refresh_token_user)
):
    access, new_refresh = await rotate_refresh_token(token, current_user.id)
    return {"access_token": access, "refresh_token": new_refresh}

@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_refresh_token_user)
):
    await rotate_refresh_token(token, current_user.id)
    return {"detail": "Logged out"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user
