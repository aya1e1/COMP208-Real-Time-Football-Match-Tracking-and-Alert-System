"""Integration test for the backend sync script."""

import importlib.util
import json
import sqlite3
import sys
import types
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
SCHEMA_PATH = ROOT_DIR / "database" / "schema.sql"
DUMMY_DIR = BACKEND_DIR / "dummy"
MAIN_PATH = BACKEND_DIR / "main.py"


def _install_stub_modules() -> None:
    """Provide lightweight stand-ins for optional packages used by main.py."""
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


def _load_main_module():
    """Load backend/main.py the same way the script runs from the backend folder."""
    _install_stub_modules()

    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))

    module_name = "sync_main_under_test"
    sys.modules.pop(module_name, None)

    spec = importlib.util.spec_from_file_location(module_name, MAIN_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _build_memory_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return conn


def _mock_api_get(path: str):
    fixture_map = {
        "/leagues": "output_leagues.json",
        "/teams?league=39&season=2024": "output_teams_league-39_season-2024.json",
        "/fixtures?league=39&season=2024": "output_fixtures_league-39_season-2024.json",
    }
    file_name = fixture_map.get(path)
    if file_name is None:
        raise AssertionError(f"Unexpected API path requested: {path}")
    return json.loads((DUMMY_DIR / file_name).read_text(encoding="utf-8"))


class TestMainSyncScript(unittest.TestCase):
    def setUp(self):
        self.main_module = _load_main_module()
        self.conn = _build_memory_db()

        self.original_get_connection = self.main_module.database.get_connection
        self.original_api_get = self.main_module.api_get

        self.main_module.database.get_connection = lambda: self.conn
        self.main_module.api_get = _mock_api_get

    def tearDown(self):
        self.main_module.database.get_connection = self.original_get_connection
        self.main_module.api_get = self.original_api_get
        self.conn.close()

    def test_main_populates_expected_records(self):
        self.main_module.main()

        league_count = self.conn.execute("SELECT COUNT(*) FROM League").fetchone()[0]
        season_count = self.conn.execute("SELECT COUNT(*) FROM Seasons").fetchone()[0]
        team_count = self.conn.execute("SELECT COUNT(*) FROM Teams").fetchone()[0]
        season_team_count = self.conn.execute(
            "SELECT COUNT(*) FROM SeasonTeams"
        ).fetchone()[0]
        fixture_count = self.conn.execute("SELECT COUNT(*) FROM Fixtures").fetchone()[0]

        self.assertEqual(league_count, 46)
        self.assertEqual(season_count, 329)
        self.assertEqual(team_count, 20)
        self.assertEqual(season_team_count, 20)
        self.assertEqual(fixture_count, 380)

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


if __name__ == "__main__":
    unittest.main()
