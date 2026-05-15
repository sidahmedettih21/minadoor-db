from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.models import TravelType
from app.schemas import TravelTypeCreate, TravelTypeResponse
from app.dependencies import get_current_active_user, get_admin_user

router = APIRouter(prefix="/api/v1/travel-types", tags=["travel_types"])

@router.get("/", response_model=List[TravelTypeResponse])
async def list_travel_types(db: AsyncSession = Depends(get_db), current_user = Depends(get_current_active_user)):
    result = await db.execute(select(TravelType).where(TravelType.is_active == True))
    return result.scalars().all()

@router.post("/", response_model=TravelTypeResponse, status_code=201)
async def create_travel_type(
    travel_type: TravelTypeCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_admin_user)
):
    db_type = TravelType(**travel_type.dict())
    db.add(db_type)
    await db.commit()
    await db.refresh(db_type)
    return db_type

@router.delete("/{type_id}", status_code=204)
async def delete_travel_type(
    type_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_admin_user)
):
    result = await db.execute(select(TravelType).where(TravelType.id == type_id))
    travel_type = result.scalar_one_or_none()
    if not travel_type:
        raise HTTPException(status_code=404, detail="Travel type not found")
    travel_type.is_active = False
    await db.commit()
    return
