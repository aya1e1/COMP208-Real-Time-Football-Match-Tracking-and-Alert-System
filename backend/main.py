import os
from datetime import datetime, UTC

import requests
import responses
from dotenv import load_dotenv

from db import database
from dummy import mock_responses

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
API_LINK = "http://example.com"


def api_get(path: str) -> dict | None:
    headers = {"x-apisports-key": API_KEY}

    try:
        response = requests.get(f"{API_LINK}{path}", headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        print(f"API request failed for {path}: {exc}")
        return None


def parse_leagues(data: dict) -> tuple[list[tuple], list[tuple]]:
    leagues = []
    seasons = []

    if not data or "response" not in data:
        return leagues, seasons

    for item in data["response"]:
        country = item.get("country", {}).get("name")
        if country != "England":
            continue

        league = item.get("league", {})
        league_id = league.get("id")
        league_name = league.get("name")

        if not league_id or not league_name:
            continue

        leagues.append((league_id, league_name))

        for season in item.get("seasons", []):
            year = season.get("year")
            start = season.get("start")
            end = season.get("end")

            if year:
                seasons.append((year, league_id, start, end))

    return leagues, seasons


def save_leagues(leagues: list[tuple]) -> None:
    for league_id, league_name in leagues:
        database.execute(
            "INSERT OR IGNORE INTO League (LeagueID, Name) VALUES (?, ?);",
            (league_id, league_name),
        )


def save_seasons(seasons: list[tuple]) -> None:
    for year, league_id, start, end in seasons:
        database.execute(
            """
            INSERT OR IGNORE INTO Seasons (SeasonYear, LeagueID, StartDate, EndDate)
            VALUES (?, ?, ?, ?);
            """,
            (year, league_id, start, end),
        )


def parse_teams(data: dict) -> tuple[list[tuple], list[tuple]]:
    teams = []
    season_links = []

    if not data or "response" not in data:
        return teams, season_links

    params = data.get("parameters", {})
    league_id = params.get("league")
    season_year = params.get("season")

    if not league_id or not season_year:
        return teams, season_links

    for item in data["response"]:
        team = item.get("team", {})
        venue = item.get("venue", {})

        if team.get("country") != "England":
            continue

        team_id = team.get("id")
        team_name = team.get("name")

        if not team_id or not team_name:
            continue

        teams.append(
            (
                team_id,
                team_name,
                team.get("code"),
                venue.get("city"),
                venue.get("name"),
            )
        )
        season_links.append((team_id, season_year, league_id))

    return teams, season_links


def save_teams(teams: list[tuple]) -> None:
    for team_row in teams:
        database.execute(
            """
            INSERT OR IGNORE INTO Teams (TeamID, Name, Abbreviation, City, Stadium)
            VALUES (?, ?, ?, ?, ?);
            """,
            team_row,
        )


def save_season_team_links(links: list[tuple]) -> None:
    for link_row in links:
        database.execute(
            """
            INSERT OR IGNORE INTO SeasonTeams (TeamID, SeasonYear, LeagueID)
            VALUES (?, ?, ?);
            """,
            link_row,
        )


def parse_fixtures(data: dict) -> list[tuple]:
    fixtures = []

    if not data or "response" not in data:
        return fixtures

    for item in data["response"]:
        fixture = item.get("fixture", {})
        league = item.get("league", {})
        teams = item.get("teams", {})
        goals = item.get("goals", {})

        fixture_id = fixture.get("id")
        league_id = league.get("id")
        home_team = teams.get("home", {}).get("id")
        away_team = teams.get("away", {}).get("id")
        location = fixture.get("venue", {}).get("name")

        timestamp = fixture.get("timestamp")
        if timestamp:
            match_date = datetime.fromtimestamp(timestamp, UTC).strftime("%Y-%m-%d %H:%M:%S")
        else:
            match_date = fixture.get("date")

        status = fixture.get("status", {}).get("short")
        completed = 1 if status == "FT" else 0

        home_score = goals.get("home") if goals.get("home") is not None else 0
        away_score = goals.get("away") if goals.get("away") is not None else 0

        if not all([fixture_id, league_id, home_team, away_team, match_date]):
            continue

        fixtures.append(
            (
                fixture_id,
                league_id,
                home_team,
                away_team,
                location,
                match_date,
                completed,
                home_score,
                away_score,
            )
        )

    return fixtures


def save_fixtures(fixtures: list[tuple]) -> None:
    for fixture_row in fixtures:
        database.execute(
            """
            INSERT OR IGNORE INTO Fixtures
            (FixtureID, LeagueID, HomeTeam, AwayTeam, Location, MatchDate, Completed, HomeScore, AwayScore)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            fixture_row,
        )


def sync_leagues() -> None:
    data = api_get("/leagues")
    leagues, seasons = parse_leagues(data)
    save_leagues(leagues)
    save_seasons(seasons)
    print(f"Saved {len(leagues)} leagues and {len(seasons)} seasons.")


def sync_teams(league_id: int, season: int) -> None:
    data = api_get(f"/teams?league={league_id}&season={season}")
    teams, links = parse_teams(data)
    save_teams(teams)
    save_season_team_links(links)
    print(f"Saved {len(teams)} teams and {len(links)} season links.")


def sync_fixtures(league_id: int, season: int) -> None:
    data = api_get(f"/fixtures?league={league_id}&season={season}")
    fixtures = parse_fixtures(data)
    save_fixtures(fixtures)
    print(f"Saved {len(fixtures)} fixtures.")

@responses.activate
def main() -> None:
    
    exists = database.query(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='League';"
    )
    if not exists:
        database.init_db()
        print("Database initialised")

    sync_leagues()
    sync_teams(league_id=39, season=2024)
    sync_fixtures(league_id=39, season=2024)


if __name__ == "__main__":
    mock_responses.register_mocks()
    main()