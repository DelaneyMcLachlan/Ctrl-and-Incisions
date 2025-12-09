# Execution Flow Script -- Sprint 1 Prototype

This script outlines how the Sprint 1 Hand-Eye Calibration prototype is
executed, what components are involved, and how data flows through the
system.


## 1. Prerequisites

-   All required Python packages installed (see `README.md` and
    `requirements.txt`).
-   Local environment configured (virtual environment recommended).
-   SQLite database file will be created/initialized automatically on
    first run by the tracking database module.

## 2. Launching the System

1.  Open a terminal in the project root directory.

2.  Activate the Python environment (if applicable).

3.  Run the main application:

    ``` bash
    python run_hand_eye_calibration.py
    ```

4.  The Qt-based UI window for the Hand-Eye Calibration tool will
    appear.


## 3. Startup & Initialization Flow

When `run_hand_eye_calibration.py` is executed, the following sequence
occurs:

1.  **Application bootstrap**
    -   Loads core modules for:
        -   UI (Qt Designer--based interface)
        -   Camera handling and overlay rendering
        -   Tracking database backend
        -   FakeTracker / synthetic data stream
2.  **Database initialization**
    -   SQLite database backend is initialized.
    -   Database schema is created if it does not exist, including
        tables for:
        -   `Devices`
        -   `Sessions`
        -   `PoseSamples` (6-DOF pose samples)
    -   Foreign key enforcement is enabled.
    -   Helper functions for:
        -   Creating new sessions
        -   Logging pose samples
        -   Retrieving pose samples are registered and ready for use.
3.  **UI setup**
    -   The updated Qt Designer layout is loaded (including Sprint 1 UI
        changes).
    -   Components are arranged according to calibration steps.
    -   Step 6 layout, scrolling, and status bar logic are configured.
    -   Icons and logos are loaded from the `assets` folder (if
        applicable).
4.  **Camera & overlay modules**
    -   `CameraController` is initialized to manage camera input.
    -   `OverlayRenderer` is initialized to render overlays on top of
        the camera feed.
    -   Any required connections between the UI, CameraController, and
        OverlayRenderer are established.
5.  **Tracking source selection**
    -   For Sprint 1, the system is configured to use the
        **FakeTracker**:
        -   Generates synthetic 6-DOF pose data.
        -   Allows development and testing without physical tracking
            hardware.

## 4. Execution / Runtime Flow

Once the system is running and the UI is visible, the typical execution
flow is:

1.  **User starts a tracking session**
    -   User navigates to the relevant step in the UI and chooses to
        start a new session.
    -   A new session entry is created in the SQLite database via helper
        functions.
    -   Session metadata is stored (e.g., timestamp, device reference).
2.  **Synthetic tracking data generation**
    -   FakeTracker begins generating 6-DOF pose samples at a configured
        rate.
    -   Each pose sample includes position and orientation values and a
        timestamp.
3.  **Data logging to database**
    -   For each generated pose sample:
        -   The pose data is logged into the `PoseSamples` table.
        -   Each sample is linked to the active session via a foreign
            key.
    -   Helper functions ensure consistent insertion and retrieval of
        tracking data.
4.  **Camera view and overlay rendering**
    -   CameraController captures frames from the camera (or test
        input).
    -   OverlayRenderer draws calibration-related overlays onto the
        video feed.
    -   The combined result is displayed in the UI so the user can
        observe the tracking behavior and overlays in real time.
5.  **User interaction through UI steps**
    -   User proceeds through the calibration steps in the updated UI:
        -   Navigating steps using the designed layout.
        -   Observing status updates in the status bar (including fixes
            from Sprint 1).
    -   Any actions in the UI that require tracking or logging interact
        with:
        -   FakeTracker (for synthetic pose data)
        -   SQLite backend (for reading/writing session data)

## 5. Ending a Session & Shutting Down

1.  **Ending a tracking session**
    -   User completes the calibration step or manually stops the
        session.
    -   No new pose samples are logged once the session is stopped.
    -   Session remains stored in the database and can be queried via
        helper functions.
2.  **Application shutdown**
    -   User closes the main UI window.
    -   CameraController stops video capture.
    -   FakeTracker stops generating data.
    -   Database connections are gracefully closed (if applicable).
    -   The application process exits.

## 6. Summary of Execution Flow

High-level sequence:

1.  Run `python run_hand_eye_calibration.py`.
2.  Initialize UI, database, FakeTracker, CameraController, and
    OverlayRenderer.
3.  User starts a new session via the UI.
4.  FakeTracker generates synthetic 6-DOF data.
5.  Pose samples are logged into the SQLite database and visualized via
    camera + overlay.
6.  User completes the calibration steps and ends the session.
7.  System stops tracking, closes resources, and exits cleanly.
