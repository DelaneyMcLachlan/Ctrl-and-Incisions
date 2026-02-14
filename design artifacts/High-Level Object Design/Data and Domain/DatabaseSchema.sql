-- Ctrl + Incision Database Schema
-- Sprint 1: Tracking & 6-DOF Logging

CREATE TABLE tracking_devices (
    device_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT,
    connection_info TEXT
);

CREATE TABLE tracking_sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    description TEXT,
    FOREIGN KEY (device_id) REFERENCES tracking_devices(device_id)
);

CREATE TABLE pose_samples (
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
