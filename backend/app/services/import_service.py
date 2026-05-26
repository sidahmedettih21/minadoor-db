from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.dependencies import redis_client
from app.logger import logger
from app.models import Client
from app.schemas import ClientCreate
from app.services.import_parser import parse_csv, parse_xlsx, validate_rows, detect_intra_batch_duplicates
from typing import List
import json
import uuid


async def parse_and_validate(file_content: bytes, filename: str) -> dict:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext == "csv":
        parsed = parse_csv(file_content)
    elif ext in ("xlsx", "xls"):
        parsed = parse_xlsx(file_content)
    else:
        raise ValueError(f"Unsupported file type: .{ext}")

    total_rows = len(parsed)
    validated, val_errors = validate_rows(parsed)
    deduped, dup_errors = detect_intra_batch_duplicates(validated)

    cross_batch_errors = []
    if deduped:
        try:
            async with AsyncSessionLocal() as session:
                existing = await session.execute(
                    select(Client.passport_number).where(
                        Client.passport_number.in_([r["passport_number"] for r in deduped])
                    )
                )
                existing_passports = set(existing.scalars().all())
                filtered = []
                for row in deduped:
                    pn = row.get("passport_number", "")
                    if pn in existing_passports:
                        cross_batch_errors.append({
                            "row": 0,
                            "field": "passport_number",
                            "message": f"Passport already exists in database: {pn}",
                        })
                    else:
                        filtered.append(row)
                deduped = filtered
        except Exception:
            logger.warning("DB unavailable, skipping cross-batch duplicate check")

    all_errors = val_errors + dup_errors + cross_batch_errors

    validation_id = str(uuid.uuid4())
    try:
        await redis_client.setex(
            f"import:{validation_id}",
            1800,
            json.dumps({"rows": deduped}),
        )
    except Exception:
        logger.warning("Redis unavailable, skipping cache for import preview")

    return {
        "validation_id": validation_id,
        "total_rows": total_rows,
        "valid_rows": len(deduped),
        "errors": all_errors,
        "preview_data": deduped[:50],
    }


async def commit_import(validation_id: str, rows: List[ClientCreate]) -> dict:
    if validation_id:
        try:
            cached = await redis_client.get(f"import:{validation_id}")
            if cached:
                rows = [ClientCreate(**r) for r in json.loads(cached)["rows"]]
        except Exception:
            logger.warning("Failed to load rows from Redis cache")

    async with AsyncSessionLocal() as session:
        try:
            existing_passports = set(
                (await session.execute(
                    select(Client.passport_number).where(
                        Client.passport_number.in_([r.passport_number for r in rows])
                    )
                )).scalars().all()
            )
            new_clients = []
            skipped = 0
            for row in rows:
                if row.passport_number in existing_passports:
                    skipped += 1
                    continue
                client = Client(**row.model_dump())
                session.add(client)
                new_clients.append(client)
            await session.commit()
            return {"imported_count": len(new_clients), "duplicates_skipped": skipped}
        except Exception:
            await session.rollback()
            raise
