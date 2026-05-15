from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User
from app.schemas import UserOut, UserCreate, UserUpdate
from app.dependencies import get_current_admin
from app.auth import hash_password
from app.utils.i18n import api_error
from typing import List

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("", response_model=List[UserOut])
async def list_users(db: AsyncSession = Depends(get_db), admin=Depends(get_current_admin)):
    result = await db.execute(select(User).where(User.is_active == True))
    return result.scalars().all()

@router.post("", response_model=UserOut)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db), admin=Depends(get_current_admin)):
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
        preferred_lang=data.preferred_lang
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.patch("/{uid}", response_model=UserOut)
async def update_user(uid: int, data: UserUpdate, db: AsyncSession = Depends(get_db), admin=Depends(get_current_admin)):
    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail=api_error("not_found", "en"))
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    await db.commit()
    await db.refresh(user)
    return user

@router.delete("/{uid}")
async def delete_user(uid: int, db: AsyncSession = Depends(get_db), admin=Depends(get_current_admin)):
    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail=api_error("not_found", "en"))
    user.is_active = False
    await db.commit()
    return {"detail": "Deactivated"}
