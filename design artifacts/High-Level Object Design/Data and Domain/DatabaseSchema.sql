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