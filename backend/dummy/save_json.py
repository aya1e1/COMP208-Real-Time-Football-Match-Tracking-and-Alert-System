import requests
import json
import os
from dotenv import load_dotenv


load_dotenv()

# Base configuration
BASE_URL = "https://v3.football.api-sports.io"
ENDPOINT = "/leagues"  

# Build full URL
url = f"{BASE_URL}{ENDPOINT}"

params = {


}

# Get API key from .env
API_KEY = os.getenv("API_FOOTBALL_KEY")

headers = {
    "x-apisports-key": API_KEY,
}

try:
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    data = response.json()

    # Build filename (include endpoint name)
    endpoint_name = ENDPOINT.strip("/").replace("/", "_")
    param_str = "_".join(f"{k}-{v}" for k, v in params.items())

    if param_str:
        filename = f"output_{endpoint_name}_{param_str}.json"
    else:
        filename = f"output_{endpoint_name}.json"

    # Save in same directory as script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"Saved to {file_path}")

except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
