from datetime import datetime, UTC

import responses

from db import database
from dummy import mock_responses
from external_api import api_get


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
            INSERT OR IGNORE INTO Seasons (Year, LeagueID, StartDate, EndDate)
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
            INSERT OR IGNORE INTO SeasonTeams (TeamID, Year, LeagueID)
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
        year = league.get("season")
        home_team = teams.get("home", {}).get("id")
        away_team = teams.get("away", {}).get("id")
        location = fixture.get("venue", {}).get("name")

        timestamp = fixture.get("timestamp")
        if timestamp:
            match_date = datetime.fromtimestamp(timestamp, UTC).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        else:
            match_date = fixture.get("date")

        status = fixture.get("status", {}).get("short")

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
                status,
                home_score,
                away_score,
                year,
            )
        )

    return fixtures


def save_fixtures(fixtures: list[tuple]) -> None:
    for fixture_row in fixtures:
        database.execute(
            """
            INSERT OR IGNORE INTO Fixtures
            (
                FixtureID,
                LeagueID,
                HomeTeamID,
                AwayTeamID,
                Location,
                MatchDate,
                Status,
                HomeScore,
                AwayScore,
                Year
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            fixture_row,
        )


def parse_events(data: dict) -> list[tuple]:
    events = []

    if not data or "response" not in data:
        return events

    fixture_id = data.get("parameters", {}).get("fixture")
    if fixture_id is None:
        return events

    for event_id, item in enumerate(data["response"], start=1):
        player = item.get("player", {})
        assist = item.get("assist", {})
        event_type = item.get("type")

        player_id = player.get("id")
        assist_player_id = assist.get("id")
        if event_type == "subst":
            event_type = "Sub"

        events.append(
            (
                fixture_id,
                event_id,
                player_id,
                assist_player_id,
                item.get("team", {}).get("id"),
                event_type,
                item.get("comments"),
                item.get("time", {}).get("elapsed"),
                item.get("time", {}).get("extra"),
            )
        )

    return events


def save_events(events: list[tuple]) -> None:
    for event_row in events:
        database.execute(
            """
            INSERT OR REPLACE INTO Events
            (
                FixtureID,
                EventID,
                PlayerID,
                AssistPlayerID,
                TeamID,
                EventType,
                Detail,
                EventMinute,
                ExtraMinute
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            event_row,
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


def sync_events(fixture_id: int) -> None:
    data = api_get(f"/fixtures/events?fixture={fixture_id}")
    events = parse_events(data)
    save_events(events)
    print(f"Saved {len(events)} events.")


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
    sync_events(fixture_id=1208399)


if __name__ == "__main__":
    mock_responses.register_mocks()
    main()
