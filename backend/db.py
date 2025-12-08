# backend/db.py
from __future__ import annotations

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "mmu_stem.db"


def get_connection() -> sqlite3.Connection:
    """
    Open a SQLite connection.
    - Uses mmu_stem.db in your project root.
    - Returns rows as dict-like objects.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Create tables if they don't exist.
    This runs automatically when the app starts.
    """
    conn = get_connection()
    cur = conn.cursor()

    # mentors table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS mentors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            field TEXT NOT NULL,
            description TEXT NOT NULL,
            research_area TEXT,
            photo TEXT
        )
        """
    )

    # projects table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT,
            description TEXT,
            team_size INTEGER
        )
        """
    )

    # requests table: both mentor & project requests
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,            -- "mentor_request" / "project_request"
            mentor_name TEXT,
            project_title TEXT,
            student_name TEXT,
            email TEXT,
            interest TEXT,
            role TEXT,
            faculty TEXT,
            skills TEXT,
            availability TEXT,
            contact TEXT,
            intro TEXT,
            message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    conn.close()
