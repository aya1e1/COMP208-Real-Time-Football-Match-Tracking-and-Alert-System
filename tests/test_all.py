"""
tests/test_all.py - Unit and integration tests.
"""
import sys
import os
import sqlite3
import hashlib
import unittest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# -- Path setup --
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# -- Shared in memory database setup --
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "database" / "schema.sql"
SCHEMA_DIR = Path(__file__).resolve().parent.parent / "database" / "schema"

def _build_memory_db():
    """Create an in-memory SQLite database and initialize it with the schema."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    if SCHEMA_DIR.exists():
        for schema_file in sorted(SCHEMA_DIR.glob("*.sql")):
            conn.executescript(schema_file.read_text(encoding="utf-8"))
    else:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
    return conn

def _patch_db(test_case, conn):
    import backend.db.database as db_module

    def _get_connection():
        return conn
    
    test_case._orig_get_connection = db_module.get_connection
    db_module.get_connection = _get_connection

def _unpatch_db(test_case):
    import backend.db.database as db_module
    db_module.get_connection = test_case._orig_get_connection

# -- 1. Auth Tests --
def _hash_password(password):
    salt = os.urandom(16).hex()
    h = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}${h}"

def _verify_password(password, stored):
    salt, h = stored.split("$", 1)
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == h

class TestAuth(unittest.TestCase):

    def test_hash_and_verify_correct(self):
        h = _hash_password("SecurePass1!")
        self.assertTrue(_verify_password("SecurePass1!", h))
    
    def test_wrong_password_fails(self):
        h = _hash_password("SecurePass1!")
        self.assertFalse(_verify_password("WrongPassword", h))

    def test_unique_salts(self):
        """Same password hashed twice must produce different hashes (salted)."""
        self.assertNotEqual(_hash_password("pass"), _hash_password("pass"))
    
    def test_hash_format(self):
        h = _hash_password("test")
        parts = h.split("$")
        self.assertEqual(len(parts), 2, "Hash must be salt$hash format")


# -- 2. Database tests --
class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.conn = _build_memory_db()
        _patch_db(self, self.conn)

    def tearDown(self):
        _unpatch_db(self)
        self.conn.close()
    
    def test_tables_created(self):
        from backend.db.database import query
        tables = {t["name"] for t in query(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        for t in ["League", "Teams", "Fixtures", "Events", "Users", "Player", "Cache"]:
            self.assertIn(t, tables)
    
    def test_insert_and_query(self):
        from backend.db.database import execute, query
        execute("INSERT INTO League (LeagueID, Name, Country) VALUES (?,?,?)",
                (39, "Premier League", "England"))
        rows = query("SELECT * FROM League WHERE LeagueID=39")
        self.assertEqual(rows[0]["Name"], "Premier League")
    
    def test_duplicate_username_rejected(self):
        from backend.db.database import execute
        execute("INSERT INTO Users (Username,Email,PasswordHash) VALUES (?,?,?)",
                ("dup", "a@a.com", "h"))
        with self.assertRaises(Exception):
            execute("INSERT INTO Users (Username,Email,PasswordHash) VALUES (?,?,?)",
                    ("dup", "b@b.com", "h"))
    
    def test_user_insert_returns_id(self):
        from backend.db.database import execute, query
        uid = execute("INSERT INTO Users (Username,Email,PasswordHash) VALUES (?,?,?)",
                      ("tom", "t@t.com", "hash"))
        rows = query("SELECT * FROM Users WHERE UserID=?", (uid,))
        self.assertEqual(rows[0]["Username"], "tom")
    
    def test_foreign_key_enforced(self):
        from backend.db.database import execute
        with self.assertRaises(Exception):
            execute(
                "INSERT INTO SeasonTeams (TeamID,LeagueID,Year) VALUES (?,?,?)",
                (1, 9999, 2024),
            )


# -- 3. Cache Tests --
class TestCache(unittest.TestCase):

    def setUp(self):
        self.conn = _build_memory_db()
        _patch_db(self, self.conn)

    def tearDown(self):
        _unpatch_db(self)
        self.conn.close()
    
    def test_miss_returns_none(self):
        from backend.api.cache import Cache
        self.assertIsNone(Cache().get("missing_key"))
    
    def test_set_and_get(self):
        from backend.api.cache import Cache
        c = Cache()
        c.set("leagues_England", [{"id": 39}], ttl=3600)
        self.assertEqual(c.get("leagues_England")[0]["id"], 39)
    
    def test_expired_returns_none(self):
        from backend.api.cache import Cache
        from backend.db.database import execute
        c = Cache()
        c.set("old_key", {"data": 1}, ttl=3600)
        # Manually backdate the expiry so it looks expired
        expired_time = (datetime.utcnow() - timedelta(seconds=60)).isoformat()
        execute("UPDATE Cache SET ExpiresAt=? WHERE CacheKey=?",
                (expired_time, "old_key"))
        self.assertIsNone(c.get("old_key"))
    
    def test_overwrite_existing(self):
        from backend.api.cache import Cache
        c = Cache()
        c.set("k", {"v": 1}, 3600)
        c.set("k", {"v": 2}, 3600)
        self.assertEqual(c.get("k")["v"], 2)
    
    def test_delete(self):
        from backend.api.cache import Cache
        c = Cache()
        c.set("del_me", "some_data", 3600)
        c.delete("del_me")
        self.assertIsNone(c.get("del_me"))


# -- 4. Event Processing Tests --

def _seed_teams(execute_fn):
    execute_fn("INSERT INTO League (LeagueID,Name) VALUES (39,'Premier League')")
    execute_fn("INSERT INTO Seasons (LeagueID,Year) VALUES (39,2024)")
    execute_fn("INSERT INTO Teams (TeamID,Name) VALUES (40,'Liverpool')")
    execute_fn("INSERT INTO Teams (TeamID,Name) VALUES (42,'Arsenal')")
    execute_fn("INSERT INTO Player (PlayerID,Name) VALUES (100,'Salah')")

def _sample_fixture():
    return {
        "fixture": {"id": 1001, "date": "2025-04-20T15:00:00+00:00",
                    "status": {"short": "FT", "elapsed": 90},
                    "venue": {"name": "Anfield", "city": "Liverpool"}},
        "league":  {"id": 39, "season": 2024},
        "teams":   {"home": {"id": 40, "name": "Liverpool"},
                    "away": {"id": 42, "name": "Arsenal"}},
        "goals":   {"home": 2, "away": 1},
    }

def _sample_events():
    return [
        {"type": "Goal", "detail": "Normal Goal", 
         "time": {"elapsed": 23, "extra": None},
         "team": {"id": 40}, "player": {"id": 100, "name": "Salah"},
         "assist": {"id": None, "name": None}},
        {"type": "Card", "detail": "Yellow Card",
         "time": {"elapsed": 55, "extra": None},
         "team": {"id": 42}, "player": {"id": None, "name": ""},
         "assist": {"id": None, "name": None}},
    ]

class TestEventProcessor(unittest.TestCase):

    def setUp(self):
        self.conn = _build_memory_db()
        _patch_db(self, self.conn)
        from backend.db.database import execute
        _seed_teams(execute)

    def tearDown(self):
        _unpatch_db(self)
        self.conn.close()
    
    def test_fixture_upserted(self):
        from backend.events.processor import upsert_fixture
        from backend.db.database import query
        upsert_fixture(_sample_fixture())
        rows = query("SELECT * FROM Fixtures WHERE FixtureID=1001")
        self.assertEqual(rows[0]["HomeScore"], 2)
    
    def test_events_stored(self):
        from backend.events.processor import process_fixture_update
        from backend.db.database import query
        process_fixture_update(_sample_fixture(), _sample_events())
        events = query("SELECT * FROM Events WHERE FixtureID=1001")
        self.assertEqual(len(events), 2)

    def test_idempotent(self):
        """Running twice must not duplicate events."""
        from backend.events.processor import process_fixture_update
        from backend.db.database import query
        process_fixture_update(_sample_fixture(), _sample_events())
        process_fixture_update(_sample_fixture(), _sample_events())
        self.assertEqual(len(query("SELECT * FROM Events WHERE FixtureID=1001")), 2)

    def test_score_updated(self):
        from backend.events.processor import upsert_fixture
        from backend.db.database import query
        upsert_fixture(_sample_fixture())
        updated = dict(_sample_fixture())
        updated["goals"] = {"home": 3, "away": 1}
        upsert_fixture(updated)
        self.assertEqual(query("SELECT HomeScore FROM Fixtures WHERE FixtureID=1001")[0]["HomeScore"], 3)


# -- 5. Notifier Tests --
class TestNotifier(unittest.TestCase):

    def setUp(self):
        self.conn = _build_memory_db()
        _patch_db(self, self.conn)
        from backend.db.database import execute
        execute("INSERT INTO League (LeagueID,Name) VALUES (39,'PL')")
        execute("INSERT INTO Teams (TeamID,Name) VALUES (40,'Liverpool')")
        execute("INSERT INTO Users (UserID,Username,Email,PasswordHash) VALUES (1,'tom','t@t.com','h')")
        execute("INSERT INTO UserFavouriteTeams (UserID,TeamID) VALUES (1,40)")
        import backend.events.notifier as n
        n._notifications.clear()
    
    def tearDown(self):
        _unpatch_db(self)
        self.conn.close()
        import backend.events.notifier as n
        n._notifications.clear()
    
    def test_goal_notification_queued(self):
        from backend.events.notifier import Notifier, _notifications
        Notifier().notify(1001, 40, "Goal", "Normal Goal", 23)
        self.assertEqual(len(_notifications), 1)
        self.assertIn("GOAL", _notifications[0]["message"])
    
    def test_disabled_preference_blocks_notification(self):
        from backend.db.database import execute
        from backend.events.notifier import Notifier, _notifications
        execute("INSERT INTO UserNotificationPreferences (UserID,TeamID,NotifyGoals) VALUES (1,40,0)")
        Notifier().notify(1001, 40, "Goal", "Normal Goal", 10)
        self.assertEqual(len(_notifications), 0)
    
    def test_get_clears_pending(self):
        from backend.events.notifier import Notifier, get_pending_notifications
        Notifier().notify(1001, 40, "Goal", "Normal Goal", 1)
        msgs = get_pending_notifications(1)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(get_pending_notifications(1), [])  # cleared


# -- 6. API Wrapper Tests (mocked - no real API calls, no API key needed) --

class TestFootballAPI(unittest.TestCase):

    def setUp(self):
        self.conn = _build_memory_db()
        _patch_db(self, self.conn)
    
    def tearDown(self):
        _unpatch_db(self)
        self.conn.close()
    
    @patch("backend.api.football_api._get")
    def test_cache_prevents_duplicate_api_call(self, mock_get):
        mock_get.return_value = {"response": [{"league": {"id": 39}}]}
        from backend.api import football_api as api
        api.get_leagues("England")
        api.get_leagues("England")  # second call should use cache
        self.assertEqual(mock_get.call_count, 1)
    
    @patch("backend.api.football_api._get")
    def test_live_fixtures_returns_data(self, mock_get):
        mock_get.return_value = {"response": [{"fixture": {"id": 999}}]}
        from backend.api import football_api as api
        result = api.get_live_fixtures()
        self.assertEqual(result[0]["fixture"]["id"], 999)

    @patch("backend.api.football_api._get")
    def test_standings_cached(self, mock_get):
        mock_get.return_value = {"response": [{"league": {"standings": []}}]}
        from backend.api import football_api as api
        api.get_standings(39, 2024)
        api.get_standings(39, 2024) # second call should use cache
        self.assertEqual(mock_get.call_count, 1)

if __name__ == "__main__":
    unittest.main(verbosity=2)
