"""
SQLite backend for Ctrl + Incision

Sprint 1 scope:
- Create tables for tracking devices, sessions, and 6-DOF pose samples.
- Provide minimal helper functions that the prototype can call to 
  start/end tracking sessions and log pose data for future analysis.
"""

import sqlite3
from pathlib import Path
from typing import Optional

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

    CREATE TABLE IF NOT EXISTS device_configs (
        config_id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER,
        config_path TEXT NOT NULL,
        config_type TEXT,
        created_at TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (device_id) REFERENCES tracking_devices(device_id)
    );

    CREATE TABLE IF NOT EXISTS capture_sessions (
        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER,
        config_id INTEGER,
        started_at TEXT NOT NULL,
        ended_at TEXT,
        status TEXT NOT NULL,
        output_dir TEXT,
        fps REAL,
        FOREIGN KEY (device_id) REFERENCES tracking_devices(device_id),
        FOREIGN KEY (config_id) REFERENCES device_configs(config_id)
    );


    CREATE TABLE IF NOT EXISTS ultrasound_streams (
        artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        stream_type TEXT,
        file_path TEXT NOT NULL,
        fps REAL,
        resolution TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES capture_sessions(session_id)
    );

    CREATE TABLE IF NOT EXISTS tracking_streams (
        artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        stream_type TEXT,
        file_path TEXT NOT NULL,
        rate_hz REAL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES capture_sessions(session_id)
    );

    CREATE TABLE IF NOT EXISTS logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        event_type TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        level TEXT NOT NULL,
        message TEXT,
        FOREIGN KEY (session_id) REFERENCES capture_sessions(session_id)
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

def get_or_create_device(name: str, type: str = "", connection_info: str = "") -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "SELECT device_id FROM tracking_devices WHERE name=? AND type=? AND connection_info=?",
            (name, type, connection_info),
        )
        row = cur.fetchone()
        if row:
            return row[0]

        cur = conn.execute(
            "INSERT INTO tracking_devices (name, type, connection_info) VALUES (?, ?, ?)",
            (name, type, connection_info),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def create_device_config(device_id: Optional[int], config_path: str, config_type: str = "PLUS_DEVICESET", notes: str = "") -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO device_configs (device_id, config_path, config_type, created_at, notes) "
            "VALUES (?, ?, ?, datetime('now'), ?)",
            (device_id, config_path, config_type, notes),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def start_capture_session(device_id, config_id, output_dir, fps, status="RUNNING") -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO capture_sessions (device_id, config_id, started_at, status, output_dir, fps) "
            "VALUES (?, ?, datetime('now'), ?, ?, ?)",
            (device_id, config_id, status, output_dir, fps),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()



def end_capture_session(session_id: int, status: str = "COMPLETED") -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE capture_sessions SET ended_at = datetime('now'), status=? WHERE session_id=?",
            (status, session_id),
        )
        conn.commit()
    finally:
        conn.close()


def log_event(session_id: Optional[int], event_type: str, level: str = "INFO", message: str = "") -> None:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO logs (session_id, event_type, timestamp, level, message) "
            "VALUES (?, ?, datetime('now'), ?, ?)",
            (session_id, event_type, level, message),
        )
        conn.commit()
    finally:
        conn.close()

def add_ultrasound_stream(
    session_id: int,
    file_path: str,
    stream_type: str = "FRAMES",
    fps: Optional[float] = None,
    resolution: str = "",
) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO ultrasound_streams (session_id, stream_type, file_path, fps, resolution, created_at) "
            "VALUES (?, ?, ?, ?, ?, datetime('now'))",
            (session_id, stream_type, file_path, fps, resolution),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def add_tracking_stream(
    session_id: int,
    file_path: str,
    stream_type: str = "CSV",
    rate_hz: Optional[float] = None,
) -> int:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO tracking_streams (session_id, stream_type, file_path, rate_hz, created_at) "
            "VALUES (?, ?, ?, ?, datetime('now'))",
            (session_id, stream_type, file_path, rate_hz),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

def get_recent_capture_sessions(limit: int = 20):
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            SELECT
                cs.session_id,
                cs.started_at,
                cs.ended_at,
                cs.status,
                cs.output_dir,
                cs.fps,
                td.name AS device_name,
                dc.config_path,
                dc.config_type
            FROM capture_sessions cs
            LEFT JOIN tracking_devices td ON cs.device_id = td.device_id
            LEFT JOIN device_configs dc ON cs.config_id = dc.config_id
            ORDER BY cs.started_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return cur.fetchall()
    finally:
        conn.close()


def get_capture_session_details(session_id: int):
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            SELECT
                cs.session_id,
                cs.started_at,
                cs.ended_at,
                cs.status,
                cs.output_dir,
                cs.fps,
                td.name AS device_name,
                td.type AS device_type,
                td.connection_info,
                dc.config_path,
                dc.config_type,
                dc.notes
            FROM capture_sessions cs
            LEFT JOIN tracking_devices td ON cs.device_id = td.device_id
            LEFT JOIN device_configs dc ON cs.config_id = dc.config_id
            WHERE cs.session_id = ?
            """,
            (session_id,),
        )
        return cur.fetchone()
    finally:
        conn.close()


def get_ultrasound_streams_for_session(session_id: int):
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            SELECT artifact_id, stream_type, file_path, fps, resolution, created_at
            FROM ultrasound_streams
            WHERE session_id = ?
            ORDER BY created_at DESC
            """,
            (session_id,),
        )
        return cur.fetchall()
    finally:
        conn.close()


def get_tracking_streams_for_session(session_id: int):
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            SELECT artifact_id, stream_type, file_path, rate_hz, created_at
            FROM tracking_streams
            WHERE session_id = ?
            ORDER BY created_at DESC
            """,
            (session_id,),
        )
        return cur.fetchall()
    finally:
        conn.close()


def get_logs_for_session(session_id: int, limit: int = 50):
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            SELECT event_type, timestamp, level, message
            FROM logs
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (session_id, limit),
        )
        return cur.fetchall()
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
    