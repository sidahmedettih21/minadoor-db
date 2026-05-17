import os
import csv
import json
from datetime import datetime
from typing import Dict, Any
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from openpyxl import Workbook
from app.database import AsyncSessionLocal
from app.models import Client, TravelType
from app.dependencies import redis_client
from app.config import get_settings

settings = get_settings()

HEADERS_I18N = {
    "en": ["Surname", "Given Name", "Father Name", "Mother Name", "Passport", "Nationality",
           "Travel Type", "Travel Date", "Status", "Gender", "Payment", "Notes"],
    "fr": ["Nom", "Prénom", "Nom du père", "Nom de la mère", "Passeport", "Nationalité",
           "Type de voyage", "Date de voyage", "Statut", "Genre", "Paiement", "Remarques"],
    "ar": ["اللقب", "الاسم", "اسم الأب", "اسم الأم", "جواز السفر", "الجنسية",
           "نوع السفر", "تاريخ السفر", "الحالة", "الجنس", "الدفع", "ملاحظات"],
}


async def create_export_job(job_id: str, filters: Dict[str, Any], user_id: int):
    try:
        async with AsyncSessionLocal() as db:
            q = select(Client).where(Client.archived == False).options(
                selectinload(Client.travel_type)
            )
            if filters.get("search"):
                term = f"%{filters['search']}%"
                q = q.where(or_(
                    Client.surname.ilike(term),
                    Client.given_name.ilike(term),
                    Client.father_name.ilike(term),
                    Client.passport_number.ilike(term),
                ))
            if filters.get("travel_type"):
                q = q.join(TravelType, Client.travel_type_id == TravelType.id).where(
                    TravelType.code == filters["travel_type"]
                )
            if filters.get("status"):
                q = q.where(Client.status == filters["status"])
            if filters.get("gender"):
                q = q.where(Client.gender == filters["gender"])
            if filters.get("travel_date_from"):
                q = q.where(Client.travel_date >= filters["travel_date_from"])
            if filters.get("travel_date_to"):
                q = q.where(Client.travel_date <= filters["travel_date_to"])

            items = (await db.execute(q)).scalars().all()

        lang = filters.get("header_lang", "en")
        fmt = filters.get("format", "xlsx")
        os.makedirs(settings.TEMP_EXPORT_DIR, exist_ok=True)
        filepath = os.path.join(settings.TEMP_EXPORT_DIR, f"{job_id}.{fmt}")
        headers = HEADERS_I18N.get(lang, HEADERS_I18N["en"])

        def row_data(c):
            tt_attr = f"name_{lang}"
            tt = getattr(c.travel_type, tt_attr, None) or (c.travel_type.name_en if c.travel_type else "")
            return [
                c.surname, c.given_name, c.father_name, c.mother_name or "",
                c.passport_number, c.nationality, tt,
                c.travel_date.isoformat() if c.travel_date else "",
                c.status, c.gender or "", c.payment_method, c.notes or "",
            ]

        if fmt == "csv":
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for c in items:
                    writer.writerow(row_data(c))

        elif fmt == "xlsx":
            wb = Workbook()
            ws = wb.active
            ws.title = "Clients"
            ws.append(headers)
            for c in items:
                ws.append(row_data(c))
            wb.save(filepath)

        elif fmt == "pdf":
            from weasyprint import HTML
            title = {"en": "Client List", "fr": "Liste des clients", "ar": "قائمة العملاء"}.get(lang, "Client List")
            rtl = lang == "ar"
            rows_html = "".join(
                f"<tr>{''.join(f'<td>{v}</td>' for v in row_data(c)[:9])}</tr>"
                for c in items
            )
            html = f"""<!DOCTYPE html>
<html dir="{'rtl' if rtl else 'ltr'}">
<head><meta charset="utf-8">
<style>
body{{font-family:sans-serif;margin:40px}}
h1{{color:#1e40af}}
table{{width:100%;border-collapse:collapse;margin-top:20px}}
th{{background:#1e40af;color:white;padding:8px;text-align:{'right' if rtl else 'left'}}}
td{{border:1px solid #ddd;padding:6px}}
tr:nth-child(even){{background:#f8fafc}}
.footer{{margin-top:20px;font-size:10px;color:#666;text-align:center}}
</style></head>
<body>
<h1>MinaDoor – {title}</h1>
<table>
<tr>{''.join(f'<th>{h}</th>' for h in headers[:9])}</tr>
{rows_html}
</table>
<div class="footer">Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
</body></html>"""
            HTML(string=html).write_pdf(filepath)

        # Fixed: await async Redis call
        await redis_client.setex(
            f"export:{job_id}",
            3600,
            json.dumps({"status": "completed", "filepath": filepath, "format": fmt}),
        )

    except Exception as exc:
        # Fixed: await async Redis call
        await redis_client.setex(
            f"export:{job_id}",
            3600,
            json.dumps({"status": "failed", "error": str(exc)}),
        )
