"""Integration and unit tests for backend sync, parsing, mocks, and API routes."""

import importlib
import importlib.util
import json
import sqlite3
import sys
import types
import unittest
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit
from unittest.mock import patch

try:
    from flask import Flask
except ModuleNotFoundError:
    Flask = None


ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
CORE_DB_PATH = ROOT_DIR / "database" / "core.db"
SCHEMA_PATH = ROOT_DIR / "database" / "schema.sql"
SCHEMA_DIR = ROOT_DIR / "database" / "schema"
DUMMY_DIR = BACKEND_DIR / "dummy"
MAIN_PATH = BACKEND_DIR / "main.py"


def _install_stub_modules() -> None:
    """Provide lightweight stand-ins for optional packages used by the backend."""
    if "responses" not in sys.modules:
        responses_module = types.ModuleType("responses")

        def activate(func):
            return func

        responses_module.activate = activate
        sys.modules["responses"] = responses_module

    if "dotenv" not in sys.modules:
        dotenv_module = types.ModuleType("dotenv")
        dotenv_module.load_dotenv = lambda: None
        sys.modules["dotenv"] = dotenv_module


def _ensure_import_paths() -> None:
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))


def _load_main_module():
    """Load backend/main.py the same way the script runs from the backend folder."""
    _install_stub_modules()
    _ensure_import_paths()

    module_name = "sync_main_under_test"
    sys.modules.pop(module_name, None)

    spec = importlib.util.spec_from_file_location(module_name, MAIN_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_external_api_module():
    """Import backend.external_api for direct mock-path testing."""
    _install_stub_modules()
    _ensure_import_paths()
    return importlib.import_module("backend.external_api")


def _load_api_module():
    """Import backend.api.api for route testing."""
    _install_stub_modules()
    _ensure_import_paths()
    return importlib.import_module("backend.api.api")


def _build_memory_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    if SCHEMA_DIR.exists():
        for schema_file in sorted(SCHEMA_DIR.glob("*.sql")):
            conn.executescript(schema_file.read_text(encoding="utf-8"))
    elif SCHEMA_PATH.exists():
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    else:
        disk_conn = sqlite3.connect(CORE_DB_PATH)
        try:
            schema_statements = disk_conn.execute(
                """
                SELECT sql
                FROM sqlite_master
                WHERE sql IS NOT NULL
                  AND type IN ('table', 'index', 'trigger', 'view')
                  AND name NOT LIKE 'sqlite_%'
                ORDER BY
                    CASE type
                        WHEN 'table' THEN 0
                        WHEN 'index' THEN 1
                        WHEN 'trigger' THEN 2
                        ELSE 3
                    END,
                    name
                """
            ).fetchall()
        finally:
            disk_conn.close()

        conn.executescript(";\n".join(statement[0] for statement in schema_statements) + ";")
    return conn


def _mock_api_get(path: str):
    fixture_map = {
        "/leagues": "output_leagues.json",
        "/teams?league=39&season=2024": "output_teams_league-39_season-2024.json",
        "/fixtures?league=39&season=2024": "output_fixtures_league-39_season-2024.json",
        "/fixtures/events?fixture=1208399": "output_fixtures_events_fixture-1208399.json",
        "/fixtures/statistics?fixture=1208399": "output_fixtures_statistics_fixture-1208399.json",
        "/players/profiles?player=138908": "output_players_profiles_player-138908.json",
    }
    file_name = fixture_map.get(path)

    if file_name is None:
        parsed_path = urlsplit(path)
        endpoint_name = parsed_path.path.strip("/").replace("/", "_") or "root"
        params = parse_qsl(parsed_path.query, keep_blank_values=True)
        param_str = "_".join(f"{key}-{value}" for key, value in params)
        file_name = (
            f"output_{endpoint_name}_{param_str}.json"
            if param_str
            else f"output_{endpoint_name}.json"
        )

    file_path = DUMMY_DIR / file_name
    if not file_path.exists():
        raise AssertionError(f"Unexpected API path requested: {path}")

    return json.loads(file_path.read_text(encoding="utf-8"))


class MainModuleDatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.main_module = _load_main_module()
        self.conn = _build_memory_db()
        self.assertEqual(self.main_module.database.DB_PATH, CORE_DB_PATH)

        self.original_get_connection = self.main_module.database.get_connection
        self.original_init_db = self.main_module.database.init_db
        self.original_api_get = self.main_module.api_get

        self.main_module.database.get_connection = lambda: self.conn
        self.main_module.database.init_db = lambda: None
        self.main_module.api_get = _mock_api_get

    def tearDown(self):
        self.main_module.database.get_connection = self.original_get_connection
        self.main_module.database.init_db = self.original_init_db
        self.main_module.api_get = self.original_api_get
        self.conn.close()


class TestMainSyncScript(MainModuleDatabaseTestCase):
    def test_main_populates_expected_records(self):
        self.main_module.main()

        league_count = self.conn.execute("SELECT COUNT(*) FROM League").fetchone()[0]
        season_count = self.conn.execute("SELECT COUNT(*) FROM Seasons").fetchone()[0]
        team_count = self.conn.execute("SELECT COUNT(*) FROM Teams").fetchone()[0]
        season_team_count = self.conn.execute(
            "SELECT COUNT(*) FROM SeasonTeams"
        ).fetchone()[0]
        fixture_count = self.conn.execute("SELECT COUNT(*) FROM Fixtures").fetchone()[0]
        event_count = self.conn.execute("SELECT COUNT(*) FROM Events").fetchone()[0]
        statistics_count = self.conn.execute(
            "SELECT COUNT(*) FROM FixtureStatistics"
        ).fetchone()[0]
        player_count = self.conn.execute("SELECT COUNT(*) FROM Player").fetchone()[0]

        self.assertEqual(league_count, 46)
        self.assertEqual(season_count, 329)
        self.assertEqual(team_count, 20)
        self.assertEqual(season_team_count, 20)
        self.assertEqual(fixture_count, 380)
        self.assertEqual(event_count, 11)
        self.assertEqual(statistics_count, 2)
        self.assertEqual(player_count, 1)

        liverpool = self.conn.execute(
            "SELECT Name, Stadium FROM Teams WHERE TeamID = 40"
        ).fetchone()
        self.assertEqual(dict(liverpool), {"Name": "Liverpool", "Stadium": "Anfield"})

        premier_league = self.conn.execute(
            "SELECT Name FROM League WHERE LeagueID = 39"
        ).fetchone()
        self.assertEqual(premier_league["Name"], "Premier League")

        fixture = self.conn.execute(
            """
            SELECT HomeTeamID, AwayTeamID, Location, MatchDate, Status, HomeScore, AwayScore
            FROM Fixtures
            WHERE FixtureID = 1208021
            """
        ).fetchone()
        self.assertEqual(
            dict(fixture),
            {
                "HomeTeamID": 33,
                "AwayTeamID": 36,
                "Location": "Old Trafford",
                "MatchDate": "2024-08-16 19:00:00",
                "Status": "FT",
                "HomeScore": 1,
                "AwayScore": 0,
            },
        )

    def test_main_is_idempotent_when_run_twice(self):
        self.main_module.main()
        counts_after_first_run = {
            "League": self.conn.execute("SELECT COUNT(*) FROM League").fetchone()[0],
            "SeasonTeams": self.conn.execute(
                "SELECT COUNT(*) FROM SeasonTeams"
            ).fetchone()[0],
            "Fixtures": self.conn.execute("SELECT COUNT(*) FROM Fixtures").fetchone()[0],
            "Events": self.conn.execute("SELECT COUNT(*) FROM Events").fetchone()[0],
            "FixtureStatistics": self.conn.execute(
                "SELECT COUNT(*) FROM FixtureStatistics"
            ).fetchone()[0],
            "Player": self.conn.execute("SELECT COUNT(*) FROM Player").fetchone()[0],
        }

        self.main_module.main()
        counts_after_second_run = {
            "League": self.conn.execute("SELECT COUNT(*) FROM League").fetchone()[0],
            "SeasonTeams": self.conn.execute(
                "SELECT COUNT(*) FROM SeasonTeams"
            ).fetchone()[0],
            "Fixtures": self.conn.execute("SELECT COUNT(*) FROM Fixtures").fetchone()[0],
            "Events": self.conn.execute("SELECT COUNT(*) FROM Events").fetchone()[0],
            "FixtureStatistics": self.conn.execute(
                "SELECT COUNT(*) FROM FixtureStatistics"
            ).fetchone()[0],
            "Player": self.conn.execute("SELECT COUNT(*) FROM Player").fetchone()[0],
        }

        self.assertEqual(counts_after_first_run, counts_after_second_run)


class TestParserFunctions(MainModuleDatabaseTestCase):
    def test_parse_teams_filters_non_english_and_builds_links(self):
        data = {
            "parameters": {"league": 39, "season": 2024},
            "response": [
                {
                    "team": {
                        "id": 1,
                        "name": "Liverpool",
                        "code": "LIV",
                        "country": "England",
                    },
                    "venue": {"city": "Liverpool", "name": "Anfield"},
                },
                {
                    "team": {
                        "id": 2,
                        "name": "Barcelona",
                        "code": "BAR",
                        "country": "Spain",
                    },
                    "venue": {"city": "Barcelona", "name": "Camp Nou"},
                },
            ],
        }

        teams, links = self.main_module.parse_teams(data)

        self.assertEqual(
            teams,
            [(1, "Liverpool", "LIV", None, "Liverpool", "Anfield")],
        )
        self.assertEqual(links, [(1, 2024, 39)])

    def test_parse_events_normalises_substitutions(self):
        data = {
            "parameters": {"fixture": 1208399},
            "response": [
                {
                    "player": {"id": 101},
                    "assist": {"id": 202},
                    "team": {"id": 40},
                    "type": "subst",
                    "detail": "Substitution 1",
                    "comments": "Tactical",
                    "time": {"elapsed": 66, "extra": None},
                }
            ],
        }

        events = self.main_module.parse_events(data)

        self.assertEqual(
            events,
            [
                (
                    1208399,
                    1,
                    101,
                    None,
                    202,
                    None,
                    40,
                    "Substitution",
                    "Substitution 1",
                    "Tactical",
                    66,
                    None,
                )
            ],
        )

    def test_parse_fixture_statistics_converts_numeric_and_percentage_values(self):
        data = {
            "parameters": {"fixture": "1208399"},
            "response": [
                {
                    "team": {"id": 40},
                    "statistics": [
                        {"type": "Shots on Goal", "value": "5"},
                        {"type": "Ball Possession", "value": "61%"},
                        {"type": "Passes %", "value": "82%"},
                        {"type": "expected_goals", "value": "1.45"},
                    ],
                }
            ],
        }

        stats = self.main_module.parse_fixture_statistics(data)

        self.assertEqual(
            stats,
            [
                (
                    1208399,
                    40,
                    5,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    61.0,
                    None,
                    None,
                    None,
                    None,
                    None,
                    82.0,
                    1.45,
                    None,
                )
            ],
        )

    def test_parse_players_builds_place_of_birth(self):
        data = {
            "response": [
                {
                    "player": {
                        "id": 138908,
                        "firstname": "Ryan",
                        "lastname": "Gravenberch",
                        "name": "Ryan Gravenberch",
                        "position": "Midfielder",
                        "nationality": "Netherlands",
                        "birth": {"date": "2002-05-16", "place": "Amsterdam", "country": "Netherlands"},
                    }
                }
            ]
        }

        players = self.main_module.parse_players(data)

        self.assertEqual(
            players,
            [
                (
                    138908,
                    "Ryan",
                    "Gravenberch",
                    "Ryan Gravenberch",
                    "Midfielder",
                    "2002-05-16",
                    "Amsterdam, Netherlands",
                    "Netherlands",
                )
            ],
        )


class TestExternalApiMocks(unittest.TestCase):
    def setUp(self):
        self.external_api = _load_external_api_module()

    def test_get_mock_file_path_matches_existing_dummy_file(self):
        file_path = self.external_api.get_mock_file_path("/teams?league=39&season=2024")
        self.assertEqual(file_path, DUMMY_DIR / "output_teams_league-39_season-2024.json")

    def test_api_get_reads_mock_json_when_mock_mode_is_enabled(self):
        with patch.object(self.external_api, "USE_MOCKS", True):
            data = self.external_api.api_get("/leagues")

        self.assertIsInstance(data, dict)
        self.assertIn("response", data)
        self.assertGreater(len(data["response"]), 0)

    def test_api_get_returns_none_when_mock_file_is_missing(self):
        with patch.object(self.external_api, "USE_MOCKS", True):
            data = self.external_api.api_get("/not-a-real-endpoint")

        self.assertIsNone(data)


@unittest.skipIf(Flask is None, "Flask is not installed in this test environment")
class TestApiRoutes(MainModuleDatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.main_module.main()

        self.api_module = _load_api_module()
        self.original_api_db_get_connection = self.api_module.database.get_connection
        self.original_sync_events = self.api_module.sync_events
        self.original_sync_fixture_statistics = self.api_module.sync_fixture_statistics
        self.original_sync_team_statistics = self.api_module.sync_team_statistics

        self.api_module.database.get_connection = lambda: self.conn
        self.api_module.sync_events = lambda fixture_id: None
        self.api_module.sync_fixture_statistics = lambda fixture_id: None
        self.api_module.sync_team_statistics = (
            lambda league_id, season, team_id: None
        )

        app = Flask(__name__)
        app.register_blueprint(self.api_module.api_bp, url_prefix="/api")
        self.client = app.test_client()

    def tearDown(self):
        self.api_module.database.get_connection = self.original_api_db_get_connection
        self.api_module.sync_events = self.original_sync_events
        self.api_module.sync_fixture_statistics = self.original_sync_fixture_statistics
        self.api_module.sync_team_statistics = self.original_sync_team_statistics
        super().tearDown()

    def test_league_teams_returns_404_for_unknown_league(self):
        response = self.client.get("/api/leagues/999999/teams")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"error": "League not found"})

    def test_fixtures_rejects_invalid_date_ranges(self):
        bad_format = self.client.get("/api/fixtures?start_date=2024/01/01")
        self.assertEqual(bad_format.status_code, 400)
        self.assertEqual(
            bad_format.get_json(),
            {"error": "Invalid date format. Use YYYY-MM-DD for start_date and end_date."},
        )

        reversed_range = self.client.get(
            "/api/fixtures?start_date=2024-08-20&end_date=2024-08-10"
        )
        self.assertEqual(reversed_range.status_code, 400)
        self.assertEqual(
            reversed_range.get_json(),
            {"error": "start_date cannot be later than end_date."},
        )

    def test_fixtures_defaults_to_latest_ten_results(self):
        response = self.client.get("/api/fixtures")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(len(payload), 10)
        self.assertGreaterEqual(payload[0]["MatchDate"], payload[-1]["MatchDate"])

    def test_fixture_route_returns_fixture_events_and_statistics(self):
        response = self.client.get("/api/fixtures/1208399")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["data"][0]["FixtureID"], 1208399)
        self.assertEqual(len(payload["events"]), 11)
        self.assertEqual(len(payload["statistics"]), 2)


if __name__ == "__main__":
    unittest.main()
