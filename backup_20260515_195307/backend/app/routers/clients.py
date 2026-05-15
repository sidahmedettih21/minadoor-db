from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, text
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import Client, TravelType
from app.schemas import (
    ClientCreate, ClientUpdate, ClientOut, ClientListResponse,
    ImportPreview, ImportConfirm, ImportResult, ExportRequest, ExportStatus
)
from app.dependencies import get_current_user, redis_client
from app.utils.i18n import api_error
from app.services.import_service import parse_import_file, validate_rows
from app.services.export_service import create_export_job
from typing import List, Optional
from datetime import date
import uuid
import json

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.get("", response_model=ClientListResponse)
async def list_clients(
    request: Request,
    search: Optional[str] = None,
    travel_type: Optional[str] = None,
    status: Optional[str] = None,
    travel_date_from: Optional[date] = None,
    travel_date_to: Optional[date] = None,
    gender: Optional[str] = None,
    sort: str = "-created_at",
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    q = select(Client).where(Client.archived == False).options(selectinload(Client.travel_type))

    if search:
        term = f"%{search}%"
        q = q.where(
            or_(
                Client.surname.ilike(term),
                Client.given_name.ilike(term),
                Client.father_name.ilike(term),
                Client.mother_name.ilike(term),
                Client.passport_number.ilike(term),
            )
        )
    if travel_type:
        q = q.join(TravelType).where(TravelType.code == travel_type)
    if status:
        q = q.where(Client.status == status)
    if gender:
        q = q.where(Client.gender == gender)
    if travel_date_from:
        q = q.where(Client.travel_date >= travel_date_from)
    if travel_date_to:
        q = q.where(Client.travel_date <= travel_date_to)

    count_q = select(func.count()).select_from(q.subquery())
    total_res = await db.execute(count_q)
    total = total_res.scalar()

    sort_col = sort.lstrip("-")
    sort_dir = "desc" if sort.startswith("-") else "asc"
    col = getattr(Client, sort_col, Client.created_at)
    if sort_dir == "desc":
        q = q.order_by(col.desc())
    else:
        q = q.order_by(col.asc())

    q = q.offset((page - 1) * limit).limit(limit)
    result = await db.execute(q)
    items = result.scalars().all()

    return {"items": items, "total": total, "page": page, "limit": limit}

@router.post("", response_model=ClientOut)
async def create_client(data: ClientCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    existing = await db.execute(select(Client).where(
        and_(Client.passport_number == data.passport_number, Client.archived == False)
    ))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=api_error("duplicate_passport", user.preferred_lang))

    client = Client(**data.model_dump(), created_by=user.id)
    db.add(client)
    await db.commit()
    await db.refresh(client)
    result = await db.execute(select(Client).options(selectinload(Client.travel_type)).where(Client.id == client.id))
    return result.scalar_one()

@router.get("/{cid}", response_model=ClientOut)
async def get_client(cid: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(Client).options(selectinload(Client.travel_type)).where(
        and_(Client.id == cid, Client.archived == False)
    ))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail=api_error("not_found", user.preferred_lang))
    return client

@router.patch("/{cid}", response_model=ClientOut)
async def update_client(cid: int, data: ClientUpdate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(Client).options(selectinload(Client.travel_type)).where(
        and_(Client.id == cid, Client.archived == False)
    ))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail=api_error("not_found", user.preferred_lang))

    if data.passport_number and data.passport_number != client.passport_number:
        existing = await db.execute(select(Client).where(
            and_(Client.passport_number == data.passport_number, Client.archived == False)
        ))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=api_error("duplicate_passport", user.preferred_lang))

    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(client, k, v)
    await db.commit()
    await db.refresh(client)
    return client

@router.delete("/{cid}")
async def delete_client(cid: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(Client).where(
        and_(Client.id == cid, Client.archived == False)
    ))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail=api_error("not_found", user.preferred_lang))
    client.archived = True
    await db.commit()
    return {"detail": "Deleted"}

@router.post("/import", response_model=ImportPreview)
async def import_preview(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    content = await file.read()
    filename = file.filename or ""
    try:
        rows, detected_lang = parse_import_file(content, filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {str(e)}")

    valid_rows, errors = await validate_rows(rows, db)
    vid = str(uuid.uuid4())
    redis_client.setex(f"import:{vid}", 1800, json.dumps({
        "rows": valid_rows,
        "errors": [e.model_dump() for e in errors],
        "lang": detected_lang
    }))

    return ImportPreview(
        validation_id=vid,
        total_rows=len(rows),
        valid_rows=len(valid_rows),
        errors=errors,
        preview_data=valid_rows[:10]
    )

@router.post("/import/confirm", response_model=ImportResult)
async def import_confirm(data: ImportConfirm, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    imported = 0
    duplicates = 0
    for row in data.rows:
        existing = await db.execute(select(Client).where(
            and_(Client.passport_number == row.get("passport_number"), Client.archived == False)
        ))
        if existing.scalar_one_or_none():
            duplicates += 1
            continue
        tt_id = row.get("travel_type_id")
        if not tt_id and row.get("travel_type"):
            tt_res = await db.execute(select(TravelType).where(
                or_(TravelType.code == row["travel_type"], TravelType.name_en == row["travel_type"],
                    TravelType.name_fr == row["travel_type"], TravelType.name_ar == row["travel_type"])
            ))
            tt = tt_res.scalar_one_or_none()
            if tt:
                tt_id = tt.id
        if not tt_id:
            duplicates += 1
            continue
        client_data = {k: v for k, v in row.items() if k != "travel_type"}
        client_data["travel_type_id"] = tt_id
        client_data["created_by"] = user.id
        client = Client(**client_data)
        db.add(client)
        imported += 1
    await db.commit()
    return {"imported_count": imported, "duplicates_skipped": duplicates}

@router.post("/export")
async def export_clients(
    data: ExportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    job_id = str(uuid.uuid4())
    redis_client.setex(f"export:{job_id}", 3600, json.dumps({
        "status": "processing",
        "format": data.format,
        "filters": data.model_dump(),
        "user_id": user.id
    }))
    background_tasks.add_task(create_export_job, job_id, data.model_dump(), user.id)
    return {"job_id": job_id, "status": "processing"}
