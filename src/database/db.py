"""
SQLite backend for Ctrl + Incision

Sprint 1 scope:
- Create tables for tracking devices, sessions, and 6-DOF pose samples.
- Provide minimal helper functions that the prototype can call to 
  start/end tracking sessions and log pose data for future analysis.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "ctrl_incision.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    schema = """
    CREATE TABLE IF NOT EXISTS tracking_devices (
        device_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT,
        connection_info TEXT
    );

    CREATE TABLE IF NOT EXISTS tracking_sessions (
        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER NOT NULL,
        started_at TEXT NOT NULL,
        ended_at TEXT,
        description TEXT,
        FOREIGN KEY (device_id) REFERENCES tracking_devices(device_id)
    );

    CREATE TABLE IF NOT EXISTS pose_samples (
        sample_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        tx REAL,
        ty REAL,
        tz REAL,
        rx REAL,
        ry REAL,
        rz REAL,
        raw_json TEXT,
        FOREIGN KEY (session_id) REFERENCES tracking_sessions(session_id)
    );
    """

    conn = get_connection()
    try:
        conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()

def start_tracking_session(device_name: str, description: str = "") -> int:
    """
    Create a tracking_device (if needed) and a new tracking_session.
    Returns the new session_id.
    """
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO tracking_devices (name) VALUES (?)",
            (device_name,),
        )
        device_id = cur.lastrowid

        cur = conn.execute(
            "INSERT INTO tracking_sessions (device_id, started_at, description) "
            "VALUES (?, datetime('now'), ?)",
            (device_id, description),
        )
        session_id = cur.lastrowid

        conn.commit()
        return session_id
    finally:
        conn.close()

def end_tracking_session(session_id: int) -> None:
    """
    Mark a tracking session as ended.
    """
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE tracking_sessions "
            "SET ended_at = datetime('now') "
            "WHERE session_id = ?",
            (session_id,),
        )
        conn.commit()
    finally:
        conn.close()

def log_pose(
    session_id: int,
    tx: float,
    ty: float,
    tz: float,
    rx: float,
    ry: float,
    rz: float,
    raw_json=None,
) -> None:
    """
    Insert a single 6-DOF pose sample into the database for a session.
    """
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO pose_samples "
            "(session_id, timestamp, tx, ty, tz, rx, ry, rz, raw_json) "
            "VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?, ?)",
            (session_id, tx, ty, tz, rx, ry, rz, raw_json),
        )
        conn.commit()
    finally:
        conn.close()

def get_recent_sessions(limit: int = 10):
    """
    Return the most recent tracking_sessions with their device names.
    """
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            SELECT s.session_id, d.name, s.started_at, s.ended_at, s.description
            FROM tracking_sessions s
            JOIN tracking_devices d ON s.device_id = d.device_id
            ORDER BY s.started_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return cur.fetchall()
    finally:
        conn.close()

def get_pose_samples(session_id: int):
    """
    Return all pose samples for a given tracking session.
    """
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            SELECT timestamp, tx, ty, tz, rx, ry, rz
            FROM pose_samples
            WHERE session_id = ?
            ORDER BY timestamp ASC
            """,
            (session_id,),
        )
        return cur.fetchall()
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")