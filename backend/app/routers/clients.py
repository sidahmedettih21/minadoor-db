import math
import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Client, TravelType
from app.schemas import ClientCreate, ClientUpdate, ClientResponse, PaginatedClients, ExportRequest, ImportPreview, ImportConfirmRequest
from app.dependencies import get_current_active_user, redis_client
from app.utils.upload_validator import validate_import_file
from app.services import import_service, export_service

import json

router = APIRouter(prefix="/api/v1/clients", tags=["clients"])

SORTABLE_COLS = {"surname", "given_name", "travel_date", "created_at", "status"}


@router.get("/", response_model=PaginatedClients)
async def list_clients(
    search: Optional[str] = Query(None, max_length=100),
    travel_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    travel_date_from: Optional[str] = Query(None),
    travel_date_to: Optional[str] = Query(None),
    sort: Optional[str] = Query("-travel_date"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    base_q = select(Client).where(Client.archived == False).options(
        selectinload(Client.travel_type)
    )

    if search:
        # Fixed: or_() instead of | operator; similarity via pg_trgm
        base_q = base_q.where(
            or_(
                func.similarity(Client.surname, search) > 0.3,
                func.similarity(Client.given_name, search) > 0.3,
                func.similarity(Client.father_name, search) > 0.3,
                Client.passport_number.ilike(f"%{search}%"),
            )
        )

    if travel_type:
        # Fixed: use JOIN instead of non-existent .has()
        base_q = base_q.join(TravelType, Client.travel_type_id == TravelType.id).where(
            TravelType.code == travel_type
        )

    if status:
        base_q = base_q.where(Client.status == status)

    if gender:
        base_q = base_q.where(Client.gender == gender.upper())

    if travel_date_from:
        base_q = base_q.where(Client.travel_date >= travel_date_from)

    if travel_date_to:
        base_q = base_q.where(Client.travel_date <= travel_date_to)

    # Count total for pagination
    count_q = select(func.count()).select_from(base_q.subquery())
    total = (await db.execute(count_q)).scalar_one()

    # Sorting
    col_name = sort.lstrip("-") if sort else "travel_date"
    if col_name not in SORTABLE_COLS:
        col_name = "travel_date"
    col = getattr(Client, col_name)
    order = col.desc() if (sort or "").startswith("-") else col.asc()
    base_q = base_q.order_by(order)

    # Pagination
    base_q = base_q.offset((page - 1) * limit).limit(limit)
    clients = (await db.execute(base_q)).scalars().all()

    return PaginatedClients(
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if total else 0,
        items=clients,
    )


@router.post("/", response_model=ClientResponse, status_code=201)
async def create_client(
    client: ClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    # Check duplicate passport for non-archived clients
    existing = await db.execute(
        select(Client).where(
            Client.passport_number == client.passport_number,
            Client.archived == False,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Client with this passport already exists")

    db_client = Client(**client.model_dump(), created_by=current_user.id)
    db.add(db_client)
    await db.commit()
    await db.refresh(db_client)
    return db_client


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    result = await db.execute(
        select(Client)
        .where(Client.id == client_id, Client.archived == False)
        .options(selectinload(Client.travel_type))
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    client_update: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.archived == False)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    for field, value in client_update.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    await db.commit()
    await db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=204)
async def delete_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.archived == False)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    client.archived = True
    await db.commit()


@router.post("/import/preview", response_model=ImportPreview)
async def import_preview(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    await validate_import_file(file)
    content = await file.read()
    return await import_service.parse_and_validate(content, file.filename)


@router.post("/import/confirm")
async def import_confirm(
    body: ImportConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    return await import_service.commit_import(body.validation_id or "", body.rows)


@router.post("/export")
async def export_request(
    body: ExportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    job_id = str(uuid.uuid4())
    await redis_client.setex(
        f"export:{job_id}",
        3600,
        json.dumps({"status": "pending"}),
    )
    background_tasks.add_task(
        export_service.create_export_job,
        job_id,
        body.model_dump(),
        current_user.id,
    )
    return {"job_id": job_id}
