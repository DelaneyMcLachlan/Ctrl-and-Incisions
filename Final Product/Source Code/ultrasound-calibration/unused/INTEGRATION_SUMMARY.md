# PLUS ToolKit Integration Summary

## What Has Been Created

A new `ultrasound-calibration` module has been added to integrate PLUS ToolKit for axial calibration functionality.

### Module Structure

```
src/sprint1_product/ultrasound-calibration/
├── __init__.py                    # Module initialization
├── axial_calibration.py          # Main axial calibration class
├── spatial_calibration.py        # Spatial calibration (image-to-probe)
├── README.md                      # Usage documentation
├── INSTALLATION.md               # PLUS ToolKit installation guide
├── example_axial_calibration.py  # Example usage script
└── INTEGRATION_SUMMARY.md        # This file
```

## Key Features

### 1. AxialCalibration Class

Provides axial calibration functionality:
- `calibrate()` - Perform calibration with probe poses and ultrasound images
- `image_to_probe()` - Transform image coordinates to probe space
- `save_calibration()` / `load_calibration()` - Persist calibration results
- Supports multiple calibration phantom types (wire, N-wire, plane, etc.)

### 2. Integration Points

The module is designed to work alongside existing calibration:
- **Hand-eye calibration** (camera-to-tracker transformation)
- **Pivot calibration** (stylus tip position)
- **Intrinsic calibration** (camera parameters)

Together, these enable complete spatial tracking of ultrasound images.

### 3. Flexible Integration

The module supports multiple integration methods:
- **Python bindings** (if available): Direct Python API
- **Command-line tools**: Subprocess calls to PLUS executables
- **Custom implementation**: Placeholder for custom algorithms

## Current Status

### ✅ Completed

- Module structure created
- Axial calibration class with full API
- Spatial calibration class (placeholder)
- Documentation (README, INSTALLATION)
- Example usage script
- Integration with existing calibration workflow

### ⚠️ Pending Implementation

The following require actual PLUS ToolKit installation and API details:

1. **PLUS ToolKit Python bindings integration**
   - Currently raises `ImportError` as placeholder
   - Needs actual PLUS Python API when available

2. **PLUS ToolKit CLI integration**
   - Subprocess calls to PLUS executables
   - Needs actual executable names and command-line arguments
   - File format parsing for calibration results

3. **Calibration algorithms**
   - Wire phantom calibration
   - N-wire phantom calibration
   - Plane calibration
   - Custom phantom calibration

## Next Steps

### Immediate

1. **Install PLUS ToolKit**
   - Follow `INSTALLATION.md` guide
   - Verify installation with example script

2. **Test Integration**
   - Run `example_axial_calibration.py`
   - Verify PLUS ToolKit executables are accessible

3. **Implement Actual Integration**
   - Replace placeholder methods with actual PLUS ToolKit calls
   - Test with real calibration data

### Future Enhancements

1. **Add Temporal Calibration**
   - Time synchronization between ultrasound frames and tracker poses
   - Critical for freehand ultrasound reconstruction

2. **Add Distortion Calibration**
   - Ultrasound probe-specific distortion correction
   - Complement existing camera distortion calibration

3. **Integration with Volume Reconstruction**
   - Use calibrated transformations for 3D volume reconstruction
   - Combine with existing tracking data

## Usage Example

```python
from ultrasound_calibration import AxialCalibration

# Initialize
calibrator = AxialCalibration()

# Calibrate with tracked poses and ultrasound images
calibration_matrix = calibrator.calibrate(
    probe_poses=tracking_data,
    ultrasound_images=image_sequence,
    calibration_phantom="wire_phantom"
)

# Transform image coordinates to probe space
probe_coords = calibrator.image_to_probe(image_coords)

# Save for later use
calibrator.save_calibration("calibration.xml")
```

## Dependencies

- NumPy (already in requirements.txt)
- OpenCV (already in requirements.txt)
- PySide6 (already in requirements.txt)
- PLUS ToolKit (separate installation - see INSTALLATION.md)

## Notes

- The module is designed to be modular and extensible
- Placeholder implementations allow for testing structure before full PLUS integration
- XML/JSON file formats match existing calibration_io.py patterns
- Integration with hand-eye calibration is demonstrated in example script

## References

- PLUS ToolKit: https://github.com/PlusToolkit/PlusLib
- PLUS Documentation: https://plustoolkit.github.io/
- Existing calibration modules: `hand-eye-calibration/`


