import responses
import requests
import json
from pathlib import Path

def get_json_from_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

directory = Path(__file__).absolute().parent

def register_mocks():
    mock_team_39 = get_json_from_file(directory / "output_team_39.json")
    mock_leagues = get_json_from_file(directory / "output_leagues.json")

    responses.add(
        method=responses.GET,
        url="http://example.com/leagues",
        json=mock_leagues,
        status=200
    )

    responses.add(
        method=responses.GET,
        url="http://example.com/team?league=39&season=2024",
        json=mock_team_39,
        status=200
    )


@responses.activate
def run_request():
    register_mocks()
    try:
        response = requests.get("http://example.com/team?league=39&season=2024")
        response.raise_for_status()
        data = response.json()
        print("Success! Data received:")
        print(data)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_request()