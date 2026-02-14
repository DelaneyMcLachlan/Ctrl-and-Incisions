# Sprint 2 Product - Running Instructions

This directory contains two main calibration applications for the Ctrl-and-Incision project:

1. **Hand-Eye Calibration** - Calibrate camera and stylus tracking systems
2. **Ultrasound Calibration** - Calibrate ultrasound probe position and orientation

---

## Prerequisites

- **Python 3.8 or higher**
- **Windows 10/11 (64-bit)** (for ultrasound calibration tools)
- **Administrator privileges** (for installing PLUS ToolKit, if needed)

---

## Quick Start

### 1. Clone or Download the Repository

```bash
git clone <repository-url>
cd Ctrl-and-Incision
```

### 2. Install Python Dependencies

Install dependencies for both applications:

```bash
# Install hand-eye calibration dependencies
cd src\sprint2_product\hand-eye-calibration
pip install -r requirements.txt

# Install scikit-surgeryutils (required for hand-eye calibration)
python -m pip install scikit-surgeryutils

# Install ultrasound calibration dependencies
cd ..\ultrasound-calibration
pip install -r requirements.txt
```

**Note**: The ultrasound calibration tools also require **PLUS ToolKit** (see [Ultrasound Calibration Setup](#ultrasound-calibration-setup) below).

---

## Hand-Eye Calibration

A standalone application to perform hand-eye calibration and collect required images and tracking data.

### Installation

1. Navigate to the hand-eye calibration directory:
   ```bash
   cd src\sprint2_product\hand-eye-calibration
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   python -m pip install scikit-surgeryutils
   ```

### Running the Application

```bash
python run_hand_eye_calibration.py
```

This will launch the hand-eye calibration GUI application.

### Requirements

- `pyside6` - GUI framework
- `numpy` - Numerical operations
- `scikit-surgerycore` - Core surgery toolkit
- `vtk` - 3D visualization
- `scikit-surgerynditracker` - NDI tracker interface
- `opencv-python` - Image processing
- `opencv-contrib-python` - Extended OpenCV features
- `scikit-surgeryutils` - Utility functions

For more details, see [hand-eye-calibration/README.md](hand-eye-calibration/README.md).

---

## Ultrasound Calibration

Tools for ultrasound probe calibration using PLUS ToolKit, including spatial, temporal, and pivot calibration, as well as 3D volume visualization.

### Ultrasound Calibration Setup

#### Step 1: Install PLUS ToolKit

The ultrasound calibration tools require **PLUS ToolKit** to be installed. See [ultrasound-calibration/INSTALLATION.md](ultrasound-calibration/INSTALLATION.md) for detailed installation instructions.

**Quick Setup:**

1. Download PLUS ToolKit from: https://github.com/PlusToolkit/PlusLib/releases
2. Install to default location: `C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\`
3. Set environment variable (PowerShell):
   ```powershell
   [Environment]::SetEnvironmentVariable("PLUS_TOOLKIT_PATH", "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin", "User")
   ```
4. **Restart your terminal/IDE** after setting the environment variable

#### Step 2: Verify Installation

```bash
cd src\sprint2_product\ultrasound-calibration
python plus_toolkit_config.py
```

This will check your PLUS ToolKit installation and display status.

### Running Ultrasound Calibration Tools

#### Option 1: Run Calibration Tests

```bash
cd src\sprint2_product\ultrasound-calibration

# Spatial calibration
python test_simulated_calibration.py --type spatial

# Temporal calibration
python test_simulated_calibration.py --type temporal

# Pivot calibration
python test_simulated_calibration.py --type pivot
```

#### Option 2: View Volume Files (Command Line)

```bash
cd src\sprint2_product\ultrasound-calibration

# List all available .mha files
python view_mha_volume.py

# View a specific file by number
python view_mha_volume.py 2

# View a specific file by path
python view_mha_volume.py "path/to/file.mha"
```

**Keyboard Controls:**
- **Right/Down Arrow or 'n'**: Next file
- **Left/Up Arrow or 'p'**: Previous file
- **Home**: First file
- **End**: Last file
- **'r'**: Reset camera
- **'q' or Escape**: Quit

#### Option 3: View Volume Files (GUI)

```bash
cd src\sprint2_product\ultrasound-calibration
python view_mha_gui.py
```

This launches a graphical interface for viewing .mha volume files.

### Requirements

- `vtk` - For 3D visualization
- `numpy` - For numerical operations
- `pyside6` - For GUI applications
- **PLUS ToolKit** - External dependency (see installation instructions above)

For more details, see [ultrasound-calibration/README.md](ultrasound-calibration/README.md).

---

## Troubleshooting

### Hand-Eye Calibration Issues

**Import errors:**
- Ensure all dependencies are installed:
  ```bash
  pip install -r requirements.txt
  python -m pip install scikit-surgeryutils
  ```

**Tracker connection issues:**
- Verify NDI tracker is connected and configured
- Check port settings in the application

### Ultrasound Calibration Issues

**"PLUS ToolKit not found":**
1. Verify PLUS ToolKit is installed
2. Set `PLUS_TOOLKIT_PATH` environment variable
3. Restart terminal/IDE
4. Run `python plus_toolkit_config.py` to verify

**"PlusLibData not found":**
1. Verify PlusLibData is installed in `data\PlusLibData\`
2. See [ultrasound-calibration/INSTALLATION.md](ultrasound-calibration/INSTALLATION.md) for installation instructions

**Environment variable not working:**
- Restart your terminal/IDE after setting the variable
- Verify with: `echo $env:PLUS_TOOLKIT_PATH` (PowerShell)

For more troubleshooting help, see:
- [hand-eye-calibration/README.md](hand-eye-calibration/README.md)
- [ultrasound-calibration/README.md](ultrasound-calibration/README.md)
- [ultrasound-calibration/INSTALLATION.md](ultrasound-calibration/INSTALLATION.md)

---

## Directory Structure

```
sprint2_product/
├── README.md                          # This file
├── hand-eye-calibration/              # Hand-eye calibration application
│   ├── README.md
│   ├── requirements.txt
│   ├── run_hand_eye_calibration.py    # Main entry point
│   └── ...
└── ultrasound-calibration/            # Ultrasound calibration tools
    ├── README.md
    ├── INSTALLATION.md
    ├── requirements.txt
    ├── test_simulated_calibration.py  # Calibration test script
    ├── view_mha_volume.py             # Command-line volume viewer
    ├── view_mha_gui.py                # GUI volume viewer
    ├── plus_toolkit_config.py         # Configuration utility
    └── ...
```

---

## Additional Resources

- **Hand-Eye Calibration**: See [hand-eye-calibration/README.md](hand-eye-calibration/README.md)
- **Ultrasound Calibration**: See [ultrasound-calibration/README.md](ultrasound-calibration/README.md)
- **PLUS ToolKit Installation**: See [ultrasound-calibration/INSTALLATION.md](ultrasound-calibration/INSTALLATION.md)
- **PLUS ToolKit Documentation**: https://plustoolkit.github.io/

---

## Quick Reference

### Hand-Eye Calibration
```bash
cd src\sprint2_product\hand-eye-calibration
pip install -r requirements.txt
python -m pip install scikit-surgeryutils
python run_hand_eye_calibration.py
```

### Ultrasound Calibration
```bash
cd src\sprint2_product\ultrasound-calibration
pip install -r requirements.txt
# Install PLUS ToolKit (see INSTALLATION.md)
python plus_toolkit_config.py  # Verify installation
python test_simulated_calibration.py --type spatial
```
