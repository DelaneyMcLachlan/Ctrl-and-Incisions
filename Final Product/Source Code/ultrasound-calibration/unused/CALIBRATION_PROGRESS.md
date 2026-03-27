# Axial Calibration Progress Summary

## ✅ What We've Accomplished

1. **Found the correct tool**: `ProbeCalibration.exe` (not PlusServer)
2. **Correct command-line syntax**: `--config-file=`, `--calibration-seq-file=`, `--output-config-file=`
3. **Basic XML structure**: DataCollection element is correct
4. **Path handling**: PLUS ToolKit path is correctly configured

## ❌ Current Issues

### Issue 1: Missing Calibration Algorithm Element
**Error:** `Unable to find required vtkPlusProbeCalibrationAlgo element`

**Solution:** Config XML needs a `vtkPlusProbeCalibrationAlgo` element with calibration algorithm settings.

### Issue 2: Missing Phantom Definition
**Error:** `No phantom definition is found in the XML tree!`

**Solution:** Config XML needs a phantom definition section specifying:
- Phantom type (wire, N-wire, plane, etc.)
- Phantom geometry/parameters
- Fiducial positions

### Issue 3: Sequence File Format
**Error:** `No reader for file: calibration_sequence.xml`

**Solution:** PLUS ToolKit requires sequence files in `.mha` format (MetaImage) or proper sequence metafile format, not simple XML.

## What Needs to Be Done

### 1. Update Config XML Structure

The config file needs:
```xml
<PlusConfiguration>
  <DataCollection>
    <Devices>...</Devices>
  </DataCollection>
  <vtkPlusProbeCalibrationAlgo>
    <!-- Calibration algorithm configuration -->
  </vtkPlusProbeCalibrationAlgo>
  <PhantomDefinition>
    <!-- Phantom geometry and parameters -->
  </PhantomDefinition>
</PlusConfiguration>
```

### 2. Create Proper Sequence Metafile

Sequence files need to be in MetaImage (.mha) format or PLUS sequence format that includes:
- Image data (embedded or referenced)
- Tracking data (transforms)
- Timestamps
- Proper headers

### 3. Research PLUS ToolKit Formats

We need to:
- Find example config files in PLUS installation
- Understand sequence metafile format
- Understand phantom definition format

## Recommendations

### Option A: Use PLUS ToolKit GUI (Easiest)
1. Use `PlusServerLauncher.exe` or GUI tools
2. Perform calibration interactively
3. Export calibration matrix
4. Load using `calibrator.load_calibration()`

### Option B: Find Example Files
1. Look in PLUS installation for example configs
2. Look in PLUS documentation/examples
3. Adapt our XML to match examples

### Option C: Implement Custom Calibration
1. Implement calibration algorithms in Python
2. Use scikit-surgerycalibration or similar
3. Bypass PLUS ToolKit complexity

## Next Steps

1. **Check for example files:**
   ```powershell
   # Look for example configs
   Get-ChildItem "C:\PlusToolkit" -Recurse -Filter "*.xml" | Select-Object FullName
   ```

2. **Check PLUS documentation:**
   - Look for calibration workflow examples
   - Find sequence file format specification
   - Find phantom definition examples

3. **Consider alternative:**
   - If PLUS integration is too complex, implement custom calibration
   - Use proven algorithms (N-wire, wire phantom, etc.)
   - Integrate with existing hand-eye calibration workflow

## Current Status

- ✅ Tool identification: **Complete**
- ✅ Basic structure: **Complete**
- ⚠️ Config XML: **Needs calibration algorithm and phantom definition**
- ⚠️ Sequence file: **Needs proper format**
- ❌ Full integration: **In progress**

The code structure is in place, but we need to understand PLUS ToolKit's specific XML formats to complete the integration.

