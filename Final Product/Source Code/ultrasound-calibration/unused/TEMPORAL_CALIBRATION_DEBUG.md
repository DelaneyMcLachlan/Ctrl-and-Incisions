# Temporal Calibration Debugging Guide

## What is Temporal Calibration?

Temporal calibration determines the **time offset** between:
- Ultrasound image acquisition timestamps
- Tracking system timestamps

This is critical for synchronizing data streams when reconstructing 3D volumes from freehand ultrasound scans.

## Common Issues with Temporal Calibration

### 1. **Different Tool Required**
Temporal calibration might require a **different executable** than `ProbeCalibration.exe`:
- `ProbeCalibration.exe` - Typically for spatial calibration
- `TemporalCalibration.exe` or similar - May be needed for temporal calibration
- Check PLUS ToolKit bin directory for temporal-specific tools

### 2. **Different Command-Line Arguments**
Temporal calibration may need different parameters:
- May not need `--calibration-seq-file` (uses different data source)
- May need `--temporal-calibration` flag
- May require different config structure

### 3. **Config File Structure Differences**
Temporal calibration configs may have:
- Different algorithm elements (not `vtkPlusProbeCalibrationAlgo`)
- Different device types (may need real-time data source, not `SavedDataSource`)
- Different coordinate frame requirements

### 4. **Data Requirements**
Temporal calibration typically needs:
- **Two synchronized data streams** (ultrasound + tracking)
- **Time-stamped data** from both sources
- **Motion data** (moving probe/phantom) to detect timing differences

## How to Debug

### Step 1: Check the Error Logs
After running the script, check the log files in:
```
calibration_output/logs/
  - stdout_[timestamp].txt
  - stderr_[timestamp].txt
```

Look for specific error messages like:
- "Unable to find..." - Missing XML element
- "No reader for file..." - File format issue
- "Failed to..." - Specific operation failure

### Step 2: Verify Config File Structure
The script now automatically checks for:
- ✓ PhantomDefinition
- ✓ vtkPlusProbeCalibrationAlgo
- ✓ DataCollection
- ✓ DeviceSet

If any are missing, that's likely the issue.

### Step 3: Compare with Working Spatial Config
Compare the temporal config with the working spatial config:
```powershell
# View both configs side-by-side
notepad "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\config\PlusDeviceSet_fCal_Sim_SpatialCalibration_2.0.xml"
notepad "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\config\PlusDeviceSet_fCal_Sim_TemporalCalibration.xml"
```

Look for differences in:
- Algorithm elements
- Device types
- Required sections

### Step 4: Check PLUS ToolKit Documentation
Look for temporal calibration examples in:
- PLUS ToolKit documentation
- Example config files in the config directory
- README files in the PLUS installation

### Step 5: Try Different Tools
Check if there's a temporal-specific calibration tool:
```powershell
cd C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin
dir *Temporal*.exe
dir *Calibration*.exe
```

## Quick Fixes to Try

### Fix 1: Check if Temporal Calibration Uses Different Tool
```powershell
# List all calibration-related executables
cd C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin
Get-ChildItem *Calibration*.exe
```

### Fix 2: Try Without Sequence File
Temporal calibration might not need `--calibration-seq-file`:
```python
# In test_simulated_calibration.py, try:
run_simulated_calibration(config_file, sequence_file=None)
```

### Fix 3: Check Config File for Temporal-Specific Elements
Open the temporal config and look for:
- `<TemporalCalibration>` elements
- Different algorithm names
- Real-time device types instead of `SavedDataSource`

## Next Steps

1. **Run the enhanced script** - It will now show detailed error analysis
2. **Check the log files** - Full error output is saved
3. **Compare configs** - See what's different between spatial and temporal
4. **Check PLUS documentation** - Look for temporal calibration examples
5. **Ask your advisor** - They may know the specific requirements

## Expected Output

If temporal calibration succeeds, you should see:
- Exit code: 0
- Output config file created in `calibration_output/`
- Temporal offset value in the output XML

If it fails, the enhanced script will now show:
- Specific error patterns detected
- Missing elements
- Log file locations for detailed analysis

