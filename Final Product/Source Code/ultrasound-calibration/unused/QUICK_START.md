# Quick Start: Running Axial Calibration

## Prerequisites

1. **PLUS ToolKit installed** at: `C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin`
2. **Python dependencies** installed (numpy, opencv-python, etc.)

## Step 1: Configure PLUS ToolKit Path

You have three options:

### Option A: Set in Code (Recommended for Testing)

```python
from ultrasound_calibration import AxialCalibration

calibrator = AxialCalibration(
    plus_toolkit_path=r"C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin"
)
```

### Option B: Set Environment Variable

**PowerShell (current session):**
```powershell
$env:PLUS_TOOLKIT_PATH = "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin"
```

**PowerShell (permanent):**
```powershell
[Environment]::SetEnvironmentVariable("PLUS_TOOLKIT_PATH", "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin", "User")
```

### Option C: Use Setup Script

```powershell
cd src\sprint1_product\ultrasound-calibration
python setup_plus_path.py "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin"
```

## Step 2: Prepare Your Data

You need:
- **Probe poses**: List of 4x4 transformation matrices from your tracker
- **Ultrasound images**: List of 2D ultrasound images (grayscale numpy arrays)

### Example Data Format

```python
import numpy as np
import cv2

# Probe poses (from tracker) - 4x4 transformation matrices
probe_poses = [
    np.eye(4),  # First pose
    np.eye(4),  # Second pose
    # ... more poses
]

# Ultrasound images - 2D grayscale arrays
ultrasound_images = [
    cv2.imread("image1.png", cv2.IMREAD_GRAYSCALE),
    cv2.imread("image2.png", cv2.IMREAD_GRAYSCALE),
    # ... more images
]
```

## Step 3: Run Calibration

### Basic Usage

```python
from ultrasound_calibration import AxialCalibration
import numpy as np
import cv2

# Initialize with your PLUS ToolKit path
calibrator = AxialCalibration(
    plus_toolkit_path=r"C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin"
)

# Load your data
probe_poses = [...]  # Your 4x4 transformation matrices
ultrasound_images = [...]  # Your ultrasound images

# Run calibration
calibration_matrix = calibrator.calibrate(
    probe_poses=probe_poses,
    ultrasound_images=ultrasound_images,
    calibration_phantom="wire_phantom"  # or "n_wire", "plane", etc.
)

print("Calibration matrix:")
print(calibration_matrix)

# Save calibration
calibrator.save_calibration("my_calibration.xml")
```

### Complete Example Script

Create a file `run_calibration.py`:

```python
import sys
import os
from pathlib import Path

# Add the ultrasound-calibration module to path
module_path = Path(__file__).parent / "ultrasound-calibration"
sys.path.insert(0, str(module_path.parent))

from ultrasound_calibration import AxialCalibration
import numpy as np
import cv2

def main():
    # 1. Initialize calibrator
    calibrator = AxialCalibration(
        plus_toolkit_path=r"C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin"
    )
    
    # 2. Load your calibration data
    # TODO: Replace with your actual data loading code
    probe_poses = load_probe_poses()  # Your function to load poses
    ultrasound_images = load_ultrasound_images()  # Your function to load images
    
    # 3. Run calibration
    try:
        calibration_matrix = calibrator.calibrate(
            probe_poses=probe_poses,
            ultrasound_images=ultrasound_images,
            calibration_phantom="wire_phantom"
        )
        
        print("✓ Calibration successful!")
        print(f"\nCalibration Matrix:\n{calibration_matrix}")
        
        # 4. Save calibration
        output_file = "axial_calibration_result.xml"
        calibrator.save_calibration(output_file)
        print(f"\n✓ Calibration saved to: {output_file}")
        
    except Exception as e:
        print(f"✗ Calibration failed: {e}")
        import traceback
        traceback.print_exc()

def load_probe_poses():
    """Load probe poses from your tracking data."""
    # Example: Load from XML file (using your existing calibration_io.py)
    # Or load from your tracking system
    poses = []
    # ... your code here ...
    return poses

def load_ultrasound_images():
    """Load ultrasound images from files."""
    # Example: Load images from directory
    images = []
    image_dir = Path("path/to/your/images")
    for img_file in sorted(image_dir.glob("*.png")):
        img = cv2.imread(str(img_file), cv2.IMREAD_GRAYSCALE)
        images.append(img)
    return images

if __name__ == "__main__":
    main()
```

## Step 4: Use Calibration Results

After calibration, you can transform image coordinates to probe space:

```python
# Load saved calibration
calibrator = AxialCalibration()
calibrator.load_calibration("my_calibration.xml")

# Transform image coordinates to probe space
image_coords = np.array([
    [128, 100],  # Point 1 in image (pixels)
    [128, 150],  # Point 2 in image (pixels)
])

probe_coords = calibrator.image_to_probe(image_coords)
print(f"Probe coordinates (mm):\n{probe_coords}")
```

## Running the Example Script

The module includes a complete example:

```powershell
cd src\sprint1_product\ultrasound-calibration
python example_axial_calibration.py
```

**Note:** The example uses simulated data. Replace it with your actual tracking and ultrasound data.

## Troubleshooting

### "PLUS ToolKit not found" Error

1. Verify PlusServer.exe exists:
   ```powershell
   Test-Path "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin\PlusServer.exe"
   ```

2. Check path in code matches your installation

3. Run setup script to test:
   ```powershell
   python setup_plus_path.py "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin"
   ```

### "Number of probe poses must match number of ultrasound images"

- Ensure you have the same number of poses and images
- Check that poses and images are in the same order

### Calibration Fails

- Verify you have at least 3 calibration images
- Check that images contain visible calibration phantom features
- Ensure probe poses are valid 4x4 transformation matrices

## Next Steps

1. **Integrate with your tracking system**: Connect to your NDI tracker or other tracking device
2. **Connect to ultrasound device**: Get real-time ultrasound images
3. **Use in 3D reconstruction**: Apply calibration for volume reconstruction

## Integration with Existing Code

To integrate with your existing hand-eye calibration:

```python
# Load hand-eye calibration (camera-to-tracker)
from hand_eye_cal_logic import analyzeFrames
# ... your existing code ...

# Load axial calibration (image-to-probe)
from ultrasound_calibration import AxialCalibration
axial_cal = AxialCalibration()
axial_cal.load_calibration("axial_calibration.xml")

# Combined transformation: Image → Probe → Tracker → Camera → World
```

