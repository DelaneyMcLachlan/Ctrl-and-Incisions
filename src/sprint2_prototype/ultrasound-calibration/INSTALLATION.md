# PLUS ToolKit and PlusLibData Installation Instructions

This document provides step-by-step instructions for installing PLUS ToolKit and PlusLibData, which are required dependencies for the ultrasound calibration tools.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installing PLUS ToolKit](#installing-plus-toolkit)
4. [Installing PlusLibData](#installing-pluslibdata)
5. [Configuration](#configuration)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

## Overview

**PLUS ToolKit** is an open-source software platform for developing image-guided intervention systems. It provides tools for:
- Ultrasound calibration (ProbeCalibration.exe, TemporalCalibration.exe)
- Volume reconstruction (VolumeReconstructor.exe)
- Data acquisition and processing

**PlusLibData** is a collection of test data, sample configurations, and example files that come with PLUS ToolKit.

## Prerequisites

- **Operating System**: Windows 10/11 (64-bit)
- **Python**: Python 3.8 or higher
- **Disk Space**: At least 2 GB free space
- **Administrator privileges** (for installation)

## Installing PLUS ToolKit

### Step 1: Download PLUS ToolKit

1. Visit the PLUS ToolKit download page:
   - **Official Repository**: https://github.com/PlusToolkit/PlusLib
   - **Releases**: https://github.com/PlusToolkit/PlusLib/releases

2. Download the Windows installer for version **2.8.0** or later:
   - Look for files like `PlusApp-2.8.0.20190617-Win64.exe` or similar
   - Or download the pre-built binaries package

### Step 2: Install PLUS ToolKit

#### Option A: Using the Installer (Recommended)

1. Run the installer executable
2. Follow the installation wizard
3. **Default installation path**: `C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\`
4. Note the installation directory for configuration

#### Option B: Manual Installation

1. Extract the downloaded ZIP file to a location of your choice
2. Recommended location: `C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\`
3. Ensure the directory structure includes:
   ```
   PlusApp-2.8.0.20190617-Win64/
   ├── bin/          (contains executables)
   ├── config/        (contains configuration files)
   ├── data/          (contains data files)
   └── lib/           (contains libraries)
   ```

### Step 3: Verify Installation

1. Navigate to the `bin` directory:
   ```powershell
   cd C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin
   ```

2. Check that key executables exist:
   ```powershell
   Test-Path ProbeCalibration.exe
   Test-Path TemporalCalibration.exe
   Test-Path VolumeReconstructor.exe
   ```

   All should return `True`.

## Installing PlusLibData

**PlusLibData** is typically included with PLUS ToolKit installation. It should be located at:

```
C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\data\PlusLibData\
```

### Verify PlusLibData Installation

1. Check that the directory exists:
   ```powershell
   Test-Path "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\data\PlusLibData\TestImages"
   ```

2. Verify test images are present:
   ```powershell
   Get-ChildItem "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\data\PlusLibData\TestImages" -Filter "*.mha" | Measure-Object
   ```

   You should see multiple `.mha` files (typically 80+ files).

3. Check for config files:
   ```powershell
   Test-Path "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\data\PlusLibData\ConfigFiles"
   ```

### If PlusLibData is Missing

If PlusLibData is not included in your installation:

1. Download it separately from the PLUS ToolKit repository
2. Extract it to: `C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\data\PlusLibData\`
3. Or download from: https://github.com/PlusToolkit/PlusLibData

## Configuration

### Setting Environment Variable (Recommended)

To make PLUS ToolKit accessible from any location, set the `PLUS_TOOLKIT_PATH` environment variable.

#### Windows PowerShell (Temporary - Current Session Only)

```powershell
$env:PLUS_TOOLKIT_PATH = "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin"
```

#### Windows PowerShell (Permanent - User Level)

```powershell
[Environment]::SetEnvironmentVariable("PLUS_TOOLKIT_PATH", "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin", "User")
```

#### Windows Command Prompt (Permanent - User Level)

```cmd
setx PLUS_TOOLKIT_PATH "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin"
```

#### Windows GUI Method

1. Press `Win + X` and select "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "User variables", click "New"
5. Variable name: `PLUS_TOOLKIT_PATH`
6. Variable value: `C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin`
7. Click "OK" on all dialogs
8. **Restart your terminal/IDE** for changes to take effect

### Verify Environment Variable

```powershell
echo $env:PLUS_TOOLKIT_PATH
```

Should display: `C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin`

## Verification

### Using the Configuration Utility

Run the configuration check script:

```powershell
cd src\sprint1_product\ultrasound-calibration
python plus_toolkit_config.py
```

This will display:
- ✅ Installation status
- Paths to all directories
- Executable availability
- PlusLibData status

### Manual Verification

1. **Check executables**:
   ```powershell
   C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin\ProbeCalibration.exe --help
   ```

2. **Check test data**:
   ```powershell
   python view_mha_volume.py
   ```
   
   Should list 80+ available .mha files if PlusLibData is installed.

3. **Run a test calibration**:
   ```powershell
   python test_simulated_calibration.py --type spatial
   ```

## Troubleshooting

### Issue: "PLUS ToolKit not found"

**Solution**: 
1. Verify PLUS ToolKit is installed at the expected location
2. Set the `PLUS_TOOLKIT_PATH` environment variable
3. Restart your terminal/IDE after setting the variable

### Issue: "PlusLibData TestImages not found"

**Solution**:
1. Verify PlusLibData is installed: `Test-Path "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\data\PlusLibData\TestImages"`
2. If missing, download PlusLibData separately
3. Extract to the correct location

### Issue: "Executable not found" errors

**Solution**:
1. Check that you're using the correct path to the `bin` directory
2. Verify executables exist: `Get-ChildItem "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin\*.exe"`
3. Ensure you have the correct version (2.8.0 or later)

### Issue: Environment variable not working

**Solution**:
1. Restart your terminal/IDE after setting the variable
2. Verify with: `echo $env:PLUS_TOOLKIT_PATH`
3. Use absolute paths in scripts if environment variable doesn't work

### Issue: Permission errors

**Solution**:
1. Run PowerShell/Command Prompt as Administrator
2. Check file permissions on the PLUS ToolKit directory
3. Ensure you have read/execute permissions

## Alternative Installation Locations

If you install PLUS ToolKit in a non-standard location:

1. Set the `PLUS_TOOLKIT_PATH` environment variable to point to your `bin` directory
2. Example: If installed to `D:\MyTools\PlusToolkit\bin`, set:
   ```powershell
   $env:PLUS_TOOLKIT_PATH = "D:\MyTools\PlusToolkit\bin"
   ```

3. The scripts will automatically detect and use this path.

## Additional Resources

- **PLUS ToolKit Documentation**: https://plustoolkit.github.io/
- **GitHub Repository**: https://github.com/PlusToolkit/PlusLib
- **User Forum**: Check PLUS ToolKit community forums for support

## Quick Start Checklist

- [ ] PLUS ToolKit installed
- [ ] PlusLibData installed (in `data\PlusLibData\`)
- [ ] `PLUS_TOOLKIT_PATH` environment variable set
- [ ] Terminal/IDE restarted after setting environment variable
- [ ] Verification script runs successfully: `python plus_toolkit_config.py`
- [ ] Test script works: `python test_simulated_calibration.py --type spatial`
- [ ] Viewer script works: `python view_mha_volume.py`

Once all items are checked, you're ready to use the ultrasound calibration tools!

