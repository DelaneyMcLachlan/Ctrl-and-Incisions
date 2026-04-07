# PLUS ToolKit Config File Analysis

## Example Config File Found

**Location:** `C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\config\PlusDeviceSet_fCal_Sim_SpatialCalibration_2.0.xml`

## Key Elements Required

### 1. DataCollection Section
```xml
<DataCollection StartupDelaySec="1.0">
  <DeviceSet Name="..." Description="...">
    <Device Id="TrackedVideoDevice" Type="SavedDataSource"
      SequenceFile="fCal_Test_Calibration_3NWires_fCal2.0.igs.mha"
      UseData="IMAGE_AND_TRANSFORM">
      ...
    </Device>
  </DeviceSet>
</DataCollection>
```

**Key Points:**
- Uses `DeviceSet` (not just `Devices`)
- Device type: `SavedDataSource` (for reading sequence files)
- Requires `SequenceFile` attribute pointing to `.mha` file
- `UseData="IMAGE_AND_TRANSFORM"` specifies what to use

### 2. PhantomDefinition Section (CRITICAL - We Were Missing This!)
```xml
<PhantomDefinition>
  <Description Name="fCAL" Type="Multi-N" Version="2.0" />
  <Geometry>
    <Pattern Type="NWire">
      <Wire Name="..." EndPointFront="..." EndPointBack="..." />
    </Pattern>
    ...
  </Geometry>
</PhantomDefinition>
```

**This is what was causing the "No phantom definition" error!**

### 3. vtkPlusProbeCalibrationAlgo Section (CRITICAL - We Were Missing This!)
```xml
<vtkPlusProbeCalibrationAlgo
  ImageCoordinateFrame="Image"
  ProbeCoordinateFrame="Probe"
  PhantomCoordinateFrame="Phantom"
  ReferenceCoordinateFrame="Reference" />
```

**This is what was causing the "Unable to find vtkPlusProbeCalibrationAlgo" error!**

### 4. Segmentation Section
```xml
<Segmentation
  ApproximateSpacingMmPerPixel="0.078"
  MorphologicalOpeningCircleRadiusMm="0.27"
  ... />
```

### 5. fCal Section
```xml
<fCal
  PhantomModelId="PhantomModel"
  NumberOfCalibrationImagesToAcquire="140"
  ... />
```

### 6. CoordinateDefinitions Section
```xml
<CoordinateDefinitions>
  <Transform From="Image" To="TransducerOriginPixel" Matrix="..." />
  ...
</CoordinateDefinitions>
```

## What We Need to Fix

### Issue 1: Sequence File Format
- **Current:** We create simple XML
- **Needed:** MetaImage format (`.mha` or `.igs.mha`)
- **Solution:** Need to create proper sequence metafile in MetaImage format

### Issue 2: Config File Structure
- **Current:** Basic structure with DataCollection
- **Needed:** Full structure with:
  - ✅ DataCollection (we have this)
  - ❌ PhantomDefinition (we need to add)
  - ❌ vtkPlusProbeCalibrationAlgo (we need to add)
  - ❌ Segmentation (may need)
  - ❌ fCal section (may need)
  - ❌ CoordinateDefinitions (may need)

### Issue 3: Device Configuration
- **Current:** VirtualDevice
- **Needed:** SavedDataSource with SequenceFile attribute

## Next Steps

1. **Update XML generation** to include all required sections
2. **Create proper sequence file** in MetaImage format
3. **Test with example config** to understand sequence file requirements

