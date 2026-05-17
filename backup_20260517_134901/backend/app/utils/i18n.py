import json
from pathlib import Path
from fastapi import Request

locales = {}
locales_dir = Path(__file__).parent.parent / "locales"
for lang in ("en", "fr", "ar"):
    with open(locales_dir / f"{lang}.json", encoding="utf-8") as f:
        locales[lang] = json.load(f)

def get_translated_error(request: Request, key: str, **kwargs) -> str:
    lang = request.headers.get("accept-language", "en")[:2]
    if lang not in locales:
        lang = "en"
    template = locales[lang].get(key, key)
    return template.format(**kwargs) if kwargs else template
