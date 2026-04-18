from datetime import datetime, UTC
import os

from dotenv import load_dotenv

try:
    from backend.db import database
    from backend.external_api import api_get
except ImportError:
    from db import database
    from external_api import api_get

load_dotenv()
USE_MOCKS = os.getenv("USE_MOCKS", "").strip().lower() == "true"


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
        league_logo = league.get("logo")

        if not league_id or not league_name:
            continue

        leagues.append((league_id, league_name, country, league_logo))

        for season in item.get("seasons", []):
            year = season.get("year")
            start = season.get("start")
            end = season.get("end")
            current = 1 if season.get("current") else 0

            if year:
                seasons.append((year, league_id, start, end, current))

    return leagues, seasons


def save_leagues(leagues: list[tuple]) -> None:
    for league_id, league_name, country, logo_url in leagues:
        database.execute(
            """
            INSERT INTO League (LeagueID, Name, Country, LogoURL)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(LeagueID) DO UPDATE SET
                Name = excluded.Name,
                Country = excluded.Country,
                LogoURL = excluded.LogoURL;
            """,
            (league_id, league_name, country, logo_url),
        )


def save_seasons(seasons: list[tuple]) -> None:
    for year, league_id, start, end, current in seasons:
        database.execute(
            """
            INSERT INTO Seasons (Year, LeagueID, StartDate, EndDate, Current)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(LeagueID, Year) DO UPDATE SET
                StartDate = excluded.StartDate,
                EndDate = excluded.EndDate,
                Current = excluded.Current;
            """,
            (year, league_id, start, end, current),
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



        team_id = team.get("id")
        team_name = team.get("name")

        if not team_id or not team_name:
            continue

        teams.append(
            (
                team_id,
                team_name,
                team.get("code"),
                team.get("logo"),
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
            INSERT INTO Teams (TeamID, Name, Abbreviation, LogoURL, City, Stadium)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(TeamID) DO UPDATE SET
                Name = excluded.Name,
                Abbreviation = excluded.Abbreviation,
                LogoURL = excluded.LogoURL,
                City = excluded.City,
                Stadium = excluded.Stadium;
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


def parse_standings(data: dict) -> list[tuple]:
    standings = []

    if not data or "response" not in data:
        return standings

    for item in data["response"]:
        league = item.get("league", {})
        league_id = league.get("id")
        year = league.get("season")

        if league_id is None or year is None:
            continue

        for standing_group in league.get("standings", []):
            for team_row in standing_group:
                team_id = team_row.get("team", {}).get("id")
                all_stats = team_row.get("all", {})
                goals = all_stats.get("goals", {})

                if team_id is None:
                    continue

                standings.append(
                    (
                        int(league_id),
                        int(year),
                        int(team_id),
                        parse_stat_number(team_row.get("rank")),
                        team_row.get("description"),
                        parse_stat_number(team_row.get("points")),
                        parse_stat_number(all_stats.get("played")),
                        parse_stat_number(all_stats.get("win")),
                        parse_stat_number(all_stats.get("draw")),
                        parse_stat_number(all_stats.get("lose")),
                        parse_stat_number(goals.get("for")),
                        parse_stat_number(goals.get("against")),
                    )
                )

    return standings


def save_standings(standings: list[tuple]) -> None:
    if standings:
        database.executemany(
            """
            INSERT OR REPLACE INTO LeagueTable
            (
                LeagueID,
                Year,
                TeamID,
                Position,
                Description,
                Points,
                Played,
                Won,
                Drawn,
                Lost,
                GF,
                GA
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            standings,
        )


def parse_stat_number(value, *, percentage: bool = False):
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return value

    if isinstance(value, str):
        stripped = value.strip()
        if percentage:
            stripped = stripped.rstrip("%").strip()
        if stripped == "":
            return None
        try:
            numeric = float(stripped)
        except ValueError:
            return None
        if percentage or "." in stripped:
            return numeric
        return int(numeric)

    return None


def parse_fixture_statistics(data: dict) -> list[tuple]:
    fixture_statistics = []

    if not data or "response" not in data:
        return fixture_statistics

    fixture_id = data.get("parameters", {}).get("fixture")
    if fixture_id is None:
        return fixture_statistics

    fixture_id = int(fixture_id)

    stat_column_map = {
        "Shots on Goal": ("ShotsOnGoal", False),
        "Shots off Goal": ("ShotsOffGoal", False),
        "Total Shots": ("TotalShots", False),
        "Blocked Shots": ("BlockedShots", False),
        "Shots insidebox": ("ShotsInsideBox", False),
        "Shots outsidebox": ("ShotsOutsideBox", False),
        "Fouls": ("Fouls", False),
        "Corner Kicks": ("CornerKicks", False),
        "Offsides": ("Offsides", False),
        "Ball Possession": ("BallPossession", True),
        "Yellow Cards": ("YellowCards", False),
        "Red Cards": ("RedCards", False),
        "Goalkeeper Saves": ("GoalkeeperSaves", False),
        "Total passes": ("TotalPasses", False),
        "Passes accurate": ("PassesAccurate", False),
        "Passes %": ("PassesPercentage", True),
        "expected_goals": ("ExpectedGoals", False),
        "goals_prevented": ("GoalsPrevented", False),
    }

    ordered_columns = [
        "ShotsOnGoal",
        "ShotsOffGoal",
        "TotalShots",
        "BlockedShots",
        "ShotsInsideBox",
        "ShotsOutsideBox",
        "Fouls",
        "CornerKicks",
        "Offsides",
        "BallPossession",
        "YellowCards",
        "RedCards",
        "GoalkeeperSaves",
        "TotalPasses",
        "PassesAccurate",
        "PassesPercentage",
        "ExpectedGoals",
        "GoalsPrevented",
    ]

    for item in data["response"]:
        team_id = item.get("team", {}).get("id")
        if team_id is None:
            continue

        row_data = {column: None for column in ordered_columns}

        for stat in item.get("statistics", []):
            stat_type = stat.get("type")
            if stat_type not in stat_column_map:
                continue

            column_name, is_percentage = stat_column_map[stat_type]
            row_data[column_name] = parse_stat_number(
                stat.get("value"), percentage=is_percentage
            )

        fixture_statistics.append(
            (
                fixture_id,
                int(team_id),
                row_data["ShotsOnGoal"],
                row_data["ShotsOffGoal"],
                row_data["TotalShots"],
                row_data["BlockedShots"],
                row_data["ShotsInsideBox"],
                row_data["ShotsOutsideBox"],
                row_data["Fouls"],
                row_data["CornerKicks"],
                row_data["Offsides"],
                row_data["BallPossession"],
                row_data["YellowCards"],
                row_data["RedCards"],
                row_data["GoalkeeperSaves"],
                row_data["TotalPasses"],
                row_data["PassesAccurate"],
                row_data["PassesPercentage"],
                row_data["ExpectedGoals"],
                row_data["GoalsPrevented"],
            )
        )

    return fixture_statistics


def save_fixture_statistics(fixture_statistics: list[tuple]) -> None:
    if fixture_statistics:
        database.executemany(
            """
            INSERT OR REPLACE INTO FixtureStatistics
            (
                FixtureID,
                TeamID,
                ShotsOnGoal,
                ShotsOffGoal,
                TotalShots,
                BlockedShots,
                ShotsInsideBox,
                ShotsOutsideBox,
                Fouls,
                CornerKicks,
                Offsides,
                BallPossession,
                YellowCards,
                RedCards,
                GoalkeeperSaves,
                TotalPasses,
                PassesAccurate,
                PassesPercentage,
                ExpectedGoals,
                GoalsPrevented
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            fixture_statistics,
        )


def parse_team_statistics(data: dict) -> list[tuple]:
    team_statistics = []

    if not data or "response" not in data:
        return team_statistics

    response = data.get("response", {})
    league = response.get("league", {})
    team = response.get("team", {})
    fixtures = response.get("fixtures", {})
    goals = response.get("goals", {})
    failed_to_score = response.get("failed_to_score", {})

    league_id = league.get("id")
    year = league.get("season")
    team_id = team.get("id")

    if league_id is None or year is None or team_id is None:
        return team_statistics

    team_statistics.append(
        (
            int(league_id),
            int(year),
            int(team_id),
            response.get("form"),
            parse_stat_number(fixtures.get("wins", {}).get("home")),
            parse_stat_number(fixtures.get("wins", {}).get("away")),
            parse_stat_number(fixtures.get("draws", {}).get("home")),
            parse_stat_number(fixtures.get("draws", {}).get("away")),
            parse_stat_number(fixtures.get("loses", {}).get("home")),
            parse_stat_number(fixtures.get("loses", {}).get("away")),
            parse_stat_number(goals.get("for", {}).get("average", {}).get("home")),
            parse_stat_number(goals.get("for", {}).get("average", {}).get("away")),
            parse_stat_number(
                goals.get("against", {}).get("average", {}).get("home")
            ),
            parse_stat_number(
                goals.get("against", {}).get("average", {}).get("away")
            ),
            parse_stat_number(failed_to_score.get("home")),
            parse_stat_number(failed_to_score.get("away")),
        )
    )

    return team_statistics


def save_team_statistics(team_statistics: list[tuple]) -> None:
    if team_statistics:
        database.executemany(
            """
            INSERT OR REPLACE INTO TeamStatistics
            (
                LeagueID,
                Year,
                TeamID,
                Form,
                WinsHome,
                WinsAway,
                DrawsHome,
                DrawsAway,
                LossesHome,
                LossesAway,
                GoalsForAverageHome,
                GoalsForAverageAway,
                GoalsAgainstAverageHome,
                GoalsAgainstAverageAway,
                FailedToScoreHome,
                FailedToScoreAway
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            team_statistics,
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

        player_id = player.get("id")
        player_name = player.get("name")
        assist_player_id = assist.get("id")
        assist_player_name = assist.get("name")

        event_type = item.get("type")
        if event_type == "subst":
            event_type = "Substitution"

        events.append(
            (
                fixture_id,
                event_id,
                player_id,
                player_name,
                assist_player_id,
                assist_player_name,
                item.get("team", {}).get("id"),
                event_type,
                item.get("detail"),
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
                PlayerName,
                AssistPlayerID,
                AssistPlayerName,
                TeamID,
                EventType,
                Detail,
                Comments,
                EventMinute,
                ExtraMinute
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            event_row,
        )


def parse_players(data: dict) -> list[tuple]:
    players = []

    if not data or "response" not in data:
        return players

    for item in data["response"]:
        player = item.get("player", {})
        birth = player.get("birth", {})

        player_id = player.get("id")
        name = player.get("name")

        if not player_id or not name:
            continue

        birth_place = birth.get("place")
        birth_country = birth.get("country")
        place_of_birth = ", ".join(
            part for part in [birth_place, birth_country] if part
        ) or None

        players.append(
            (
                player_id,
                player.get("firstname"),
                player.get("lastname"),
                name,
                player.get("position"),
                birth.get("date"),
                place_of_birth,
                player.get("nationality"),
            )
        )

    return players


def save_players(players: list[tuple]) -> None:
    for player_row in players:
        database.execute(
            """
            INSERT OR REPLACE INTO Player
            (
                PlayerID,
                FirstName,
                LastName,
                Name,
                MainPosition,
                DateOfBirth,
                PlaceOfBirth,
                Nationality
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            player_row,
        )


def record_exists(sql: str, params: tuple) -> bool:
    return bool(database.query(sql, params))


def sync_leagues() -> None:
    data = api_get("/leagues")
    leagues, seasons = parse_leagues(data)
    save_leagues(leagues)
    save_seasons(seasons)
    print(f"Saved {len(leagues)} leagues and {len(seasons)} seasons.")


def sync_teams(league_id: int, season: int, force: bool = False) -> None:
    if not force and record_exists(
        """
        SELECT 1
        FROM SeasonTeams
        WHERE LeagueID = ? AND Year = ?
        LIMIT 1
        """,
        (league_id, season),
    ):
        print(
            f"Skipped team sync for league {league_id}, season {season}: records already exist."
        )
        return

    data = api_get(f"/teams?league={league_id}&season={season}")
    teams, links = parse_teams(data)
    save_teams(teams)
    save_season_team_links(links)
    print(f"Saved {len(teams)} teams and {len(links)} season links.")


def sync_fixtures(league_id: int, season: int, force: bool = False) -> None:
    if not force and record_exists(
        """
        SELECT 1
        FROM Fixtures
        WHERE LeagueID = ? AND Year = ?
        LIMIT 1
        """,
        (league_id, season),
    ):
        print(
            f"Skipped fixture sync for league {league_id}, season {season}: records already exist."
        )
        return

    data = api_get(f"/fixtures?league={league_id}&season={season}")
    fixtures = parse_fixtures(data)
    save_fixtures(fixtures)
    print(f"Saved {len(fixtures)} fixtures.")


def sync_standings(league_id: int, season: int, force: bool = False) -> None:
    if not force and record_exists(
        """
        SELECT 1
        FROM LeagueTable
        WHERE LeagueID = ? AND Year = ?
        LIMIT 1
        """,
        (league_id, season),
    ):
        print(
            f"Skipped standings sync for league {league_id}, season {season}: records already exist."
        )
        return

    data = api_get(f"/standings?league={league_id}&season={season}")
    standings = parse_standings(data)
    save_standings(standings)
    print(f"Saved {len(standings)} league table rows.")


def sync_events(fixture_id: int, force: bool = False) -> None:
    if not force and record_exists(
        """
        SELECT 1
        FROM Events
        WHERE FixtureID = ?
          AND (PlayerName IS NOT NULL OR AssistPlayerName IS NOT NULL)
        LIMIT 1
        """,
        (fixture_id,),
    ):
        print(f"Skipped event sync for fixture {fixture_id}: records already exist.")
        return

    data = api_get(f"/fixtures/events?fixture={fixture_id}")
    events = parse_events(data)
    save_events(events)
    print(f"Saved {len(events)} events.")


def sync_fixture_statistics(fixture_id: int, force: bool = False) -> None:
    if not force and record_exists(
        """
        SELECT 1
        FROM FixtureStatistics
        WHERE FixtureID = ?
        LIMIT 1
        """,
        (fixture_id,),
    ):
        print(
            f"Skipped fixture statistics sync for fixture {fixture_id}: records already exist."
        )
        return

    data = api_get(f"/fixtures/statistics?fixture={fixture_id}")
    fixture_statistics = parse_fixture_statistics(data)
    save_fixture_statistics(fixture_statistics)
    print(f"Saved {len(fixture_statistics)} fixture statistics rows.")


def sync_team_statistics(
    league_id: int, season: int, team_id: int, force: bool = False
) -> None:
    if not force and record_exists(
        """
        SELECT 1
        FROM TeamStatistics
        WHERE LeagueID = ? AND Year = ? AND TeamID = ?
        LIMIT 1
        """,
        (league_id, season, team_id),
    ):
        print(
            "Skipped team statistics sync for "
            f"league {league_id}, season {season}, team {team_id}: record already exists."
        )
        return

    data = api_get(f"/teams/statistics?league={league_id}&season={season}&team={team_id}")
    team_statistics = parse_team_statistics(data)
    save_team_statistics(team_statistics)
    print(f"Saved {len(team_statistics)} team statistics rows.")


def sync_players(player_id: int, force: bool = False) -> None:
    if not force and record_exists(
        """
        SELECT 1
        FROM Player
        WHERE PlayerID = ?
        LIMIT 1
        """,
        (player_id,),
    ):
        print(f"Skipped player sync for player {player_id}: record already exists.")
        return

    data = api_get(f"/players/profiles?player={player_id}")
    players = parse_players(data)
    save_players(players)
    print(f"Saved {len(players)} players.")


def main() -> None:
    if USE_MOCKS:
        print("Using mock API responses")

    database.init_db()
    print("Database initialised")

    sync_leagues()
    sync_teams(league_id=39, season=2024)
    sync_fixtures(league_id=39, season=2024)
    sync_standings(league_id=39, season=2024)
    sync_events(fixture_id=1208399)
    sync_fixture_statistics(fixture_id=1208399)
    sync_team_statistics(league_id=39, season=2024, team_id=41)
    sync_players(player_id=138908)


if __name__ == "__main__":
    main()
