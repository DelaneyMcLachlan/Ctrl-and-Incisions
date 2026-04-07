# Temporal Calibration Report

## Overview

This report documents how **Temporal Calibration** works in PLUS ToolKit, what it does, and what outputs it produces.

## What is Temporal Calibration?

**Temporal calibration** determines the **time offset (lag)** between:
- **Ultrasound image acquisition timestamps** (when the ultrasound system captured the image)
- **Tracking system timestamps** (when the tracking system recorded the probe pose)

This time offset is critical for **synchronizing** the two data streams when reconstructing 3D volumes from freehand ultrasound scans. Without proper temporal calibration, images and poses won't be correctly aligned in time, leading to inaccurate 3D reconstructions.

## How TemporalCalibration.exe Works

### Algorithm Overview

TemporalCalibration.exe uses a **cross-correlation-based approach**:

1. **Extracts position signals** from both data streams:
   - From **video sequence**: Detects lines/features in ultrasound images and tracks their position over time
   - From **tracking sequence**: Extracts probe position from tracking transforms over time

2. **Computes cross-correlation** between the two position signals:
   - Shifts one signal in time relative to the other
   - Finds the time offset that produces maximum correlation

3. **Outputs the time offset** (tracker lag) in seconds

### Internal Process (from STDERR analysis)

Based on the error messages and code references, the process involves:

1. **Line Segmentation** (`vtkLineSegmentationAlgo`):
   - Detects lines/features in ultrasound video frames
   - Used to compute position signal from video data
   - **Warning**: Low line detection rate is common but doesn't prevent calibration

2. **Signal Extraction** (`vtkTemporalCalibrationAlgo`):
   - Extracts position signals from both fixed and moving sequences
   - Computes cross-correlation to find optimal time offset
   - Validates that signals vary sufficiently (not constant)

3. **Time Offset Calculation**:
   - Determines the tracker lag (positive = tracker lags behind video, negative = tracker ahead)

## Command-Line Interface

### Basic Usage

```powershell
TemporalCalibration.exe --fixed-seq-file=<video_file> --moving-seq-file=<tracking_file>
```

### Required Arguments

- `--fixed-seq-file=<path>`: Sequence file containing **video/images** (ultrasound frames)
- `--moving-seq-file=<path>`: Sequence file containing **tracking data** (probe poses)

### Optional Arguments

- `--moving-probe-to-reference-transform=<name>`: Transform name to extract from tracking sequence (e.g., "ToolToTracker", "ProbeToTracker")
- `--fixed-probe-to-reference-transform=<name>`: Transform name if fixed sequence contains tracking data
- `--max-time-offset-sec=<seconds>`: Maximum expected time offset (default: 2 seconds)
- `--sampling-resolution-sec=<seconds>`: Sampling resolution (default: 0.001 seconds)
- `--save-intermediate-images`: Save intermediate processing images (scanlines, detected lines)
- `--intermediate-file-output-dir=<path>`: Directory for intermediate files
- `--plot-results`: Display position vs. time plots
- `--verbose=<level>`: Verbose level (1=error, 2=warning, 3=info, 4=debug, 5=trace)

## Output

### Primary Output: STDOUT

**TemporalCalibration.exe outputs results to STDOUT only** - it does NOT generate output files by default.

The output includes:
```
Tracker lag: <value> sec (>0 if the tracker data lags)
Calibration error: <value>
Max calibration error: <value>
```

**Important**: TemporalCalibration.exe does NOT create XML output files like ProbeCalibration.exe does. All results are printed to STDOUT.

**Example Output:**
```
Tracker lag: -0.166 sec (>0 if the tracker data lags)
Calibration error: 15.6132
Max calibration error: 19.0812
```

**Interpretation:**
- **Tracker lag**: Time offset in seconds
  - Positive value = tracker lags behind video (tracker is slower)
  - Negative value = tracker is ahead of video (tracker is faster)
- **Calibration error**: Average error in the calibration
- **Max calibration error**: Maximum error encountered

### Secondary Output: STDERR

STDERR contains:
- **Warnings**: Non-fatal issues (e.g., low line segmentation success rate)
- **Errors**: Fatal issues that prevent calibration (e.g., empty signals, constant signals)

**Common Warnings:**
- `Line segmentation success rate is very low (X%): a line could only be detected on Y frames out of Z`
  - This is **normal** and doesn't prevent successful calibration
  - TemporalCalibration can work with partial line detection

**Common Errors:**
- `Cannot get signal range, the signal is empty` - No valid data extracted
- `Detected metric values do not vary sufficiently` - Signals are constant (no motion)
- `Failed to compute position signal` - Cannot extract position from frames
- `Cannot determine tracker lag, temporal calibration failed` - Calibration failed

### Optional Output Files

**By default, TemporalCalibration.exe creates NO output files.**

Optional outputs (if flags are used):

1. **Intermediate Images** (`--save-intermediate-images`):
   - Saves processing images to `--intermediate-file-output-dir`
   - Images show: scanlines used, detected lines, processing steps
   - File format: PNG images (e.g., `LineSegmentationResult_001.png`)
   - **Note**: Directory must exist and be writable

2. **Plot Display** (`--plot-results`):
   - Displays graphical plots (position vs. time) in a window
   - Does NOT save files - only displays on screen

3. **Baseline Comparison** (`--baseline-file`):
   - Compares results against a baseline file
   - Still outputs to STDOUT, doesn't create new files

**Summary**: The only persistent output is what you capture from STDOUT. No XML files, no result files - just text output to console.

## How Our Script Works

### Current Implementation

The script (`test_simulated_calibration.py`) does the following for temporal calibration:

1. **Detects calibration type** from config filename or `--type temporal` parameter

2. **Finds working sequence files** from PlusLibData:
   - Priority 1: `ShortTrackedUltrasoundCapture.igs.mha` (verified to work)
   - Priority 2: `fCal_Test_Calibration_3NWires_fCal2.0.igs.mha`
   - Priority 3: `WaterTankBottomTranslationCombined.igs.mha`

3. **Builds command**:
   ```powershell
   TemporalCalibration.exe 
     --fixed-seq-file=<video_file>
     --moving-seq-file=<tracking_file>
   ```

4. **Captures output**:
   - Saves STDOUT to: `calibration_output/logs/stdout_[timestamp].txt`
   - Saves STDERR to: `calibration_output/logs/stderr_[timestamp].txt`

5. **Extracts results** from STDOUT:
   - Tracker lag value
   - Calibration error values

### Working Files

**Currently using**: `ShortTrackedUltrasoundCapture.igs.mha`
- **Location**: `PlusLibData/TestImages/`
- **Type**: Combined file (contains both video and tracking data)
- **Usage**: Same file used for both `--fixed-seq-file` and `--moving-seq-file`
- **Results**: Completes successfully with valid time offset

## Output Files Generated

### Default Behavior: NO Files Created

**TemporalCalibration.exe does NOT create any output files by default.**

Unlike `ProbeCalibration.exe` which creates an XML output file, `TemporalCalibration.exe`:
- ✅ Outputs results to **STDOUT only** (console/text)
- ❌ Does NOT create XML result files
- ❌ Does NOT create output configuration files
- ❌ Does NOT save results to disk automatically

### What Gets Created

**Only files created are by our script:**
- `calibration_output/logs/stdout_[timestamp].txt` - Captured STDOUT
- `calibration_output/logs/stderr_[timestamp].txt` - Captured STDERR

**Optional files (if flags used):**
- `--save-intermediate-images`: Creates PNG images in specified directory
  - Example: `LineSegmentationResult_001.png`, `LineSegmentationResult_002.png`, etc.
  - Shows intermediate processing steps (scanlines, detected lines)
  - **Note**: Directory must exist before running

### How to Extract Results

Since there are no output files, you must:

1. **Capture STDOUT** (our script does this automatically)
2. **Parse the text output** for:
   - `Tracker lag: <value> sec`
   - `Calibration error: <value>`
   - `Max calibration error: <value>`

3. **Save results manually** if needed (the script saves to log files)

## Verification Steps

### 1. Check STDOUT for Results

Look for these lines in STDOUT:
```
Tracker lag: <value> sec
Calibration error: <value>
Max calibration error: <value>
```

**Success criteria:**
- Tracker lag value is present (can be positive or negative)
- Calibration error values are present
- Exit code is 0

### 2. Check STDERR for Errors

**Acceptable:**
- Warnings about line segmentation (normal, doesn't prevent success)

**Not acceptable:**
- Errors about empty signals
- Errors about constant signals
- Errors about failed calibration

### 3. Verify Output Files

**TemporalCalibration.exe does NOT create output files by default.**

The only files created are:
- **Log files** (created by our script):
  - `calibration_output/logs/stdout_[timestamp].txt` - Full STDOUT
  - `calibration_output/logs/stderr_[timestamp].txt` - Full STDERR

**Optional files** (if `--save-intermediate-images` is used):
- Intermediate processing images in the specified output directory

## Example Successful Run

```
[INFO] Found ShortTrackedUltrasoundCapture file in PlusLibData
[INFO] Using: ShortTrackedUltrasoundCapture.igs.mha
[INFO] Verified to work with TemporalCalibration.exe - completes successfully

COMMAND:
TemporalCalibration.exe 
  --fixed-seq-file=C:\...\ShortTrackedUltrasoundCapture.igs.mha 
  --moving-seq-file=C:\...\ShortTrackedUltrasoundCapture.igs.mha

STDOUT:
Tracker lag: -0.166 sec (>0 if the tracker data lags)
Calibration error: 15.6132
Max calibration error: 19.0812

STDERR:
|WARNING| Line segmentation success rate is very low (26.6667%): 
  a line could only be detected on 4 frames out of 15

[SUCCESS] Calibration completed successfully!
```

## Key Points

1. **No output files by default**: TemporalCalibration.exe outputs to STDOUT only
2. **Line segmentation warnings are normal**: Low success rate doesn't prevent calibration
3. **Results are in STDOUT**: Look for "Tracker lag", "Calibration error", "Max calibration error"
4. **STDERR contains diagnostics**: Warnings are acceptable, errors indicate failure
5. **Combined files work**: Can use same file for both fixed and moving sequences if it contains both data types

## Next Steps for Your Own Data

When you get your own data files from your advisor:

1. **Ensure files are in correct format**: `.igs.mha` or `.mha` (MetaImage format)
2. **Verify data content**: 
   - Fixed sequence should have video/images
   - Moving sequence should have tracking data (or use combined file)
3. **Check transform names**: If using separate tracking file, verify transform name (e.g., "ToolToTracker")
4. **Run calibration**: Use the script or command line directly
5. **Extract results**: Get time offset from STDOUT output

## References

- PLUS ToolKit Documentation
- TemporalCalibration.exe help: `TemporalCalibration.exe --help`
- Source code references in error messages point to:
  - `vtkTemporalCalibrationAlgo` - Main algorithm
  - `vtkLineSegmentationAlgo` - Line detection for video signal
  - `vtkPlusTrackedFrameList` - Data structure handling

