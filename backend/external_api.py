import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
API_LINK = os.getenv("API_FOOTBALL_BASE_URL", "http://example.com")


def api_get(path: str) -> dict | None:
    headers = {"x-apisports-key": API_KEY}

    try:
        response = requests.get(f"{API_LINK}{path}", headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        status_code = exc.response.status_code if exc.response is not None else "N/A"
        print(f"API request failed for {path} (status code: {status_code}): {exc}")
        return None
