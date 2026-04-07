"""
Test script to run axial calibration and capture errors.
"""

import sys
import traceback
import numpy as np
import cv2
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from ultrasound_calibration import AxialCalibration
    print("[OK] Successfully imported AxialCalibration")
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    print("Trying direct import...")
    from axial_calibration import AxialCalibration
    print("[OK] Successfully imported AxialCalibration (direct)")

def test_calibration():
    """Test the axial calibration with simulated data."""
    print("\n=== Testing Axial Calibration ===\n")
    
    # Initialize with your PLUS ToolKit path
    plus_path = r"C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin"
    print(f"Initializing with path: {plus_path}")
    
    try:
        calibrator = AxialCalibration(plus_toolkit_path=plus_path)
        print("[OK] AxialCalibration initialized successfully")
    except Exception as e:
        print(f"[ERROR] Failed to initialize: {e}")
        traceback.print_exc()
        return
    
    # Create simulated calibration data
    print("\nCreating simulated calibration data...")
    num_images = 5
    
    # Simulate probe poses (4x4 transformation matrices)
    probe_poses = []
    for i in range(num_images):
        pose = np.eye(4)
        pose[0:3, 3] = [i * 5.0, 0.0, 100.0]  # Translation
        probe_poses.append(pose)
    
    # Simulate ultrasound images
    ultrasound_images = []
    for i in range(num_images):
        img = np.zeros((256, 256), dtype=np.uint8)
        # Draw a vertical line (simulating a wire in phantom)
        cv2.line(img, (128, 50), (128, 200), 255, 2)
        ultrasound_images.append(img)
    
    print(f"  - Created {len(probe_poses)} probe poses")
    print(f"  - Created {len(ultrasound_images)} ultrasound images")
    print(f"  - Image size: {ultrasound_images[0].shape}")
    
    # Try to run calibration
    print("\nAttempting calibration...")
    try:
        calibration_matrix = calibrator.calibrate(
            probe_poses=probe_poses,
            ultrasound_images=ultrasound_images,
            calibration_phantom="wire_phantom",
            phantom_parameters={
                'wire_position': [128, 128],
                'wire_depth_mm': 50.0
            }
        )
        
        print("[OK] Calibration completed successfully!")
        print(f"\nCalibration Matrix:\n{calibration_matrix}")
        
    except FileNotFoundError as e:
        print(f"[ERROR] FileNotFoundError: {e}")
        print("\nThis usually means:")
        print("  1. PlusServer.exe not found at the specified path")
        print("  2. Path is incorrect")
        print("\nChecking for PlusServer.exe...")
        import os
        plus_server = os.path.join(plus_path, "PlusServer.exe")
        if os.path.exists(plus_server):
            print(f"  [OK] Found: {plus_server}")
        else:
            print(f"  [ERROR] Not found: {plus_server}")
            print(f"  Files in directory:")
            try:
                for f in os.listdir(plus_path):
                    print(f"    - {f}")
            except Exception as list_err:
                print(f"    Error listing directory: {list_err}")
        traceback.print_exc()
        
    except RuntimeError as e:
        print(f"[ERROR] RuntimeError: {e}")
        print("\nThis usually means:")
        print("  1. PlusServer failed to run")
        print("  2. Configuration XML is incorrect")
        print("  3. PlusServer command-line syntax is wrong")
        traceback.print_exc()
        
    except Exception as e:
        print(f"[ERROR] Unexpected error: {type(e).__name__}: {e}")
        traceback.print_exc()

def test_plus_server_directly():
    """Test if PlusServer can be run directly."""
    print("\n=== Testing PlusServer Directly ===\n")
    
    import os
    import subprocess
    
    plus_path = r"C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin"
    plus_server = os.path.join(plus_path, "PlusServer.exe")
    
    if not os.path.exists(plus_server):
        print(f"[ERROR] PlusServer.exe not found at: {plus_server}")
        return
    
    print(f"[OK] Found PlusServer.exe at: {plus_server}")
    
    # Try to get help/version
    print("\nTesting PlusServer --help...")
    try:
        result = subprocess.run(
            [plus_server, "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
    except subprocess.TimeoutExpired:
        print("[ERROR] PlusServer --help timed out")
    except Exception as e:
        print(f"[ERROR] Error running PlusServer: {e}")
        traceback.print_exc()
    
    # Try version
    print("\nTesting PlusServer --version...")
    try:
        result = subprocess.run(
            [plus_server, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
    except Exception as e:
        print(f"[ERROR] Error: {e}")

if __name__ == "__main__":
    # Test PlusServer directly first
    test_plus_server_directly()
    
    # Then test calibration
    test_calibration()
    
    print("\n=== Test Complete ===")

