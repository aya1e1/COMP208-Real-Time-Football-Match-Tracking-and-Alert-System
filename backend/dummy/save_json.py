import requests
import json
import os

url = "https://v3.football.api-sports.io/leagues"

params = {
    "country": "England",
    "season": 2023
}

headers = {
    "x-apisports-key": "7f14422097825f6406284820ff8f58cc",
}

try:
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    data = response.json()

    # Build filename
    param_str = "_".join(f"{k}-{v}" for k, v in params.items())
    filename = f"output_{param_str}.json"

    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Full path
    file_path = os.path.join(script_dir, filename)

    # Save JSON
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"Saved to {file_path}")

except requests.exceptions.RequestException as e:
    print(f"Error: {e}")