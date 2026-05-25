from typing import Optional
import csv
import io
import openpyxl


HEADER_ALIASES: dict[str, dict[str, str]] = {
    "en": {
        "surname": "surname",
        "given name": "given_name",
        "father name": "father_name",
        "mother name": "mother_name",
        "passport number": "passport_number",
        "passport no": "passport_number",
        "passport #": "passport_number",
        "nationality": "nationality",
        "date of birth": "date_of_birth",
        "dob": "date_of_birth",
        "passport issue": "passport_issue_date",
        "passport issue date": "passport_issue_date",
        "passport expiry": "passport_expiry",
        "passport expiry date": "passport_expiry",
        "gender": "gender",
        "sex": "gender",
        "travel type": "travel_type_id",
        "travel date": "travel_date",
        "payment method": "payment_method",
        "payment": "payment_method",
        "status": "status",
        "notes": "notes",
        "remarks": "notes",
    },
    "fr": {
        "nom": "surname",
        "prénom": "given_name",
        "nom du père": "father_name",
        "nom de la mère": "mother_name",
        "passeport": "passport_number",
        "n° passeport": "passport_number",
        "numéro de passeport": "passport_number",
        "nationalité": "nationality",
        "date de naissance": "date_of_birth",
        "date d'émission": "passport_issue_date",
        "date d'expiration": "passport_expiry",
        "genre": "gender",
        "sexe": "gender",
        "type de voyage": "travel_type_id",
        "date de voyage": "travel_date",
        "mode de paiement": "payment_method",
        "paiement": "payment_method",
        "statut": "status",
        "remarques": "notes",
    },
    "ar": {
        "اللقب": "surname",
        "الاسم": "given_name",
        "اسم الأب": "father_name",
        "اسم الأم": "mother_name",
        "جواز السفر": "passport_number",
        "رقم جواز السفر": "passport_number",
        "الجنسية": "nationality",
        "تاريخ الميلاد": "date_of_birth",
        "تاريخ الإصدار": "passport_issue_date",
        "تاريخ الانتهاء": "passport_expiry",
        "الجنس": "gender",
        "نوع السفر": "travel_type_id",
        "تاريخ السفر": "travel_date",
        "طريقة الدفع": "payment_method",
        "الدفع": "payment_method",
        "الحالة": "status",
        "ملاحظات": "notes",
    },
}


def resolve_field(header: str | None) -> Optional[str]:
    if not header:
        return None

    cleaned = header.strip().lower()

    for lang_map in HEADER_ALIASES.values():
        if cleaned in lang_map:
            return lang_map[cleaned]

    return None


def parse_csv(file_content: bytes) -> list[dict]:
    if not file_content or not file_content.strip():
        return []

    if file_content.startswith(b'\xef\xbb\xbf'):
        decoded = file_content.decode('utf-8-sig')
    else:
        try:
            decoded = file_content.decode('utf-8')
        except UnicodeDecodeError:
            decoded = file_content.decode('latin-1')

    reader = csv.DictReader(io.StringIO(decoded))

    if not reader.fieldnames:
        return []

    resolved = {}
    for h in reader.fieldnames:
        field = resolve_field(h)
        if field:
            resolved[h] = field

    if not resolved:
        raise ValueError("No headers could be resolved from the CSV file")

    result = []
    for row in reader:
        if all(v is None or (isinstance(v, str) and v.strip() == '') for v in row.values()):
            continue
        mapped = {}
        for orig_header, field_name in resolved.items():
            val = row.get(orig_header)
            if val and isinstance(val, str) and val.strip():
                mapped[field_name] = val.strip()
        if mapped:
            result.append(mapped)

    return result


def parse_xlsx(file_content: bytes) -> list[dict]:
    wb = openpyxl.load_workbook(io.BytesIO(file_content), read_only=True, data_only=True)
    ws = wb.active

    if ws is None:
        wb.close()
        return []

    rows_iter = ws.iter_rows(values_only=True)

    try:
        first_row = next(rows_iter)
    except StopIteration:
        wb.close()
        return []

    headers = list(first_row)

    resolved = {}
    for h in headers:
        if h is None:
            continue
        field = resolve_field(str(h))
        if field:
            resolved[str(h)] = field

    if not resolved:
        wb.close()
        raise ValueError("No headers could be resolved from the XLSX file")

    result = []
    for row in rows_iter:
        if all(cell is None for cell in row):
            continue
        mapped = {}
        for i, cell in enumerate(row):
            if i >= len(headers):
                break
            h = headers[i]
            if h is None or str(h) not in resolved:
                continue
            if cell is not None:
                val = str(cell).strip()
                if val:
                    mapped[resolved[str(h)]] = val
        if mapped:
            result.append(mapped)

    wb.close()
    return result
