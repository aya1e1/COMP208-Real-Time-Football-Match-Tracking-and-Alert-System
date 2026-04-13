import requests

from db import database
from dummy import mock_responses

import responses

#API_LINK = "https://v3.football.api-sports.io/"
API_KEY = "7f14422097825f6406284820ff8f58cc"
API_LINK = "http://example.com"

mock_responses.register_mocks()
@responses.activate
def get(request):
    headers = {
        "x-apisports-key": API_KEY,
    }
    try:
        response = requests.request("GET", API_LINK + request, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(e)


def process_league(data):
    if not data or "response" not in data:
        print("No league data found.")
        return

    for item in data["response"]:
        save_league_and_seasons(item)

    print("Leagues + seasons saved.")

def save_league_and_seasons(item):
    """
    Saves 1 league + its seasons into the DB.
    Uses INSERT OR IGNORE to avoid duplicates.
    """
    country = item.get("country", {}).get("name")
    league = item.get("league", {})
    seasons = item.get("seasons", [])

    if country != "England":
        return

    league_id = league.get("id")
    league_name = league.get("name")
    if not league_id or not league_name:
        return

    # insert league once
    database.execute(
        "INSERT OR IGNORE INTO League (LeagueID, Name) VALUES (?, ?);",
        (league_id, league_name)
    )

    # innsert seasons for that league
    for season in seasons:
        year = season.get("year")     # eg. 2024
        start = season.get("start")
        end = season.get("end")
        if not year:
            continue

        database.execute(
            """INSERT OR IGNORE INTO Seasons (SeasonYear, LeagueID, StartDate, EndDate)
               VALUES (?, ?, ?, ?);""",
            (year, league_id, start, end)
        )

def init_db():
    try:
        database.init_db()
        print("Database initialised")
    except Exception as e:
        print(e)


if __name__ == "__main__":
    try:
        exists = database.query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='League';"
        )
        if not exists:
            init_db()
            raise Exception("DB not initialised")

    except Exception as e:
        print(e)
        # init_db()


    seasons = database.query("SELECT * FROM Seasons;")
    print("Seasons rows:", seasons)

    league_data = get("/leagues")
    process_league(league_data)

    leagues = database.query("SELECT * FROM League;")
    print("League rows:", leagues)

    # season_rows = database.query("SELECT * FROM Seasons LIMIT 10;")
    # print("Season rows:", season_rows)
