# Elbow Sweep .mha Integration Summary

## What We Did

### 1. Updated Code to Use Existing .mha Files
- Modified `calibrate()` method to accept `sequence_file` parameter
- Added `_calibrate_with_sequence_file()` method
- Added `_create_config_for_sequence_file()` method
- Created `use_existing_mha.py` script for testing

### 2. Created Proper Config File Structure
Based on your example config, we now generate configs with:
- ✅ **DataCollection with DeviceSet** (correct structure)
- ✅ **SavedDataSource device** (points to .mha file)
- ✅ **PhantomDefinition** (required element)
- ✅ **vtkPlusProbeCalibrationAlgo** (required element)
- ✅ **Segmentation** (with all required attributes)

### 3. Integrated Your Elbow Sweep File
- File: `ElbowUltrasoundSweep.mha`
- Size: 6.70 MB
- Contains: 40 frames (820x616 pixels each)
- Has tracking data: `ProbeToTrackerTransform`, `ReferenceToTrackerTransform`, `StylusToTrackerTransform`

## Current Status

### ✅ Working
- Config file is created correctly
- Config file is read by ProbeCalibration
- Sequence file is found and referenced
- All required XML elements are present
- Segmentation warnings are resolved

### ❌ Not Working
- **ProbeCalibration crashes** (exit code: 3221226505 - Windows access violation)

## The Problem

**ProbeCalibration is crashing** after reading the config file. This could be because:

1. **Data Type Mismatch**: 
   - Your `.mha` file is an **elbow sweep** (clinical ultrasound data)
   - ProbeCalibration expects **calibration phantom data** (N-wire, wire phantom, etc.)
   - The images need to contain visible calibration phantom features (wires, fiducials)

2. **Phantom Definition Mismatch**:
   - We're using a generic wire phantom definition
   - Your images might not contain this phantom
   - Or the phantom geometry doesn't match what's in the images

3. **Coordinate Frame Issues**:
   - The transforms in your .mha file use specific coordinate frames
   - The config might need different coordinate frame mappings

## Important Note

**ProbeCalibration is designed for calibration phantoms**, not general ultrasound scans. An "elbow sweep" is likely:
- Clinical/anatomical ultrasound data
- Not calibration phantom data
- May not be suitable for probe calibration

## What You Need for Calibration

To use ProbeCalibration, you need:
1. **Calibration phantom images** (N-wire, wire phantom, etc.)
2. **Tracking data** for each image (probe poses)
3. **Known phantom geometry** (wire positions, etc.)

## Solutions

### Option 1: Use Calibration Phantom Data
If you have calibration phantom images:
- Use those instead of the elbow sweep
- Update phantom definition to match your phantom
- Run calibration

### Option 2: Check if Elbow Sweep Has Phantom
If your elbow sweep actually contains a calibration phantom:
- Verify phantom is visible in images
- Update phantom definition to match
- Adjust segmentation parameters

### Option 3: Different Calibration Approach
If this is not calibration data:
- Use different calibration method
- Or use PLUS ToolKit's GUI tools
- Or implement custom calibration algorithm

## How to Use the Updated Code

### Method 1: Direct Sequence File
```python
from ultrasound_calibration import AxialCalibration

calibrator = AxialCalibration(
    plus_toolkit_path=r"C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin"
)

# Use existing .mha file
calibration_matrix = calibrator.calibrate(
    sequence_file="ElbowUltrasoundSweep.mha",
    calibration_phantom="wire_phantom"
)
```

### Method 2: Using the Script
```powershell
cd src\sprint1_product\ultrasound-calibration
python use_existing_mha.py
```

## Files Modified

1. **axial_calibration.py**:
   - Added `sequence_file` parameter to `calibrate()`
   - Added `_calibrate_with_sequence_file()` method
   - Added `_create_config_for_sequence_file()` method

2. **use_existing_mha.py** (new):
   - Script to test calibration with existing .mha files
   - Creates proper config files
   - Runs ProbeCalibration

## Next Steps

1. **Verify your data**: Is the elbow sweep actually calibration phantom data?
2. **Check images**: Do the images contain visible calibration features?
3. **Update phantom definition**: Match the actual phantom in your images
4. **Try with calibration data**: Use actual calibration phantom images if available

## Questions to Answer

1. **Is this calibration data?** Does the elbow sweep contain a calibration phantom?
2. **What phantom type?** N-wire, wire, plane, or other?
3. **Phantom geometry?** What are the actual wire/feature positions?

Once we know this, we can update the phantom definition and segmentation parameters to match your actual data.

