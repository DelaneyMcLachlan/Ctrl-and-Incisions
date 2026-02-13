# Sprint 2 -- Feature Documentation (What Was Built)

## 1. Live Data Acquisition Integration

### PlusServer Device Integration

Integrated live hardware acquisition using **PlusServer**.

Configured `PlusDeviceSet` XML for: - Ultrasound device input (2D B-mode
frames) - NDI Aurora tracker input (6-DOF tool pose) - Timestamp
synchronization - Transform hierarchy configuration

Enabled: - Direct device capture through laptop-connected hardware -
Real-time merging of ultrasound frames and tracking poses - Stable
logging of synchronized data streams

Validated: - Active tool detection - Port configuration - Device
connection stability - Log file inspection for debugging

------------------------------------------------------------------------

## 2. Tracked Data Recording Pipeline

### .mha Sequence Generation

Configured PlusServer to record tracked ultrasound sequences into `.mha`
files.

Each generated `.mha` contains: - 2D ultrasound image frames - Per-frame
6-DOF tracking transforms - Timestamp metadata - Calibration transform
placeholders - Device metadata and sequence headers

Tested: - Synthetic and live tracking cases - Proper transform injection
into frame metadata - Consistent frame-to-pose alignment

Result: System now produces tracked ultrasound sequences suitable for
downstream reconstruction.

------------------------------------------------------------------------

## 3. Offline 3D Volume Reconstruction

### VolumeReconstructor Pipeline

Integrated offline reconstruction using **PlusToolkit
VolumeReconstructor**.

Workflow: TrackedUltrasoundSequence.mha → VolumeReconstructor →
Reconstructed 3D Volume

Configured: - Output spacing parameters - Reconstruction grid
dimensions - Interpolation settings

Validated: - Volume bounding box correctness - Frame accumulation into
voxel grid - Output volume format compatibility

Reconstruction now generates: - 3D volumetric dataset - Suitable for
visualization and further processing

------------------------------------------------------------------------

## 4. VTK-Based Visualization

### 2D + 3D Rendering Integration

Extended application to load and render: - Raw tracked `.mha`
sequences - Reconstructed 3D volumes

Implemented VTK rendering pipeline: - vtkImageData loading - Slice
viewers - Volume ray casting (where applicable) - Adjustable
visualization parameters

Improved: - Separation between data loading and rendering logic -
Stability when switching between 2D sequence and 3D volume modes

System now supports: - Viewing tracked ultrasound frames - Viewing
reconstructed volumetric output - Debugging spatial consistency of
tracking data

## 5. ArUco Stylus Tracking

### ArucoStylusTracker  

Implements ArUco-based 6-DOF pose estimation from a camera frame.

**Functionality:**
- Detects ArUco markers
- Estimates pose using camera intrinsics
- Returns 4×4 homogeneous transform (marker → camera frame)
- Draws marker + axes for visualization

Includes optional marker ID filtering and 3D → 2D projection utility.


# Summary of Sprint 2 Deliverable

Sprint 2 successfully delivered a functional tracked ultrasound
acquisition and reconstruction pipeline. The system can now:

-   Capture live ultrasound and tracking data from physical devices\
-   Synchronize and record tracked sequences into `.mha` format\
-   Perform offline 3D volume reconstruction\
-   Render both 2D tracked frames and reconstructed volumes using VTK


