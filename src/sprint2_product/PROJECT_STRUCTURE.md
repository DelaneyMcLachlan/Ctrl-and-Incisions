# Sprint 2 Product — Project Structure

This document describes the recommended folder structure for the project, what each file does, and where new files should be created as the project grows.

---

## Directory Tree

```
sprint2_product/
│
├── main.py
│
├── pages/
│   ├── landing_page.py
│   ├── ultrasound_recording_page.py        
│   ├── ultrasound_viewer_page.py
│   ├── stylus_overlay_page.py
│   └── stylus_tracker_page.py
│
├── core/
│   ├── ultrasound/
│   │   ├── recording_controller.py        
│   │   └── mha_viewer.py
│   └── stylus/
│       ├── aruco_tracker.py
│       ├── calibration_solver.py
│       └── calibration_io.py
│
├── data/
│   ├── recordings/                        
│   └── calibrations/
│
├── config/
│   └── plus_toolkit_config.py
│
├── assets/
│   └── icons/
│
└── requirements.txt
```

---

## File Descriptions

### Root

| File | Description |
|------|-------------|
| `main.py` | Application entry point. Initializes the Qt application and launches the landing page. |
| `requirements.txt` | Python dependencies list (PySide6, VTK, OpenCV, numpy, etc.). |

---

### `pages/` — UI Pages

All interface screens live here. Each file is a `QWidget` or `QMainWindow` subclass representing one screen of the application. No business logic should live in these files — they only handle layout, user interaction, and calling into `core/`.

| File | Origin | Description |
|------|--------|-------------|
| `landing_page.py`  The main home screen of the application. Acts as the central navigation hub, routing the user to either the ultrasound recording/viewing workflow or the stylus calibration workflow. |
| `ultrasound_recording_page.py`  Dedicated page for recording a tracked ultrasound sequence. Features Start and Stop buttons that trigger the PlusToolkit executable as a subprocess. Once a recording is complete, the user is given the option to save the output `.mha` file to `data/recordings/`. |
| `ultrasound_viewer_page.py` | Renamed from `view_mha_gui.py` | Full 3D viewer for `.mha` volume files. Contains a file browser sidebar (local file picker + sample file list), visualization controls (opacity, brightness, color/opacity presets for ultrasound and CT/MRI modalities), and an interactive VTK render window with camera controls. Calls into `core/ultrasound/mha_viewer.py` for all file loading and rendering logic. |
| `stylus_overlay_page.py` | Renamed from `OverlayApp.py` | Menu/overlay page for the stylus calibration workflow. Acts as a launcher and status display for the stylus tracking process, embedding the live camera feed and providing controls to start the ArUco-based tracking session. |
| `stylus_tracker_page.py` | From `QVTKViewer.py` / `run_hand_eye_calibration.py` | The main interface for the hand-eye calibration workflow. Hosts the VTK 3D tracker viewport alongside the live camera feed. Walks the user through the step-by-step calibration process: connecting the tracker, running pivot calibration, capturing image/tracking pairs, computing the extrinsic matrix, and saving results. Also manages continuous capture sessions with start/stop controls and logs events to the database. |

---

### `core/` — Business Logic & Backend Processes

Contains all processing, computation, and I/O logic. Files here are pure Python with no UI code. Split by feature domain.

#### `core/ultrasound/`

| File | Origin | Description |
|------|--------|-------------|
| `recording_controller.py`  Manages the lifecycle of a PlusToolkit recording session. Launches the PlusToolkit executable as a subprocess, monitors its output, handles start/stop signals from the UI, and receives the output `.mha` file path when the recording ends. Also handles saving the file to `data/recordings/`. |
| `mha_viewer.py` | Renamed from `view_mha_volume.py` | Core VTK utility library for `.mha` files. Provides `find_available_mha_files()` to scan known locations for `.mha` files, `load_mha_file()` to read a file using VTK's MetaImage reader (returns volume dimensions, spacing, scalar range), and `create_volume_renderer()` to build a VTK volume with opacity and color transfer functions. Also includes `create_slice_viewer()` for 2D axial/coronal/sagittal slices and a `FileScrollerInteractorStyle` for keyboard-based file navigation. |

#### `core/stylus/`

| File | Origin | Description |
|------|--------|-------------|
| `aruco_tracker.py` | From `ArucoStylusTracker.py` | Self-contained ArUco marker tracker. Wraps OpenCV's ArUco detector to track a specific marker by ID in real-time from a camera frame. Given camera intrinsics (`K`, `dist`), it detects the marker, estimates its 6-DOF pose using `estimatePoseSingleMarkers`, draws the axes overlay on the frame, and returns a 4×4 homogeneous transform matrix (rotation + translation). Also provides `project_point()` to project a 3D camera-space point back to 2D pixel coordinates. |
| `calibration_solver.py` | From `calibration_solver.py` | Implements the hand-eye calibration mathematics. `solve_hand_eye_p2l()` solves for the extrinsic matrix (rotation + translation) using Point-to-Line registration between 3D tracker-space coordinates and 2D image-space pixel locations. Also provides three validation error metrics: `compute_reprojection_error()` (pixel-level error), `compute_distance_error()` (perpendicular distance from a 3D point to a camera ray), and `compute_angular_error()` (angle in degrees between the point vector and ray). |
| `calibration_io.py` | From `calibration_io.py` | Handles all calibration file reading and writing using Qt's XML stream API and Python's CSV module. **Readers:** `readIntCalFromXml()` (intrinsic matrix + distortion coefficients), `readTrackingFromXml()` (tracker positions and rotation matrices), `readPivotCalFromXml()` (4×4 pivot calibration matrix), `readHECalibrationFromXml()` (full hand-eye calibration: intrinsic + distortion + extrinsic). **Writers:** matching `write*ToXml()` functions for each of the above, plus `writeErrToCsv()` to export per-frame pixel, distance, and angular errors to a CSV file. |

---

### `data/` — Persistent Storage

Stores all output files generated during sessions. These folders should be treated as a local database and should not contain code.

| Folder | Description |
|--------|-------------|
| `data/recordings/` Destination for `.mha` files captured via the ultrasound recording workflow. Files are saved here after the PlusToolkit executable finishes and the user confirms the save action from `ultrasound_recording_page.py`. |
| `data/calibrations/` | Output files from the hand-eye calibration workflow: intrinsic XML, pivot calibration XML, full hand-eye calibration XML, and error CSVs. Mirrors the existing `calibration_output/` folder. |

---

### `config/` — Configuration

| File | Origin | Description |
|------|--------|-------------|
| `plus_toolkit_config.py` | From `plus_toolkit_config.py` | Utility that resolves the PlusToolkit installation path (via the `PLUS_TOOLKIT_PATH` environment variable or a known default), locates the `PlusLibData/TestImages` directory for sample `.mha` files, and exposes helper functions consumed by both `mha_viewer.py` and `recording_controller.py`. |

---

### `assets/` — Static Resources

| Folder | Description |
|--------|-------------|
| `assets/icons/` | UI icons referenced by the pages (e.g., capture, settings, play/pause, adjust icons). Currently used in `stylus_tracker_page.py` to decorate toolbar buttons and the application logo. |

---

## Mapping: Old Filenames → New Locations

| Old File | New Location |
|----------|--------------|
| `view_mha_gui.py` | `pages/ultrasound_viewer_page.py` |
| `view_mha_volume.py` | `core/ultrasound/mha_viewer.py` |
| `OverlayApp.py` | `pages/stylus_overlay_page.py` |
| `QVTKViewer.py` | `pages/stylus_tracker_page.py` |
| `run_hand_eye_calibration.py` | Merged into `main.py` (entry point logic only) |
| `ArucoStylusTracker.py` | `core/stylus/aruco_tracker.py` |
| `calibration_solver.py` | `core/stylus/calibration_solver.py` |
| `calibration_io.py` | `core/stylus/calibration_io.py` |
| `plus_toolkit_config.py` | `config/plus_toolkit_config.py` |
| `calibration_output/` | `data/calibrations/` |

---

## New Files Required

| File | Purpose |
|------|---------|
| `main.py` | App entry point — replaces `run_hand_eye_calibration.py` with proper routing to landing page |
| `pages/landing_page.py` | Main menu / home screen |
| `pages/ultrasound_recording_page.py` | Start/stop recording UI + PlusToolkit subprocess trigger |
| `core/ultrasound/recording_controller.py` | PlusToolkit process management + `.mha` file handling |
| `data/recordings/` | Folder (database) for saved `.mha` recording files |