# Ultrasound Calibration Tools

This module provides tools for ultrasound probe calibration using PLUS ToolKit, including spatial, temporal, and pivot calibration, as well as 3D volume visualization.

## Features

- **Spatial Calibration**: Calibrate ultrasound probe position and orientation
- **Temporal Calibration**: Synchronize ultrasound images with tracking data
- **Pivot Calibration**: Calibrate tool pivot points
- **3D Volume Viewer**: Visualize .mha volume files with VTK
- **File Scrolling**: Browse through multiple volume files in a single viewer session

## Prerequisites

Before using these tools, you must install:

1. **PLUS ToolKit** - Required for calibration executables
2. **PlusLibData** - Test data and sample configurations
3. **Python Dependencies** - See `requirements.txt`

See [INSTALLATION.md](INSTALLATION.md) for detailed installation instructions.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install PLUS ToolKit

Follow the instructions in [INSTALLATION.md](INSTALLATION.md) to:
- Download and install PLUS ToolKit
- Set the `PLUS_TOOLKIT_PATH` environment variable
- Verify installation

### 3. Verify Installation

```bash
python plus_toolkit_config.py
```

This will check your PLUS ToolKit installation and display status.

### 4. Run Calibration

```bash
# Spatial calibration
python test_simulated_calibration.py --type spatial

# Temporal calibration
python test_simulated_calibration.py --type temporal

# Pivot calibration
python test_simulated_calibration.py --type pivot
```

### 5. View Volume Files

```bash
# List all available .mha files
python view_mha_volume.py

# View a specific file by number
python view_mha_volume.py 2

# View a specific file by path
python view_mha_volume.py "path/to/file.mha"
```

## Configuration

### Environment Variable

Set the `PLUS_TOOLKIT_PATH` environment variable to point to your PLUS ToolKit bin directory:

**Windows PowerShell:**
```powershell
[Environment]::SetEnvironmentVariable("PLUS_TOOLKIT_PATH", "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin", "User")
```

**Windows Command Prompt:**
```cmd
setx PLUS_TOOLKIT_PATH "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin"
```

**Important**: Restart your terminal/IDE after setting the environment variable.

### Default Location

If the environment variable is not set, the scripts will check the default location:
- `C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin`

## Scripts

### `test_simulated_calibration.py`

Runs calibration using simulated or real data from PLUS ToolKit.

**Usage:**
```bash
python test_simulated_calibration.py [--type spatial|temporal|pivot] [--config path/to/config.xml]
```

**Examples:**
```bash
# Run spatial calibration with default config
python test_simulated_calibration.py --type spatial

# Run temporal calibration
python test_simulated_calibration.py --type temporal

# Use a custom config file
python test_simulated_calibration.py --config path/to/my_config.xml
```

### `view_mha_volume.py`

3D volume viewer for .mha files with file scrolling capability.

**Usage:**
```bash
python view_mha_volume.py [number|path]
```

**Examples:**
```bash
# List all available files
python view_mha_volume.py

# View file #2
python view_mha_volume.py 2

# View specific file
python view_mha_volume.py "path/to/file.mha"
```

**Keyboard Controls:**
- **Right/Down Arrow or 'n'**: Next file
- **Left/Up Arrow or 'p'**: Previous file
- **Home**: First file
- **End**: Last file
- **'r'**: Reset camera
- **'q' or Escape**: Quit

See [VIEW_MHA_README.md](VIEW_MHA_README.md) for detailed viewer documentation.

### `plus_toolkit_config.py`

Configuration utility to check PLUS ToolKit installation status.

**Usage:**
```bash
python plus_toolkit_config.py
```

This will display:
- Installation status
- Directory paths
- Executable availability
- PlusLibData status

## File Structure

```
ultrasound-calibration/
├── README.md                          # This file
├── INSTALLATION.md                    # Installation instructions
├── VIEW_MHA_README.md                 # Volume viewer documentation
├── requirements.txt                   # Python dependencies
├── plus_toolkit_config.py             # Configuration utility
├── test_simulated_calibration.py      # Calibration test script
├── view_mha_volume.py                 # 3D volume viewer
├── calibration_output/                # Calibration results
│   ├── *.xml                          # Calibration result files
│   └── logs/                          # Execution logs
└── ElbowUltrasoundSweep.mha          # Sample data file
```

## Output

Calibration results are saved to:
- `calibration_output/` - Calibration XML files
- `calibration_output/logs/` - Execution logs (stdout/stderr)

## Troubleshooting

### "PLUS ToolKit not found"

1. Verify PLUS ToolKit is installed
2. Set `PLUS_TOOLKIT_PATH` environment variable
3. Restart terminal/IDE
4. Run `python plus_toolkit_config.py` to verify

### "PlusLibData not found"

1. Verify PlusLibData is installed in `data\PlusLibData\`
2. Check that test images exist: `Test-Path "C:\PlusToolkit\...\data\PlusLibData\TestImages"`
3. See [INSTALLATION.md](INSTALLATION.md) for installation instructions

### "Executable not found"

1. Check that executables exist in the bin directory
2. Verify `PLUS_TOOLKIT_PATH` points to the `bin` directory (not the base directory)
3. Ensure you have the correct PLUS ToolKit version (2.8.0 or later)

## Documentation

- [INSTALLATION.md](INSTALLATION.md) - Detailed installation guide
- [VIEW_MHA_README.md](VIEW_MHA_README.md) - Volume viewer documentation
- [CALIBRATION_EXECUTABLES.md](CALIBRATION_EXECUTABLES.md) - Calibration executable reference

## Requirements

See `requirements.txt` for Python package dependencies. Main requirements:
- `vtk` - For 3D visualization
- `numpy` - For numerical operations

## License

This code is part of the Ctrl-and-Incision project.

## Contributing

When contributing code:
1. Ensure all hardcoded paths use the `plus_toolkit_config.py` utility
2. Test with both environment variable and default path configurations
3. Update documentation if adding new features

