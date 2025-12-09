# **Sprint 1 -- Feature Documentation (What Was Built)**

## **1. Tracking & Data Infrastructure**

### **SQLite Database Backend**

-   Implemented full SQLite backend for Sprint 1 prototype.
-   Designed initial **database schema**:
    -   **Devices** table\
    -   **Sessions** table\
    -   **PoseSamples** table (6-DOF pose data)
-   Added database initialization script:
    -   Enforces **foreign key constraints**
    -   Creates tables on first run
-   Added helper functions:
    -   Create new tracking sessions
    -   Log pose samples into DB
    -   Retrieve pose samples programmatically
-   Fixed compatibility issues and cleaned up DB module for stability.
-   Added documentation for the DB module to support maintainability.
-   Tested schema with placeholder/synthetic pose logging.

## **2. Tracking Pipeline Enhancements**

### **FakeTracker System (Remote Development Support)**

-   Implemented **FakeTracker** module generating synthetic 6-DOF
    tracking data.
-   Added GUI integration so the app behaves as if real hardware is
    connected.
-   Enables team to continue work remotely without physical trackers.
-   Integrated synthetic data stream into end-to-end workflow for Sprint
    1.

### **Camera & Overlay System Modularization**

-   Refactored monolithic OverlayApp into two clean modules:
    -   **CameraController** -- camera handling, frame capture\
    -   **OverlayRenderer** -- draws overlays and visual aids\
-   Improves readability, maintainability, and future extension for
    calibration tasks.

## **3. UI & Frontend Improvements**

-   Updated Qt Designer UI layout:
    -   Reordered components
    -   Improved structure for calibration steps
-   Updated generated UI files to reflect new Designer changes.
-   Fixed Step 6 UI layout:
    -   Scroll behavior corrected\
    -   Status bar logic improved\
-   Added **assets folder** (icons, logos) for consistent UI visuals.

## **4. Documentation & Team Artifacts**

-   Added full **README.md** with project setup and run instructions.
-   Added general prototype launch workflow applicable to all team
    members.
-   Updated:
    -   **Sprint 1 and Sprint 2 readiness documents**
    -   **Backlog, Roadmap, and RACI chart**
    -   **Team Charter** to reflect new task assignments.
-   Added architecture update:
    -   Updated diagram to include database layer, UI changes, and
        remote data streaming flow.

## **5. Integration & Merging**

-   Multiple PR merges incorporating contributions from:
    -   Database development\
    -   UI updates\
    -   Architecture documentation\
    -   Code refactoring (as part of modularization)\
-   Ensured Sprint 1 slice is functional: data generation → tracking
    pipeline → UI visualization → database logging.


## **Summary of Sprint 1 Deliverable**

Sprint 1 successfully delivered a **functional vertical slice** of the
Hand-Eye Calibration system, including synthetic tracking support,
modularized core components, a persistent data backend, and a stable UI
foundation. The system can now:\
- Generate and visualize 6-DOF tracking data\
- Capture synthetic pose data\
- Store data in a structured SQLite backend\
- Support ongoing UI development and future calibration algorithms
