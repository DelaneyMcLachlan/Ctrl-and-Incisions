# Ultrasound Calibration Module

This module integrates PLUS ToolKit for ultrasound probe calibration, specifically for **axial calibration**.

## Overview

Axial calibration is used to determine the relationship between ultrasound image coordinates and the physical probe coordinate system. This is essential for accurate 3D reconstruction from freehand ultrasound scans.

## PLUS ToolKit Integration

PLUS (Public software Library for UltraSound) is a medical imaging toolkit that provides tools for:
- Ultrasound probe calibration (axial, lateral, temporal)
- Spatial calibration (image-to-probe transformation)
- Temporal calibration (time synchronization)
- Volume reconstruction

### Installation

PLUS ToolKit can be integrated in several ways:

1. **Python bindings** (if available via pip):
   ```bash
   pip install plustoolkit
   ```

2. **C++ library with Python bindings** (requires building from source):
   - Download from: https://github.com/PlusToolkit/PlusLib
   - Follow build instructions for Python bindings
   - Or use pre-built binaries if available

3. **Subprocess calls** to PLUS executables:
   - Use PLUS command-line tools via Python subprocess
   - Requires PLUS to be installed and in PATH

### Dependencies

- NumPy
- OpenCV (for image processing)
- VTK (for visualization, if needed)
- PLUS ToolKit (C++ library or Python bindings)

## Usage

```python
from ultrasound_calibration import AxialCalibration

# Initialize axial calibration
calibrator = AxialCalibration()

# Run calibration with tracked probe poses and ultrasound images
calibration_matrix = calibrator.calibrate(
    probe_poses=tracking_data,
    ultrasound_images=image_sequence,
    calibration_phantom="wire_phantom"  # or "n-wire", "plane", etc.
)

# Apply calibration to transform image coordinates to probe space
probe_coords = calibrator.image_to_probe(image_coords, calibration_matrix)
```

## Calibration Methods

This module supports various axial calibration methods:
- **Wire phantom calibration** (single or multiple wires)
- **N-wire phantom calibration**
- **Plane calibration**
- **Custom phantom calibration**

## Integration with Existing Calibration

This module works alongside:
- **Hand-eye calibration** (camera-to-tracker transformation)
- **Pivot calibration** (stylus tip position)
- **Intrinsic calibration** (camera parameters)

Together, these calibrations enable complete spatial tracking of ultrasound images in 3D space.

## References

- PLUS ToolKit Documentation: https://plustoolkit.github.io/
- PLUS GitHub: https://github.com/PlusToolkit/PlusLib
- Axial Calibration Theory: See medical imaging literature on ultrasound probe calibration


