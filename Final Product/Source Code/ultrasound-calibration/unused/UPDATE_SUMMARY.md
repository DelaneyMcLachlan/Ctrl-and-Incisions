# Update Summary: Running ProbeCalibration with Your Config

## What Happened

You provided an example config file that shows the **correct structure**:
- `C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\config\PlusDeviceSet_fCal_Sim_SpatialCalibration_2.0.xml`

## Error from Running Your Config

```
|ERROR| File:  does not exist.
|ERROR| Reading calibration images from '' failed!
```

**Problem:** The config file references a sequence file `fCal_Test_Calibration_3NWires_fCal2.0.igs.mha` that doesn't exist.

## What We Learned from Your Config File

### Required Structure (from your example):

1. **DataCollection with DeviceSet** (not just Devices)
   ```xml
   <DataCollection>
     <DeviceSet>
       <Device Type="SavedDataSource" SequenceFile="...">
   ```

2. **PhantomDefinition** (we were missing this!)
   ```xml
   <PhantomDefinition>
     <Description Name="fCAL" Type="Multi-N" />
     <Geometry>
       <Pattern Type="NWire">
         <Wire EndPointFront="..." EndPointBack="..." />
   ```

3. **vtkPlusProbeCalibrationAlgo** (we were missing this!)
   ```xml
   <vtkPlusProbeCalibrationAlgo
     ImageCoordinateFrame="Image"
     ProbeCoordinateFrame="Probe"
     PhantomCoordinateFrame="Phantom"
     ReferenceCoordinateFrame="Reference" />
   ```

4. **Sequence File Format**
   - Must be `.mha` or `.igs.mha` format (MetaImage)
   - Contains both images and tracking data
   - Referenced by `SequenceFile` attribute in Device

## What Needs to Be Fixed

### 1. Update XML Generation
Our `_create_plus_config_xml()` needs to match your example format:
- Use `DeviceSet` instead of `Devices`
- Use `SavedDataSource` device type
- Add `PhantomDefinition` section
- Add `vtkPlusProbeCalibrationAlgo` section
- Remove old `Calibration` section (not needed)

### 2. Create Proper Sequence File
- Must be MetaImage format (`.mha`)
- Contains embedded image data and tracking transforms
- Complex format - may need to use PLUS tools to create it

## Next Steps

**Option 1: Use Your Existing Config**
- Find or create the sequence file it references
- Run calibration with your config

**Option 2: Update Our Code**
- Rewrite XML generation to match your example
- Implement proper sequence file creation
- Test with your data

**Option 3: Use PLUS Tools to Create Sequence**
- Use `EditSequenceFile.exe` or similar
- Create sequence from your images/poses
- Then use our code to generate config

## Recommendation

Since you have a working example config, the fastest path is:
1. **Create the sequence file** your config needs (or modify config to point to our sequence)
2. **Use your config as a template** to update our code
3. **Test with your actual data**

Would you like me to:
- Update our code to match your example config format?
- Help create the sequence file your config needs?
- Modify your config to work with our generated sequence files?

