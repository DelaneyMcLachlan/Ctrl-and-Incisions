# ProbeCalibration Run Results

## Command Executed

```powershell
C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin\ProbeCalibration.exe --config-file="C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\config\PlusDeviceSet_fCal_Sim_SpatialCalibration_2.0.xml"
```

## Result

**Exit Code:** 1 (Failed)

**Error Messages:**
```
|ERROR| File:  does not exist.
|ERROR| Reading calibration images from '' failed!
```

## Analysis

### What Worked ✅
1. **ProbeCalibration.exe runs** - Tool is found and executes
2. **Config file is read** - "Read configuration file..." message appears
3. **Config structure is valid** - No XML parsing errors

### What Failed ❌
1. **Sequence file missing** - Config references `fCal_Test_Calibration_3NWires_fCal2.0.igs.mha` which doesn't exist
2. **Empty file path** - Error shows `File: ` (empty), meaning the sequence file path is not found

## What We Learned

### From Your Example Config File

Your config file (`PlusDeviceSet_fCal_Sim_SpatialCalibration_2.0.xml`) shows the **correct structure**:

1. **DataCollection with DeviceSet**
   ```xml
   <DataCollection>
     <DeviceSet Name="..." Description="...">
       <Device Type="SavedDataSource" SequenceFile="...">
   ```

2. **PhantomDefinition** (This is what we were missing!)
   ```xml
   <PhantomDefinition>
     <Description Name="fCAL" Type="Multi-N" Version="2.0" />
     <Geometry>
       <Pattern Type="NWire">
         <Wire EndPointFront="..." EndPointBack="..." />
   ```

3. **vtkPlusProbeCalibrationAlgo** (This is what we were missing!)
   ```xml
   <vtkPlusProbeCalibrationAlgo
     ImageCoordinateFrame="Image"
     ProbeCoordinateFrame="Probe"
     PhantomCoordinateFrame="Phantom"
     ReferenceCoordinateFrame="Reference" />
   ```

4. **Sequence File Format**
   - Must be `.igs.mha` or `.mha` (MetaImage format)
   - Contains both images AND tracking data
   - Referenced by `SequenceFile` attribute in Device

## The Problem

Your config file expects:
- **Sequence file:** `fCal_Test_Calibration_3NWires_fCal2.0.igs.mha`
- **Location:** Should be in same directory as config or absolute path
- **Format:** MetaImage format with embedded images and tracking

**This file doesn't exist**, so ProbeCalibration can't find the calibration data.

## Solutions

### Option 1: Find/Create the Sequence File
- Look for `fCal_Test_Calibration_3NWires_fCal2.0.igs.mha` in PLUS installation
- Or create it from your images/poses using PLUS tools

### Option 2: Modify Config to Use Our Sequence
- Update the `SequenceFile` attribute to point to our generated sequence
- But we need to create proper `.mha` format (not simple XML)

### Option 3: Use PLUS Tools to Create Sequence
- Use `EditSequenceFile.exe` or similar to create sequence from your data
- Then point config to that sequence file

## What This Means for Our Code

We need to update our code to:

1. **Match your config format:**
   - Use `DeviceSet` instead of `Devices`
   - Use `SavedDataSource` device type
   - Add `PhantomDefinition` section
   - Add `vtkPlusProbeCalibrationAlgo` section

2. **Create proper sequence files:**
   - Generate `.mha` format (MetaImage)
   - Include embedded image data
   - Include tracking transforms
   - Use proper MetaImage headers

## Next Steps

1. **Check for sequence file:**
   ```powershell
   Get-ChildItem "C:\PlusToolkit" -Recurse -Filter "*fCal*.mha"
   ```

2. **Update our code** to match your example config format

3. **Implement proper sequence file creation** in MetaImage format

Would you like me to:
- Update our code to match your example config format?
- Help find/create the sequence file?
- Research MetaImage format for sequence file creation?

