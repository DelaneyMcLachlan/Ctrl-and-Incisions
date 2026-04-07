# Files Needed from Advisor to Run Calibration with Your Own Data

Based on your `test_simulated_calibration.py` script, here are the files you need from your advisor to run calibration with real data instead of simulated data.

## Required Files

### 1. **Config File (XML)** - **CRITICAL**

**What it is:** A PLUS ToolKit configuration file that defines how to run the calibration.

**What it contains:**
- Device configuration (data source, tracking device, etc.)
- **PhantomDefinition** - Defines the calibration phantom geometry (wire positions, phantom type, etc.)
- **vtkPlusProbeCalibrationAlgo** - Calibration algorithm settings
- Coordinate frame definitions
- Segmentation parameters

**Current file you're using (simulated):**
```
C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\config\PlusDeviceSet_fCal_Sim_SpatialCalibration_2.0.xml
```

**What you need:** A similar config file but configured for:
- Your actual data source (not simulated)
- Your specific phantom type and geometry
- Your tracking system setup

**Key differences from simulated config:**
- Uses `SavedDataSource` device type pointing to your `.mha` file
- Contains actual phantom geometry (wire positions, phantom dimensions)
- Configured for your specific hardware setup

---

### 2. **Sequence File (.mha or .igs.mha)** - **REQUIRED**

**What it is:** A MetaImage format file containing your calibration data.

**What it contains:**
- Ultrasound images (2D frames)
- Tracking/pose data (4x4 transformation matrices)
- Timestamps for synchronization
- Metadata about the acquisition

**Format:** Must be in MetaImage format (`.mha` or `.igs.mha`)

**Note:** You already have `ElbowUltrasoundSweep.mha` in your directory, but you may need a different file specifically for calibration (with calibration phantom images).

---

### 3. **Phantom Definition Information** (if not in config)

**What it is:** Specifications about your calibration phantom.

**What you need:**
- Phantom type (N-wire, wire phantom, plane, etc.)
- Wire positions/endpoints (if using wire phantom)
- Phantom dimensions
- Coordinate system definition

**Note:** This might be embedded in the config file, or you might need it separately to create/verify the config.

---

## Optional but Helpful Files

### 4. **Example Real Config File**
- A working example config file that your advisor has used successfully
- This helps you understand the correct structure and parameters

### 5. **Documentation**
- Any specific instructions for your hardware setup
- Phantom specifications document
- Calibration procedure notes

---

## How to Use These Files

Once you have the files, you can modify your test script like this:

```python
if __name__ == "__main__":
    # Use your real config file instead of simulated one
    config_file = r"path\to\your\real_config.xml"
    sequence_file = r"path\to\your\calibration_data.mha"
    
    run_simulated_calibration(config_file, sequence_file)
```

Or run directly:
```powershell
.\ProbeCalibration.exe `
  --config-file="path\to\your\real_config.xml" `
  --calibration-seq-file="path\to\your\calibration_data.mha" `
  --output-config-file="calibration_result.xml"
```

---

## Questions to Ask Your Advisor

1. **"Do you have a config file configured for our hardware setup?"**
   - This is the most important file

2. **"What format is our calibration data in?"**
   - Is it already in `.mha` format, or do we need to convert it?

3. **"What type of calibration phantom are we using?"**
   - N-wire, wire phantom, plane, etc.
   - What are the exact dimensions/wire positions?

4. **"Do you have an example sequence file from a successful calibration?"**
   - This helps verify the data format is correct

5. **"Are there any specific calibration parameters we need to set?"**
   - Segmentation parameters, image spacing, etc.

---

## Summary Checklist

- [ ] **Config file (XML)** - Configured for your hardware and phantom
- [ ] **Sequence file (.mha)** - Your calibration data with images and tracking
- [ ] **Phantom specifications** - Geometry and dimensions
- [ ] **Example working config** (optional but helpful)
- [ ] **Hardware setup documentation** (optional but helpful)

