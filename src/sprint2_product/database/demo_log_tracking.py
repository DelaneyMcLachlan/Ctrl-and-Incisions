"""
Demo script to show the tracking databse in action

- Initializes the SQLite database
- Creates a demo tracking session
- Logs 10 fake 6-DOF pose samples
- Prints how many samples were stored
- Shows recent sessions
"""

import random
import time

from db import (
    init_db,
    start_tracking_session,
    log_pose,
    get_recent_sessions,
    get_connection,
)

def main() -> None:
    print("=== Ctrl + Incision DB Demo ===")

    # Make sure tables exist
    print ("Initializing database...")
    init_db()

    # Start a demo tracking session
    session_id = start_tracking_session("Demo Tracker", "Sprint 1 DB demo run")
    print(f"Created tracking session with id={session_id}")

    # Log 10 fake pose samples
    print("Logging 10 fake pose samples...")
    for i in range(10):
        tx = random.uniform(-100.0, 100.0)
        ty = random.uniform(-100.0, 100.0)
        tz = random.uniform(-100.0, 100.0)
        rx = random.uniform(-3.14, 3.14)
        ry = random.uniform(-3.14, 3.14)
        rz = random.uniform(-3.14, 3.14)

        log_pose(session_id, tx, ty, tz, rx, ry, rz)
        print(f"  -> Logged pose {i + 1}")

        # small sleep to mimic a stream
        time.sleep(0.05)

    # Check how many rows were stored for this session
    conn = get_connection()
    try:
        cur = conn.execute(
            "SELECT COUNT(*) FROM pose_samples WHERE session_id = ?",
            (session_id,),
        )
        (count,) = cur.fetchone()
    finally:
        conn.close()

    print(f"Total poses stored for session {session_id}: {count}")

    # Show recent sessions with their metadata
    print("\nRecent sessions:")
    for row in get_recent_sessions():
        session_id, device_name, started_at, ended_at, description = row
        print(
            f"  session_id={session_id}, device='{device_name}', "
            f"started_at={started_at}, ended_at={ended_at}, desc='{description}'"
        )
    
    print("\nDemo complete. Data is now persisted in ctrl_incision.db.")

if __name__ == "__main__":
    main()