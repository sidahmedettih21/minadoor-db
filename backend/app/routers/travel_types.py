from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import TravelType
from app.schemas import TravelTypeOut, TravelTypeCreate, TravelTypeUpdate
from app.dependencies import get_current_user, get_current_admin
from app.utils.i18n import api_error
from typing import List

router = APIRouter(prefix="/travel-types", tags=["Travel Types"])

def localize(tt: TravelType, lang: str) -> TravelTypeOut:
    name = getattr(tt, f"name_{lang}", tt.name_en) or tt.name_en
    return TravelTypeOut(
        id=tt.id, code=tt.code, name=name,
        name_en=tt.name_en, name_fr=tt.name_fr, name_ar=tt.name_ar,
        is_active=tt.is_active
    )

@router.get("", response_model=List[TravelTypeOut])
async def list_travel_types(lang: str = "en", db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(TravelType).where(TravelType.is_active == True))
    items = result.scalars().all()
    return [localize(i, lang if lang in ("en","fr","ar") else user.preferred_lang) for i in items]

@router.post("", response_model=TravelTypeOut)
async def create_travel_type(data: TravelTypeCreate, db: AsyncSession = Depends(get_db), admin=Depends(get_current_admin)):
    tt = TravelType(**data.model_dump())
    db.add(tt)
    await db.commit()
    await db.refresh(tt)
    return localize(tt, "en")

@router.patch("/{tid}", response_model=TravelTypeOut)
async def update_travel_type(tid: int, data: TravelTypeUpdate, db: AsyncSession = Depends(get_db), admin=Depends(get_current_admin)):
    result = await db.execute(select(TravelType).where(TravelType.id == tid))
    tt = result.scalar_one_or_none()
    if not tt:
        raise HTTPException(status_code=404, detail=api_error("not_found", "en"))
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(tt, k, v)
    await db.commit()
    await db.refresh(tt)
    return localize(tt, "en")

@router.delete("/{tid}")
async def delete_travel_type(tid: int, db: AsyncSession = Depends(get_db), admin=Depends(get_current_admin)):
    result = await db.execute(select(TravelType).where(TravelType.id == tid))
    tt = result.scalar_one_or_none()
    if not tt:
        raise HTTPException(status_code=404, detail=api_error("not_found", "en"))
    tt.is_active = False
    await db.commit()
    return {"detail": "Deactivated"}
