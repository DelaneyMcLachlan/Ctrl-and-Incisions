# How to Run ProbeCalibration

## Option 1: Using the Test Script (Easiest)

Simply run:
```powershell
cd src\sprint1_product\ultrasound-calibration
python test_simulated_calibration.py
```

This will automatically:
- Find the config file
- Find the test data file
- Run ProbeCalibration with correct paths
- Show you the results

## Option 2: Direct Command Line

### From PowerShell:

```powershell
cd C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin

.\ProbeCalibration.exe `
  --config-file="C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\config\PlusDeviceSet_fCal_Sim_SpatialCalibration_2.0.xml" `
  --calibration-seq-file="C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\data\fCal_Test_Calibration_3NWires_fCal2.0.igs.mha" `
  --output-config-file="C:\Users\mclac\Desktop\Ctrl-and-Incision\calibration_result.xml"
```

### From Command Prompt (CMD):

```cmd
cd C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin

ProbeCalibration.exe --config-file="C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\config\PlusDeviceSet_fCal_Sim_SpatialCalibration_2.0.xml" --calibration-seq-file="C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\data\fCal_Test_Calibration_3NWires_fCal2.0.igs.mha" --output-config-file="C:\Users\mclac\Desktop\Ctrl-and-Incision\calibration_result.xml"
```

## Option 3: Using Your Own .mha File

If you want to use your own `.mha` file (like `ElbowUltrasoundSweep.mha`):

```powershell
cd C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin

.\ProbeCalibration.exe `
  --config-file="C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\config\PlusDeviceSet_fCal_Sim_SpatialCalibration_2.0.xml" `
  --calibration-seq-file="C:\Users\mclac\Desktop\Ctrl-and-Incision\src\sprint1_product\ultrasound-calibration\ElbowUltrasoundSweep.mha" `
  --output-config-file="C:\Users\mclac\Desktop\Ctrl-and-Incision\calibration_result.xml"
```

## Notes

- Replace the output path with wherever you want the result saved
- The output file will contain the calibration matrix and results
- Make sure all paths are in quotes if they contain spaces

