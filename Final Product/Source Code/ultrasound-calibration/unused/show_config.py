"""
Script to generate and display the config file that will be used for calibration.
"""

import sys
from pathlib import Path
import xml.etree.ElementTree as ET

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from use_existing_mha import create_config_for_existing_mha

def show_config():
    """Generate and display the config file."""
    import tempfile
    import os
    
    # Get the .mha file path
    mha_file = Path(__file__).parent / "ElbowUltrasoundSweep.mha"
    
    if not mha_file.exists():
        print(f"[ERROR] .mha file not found: {mha_file}")
        print("Please ensure 'ElbowUltrasoundSweep.mha' is in the ultrasound-calibration directory")
        return
    
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as tmp:
        config_path = tmp.name
    
    try:
        # Generate the config file
        create_config_for_existing_mha(str(mha_file.resolve()), config_path)
        
        # Read and display it
        print("=" * 80)
        print("CONFIG FILE CONTENT")
        print("=" * 80)
        print()
        
        tree = ET.parse(config_path)
        root = tree.getroot()
        
        # Pretty print the XML
        ET.indent(tree, space="  ")
        xml_str = ET.tostring(root, encoding='unicode')
        print(xml_str)
        
        print()
        print("=" * 80)
        print(f"Config file saved to: {config_path}")
        print("=" * 80)
        
    finally:
        # Optionally keep the file for inspection
        print(f"\nConfig file kept at: {config_path}")
        print("(You can delete it manually if needed)")

if __name__ == "__main__":
    show_config()



