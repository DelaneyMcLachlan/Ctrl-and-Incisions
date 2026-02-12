"""
Debug script to see what XML is being generated and save it for inspection.
"""

import sys
from pathlib import Path
import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).parent))

from axial_calibration import AxialCalibration

# Create test data
probe_poses = [np.eye(4) for _ in range(3)]
ultrasound_images = [np.zeros((256, 256), dtype=np.uint8) for _ in range(3)]

# Initialize
calibrator = AxialCalibration(
    plus_toolkit_path=r"C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin"
)

# Manually create XML to inspect
import tempfile
import os
temp_dir = tempfile.mkdtemp()
config_file = os.path.join(temp_dir, "debug_config.xml")

# Save test images
images_dir = os.path.join(temp_dir, "images")
os.makedirs(images_dir, exist_ok=True)
image_files = []
for i, img in enumerate(ultrasound_images):
    img_file = os.path.join(images_dir, f"image_{i:04d}.png")
    cv2.imwrite(img_file, img)
    image_files.append(img_file)

# Create XML
calibrator._create_plus_config_xml(
    config_file, probe_poses, image_files, "wire_phantom", None
)

print(f"XML saved to: {config_file}")
print("\nXML Content:")
with open(config_file, 'r') as f:
    print(f.read())

