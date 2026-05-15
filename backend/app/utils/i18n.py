import json
import os

LOCALES = {}

locales_dir = os.path.join(os.path.dirname(__file__), "../../frontend/locales")
if os.path.exists(locales_dir):
    for fname in os.listdir(locales_dir):
        if fname.endswith(".json"):
            lang = fname.replace(".json", "")
            with open(os.path.join(locales_dir, fname), "r", encoding="utf-8") as f:
                LOCALES[lang] = json.load(f)

def get_message(key: str, lang: str = "en", default: str = None) -> str:
    lang = lang if lang in LOCALES else "en"
    return LOCALES.get(lang, {}).get(key, default or key)

API_ERRORS = {
    "en": {
        "auth_failed": "Authentication failed",
        "not_found": "Resource not found",
        "duplicate_passport": "Passport number already exists",
        "invalid_travel_type": "Invalid travel type",
        "import_failed": "Import processing failed",
        "export_failed": "Export generation failed",
        "unauthorized": "Unauthorized",
        "forbidden": "Forbidden",
        "validation_error": "Validation error",
    },
    "fr": {
        "auth_failed": "Échec de l'authentification",
        "not_found": "Ressource non trouvée",
        "duplicate_passport": "Numéro de passeport existe déjà",
        "invalid_travel_type": "Type de voyage invalide",
        "import_failed": "Échec du traitement de l'import",
        "export_failed": "Échec de la génération de l'export",
        "unauthorized": "Non autorisé",
        "forbidden": "Interdit",
        "validation_error": "Erreur de validation",
    },
    "ar": {
        "auth_failed": "فشل المصادقة",
        "not_found": "المورد غير موجود",
        "duplicate_passport": "رقم جواز السفر موجود مسبقاً",
        "invalid_travel_type": "نوع السفر غير صالح",
        "import_failed": "فشل معالجة الاستيراد",
        "export_failed": "فشل إنشاء التصدير",
        "unauthorized": "غير مصرح",
        "forbidden": "ممنوع",
        "validation_error": "خطأ في التحقق",
    }
}

def api_error(key: str, lang: str = "en") -> str:
    lang = lang if lang in API_ERRORS else "en"
    return API_ERRORS.get(lang, API_ERRORS["en"]).get(key, key)
