from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Client
from app.schemas import ClientCreate
from typing import List
import uuid


async def parse_and_validate(file_content: bytes, filename: str) -> dict:
    # placeholder – actual import logic here
    # Returns validation_id, rows, errors
    return {
        "validation_id": str(uuid.uuid4()),
        "total_rows": 0,
        "valid_rows": 0,
        "errors": [],
        "preview_data": [],
    }


async def commit_import(validation_id: str, rows: List[ClientCreate]) -> dict:
    async with AsyncSessionLocal() as session:
        existing_passports = set(
            (await session.execute(
                select(Client.passport_number).where(Client.passport_number.in_([r.passport_number for r in rows]))
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
