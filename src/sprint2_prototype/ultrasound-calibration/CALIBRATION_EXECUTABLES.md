# PLUS ToolKit Calibration Executables

## Key Finding: Different Executables for Different Calibration Types

**YES, you need different executables!**

### Executables Available

1. **`ProbeCalibration.exe`** - For **spatial calibration** (image-to-probe transformation)
2. **`TemporalCalibration.exe`** - For **temporal calibration** (time synchronization)
3. **`fCal.exe`** - May be for fCal-specific calibration workflows

## Config File Structure Differences

### Spatial Calibration Config
- Uses: `ProbeCalibration.exe`
- Algorithm element: `<vtkPlusProbeCalibrationAlgo>`
- Data source: Single device with `UseData="IMAGE_AND_TRANSFORM"`
- Sequence file: One `.igs.mha` file with combined image and tracking data

### Temporal Calibration Config
- Uses: `TemporalCalibration.exe` ✅ (NOT ProbeCalibration.exe)
- Algorithm element: `<vtkTemporalCalibrationAlgo>` ✅
- Data sources: Two separate devices:
  - `TrackerDeviceSavedDataset` with `UseData="TRANSFORM"` (tracking only)
  - `VideoDeviceSavedDataset` with `UseData="IMAGE"` (video only)
- Sequence files: Two separate `.igs.mha` files:
  - One for tracking data
  - One for video data

## File Types

✅ **Correct file types**: `.igs.mha` and `.mha` are both valid PLUS ToolKit MetaImage formats
- `.igs.mha` - Image Guided Surgery format (includes tracking data)
- `.mha` - Standard MetaImage format

## Updated Script Behavior

The script now:
1. ✅ **Detects calibration type** from config filename or parameter
2. ✅ **Uses correct executable**:
   - `TemporalCalibration.exe` for temporal calibration
   - `ProbeCalibration.exe` for spatial/pivot calibration
3. ✅ **Checks for correct algorithm element**:
   - `vtkTemporalCalibrationAlgo` for temporal
   - `vtkPlusProbeCalibrationAlgo` for spatial
   - `vtkPlusPivotCalibrationAlgo` for pivot
4. ✅ **Handles multiple sequence files** for temporal calibration

## Summary

| Calibration Type | Executable | Algorithm Element | Sequence Files |
|-----------------|------------|-------------------|----------------|
| **Spatial** | `ProbeCalibration.exe` | `vtkPlusProbeCalibrationAlgo` | 1 file (combined) |
| **Temporal** | `TemporalCalibration.exe` ✅ | `vtkTemporalCalibrationAlgo` ✅ | 2 files (separate) |
| **Pivot** | `ProbeCalibration.exe` | `vtkPlusPivotCalibrationAlgo` | 1 file |

## Verification

To verify your setup is correct:

1. **Check executables exist**:
   ```powershell
   Test-Path "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin\TemporalCalibration.exe"
   Test-Path "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin\ProbeCalibration.exe"
   ```

2. **Check config file has correct algorithm**:
   ```powershell
   Select-String -Path "PlusDeviceSet_fCal_Sim_TemporalCalibration.xml" -Pattern "vtkTemporalCalibrationAlgo"
   ```

3. **Check sequence files exist** (for temporal):
   - `WaterTankBottomTranslationTrackerBuffer-trimmed.igs.mha` (tracking)
   - `WaterTankBottomTranslationVideoBuffer.igs.mha` (video)

## Next Steps

The script has been updated to automatically:
- Use `TemporalCalibration.exe` when `--type temporal` is specified
- Check for `vtkTemporalCalibrationAlgo` in the config
- Handle the two separate sequence files correctly

You can now run:
```powershell
python test_simulated_calibration.py --type temporal
```

And it will use the correct executable and verify the config structure!



