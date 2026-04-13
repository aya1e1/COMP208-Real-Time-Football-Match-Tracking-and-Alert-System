import requests

from db import database
from dummy import mock_responses

from datetime import datetime, UTC

import responses

#API_LINK = "https://v3.football.api-sports.io/"
API_KEY = "7f14422097825f6406284820ff8f58cc"
API_LINK = "http://example.com"

mock_responses.register_mocks()


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

def process_teams(data):
    if not data or "response" not in data:
        print("No team data found.")
        return

    params = data.get("parameters", {})
    league_id = params.get("league")
    season_year = params.get("season")

    if not league_id or not season_year:
        print("Missing league or season in team data.")
        return

    for item in data["response"]:
        save_team_and_season(item, league_id, season_year)

    print("Teams + season links saved.")


def save_team_and_season(item, league_id, season_year):

    team = item.get("team", {})
    venue = item.get("venue", {})

    team_id = team.get("id")
    team_name = team.get("name")
    abbreviation = team.get("code")
    country = team.get("country")
    city = venue.get("city")
    stadium = venue.get("name")

    if country != "England":
        return

    if not team_id or not team_name:
        return

    # insert team once
    database.execute(
        """INSERT OR IGNORE INTO Teams (TeamID, Name, Abbreviation, City, Stadium)
           VALUES (?, ?, ?, ?, ?);""",
        (team_id, team_name, abbreviation, city, stadium)
    )

    # link team to season + league
    database.execute(
        """INSERT OR IGNORE INTO SeasonTeams (TeamID, SeasonYear, LeagueID)
           VALUES (?, ?, ?);""",
        (team_id, season_year, league_id)
    )

def process_fixtures(data):
    if not data or "response" not in data:
        print("No fixture data found.")
        return

    for item in data["response"]:
        save_fixture(item)

    print("Fixtures saved.")


def save_fixture(item):
    fixture = item.get("fixture", {})
    league = item.get("league", {})
    teams = item.get("teams", {})
    goals = item.get("goals", {})

    fixture_id = fixture.get("id")
    league_id = league.get("id")

    home_team = teams.get("home", {}).get("id")
    away_team = teams.get("away", {}).get("id")

    venue = fixture.get("venue", {})
    location = venue.get("name")

    timestamp = fixture.get("periods", {}).get("second")

    if timestamp:
        match_date = datetime.fromtimestamp(timestamp, UTC).strftime("%Y-%m-%d %H:%M:%S")
    else:
        match_date = fixture.get("date")  # fallback

    status = fixture.get("status", {}).get("short")
    completed = status == "FT"

    home_score = goals.get("home") or 0
    away_score = goals.get("away") or 0

    if not fixture_id or not league_id or not home_team or not away_team or not match_date:
        return

    database.execute(
        """INSERT OR IGNORE INTO Fixtures
           (FixtureID, LeagueID, HomeTeam, AwayTeam, Location, MatchDate, Completed, HomeScore, AwayScore)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);""",
        (
            fixture_id,
            league_id,
            home_team,
            away_team,
            location,
            match_date,
            completed,
            home_score,
            away_score
        )
    )

@responses.activate
def main():
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


    league_data = get("/leagues")
    process_league(league_data)

    leagues = database.query("SELECT * FROM League;")

    team_data = get("/teams?league=39&season=2024")
    process_teams(team_data)
    
    fixture_data = get("/fixtures?league=39&season=2024")
    process_fixtures(fixture_data)

if __name__ == "__main__":

    main()
    # season_rows = database.query("SELECT * FROM Seasons LIMIT 10;")
    # print("Season rows:", season_rows)
