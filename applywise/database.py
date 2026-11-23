"""SQLite setup using only Python's standard library."""

import os
import sqlite3
from pathlib import Path
from typing import Iterator

DATABASE_PATH = Path(os.getenv("APPLYWISE_DATABASE_PATH", "./applywise.db")).resolve()


def connect() -> sqlite3.Connection:
    """Open a row-aware SQLite connection for one unit of work."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    # FastAPI runs synchronous routes in a worker thread after dependencies resolve.
    connection = sqlite3.connect(DATABASE_PATH, timeout=10, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def get_db() -> Iterator[sqlite3.Connection]:
    """Yield a request-scoped connection and always close it afterwards."""
    connection = connect()
    try:
        yield connection
    finally:
        connection.close()


def initialize_database() -> None:
    """Create the application table and useful indexes if they do not exist."""
    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'saved'
                    CHECK (status IN ('saved', 'applied', 'interview', 'offer', 'rejected', 'withdrawn')),
                location TEXT,
                job_url TEXT,
                source TEXT,
                salary TEXT,
                applied_on TEXT,
                follow_up_on TEXT,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f+00:00', 'now')),
                updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f+00:00', 'now'))
            );
            CREATE INDEX IF NOT EXISTS ix_applications_status ON applications(status);
            CREATE INDEX IF NOT EXISTS ix_applications_company ON applications(company);
            CREATE INDEX IF NOT EXISTS ix_applications_role ON applications(role);
            CREATE INDEX IF NOT EXISTS ix_applications_follow_up ON applications(follow_up_on);
            CREATE INDEX IF NOT EXISTS ix_applications_updated ON applications(updated_at);
            """
        )


initialize_database()
