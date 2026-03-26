"""database.py - SQLite connection helper and initialisation."""
import sqlite3
from pathlib import Path

# Path to the database file and schema file
BASE_DIR    = Path(__file__).resolve().parent.parent.parent
DB_PATH     = BASE_DIR / 'database' / 'database.db'
SCHEMA_PATH = BASE_DIR / 'database' / 'schema.sql'


def get_connection():
    """Create and return a new SQLite database connection.
    Row factory is set so results can be accessed as dictionaries.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # allows dict-like access e.g. row["Name"]
    conn.execute("PRAGMA foreign_keys = ON")  # enforce foreign key constraints
    return conn


def init_db():
    """Initialise the database by running the schema.sql file.
    Creates all tables if they do not already exist.
    Called once when the Flask app starts.
    """
    with open(SCHEMA_PATH) as f:
        schema_sql = f.read()
    with get_connection() as conn:
        conn.executescript(schema_sql) # run all SQL statements in the schema.sql
    print("[DB] Initialised database.")


def query(sql, params=()):
    """Execute a SELECT query and return the results as a list of dictionaries.
    
    Args:
        sql: SQL SELECT statement
        params: tuple of parameters to safely substitute into the query
    Returns:
        list of rows as dictionaries
    """
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def execute(sql, params=()):
    """Execute an INSERT, UPDATE, or DELETE statement.
    
    Args:
        sql: SQL statement to execute
        params: tuple of parameters to safely substitute into the statement
    Returns:
        lastrowid: the ID of the last inserted row
    """
    with get_connection() as conn:
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor.lastrowid


def executemany(sql, data):
    """Execute the same SQL statement for multiple rows of data.
    
    Args:
        sql: SQL statement to execute
        data: list of tuples, one per row
    """
    with get_connection() as conn:
        conn.executemany(sql, data)
        conn.commit()