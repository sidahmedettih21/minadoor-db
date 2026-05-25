from typing import Optional

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
