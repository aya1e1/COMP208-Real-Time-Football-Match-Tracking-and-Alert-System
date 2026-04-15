import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / 'database' / 'database.db'
SCHEMA_PATH = BASE_DIR / 'database' / 'schema.sql'
SCHEMA_DIR = BASE_DIR / 'database' / 'schema'


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    db_already_exists = DB_PATH.exists()
    with get_connection() as conn:
        if SCHEMA_DIR.exists():
            for schema_file in sorted(SCHEMA_DIR.glob("*.sql")):
                with open(schema_file) as f:
                    conn.executescript(f.read())
        else:
            with open(SCHEMA_PATH) as f:
                conn.executescript(f.read())
    if db_already_exists:
        print("[DB] Schema ensured.")
    else:
        print("[DB] Initialised database.")


def query(sql, params=()):
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def execute(sql, params=()):
    with get_connection() as conn:
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor.lastrowid


def executemany(sql, data):
    with get_connection() as conn:
        conn.executemany(sql, data)
        conn.commit()
