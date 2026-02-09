# PLUS ToolKit Installation Guide

This guide explains how to install and configure PLUS ToolKit for use with the ultrasound calibration module.

## What is PLUS ToolKit?

PLUS (Public software Library for UltraSound) is an open-source software library for ultrasound-guided interventions. It provides tools for:
- Ultrasound probe calibration (axial, lateral, temporal)
- Spatial calibration (image-to-probe transformation)
- Temporal calibration (time synchronization)
- Volume reconstruction from freehand ultrasound

## Installation Options

### Option 1: Pre-built Binaries (Recommended for Windows)

1. Download PLUS ToolKit from: https://github.com/PlusToolkit/PlusLib/releases
2. Extract to a directory (e.g., `C:\Program Files\PlusToolkit`)
3. Add the `bin` directory to your system PATH
4. Verify installation:
   ```bash
   PlusServer --help
   ```

### Option 2: Build from Source

#### Windows (Visual Studio)

1. Install prerequisites:
   - Visual Studio 2019 or later
   - CMake (3.10 or later)
   - Git

2. Clone PLUS repository:
   ```bash
   git clone https://github.com/PlusToolkit/PlusLib.git
   cd PlusLib
   ```

3. Build with CMake:
   ```bash
   mkdir build
   cd build
   cmake .. -DCMAKE_BUILD_TYPE=Release
   cmake --build . --config Release
   ```

4. Install:
   ```bash
   cmake --install . --config Release
   ```

#### Linux/macOS

1. Install dependencies:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install cmake git build-essential
   
   # macOS
   brew install cmake git
   ```

2. Clone and build:
   ```bash
   git clone https://github.com/PlusToolkit/PlusLib.git
   cd PlusLib
   mkdir build && cd build
   cmake .. -DCMAKE_BUILD_TYPE=Release
   make -j4
   sudo make install
   ```

### Option 3: Python Bindings (If Available)

If PLUS ToolKit Python bindings become available via pip:
```bash
pip install plustoolkit
```

**Note:** As of now, official Python bindings may not be available. The module uses subprocess calls to PLUS executables.

## Configuration

### Setting PLUS ToolKit Path

If PLUS ToolKit is not in your system PATH, specify the path when initializing:

```python
from ultrasound_calibration import AxialCalibration

calibrator = AxialCalibration(plus_toolkit_path="C:/Program Files/PlusToolkit/bin")
```

### Environment Variables

Alternatively, set the `PLUS_TOOLKIT_PATH` environment variable:

**Windows (PowerShell):**
```powershell
$env:PLUS_TOOLKIT_PATH = "C:\Program Files\PlusToolkit\bin"
```

**Linux/macOS:**
```bash
export PLUS_TOOLKIT_PATH="/usr/local/bin"
```

## Verification

Test the installation:

```python
from ultrasound_calibration import AxialCalibration

try:
    calibrator = AxialCalibration()
    print("PLUS ToolKit integration ready!")
except Exception as e:
    print(f"Error: {e}")
    print("Please check PLUS ToolKit installation and PATH configuration.")
```

## Troubleshooting

### "PLUS ToolKit not found" Error

1. Verify PLUS ToolKit is installed
2. Check that executables are in PATH:
   ```bash
   # Windows
   where PlusServer
   
   # Linux/macOS
   which PlusServer
   ```
3. Specify the path explicitly in code (see Configuration above)

### Permission Errors

- Ensure you have read/write permissions for calibration data directories
- On Linux/macOS, you may need `sudo` for system-wide installation

### Build Errors

- Ensure all prerequisites are installed
- Check CMake version: `cmake --version` (should be 3.10+)
- Review PLUS ToolKit build documentation: https://plustoolkit.github.io/

## Additional Resources

- PLUS ToolKit Documentation: https://plustoolkit.github.io/
- PLUS GitHub Repository: https://github.com/PlusToolkit/PlusLib
- PLUS User Forum: Check PLUS ToolKit community forums for support

## Next Steps

Once PLUS ToolKit is installed:
1. Review the `README.md` for usage examples
2. Try the example script: `example_axial_calibration.py`
3. Integrate with your existing hand-eye calibration workflow


