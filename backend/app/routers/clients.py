from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from app.database import get_db
from app.models import Client, TravelType
from app.schemas import ClientCreate, ClientUpdate, ClientResponse
from app.dependencies import get_current_active_user
from app.utils.upload_validator import validate_import_file
import uuid

router = APIRouter(prefix="/api/v1/clients", tags=["clients"])

@router.get("/", response_model=List[ClientResponse])
async def list_clients(
    search: Optional[str] = Query(None),
    travel_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    travel_date_from: Optional[str] = Query(None),
    travel_date_to: Optional[str] = Query(None),
    sort: Optional[str] = Query("-travel_date"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    query = select(Client).where(Client.archived == False)
    if search:
        query = query.where(
            func.similarity(Client.surname, search) > 0.3 |
            func.similarity(Client.given_name, search) > 0.3 |
            func.similarity(Client.father_name, search) > 0.3 |
            Client.passport_number.ilike(f'%{search}%')
        )
    if travel_type:
        query = query.where(Client.travel_type.has(code=travel_type))
    if status:
        query = query.where(Client.status == status)
    if gender:
        query = query.where(Client.gender == gender.upper())
    if travel_date_from:
        query = query.where(Client.travel_date >= travel_date_from)
    if travel_date_to:
        query = query.where(Client.travel_date <= travel_date_to)
    # Sorting
    if sort:
        col = sort.lstrip('-')
        if col in ('surname', 'given_name', 'travel_date', 'created_at'):
            order = col if sort.startswith('-') else col
            query = query.order_by(getattr(Client, col).desc() if sort.startswith('-') else getattr(Client, col))
    # Pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    clients = result.scalars().all()
    return clients

@router.post("/", response_model=ClientResponse, status_code=201)
async def create_client(
    client: ClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    db_client = Client(**client.dict(), created_by=current_user.id)
    db.add(db_client)
    await db.commit()
    await db.refresh(db_client)
    return db_client

@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    result = await db.execute(select(Client).where(Client.id == client_id, Client.archived == False))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    client_update: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    result = await db.execute(select(Client).where(Client.id == client_id, Client.archived == False))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    for field, value in client_update.dict(exclude_unset=True).items():
        setattr(client, field, value)
    await db.commit()
    await db.refresh(client)
    return client

@router.delete("/{client_id}", status_code=204)
async def delete_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    result = await db.execute(select(Client).where(Client.id == client_id, Client.archived == False))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    client.archived = True
    await db.commit()
    return

@router.post("/import")
async def import_preview(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    await validate_import_file(file)
    # Placeholder – return fake preview for now
    return {
        "validation_id": str(uuid.uuid4()),
        "total_rows": 0,
        "valid_rows": 0,
        "errors": []
    }

@router.post("/import/confirm")
async def import_confirm(
    validation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    return {"imported": 0, "skipped": 0}

@router.post("/export")
async def export_request(
    format: str = "xlsx",
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    return {"job_id": str(uuid.uuid4())}
