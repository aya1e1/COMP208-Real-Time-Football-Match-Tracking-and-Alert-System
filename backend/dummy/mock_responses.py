import json
from pathlib import Path
from urllib.parse import urlencode

import requests
import responses


BASE_URL = "http://example.com"
DIRECTORY = Path(__file__).absolute().parent


def get_json_from_file(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def parse_mock_filename(file_path: Path):
    """
    Convert filenames like:
      output_leagues.json
      output_teams_league-39_season-2024.json
      output_fixtures_events_fixture-1208399.json

    into:
      endpoint = "leagues", params = {}
      endpoint = "teams", params = {"league": "39", "season": "2024"}
      endpoint = "fixtures/events", params = {"fixture": "1208399"}
    """
    stem = file_path.stem  # e.g. "output_team_league-39_season-2024"

    if not stem.startswith("output_"):
        return None

    remainder = stem[len("output_"):]  # e.g. "team_league-39_season-2024"

    if not remainder:
        return None

    parts = remainder.split("_")

    endpoint_parts = []
    param_parts = []
    found_params = False

    for part in parts:
        if not found_params and "-" not in part:
            endpoint_parts.append(part)
            continue

        found_params = True
        param_parts.append(part)

    if not endpoint_parts:
        return None

    endpoint = "/".join(endpoint_parts)

    params = {}
    for part in param_parts:
        if "-" not in part:
            continue
        key, value = part.split("-", 1)
        params[key] = value

    return endpoint, params


def build_url(endpoint: str, params: dict):
    url = f"{BASE_URL}/{endpoint}"
    if params:
        url = f"{url}?{urlencode(params)}"
    return url


def register_mocks():
    for file_path in DIRECTORY.glob("output_*.json"):
        parsed = parse_mock_filename(file_path)
        if parsed is None:
            continue

        endpoint, params = parsed
        url = build_url(endpoint, params)
        mock_data = get_json_from_file(file_path)

        responses.add(
            method=responses.GET,
            url=url,
            json=mock_data,
            status=200,
        )

        print(f"Registered mock: {url} -> {file_path.name}")


@responses.activate
def run_request():
    register_mocks()

    test_urls = [
        "http://example.com/leagues",
        "http://example.com/teams?league=39&season=2024",
    ]

    for url in test_urls:
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            print(f"\nSuccess: {url}")
            print(data)
        except Exception as e:
            print(f"\nError for {url}: {e}")


if __name__ == "__main__":
    run_request()
