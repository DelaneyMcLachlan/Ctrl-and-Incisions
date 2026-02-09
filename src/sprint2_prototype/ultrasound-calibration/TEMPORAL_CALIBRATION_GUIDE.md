# Temporal Calibration Guide

## What is Temporal Calibration?

**Temporal calibration** determines the **time offset** between:
- **Ultrasound image timestamps** (when the image was acquired)
- **Tracking system timestamps** (when the pose was recorded)

This is essential for **synchronizing** the two data streams when reconstructing 3D volumes from freehand ultrasound scans.

## How It Works

### Key Difference from Spatial Calibration

**Spatial Calibration:**
- Uses **one data source** with both images and tracking data combined
- Determines the **spatial transformation** (image coordinates → probe coordinates)
- Config uses: `UseData="IMAGE_AND_TRANSFORM"` in a single device

**Temporal Calibration:**
- Uses **two separate data sources** (tracking and video)
- Determines the **time offset** between the two streams
- Config uses:
  - `TrackerDeviceSavedDataset` with `UseData="TRANSFORM"` (tracking only)
  - `VideoDeviceSavedDataset` with `UseData="IMAGE"` (video only)

### Why Two Separate Sources?

Temporal calibration needs to compare timestamps from two independent systems:
1. **Tracking system** - Records probe poses with its own clock
2. **Ultrasound system** - Records images with its own clock

By having them in separate files with their original timestamps, the calibration algorithm can:
- Detect the time offset between the two clocks
- Synchronize the data streams for accurate 3D reconstruction

## How to Run Temporal Calibration

### Option 1: Using Command Line Arguments (Recommended)

```powershell
cd src\sprint1_product\ultrasound-calibration
python test_simulated_calibration.py --type temporal
```

### Option 2: Direct Function Call

```python
from test_simulated_calibration import run_simulated_calibration

config_file = r"C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\config\PlusDeviceSet_fCal_Sim_TemporalCalibration.xml"
run_simulated_calibration(config_file, calibration_type="temporal")
```

### Option 3: Auto-Detect from Config Filename

```python
# The script will auto-detect "temporal" from the filename
config_file = r"C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\config\PlusDeviceSet_fCal_Sim_TemporalCalibration.xml"
run_simulated_calibration(config_file)  # calibration_type="auto" by default
```

## What the Script Does Differently for Temporal Calibration

1. **Detects calibration type** from config filename or parameter
2. **Finds multiple sequence files** - Temporal configs have 2+ sequence files (tracking + video)
3. **Skips --calibration-seq-file** - Temporal calibration uses sequence files specified in the config, not command line
4. **Names output files** with calibration type: `temporal_calibration_result_[timestamp].xml`

## Expected Output

When temporal calibration succeeds, you'll get:
- **Output file**: `calibration_output/temporal_calibration_result_[timestamp].xml`
- **Contains**: Time offset value (in seconds) between ultrasound and tracking systems
- **Usage**: Apply this offset when synchronizing data streams for 3D reconstruction

## Example Output Structure

The output XML will contain something like:
```xml
<TemporalCalibration>
  <TimeOffsetSec>0.0234</TimeOffsetSec>  <!-- Time difference in seconds -->
  <!-- Other calibration parameters -->
</TemporalCalibration>
```

## Troubleshooting

### Issue: "Sequence file not found"
- **Cause**: The config references sequence files that don't exist
- **Solution**: Check that the sequence files exist in the PLUS data directory
- **Note**: Temporal calibration needs BOTH tracking and video sequence files

### Issue: "Unable to find required element"
- **Cause**: Config file missing required XML elements
- **Solution**: The script now checks for required elements and warns you

### Issue: Calibration fails
- **Check logs**: Look in `calibration_output/logs/` for detailed error messages
- **Compare configs**: Temporal config structure differs from spatial - this is normal
- **Verify data**: Ensure both sequence files have valid timestamps

## Comparison: Spatial vs Temporal

| Aspect | Spatial Calibration | Temporal Calibration |
|--------|---------------------|----------------------|
| **Purpose** | Image → Probe transformation | Time synchronization |
| **Data Sources** | 1 file (images + tracking) | 2 files (tracking + video) |
| **Output** | 4x4 transformation matrix | Time offset (seconds) |
| **Config Devices** | Single `SavedDataSource` | Two `SavedDataSource` devices |
| **Command Line** | May use `--calibration-seq-file` | Uses config-specified files |

## Next Steps

1. **Run temporal calibration**: `python test_simulated_calibration.py --type temporal`
2. **Check output**: Look for `temporal_calibration_result_*.xml` in `calibration_output/`
3. **Use the time offset**: Apply it when synchronizing your data streams
4. **Combine with spatial**: You typically need BOTH spatial and temporal calibration for accurate 3D reconstruction

## Additional Resources

- PLUS ToolKit documentation on temporal calibration
- Your advisor's notes on temporal calibration procedure
- Example temporal calibration configs in PLUS installation



