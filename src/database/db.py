import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "ctrl_incision.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

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


