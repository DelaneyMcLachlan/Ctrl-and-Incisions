# PLUS ToolKit Integration Notes

## Important: PLUS ToolKit Uses XML Configuration Files

PLUS ToolKit does **NOT** use command-line arguments like `--phantom`, `--poses`, etc. Instead, it uses **XML configuration files** that specify:
- Devices (tracking, ultrasound)
- Calibration settings
- Input/output paths
- Phantom parameters

## How PLUS ToolKit Actually Works

1. **Create XML Configuration File** - Define all settings in XML
2. **Run PlusServer** - Execute: `PlusServer.exe --config-file=config.xml`
3. **Parse Output** - Read calibration results from output XML files

## Current Implementation

The `axial_calibration.py` module now:
- Creates a proper PLUS ToolKit XML configuration file
- Runs PlusServer with the config file
- Attempts to parse the output

## Known Issues & Limitations

### 1. XML Configuration Format

The XML format I've created is a **best guess** based on PLUS ToolKit documentation patterns. You may need to adjust:

- **Device definitions** - May need specific device types
- **Calibration section** - Format may vary by phantom type
- **Pose/image format** - May need different XML structure

### 2. PlusServer Command-Line Syntax

PlusServer may use different syntax:
- `PlusServer.exe --config-file=config.xml`
- `PlusServer.exe config.xml`
- `PlusServer.exe -c config.xml`

If you get errors, check the actual PlusServer help:
```powershell
C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin\PlusServer.exe --help
```

### 3. Output File Location

PLUS ToolKit may output calibration results in different locations:
- Same directory as config file
- Specified output directory
- Default PLUS output directory

The code tries to find common output file names, but you may need to adjust based on your PLUS version.

## How to Debug

### Step 1: Check PlusServer Help

```powershell
cd C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin
.\PlusServer.exe --help
```

This will show you the actual command-line options.

### Step 2: Check PLUS ToolKit Documentation

Look for:
- Example configuration XML files
- Calibration workflow documentation
- Output file format specifications

### Step 3: Test with Simple Config

Create a minimal XML config file and test PlusServer manually:

```xml
<?xml version="1.0"?>
<PlusConfiguration version="2.8">
  <!-- Minimal config for testing -->
</PlusConfiguration>
```

Run:
```powershell
.\PlusServer.exe --config-file=test_config.xml
```

### Step 4: Adjust Code Based on Results

Once you know:
- The correct XML format
- The correct command-line syntax
- The output file location

Update the `_create_plus_config_xml()` and `_calibrate_with_plus_cli()` methods accordingly.

## Alternative Approach: Use PLUS ToolKit GUI

If command-line is problematic, you can:
1. Use PLUS ToolKit's GUI tools to perform calibration
2. Export the calibration matrix
3. Load it using `calibrator.load_calibration()`

## Getting Help

- PLUS ToolKit Documentation: https://plustoolkit.github.io/
- PLUS ToolKit GitHub Issues: https://github.com/PlusToolkit/PlusLib/issues
- Check example config files in PLUS ToolKit installation directory

## Next Steps

1. **Test PlusServer command-line** - Run `PlusServer.exe --help` to see actual options
2. **Find example config files** - Look in PLUS installation for example XML files
3. **Update XML generation** - Adjust `_create_plus_config_xml()` to match actual format
4. **Test calibration** - Run a simple calibration and check output location
5. **Update parsing** - Adjust `_read_plus_calibration_result()` to match actual output format

