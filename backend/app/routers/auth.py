from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User
from app.schemas import Token
from app.auth import create_tokens, rotate_refresh_token, verify_password
from app.dependencies import get_refresh_token_user, rate_limit

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/login", response_model=Token)
@rate_limit(max_requests=5, window=60)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, form_data.username)  # username = email
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
    current_user: User = Depends(get_refresh_token_user),
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login"))  # we need the raw token
):
    # get_refresh_token_user already validated token & blocklist
    # token is passed via dependency, but we need the raw string; use Depends as above
    access, new_refresh = await rotate_refresh_token(token, current_user.id)
    return {"access_token": access, "refresh_token": new_refresh}

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_refresh_token_user),
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login"))
):
    # We'll invalidate refresh token by adding to blocklist
    await rotate_refresh_token(token, current_user.id)  # just call rotation to blacklist
    return {"detail": "Logged out"}
