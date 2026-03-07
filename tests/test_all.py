"""
tests/test_all.py - Unit and integration tests.
"""
import sys
import os
import sqlite3
import hashlib
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# -- Path setup --
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# -- Shared in memory database setup --
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "database" / "schema.sql"

def _build_in_memory_db():
    """Create an in-memory SQLite database and initialize it with the schema."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    with open(SCHEMA_PATH, "r") as f:
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

# AUTH TESTS
def _hash_password(password):
    salt = os.unrandom(16).hex()
    h = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}${h}"

def _verify_password(password, stored):
    salt, h= stored.split("$", 1)
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == h

class TestAuth(unittest.TestCase):

    def test_hash_and_verify_correct(self):
        h = _hash_password("SecurePass1!")
        self.assertTrue(_verify_password("SecurePass1!", h))
    
    def test_wrong_password_fails(self):
        h = _hash_password("SecurePass1!")
        self.assertFalse(_verify_password("WrongPass!", h))

    def test_unique_salts(self):
        """Same password hashed twice must produce different hashes."""
        self.assertNotEqual(_hash_password("pass"), _hash_password("pass"))
    
    def test_hash_format(self):
        h = _hash_password("test")
        parts = h.split("$")
        self.assertEqual(len(parts), 2, "Hash must be salt$hash format")


# -- Database tests --

class TestDatabase(unittest.TestCase):
    
    def setUp(self):
        self.conn = _build_in_memory_db()
        _patch_db(self, self.conn)

    def tearDown(self):
        _unpatch_db(self)
        self.conn.close()
    
    def test_tables_created(self):
        from backend.db.database import query
        tables = {t["name"] for t in query(
            "SELECT name From sqlite_master WHERE type='table'")}
        for t in ["League", "Teams", "Fixtures", "Events", "Users", "Player", "Cache"]:
            self.assertIn(t, tables)
    
    def test_insert_and_query(self):
        from backend.db.database import execute, query
        execute("INSERT INTO League (LeagueID, Name, Country) VALUES (?, ?, ?)",
                (39, "Premier League", "England"))
        rows = query("SELECT * FROM League WHERE LeagueID=39")
        self.assertEqual(rows[0]["Name"], "Premier League")
    
    def test_duplicate_username_rejected(self):
        from backend.db.database import execute
        execute("INSERT INTO USERS (Username,Email,PasswordHash) VALUES (?, ?, ?)",
                ("dup", "a@a.com", "h"))
        with self.assertRaises(Exception):
            execute("INSERT INTO USERS (Username,Email,PasswordHash) VALUES (?, ?, ?)",
                    ("dup", "b@b.com", "h"))
    
    def test_user_insert_return_id(self):
        from backend.db.database import execute, query
        uid = execute("INSERT INTO USERS (Username,Email,PasswordHash) VALUES (?, ?, ?)",
                        ("tom", "t@t.com", "hash"))
        rows: = query("SELECT * FROM USERS WHERE UserID=?", (uid,))
        self.assertEqual(rows[0]["Username"], "tom")
    
    def test_foreign_key_enforced(self):
        from backend.db.database import execute
        with self.assertRaises(Exception):
            execute("INSERT INTO Teams (TeamID, Name, LeagueID) VALUES (?, ?, ?)",
                    (1, "Ghost fC", 9999))  # LeagueID 9999 does not exist


# -- Cache Tests --
class TestCache(unittest.TestCase):

    def setUp(self):
        self.conn = _build_in_memory_db()
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
    
    def test_expired_return_none(self):
        from backend.api.cache import Cache
        from backend.db.database import execute
        c = Cache()
        c.set("old_key", {"data": 1}, ttl=3600)
        # Manually backdate the expiry so it looks expired
        expired_time = (datetime.utcnow() - timedelta(seconds=60)).isoformat()
        execute("UPDATE Cache SET ExpiryAt=? WHERE Key=?",
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

# -- Event Processing Tests --
def _seed_teams(execute_fn):
    execute_fn("INSERT INTO League (LeagueID ,Name) VALUES (39, 'Premier League')")
    execute_fn("INSERT INTO Seasons (SeasonID, LeagueID, Year) VALUES (2024, 39, 2024)")
    execute_fn("INSERT INTO Teams (TeamID, Name, LeagueID) VALUES (40, 'Liverpool', 39)")
    execute_fn("INSERT INTO Teams (TeamID, Name, LeagueID) VALUES (42, 'Arsenal', 39)")
    execute_fn("INSERT INTO Player (PlayerID, Name) VALUES (100, 'Salah')")

def _sample_fixture():
    return {
        "fixture": {"id": 1001, "data": "2024_04_20T15:00:00+00:00",
                    "status": {"short": "FT", "elapsed": 90},
                    "venue": {"name": "Anfield", "city": "Liverpool"}},
        "league": {"id": 39, "season": 2024},
        "teams": {"home": {"id": 40, "name": "Liverpool"},
                  "away": {"id": 42, "name": "Arsenal"}},
        "goals": {"home": 2, "away": 1},
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
            "assist": {"id": None, "name": None}} , 
    ]

class TestEventProcessing(unittest.TestCase):
