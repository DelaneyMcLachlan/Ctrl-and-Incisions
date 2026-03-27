# PLUS ToolKit Integration: Process, Problems, and Changes

## What is Axial Calibration?

**Axial calibration** determines the relationship between:
- **Ultrasound image coordinates** (pixels in 2D images)
- **Probe coordinate system** (3D physical space)

This is essential for **3D reconstruction** from freehand ultrasound scans. Without it, you can't accurately map where each ultrasound pixel is in 3D space.

### The Goal
Transform ultrasound image pixels → 3D probe coordinates → 3D world coordinates (for volume reconstruction)

## What We Built

### 1. Created Ultrasound Calibration Module
**Location:** `src/sprint1_product/ultrasound-calibration/`

**Files Created:**
- `axial_calibration.py` - Main calibration class
- `spatial_calibration.py` - Spatial calibration (image-to-probe)
- `__init__.py` - Module initialization
- `README.md` - Usage documentation
- `INSTALLATION.md` - Setup guide
- `QUICK_START.md` - How to run
- `example_axial_calibration.py` - Example code

### 2. Integration with PLUS ToolKit
PLUS ToolKit is a medical imaging library that provides calibration tools. We integrated it to perform axial calibration.

## The Process (What Should Happen)

1. **Input Data:**
   - Probe poses (4x4 transformation matrices from tracker)
   - Ultrasound images (2D grayscale images)

2. **Calibration:**
   - Run PLUS ToolKit's `ProbeCalibration.exe`
   - It analyzes images and poses
   - Computes transformation matrix (image → probe)

3. **Output:**
   - 4x4 calibration matrix
   - Can transform image coordinates to probe space

## The Problem (What's Not Working)

### Issue 1: Wrong Tool Initially
- **First attempt:** Used `PlusServer.exe` (for real-time data collection)
- **Fixed:** Switched to `ProbeCalibration.exe` (for calibration)

### Issue 2: Missing XML Configuration Elements
**Error:** `Unable to find required vtkPlusProbeCalibrationAlgo element`

**Problem:** PLUS ToolKit needs specific XML structure:
- ✅ We have: `DataCollection`, `Devices`
- ❌ Missing: `vtkPlusProbeCalibrationAlgo` (calibration algorithm config)
- ❌ Missing: `PhantomDefinition` (phantom geometry)

### Issue 3: Wrong Sequence File Format
**Error:** `No reader for file: calibration_sequence.xml`

**Problem:** PLUS ToolKit expects:
- ❌ What we create: Simple XML file
- ✅ What it needs: MetaImage format (`.mha`) with embedded image data

## All Changes Made

### Change 1: Module Structure
**Created:** Complete module structure for ultrasound calibration
- Python classes for calibration
- Documentation files
- Example scripts

### Change 2: Path Configuration
**Added:** Support for specifying PLUS ToolKit path
- Environment variable support
- Direct path specification
- Automatic path detection

### Change 3: Tool Selection
**Changed:** From `PlusServer.exe` → `ProbeCalibration.exe`
- Found correct calibration tool
- Updated command-line calls

### Change 4: XML Configuration
**Added:** XML config file generation
- `DataCollection` element (required by PlusServer)
- `Devices` section
- Basic structure (needs more elements)

### Change 5: Sequence File Creation
**Added:** Sequence metafile generation
- Creates XML sequence file
- Includes poses and image references
- **Problem:** Format is wrong (needs `.mha`)

## Current Status

### ✅ Working
- Module structure created
- Path configuration works
- Correct tool identified (`ProbeCalibration.exe`)
- Basic XML structure created
- Command-line syntax correct

### ❌ Not Working
- XML config missing required elements:
  - `vtkPlusProbeCalibrationAlgo` (calibration algorithm)
  - `PhantomDefinition` (phantom geometry)
- Sequence file format incorrect:
  - Currently: Simple XML
  - Needed: MetaImage (`.mha`) format

## Why It's Complex

PLUS ToolKit has **very specific requirements**:
1. **XML format** must match exact schema
2. **Sequence files** must be in MetaImage format (not simple XML)
3. **Phantom definitions** need exact geometry specifications
4. **Documentation** is limited - formats aren't well-documented

## Solutions

### Option 1: Complete PLUS Integration (Complex)
**What's needed:**
- Find example PLUS config files
- Understand MetaImage format
- Implement proper sequence file creation
- Add phantom definition to config

**Effort:** High (requires reverse-engineering PLUS formats)

### Option 2: Use PLUS GUI (Easier)
**Process:**
1. Use `PlusServerLauncher.exe` GUI
2. Perform calibration interactively
3. Export calibration matrix
4. Load using our `load_calibration()` method

**Effort:** Medium (manual process, but works)

### Option 3: Custom Calibration (Most Flexible)
**Process:**
1. Implement calibration algorithms in Python
2. Use known algorithms (N-wire, wire phantom, etc.)
3. Work directly with your data format
4. No dependency on PLUS ToolKit formats

**Effort:** Medium-High (but gives full control)

## Recommendation

**For now:** Use Option 2 (PLUS GUI) to get calibration working quickly.

**Long-term:** Consider Option 3 (custom calibration) for better integration with your existing codebase.

## Files Modified/Created

### New Files
- `ultrasound-calibration/axial_calibration.py` (551 lines)
- `ultrasound-calibration/spatial_calibration.py` (91 lines)
- `ultrasound-calibration/__init__.py`
- `ultrasound-calibration/README.md`
- `ultrasound-calibration/INSTALLATION.md`
- `ultrasound-calibration/QUICK_START.md`
- `ultrasound-calibration/example_axial_calibration.py`
- `ultrasound-calibration/test_calibration.py`
- `ultrasound-calibration/setup_plus_path.py`
- `ultrasound-calibration/debug_xml.py`
- Various documentation files

### Modified Files
- `hand-eye-calibration/requirements.txt` (added note about PLUS)

## Key Code Changes

### 1. AxialCalibration Class
- `__init__()` - Path configuration
- `calibrate()` - Main calibration method
- `_calibrate_with_plus_cli()` - Calls ProbeCalibration.exe
- `_create_plus_config_xml()` - Generates XML config
- `_create_sequence_metafile()` - Creates sequence file (needs format fix)

### 2. Error Handling
- FileNotFoundError for missing executables
- RuntimeError for calibration failures
- Detailed error messages

## Next Steps

1. **If using PLUS ToolKit:**
   - Find example config files in PLUS installation
   - Research MetaImage format
   - Complete XML configuration

2. **If using custom calibration:**
   - Implement calibration algorithms
   - Remove PLUS ToolKit dependency
   - Integrate with existing code

3. **If using PLUS GUI:**
   - Use GUI to calibrate
   - Export results
   - Load using existing code

## Summary

**What we did:** Created a complete module structure to integrate PLUS ToolKit for axial calibration.

**What works:** Module structure, path handling, tool identification, basic XML generation.

**What doesn't work:** Complete XML configuration (missing elements) and sequence file format (wrong format).

**Why:** PLUS ToolKit has very specific, poorly-documented format requirements.

**Solution:** Either complete the PLUS integration (complex) or use alternative approach (GUI or custom implementation).

