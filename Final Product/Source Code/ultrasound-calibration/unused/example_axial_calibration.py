"""
Example: Axial Calibration using PLUS ToolKit

This example demonstrates how to use the axial calibration module
for ultrasound probe calibration.
"""

import numpy as np
from axial_calibration import AxialCalibration
import cv2


def example_axial_calibration():
    """
    Example workflow for axial calibration.
    """
    print("=== Axial Calibration Example ===\n")
    
    # Initialize calibration
    # Option 1: Use system PATH or environment variable
    # calibrator = AxialCalibration()
    
    # Option 2: Specify PLUS ToolKit path explicitly (RECOMMENDED)
    # Update this path to match your installation
    plus_path = r"C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin"
    calibrator = AxialCalibration(plus_toolkit_path=plus_path)
    
    # Option 3: Use environment variable
    # Set: $env:PLUS_TOOLKIT_PATH = "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin"
    # Then: calibrator = AxialCalibration()
    
    # Simulate calibration data
    # In practice, these would come from:
    # - Tracker: probe poses (4x4 transformation matrices)
    # - Ultrasound device: 2D ultrasound images
    
    num_calibration_images = 10
    
    # Simulate probe poses (4x4 transformation matrices from tracker)
    probe_poses = []
    for i in range(num_calibration_images):
        # Create a simple transformation matrix
        pose = np.eye(4)
        pose[0:3, 3] = [i * 5.0, 0.0, 100.0]  # Translation
        probe_poses.append(pose)
    
    # Simulate ultrasound images (grayscale, 256x256)
    ultrasound_images = []
    for i in range(num_calibration_images):
        # Create a simple test image with a wire/phantom pattern
        img = np.zeros((256, 256), dtype=np.uint8)
        # Draw a vertical line (simulating a wire in phantom)
        cv2.line(img, (128, 50), (128, 200), 255, 2)
        ultrasound_images.append(img)
    
    print(f"Calibration data prepared:")
    print(f"  - Number of images: {len(ultrasound_images)}")
    print(f"  - Image size: {ultrasound_images[0].shape}")
    print(f"  - Number of poses: {len(probe_poses)}\n")
    
    # Perform calibration
    try:
        print("Running axial calibration...")
        calibration_matrix = calibrator.calibrate(
            probe_poses=probe_poses,
            ultrasound_images=ultrasound_images,
            calibration_phantom="wire_phantom",
            phantom_parameters={
                'wire_position': [128, 128],  # Wire position in image
                'wire_depth_mm': 50.0  # Known depth of wire in mm
            }
        )
        
        print("✓ Calibration completed successfully!")
        print(f"\nCalibration Matrix:\n{calibration_matrix}\n")
        
        # Save calibration
        calibrator.save_calibration("axial_calibration_result.xml")
        print("✓ Calibration saved to: axial_calibration_result.xml\n")
        
        # Example: Transform image coordinates to probe space
        image_coords = np.array([
            [128, 100],  # Point 1 in image (pixels)
            [128, 150],  # Point 2 in image (pixels)
            [128, 200]   # Point 3 in image (pixels)
        ])
        
        probe_coords = calibrator.image_to_probe(image_coords)
        print("Image to Probe Coordinate Transformation:")
        print(f"  Image coords (pixels):\n{image_coords}")
        print(f"  Probe coords (mm):\n{probe_coords}\n")
        
        # Load calibration from file
        calibrator2 = AxialCalibration()
        calibrator2.load_calibration("axial_calibration_result.xml")
        print("✓ Calibration loaded from file")
        print(f"  Status: {calibrator2.calibration_status}")
        
    except RuntimeError as e:
        print(f"✗ Calibration failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure PLUS ToolKit is installed")
        print("  2. Check that PLUS executables are in PATH")
        print("  3. Or specify plus_toolkit_path when initializing AxialCalibration")
        print("\nSee INSTALLATION.md for detailed setup instructions.")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


def example_integration_with_hand_eye():
    """
    Example of integrating axial calibration with existing hand-eye calibration.
    """
    print("\n=== Integration with Hand-Eye Calibration ===\n")
    
    # Load existing hand-eye calibration
    # (This would come from your existing calibration_io.py)
    from pathlib import Path
    import sys
    
    # Add parent directory to path to import hand-eye calibration modules
    parent_dir = Path(__file__).parent.parent / "hand-eye-calibration"
    sys.path.insert(0, str(parent_dir))
    
    try:
        import calibration_io as cio
        
        # Load hand-eye calibration (camera-to-tracker transformation)
        he_cal_file = "hand_eye_calibration.xml"  # Your existing calibration file
        if Path(he_cal_file).exists():
            int_mat, dist_coeffs, ext_mat = cio.readHECalibrationFromXml(he_cal_file)
            print(f"✓ Loaded hand-eye calibration from {he_cal_file}")
            print(f"  Extrinsic matrix (camera-to-tracker):\n{ext_mat}\n")
        
        # Initialize axial calibration
        axial_cal = AxialCalibration()
        
        # Load axial calibration (image-to-probe transformation)
        axial_cal_file = "axial_calibration_result.xml"
        if Path(axial_cal_file).exists():
            axial_cal.load_calibration(axial_cal_file)
            print(f"✓ Loaded axial calibration from {axial_cal_file}")
            print(f"  Calibration matrix (image-to-probe):\n{axial_cal.get_calibration_matrix()}\n")
        
        # Combined transformation chain:
        # Image space → Probe space → Tracker space → Camera space → World space
        print("Transformation chain:")
        print("  Image → Probe: Axial calibration")
        print("  Probe → Tracker: Probe pose (from tracker)")
        print("  Tracker → Camera: Hand-eye calibration")
        print("  Camera → World: Camera pose (from tracker)")
        
    except ImportError:
        print("Note: Hand-eye calibration module not found in expected location.")
        print("This is just an example of integration workflow.")


if __name__ == "__main__":
    # Run basic example
    example_axial_calibration()
    
    # Run integration example
    example_integration_with_hand_eye()
    
    print("\n=== Example Complete ===")


