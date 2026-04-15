import os
import json
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
API_LINK = os.getenv("API_FOOTBALL_BASE_URL", "http://example.com")
DUMMY_DIR = Path(__file__).resolve().parent / "dummy"
SAVE_JSON = False


def save_api_json(path: str, data: dict) -> None:
    endpoint_name = path.strip("/").replace("/", "_") or "root"
    file_path = DUMMY_DIR / f"output_{endpoint_name}.json"

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

    print(f"Saved to {file_path}")


def api_get(path: str) -> dict | None:
    headers = {"x-apisports-key": API_KEY}

    try:
        response = requests.get(f"{API_LINK}{path}", headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        if SAVE_JSON:
            save_api_json(path, data)

        return data
    except requests.RequestException as exc:
        status_code = exc.response.status_code if exc.response is not None else "N/A"
        print(f"API request failed for {path} (status code: {status_code}): {exc}")
        return None
