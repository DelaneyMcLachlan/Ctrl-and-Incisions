"""
Quick setup script to configure PLUS ToolKit path.

This script helps you set up the PLUS_TOOLKIT_PATH environment variable
or test your PLUS ToolKit installation.
"""

import os
import sys
from pathlib import Path


def set_plus_path_windows(plus_path: str):
    """
    Set PLUS_TOOLKIT_PATH environment variable for Windows (current session).
    
    Args:
        plus_path: Path to PLUS ToolKit bin directory
    """
    # Normalize path
    plus_path = os.path.normpath(plus_path)
    
    # Verify path exists
    if not os.path.exists(plus_path):
        print(f"✗ Error: Path does not exist: {plus_path}")
        return False
    
    # Check for PlusServer.exe
    plus_server = os.path.join(plus_path, "PlusServer.exe")
    if not os.path.exists(plus_server):
        print(f"⚠ Warning: PlusServer.exe not found in {plus_path}")
        print("  Make sure this is the 'bin' directory of your PLUS installation.")
    else:
        print(f"✓ Found PlusServer.exe at: {plus_server}")
    
    # Set environment variable for current session
    os.environ['PLUS_TOOLKIT_PATH'] = plus_path
    print(f"✓ Set PLUS_TOOLKIT_PATH = {plus_path} (current session only)")
    
    return True


def test_plus_installation(plus_path: str = None):
    """
    Test PLUS ToolKit installation.
    
    Args:
        plus_path: Optional path to PLUS ToolKit. If None, uses environment variable.
    """
    print("=== Testing PLUS ToolKit Installation ===\n")
    
    if plus_path is None:
        plus_path = os.environ.get('PLUS_TOOLKIT_PATH', None)
    
    if plus_path:
        plus_path = os.path.normpath(plus_path)
        print(f"Using path: {plus_path}\n")
    else:
        print("No PLUS ToolKit path specified.\n")
        return False
    
    # Check if path exists
    if not os.path.exists(plus_path):
        print(f"✗ Error: Path does not exist: {plus_path}")
        return False
    
    # Check for common executables
    executables = ["PlusServer.exe", "PlusCalibration.exe", "PlusServer", "PlusCalibration"]
    found_executables = []
    
    for exe in executables:
        exe_path = os.path.join(plus_path, exe)
        if os.path.exists(exe_path):
            found_executables.append(exe)
            print(f"✓ Found: {exe}")
    
    if not found_executables:
        print("✗ No PLUS executables found in specified path")
        print(f"  Checked: {plus_path}")
        return False
    
    # Try to import the calibration module
    try:
        from axial_calibration import AxialCalibration
        calibrator = AxialCalibration(plus_toolkit_path=plus_path)
        print("\n✓ AxialCalibration module initialized successfully!")
        return True
    except Exception as e:
        print(f"\n✗ Error initializing AxialCalibration: {e}")
        return False


if __name__ == "__main__":
    # Default path based on user's installation
    default_path = r"C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin"
    
    if len(sys.argv) > 1:
        plus_path = sys.argv[1]
    else:
        plus_path = default_path
        print(f"Using default path: {plus_path}")
        print("To specify a different path, run: python setup_plus_path.py <path>\n")
    
    # Test installation
    if test_plus_installation(plus_path):
        print("\n=== Setup Complete ===")
        print("\nTo use this path permanently, you have two options:")
        print("\n1. Set environment variable (PowerShell - current session):")
        print(f'   $env:PLUS_TOOLKIT_PATH = "{plus_path}"')
        print("\n2. Set environment variable (PowerShell - permanently):")
        print(f'   [Environment]::SetEnvironmentVariable("PLUS_TOOLKIT_PATH", "{plus_path}", "User")')
        print("\n3. Or specify path in code:")
        print(f'   calibrator = AxialCalibration(plus_toolkit_path=r"{plus_path}")')
    else:
        print("\n=== Setup Failed ===")
        print(f"\nPlease verify your PLUS ToolKit installation at: {plus_path}")
        print("The path should point to the 'bin' directory containing PlusServer.exe")

