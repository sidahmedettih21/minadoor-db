from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse
from app.dependencies import get_current_active_user, get_admin_user
from app.auth import get_password_hash

router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.get("/", response_model=List[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db), current_user = Depends(get_admin_user)):
    result = await db.execute(select(User).where(User.is_active == True))
    return result.scalars().all()

@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_admin_user)
):
    existing = await db.execute(select(User).where(User.email == user.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = User(
        email=user.email,
        password_hash=get_password_hash(user.password),
        full_name=user.full_name,
        role=user.role
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
