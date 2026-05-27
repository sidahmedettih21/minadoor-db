from typing import Optional
import csv
import io
import openpyxl
from datetime import datetime


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


DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]


def _parse_date(value: str) -> datetime | None:
    raw = value.strip()
    if not raw:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


REQUIRED_FIELDS = {"surname", "given_name", "father_name", "passport_number", "nationality", "travel_type_id", "travel_date"}
DATE_FIELDS = {"travel_date", "date_of_birth", "passport_issue_date", "passport_expiry"}


def normalize_row_dates(row: dict) -> dict:
    for field in DATE_FIELDS:
        val = row.get(field)
        if val and isinstance(val, str) and val.strip():
            parsed = _parse_date(val)
            if parsed is not None:
                row[field] = parsed.strftime("%Y-%m-%d")
    return row

TRAVEL_TYPE_LOOKUP: dict[str, int] = {
    "cash_umrah": 1, "cash_hajj": 2,
    "instalment_umrah": 3, "instalment_hajj": 4,
    "organised_travel": 5,
    "cash umrah": 1, "cash hajj": 2,
    "instalment umrah": 3, "instalment hajj": 4,
    "organised travel": 5,
    "omra au comptant": 1, "hajj au comptant": 2,
    "omra à tempérament": 3, "hajj à tempérament": 4,
    "voyage organisé": 5,
    "عمرة نقدًا": 1, "حج نقدًا": 2,
    "عمرة بالتقسيط": 3, "حج بالتقسيط": 4,
    "سفر منظم": 5,
}


def resolve_travel_type_id(raw: str) -> tuple[int | None, str | None]:
    key = raw.strip().lower()
    id_ = TRAVEL_TYPE_LOOKUP.get(key)
    if id_ is not None:
        return id_, None
    return None, f"Unknown travel type: '{raw}'. Use a valid code or name."


def validate_travel_types(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    good: list[dict] = []
    errors: list[dict] = []
    for idx, row in enumerate(rows):
        raw = row.get("travel_type_id", "")
        if not raw or not isinstance(raw, str) or not raw.strip():
            good.append(row)
            continue
        id_, err = resolve_travel_type_id(raw)
        if err:
            errors.append({"row": row.get("_original_index", idx), "field": "travel_type_id", "message": err})
        else:
            row["travel_type_id"] = id_
            good.append(row)
    return good, errors


def _original_or_idx(row: dict, idx: int) -> int:
    return row.get("_original_index", idx)


def validate_rows(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    valid_rows: list[dict] = []
    errors: list[dict] = []

    for idx, row in enumerate(rows):
        row_errors: list[dict] = []
        orig = _original_or_idx(row, idx)

        for field in REQUIRED_FIELDS:
            val = row.get(field, "")
            if not val or (isinstance(val, str) and not val.strip()):
                row_errors.append({
                    "row": orig,
                    "field": field,
                    "message": f"{field} is required",
                })

        gender = row.get("gender", "")
        if gender and isinstance(gender, str) and gender.strip():
            if gender.strip().upper() not in ("M", "F"):
                row_errors.append({
                    "row": orig,
                    "field": "gender",
                    "message": "Gender must be M or F",
                })

        for field in DATE_FIELDS:
            val = row.get(field, "")
            if val and isinstance(val, str) and val.strip():
                if _parse_date(val) is None:
                    row_errors.append({
                        "row": orig,
                        "field": field,
                        "message": f"Invalid date format for {field}",
                    })

        if row_errors:
            errors.extend(row_errors)
        else:
            valid_rows.append(row)

    return valid_rows, errors


def detect_intra_batch_duplicates(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    seen: set[str] = set()
    unique_rows: list[dict] = []
    errors: list[dict] = []

    for idx, row in enumerate(rows):
        passport = row.get("passport_number", "")
        if not passport or not isinstance(passport, str) or not passport.strip():
            unique_rows.append(row)
            continue

        normalized = passport.strip()
        if normalized in seen:
            errors.append({
                "row": row.get("_original_index", idx),
                "field": "passport_number",
                "message": f"Duplicate passport number: {normalized}",
            })
        else:
            seen.add(normalized)
            unique_rows.append(row)

    return unique_rows, errors
