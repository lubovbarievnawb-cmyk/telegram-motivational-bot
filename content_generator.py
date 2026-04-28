import json
from typing import Final

import requests


FORISMATIC_URL: Final[str] = "http://api.forismatic.com/api/1.0/"
REQUEST_TIMEOUT: Final[int] = 15
FALLBACK_TEXT: Final[str] = (
    "Действуй сегодня, даже если идеальный момент еще не наступил."
)
FALLBACK_AUTHOR: Final[str] = "Неизвестный автор"


def generate_motivational_post() -> str:
    params = {
        "method": "getQuote",
        "format": "json",
        "lang": "ru",
    }

    try:
        response = requests.get(FORISMATIC_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        try:
            data = response.json()
        except json.JSONDecodeError:
            data = json.loads(response.text.replace("\\'", "'"))

        quote = (data.get("quoteText") or "").strip()
        author = (data.get("quoteAuthor") or "").strip() or FALLBACK_AUTHOR

        if not quote:
            raise ValueError("Empty quote received from API")

        return f"{quote}\n\n— {author}"
    except (requests.RequestException, ValueError, json.JSONDecodeError):
        return f"{FALLBACK_TEXT}\n\n— {FALLBACK_AUTHOR}"
