from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import TravelType
from app.dependencies import get_current_user
from fastapi.responses import StreamingResponse
import io
from openpyxl import Workbook
from openpyxl.worksheet.datavalidation import DataValidation

router = APIRouter(prefix="/templates", tags=["Templates"])

HEADERS = {
    "en": ["Surname", "Given Name", "Father Name", "Mother Name", "Passport Number", "Nationality",
           "Date of Birth", "Passport Issue Date", "Passport Expiry", "Gender", "Travel Type",
           "Payment Method", "Travel Date", "Notes"],
    "fr": ["Nom", "Prénom", "Nom du père", "Nom de la mère", "N° Passeport", "Nationalité",
           "Date de naissance", "Date d'émission", "Date d'expiration", "Genre", "Type de voyage",
           "Mode de paiement", "Date de voyage", "Remarques"],
    "ar": ["اللقب", "الاسم", "اسم الأب", "اسم الأم", "رقم جواز السفر", "الجنسية",
           "تاريخ الميلاد", "تاريخ الإصدار", "تاريخ الانتهاء", "الجنس", "نوع السفر",
           "طريقة الدفع", "تاريخ السفر", "ملاحظات"]
}

@router.get("/{lang}")
async def download_template(lang: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    if lang not in HEADERS:
        raise HTTPException(status_code=400, detail="Invalid language")

    result = await db.execute(select(TravelType).where(TravelType.is_active == True))
    types = result.scalars().all()
    type_names = [t.name_fr if lang == "fr" else (t.name_ar if lang == "ar" else t.name_en) for t in types]

    wb = Workbook()
    ws = wb.active
    ws.title = "Clients"
    ws.append(HEADERS[lang])

    # Data validation for travel type column (index 10)
    if type_names:
        dv = DataValidation(type="list", formula1='"' + ",".join(type_names) + '"', allow_blank=True)
        dv.error = "Invalid travel type"
        dv.errorTitle = "Error"
        ws.add_data_validation(dv)
        dv.add(f"K2:K1000")

    # Data validation for gender
    genders = "M,F" if lang == "en" else ("M,F" if lang == "fr" else "ذكر,أنثى")
    dv_g = DataValidation(type="list", formula1='"' + genders + '"', allow_blank=True)
    ws.add_data_validation(dv_g)
    dv_g.add(f"J2:J1000")

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    fname = f"minadoor_template_{lang}.xlsx"
    return StreamingResponse(stream, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f"attachment; filename={fname}"})
