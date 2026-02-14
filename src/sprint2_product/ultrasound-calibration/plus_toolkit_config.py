"""
Configuration utility for PLUS ToolKit paths.

This module provides functions to locate PLUS ToolKit installation paths
using environment variables or default locations.
"""

import os
from pathlib import Path


def get_plus_toolkit_path():
    """
    Get the PLUS ToolKit bin directory path.
    
    Checks in order:
    1. PLUS_TOOLKIT_PATH environment variable
    2. Default Windows location: C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin
    3. Common alternative locations
    
    Returns:
        str: Path to PLUS ToolKit bin directory, or None if not found
    """
    # Check environment variable first
    env_path = os.getenv('PLUS_TOOLKIT_PATH')
    if env_path and os.path.exists(env_path):
        return os.path.abspath(env_path)
    
    # Check default Windows location
    default_path = r"C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin"
    if os.path.exists(default_path):
        return os.path.abspath(default_path)
    
    # Try to find PlusToolkit in common locations
    common_locations = [
        r"C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin",
        r"C:\Program Files\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin",
        r"C:\Program Files (x86)\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin",
    ]
    
    for location in common_locations:
        if os.path.exists(location):
            return os.path.abspath(location)
    
    return None


def get_plus_toolkit_base_path():
    """
    Get the PLUS ToolKit base installation directory (parent of bin).
    
    Returns:
        str: Path to PLUS ToolKit base directory, or None if not found
    """
    bin_path = get_plus_toolkit_path()
    if bin_path:
        return os.path.abspath(os.path.join(bin_path, ".."))
    return None


def get_plus_config_dir():
    """
    Get the PLUS ToolKit config directory.
    
    Returns:
        str: Path to config directory, or None if not found
    """
    base_path = get_plus_toolkit_base_path()
    if base_path:
        config_dir = os.path.join(base_path, "config")
        if os.path.exists(config_dir):
            return os.path.abspath(config_dir)
    return None


def get_plus_data_dir():
    """
    Get the PLUS ToolKit data directory.
    
    Returns:
        str: Path to data directory, or None if not found
    """
    base_path = get_plus_toolkit_base_path()
    if base_path:
        data_dir = os.path.join(base_path, "data")
        if os.path.exists(data_dir):
            return os.path.abspath(data_dir)
    return None


def get_pluslibdata_testimages_dir():
    """
    Get the PlusLibData TestImages directory.
    
    Returns:
        str: Path to PlusLibData TestImages directory, or None if not found
    """
    data_dir = get_plus_data_dir()
    if data_dir:
        testimages_dir = os.path.join(data_dir, "PlusLibData", "TestImages")
        if os.path.exists(testimages_dir):
            return os.path.abspath(testimages_dir)
    return None


def get_pluslibdata_config_dir():
    """
    Get the PlusLibData ConfigFiles directory.
    
    Returns:
        str: Path to PlusLibData ConfigFiles directory, or None if not found
    """
    data_dir = get_plus_data_dir()
    if data_dir:
        config_dir = os.path.join(data_dir, "PlusLibData", "ConfigFiles")
        if os.path.exists(config_dir):
            return os.path.abspath(config_dir)
    return None


def check_plus_toolkit_installation():
    """
    Check if PLUS ToolKit is properly installed.
    
    Returns:
        dict: Dictionary with installation status and paths
    """
    result = {
        'installed': False,
        'bin_path': None,
        'base_path': None,
        'config_dir': None,
        'data_dir': None,
        'pluslibdata_testimages': None,
        'pluslibdata_config': None,
        'executables': {}
    }
    
    bin_path = get_plus_toolkit_path()
    if not bin_path:
        return result
    
    result['installed'] = True
    result['bin_path'] = bin_path
    result['base_path'] = get_plus_toolkit_base_path()
    result['config_dir'] = get_plus_config_dir()
    result['data_dir'] = get_plus_data_dir()
    result['pluslibdata_testimages'] = get_pluslibdata_testimages_dir()
    result['pluslibdata_config'] = get_pluslibdata_config_dir()
    
    # Check for common executables
    executables = ['ProbeCalibration.exe', 'TemporalCalibration.exe', 'VolumeReconstructor.exe']
    for exe in executables:
        exe_path = os.path.join(bin_path, exe)
        result['executables'][exe] = os.path.exists(exe_path)
    
    return result


def print_installation_status():
    """Print the current PLUS ToolKit installation status."""
    status = check_plus_toolkit_installation()
    
    print("=" * 60)
    print("PLUS ToolKit Installation Status")
    print("=" * 60)
    
    if not status['installed']:
        print("[X] PLUS ToolKit is NOT installed or not found.")
        print("\nPlease install PLUS ToolKit and set PLUS_TOOLKIT_PATH environment variable,")
        print("or install it in the default location: C:\\PlusToolkit\\")
        return
    
    print("[OK] PLUS ToolKit is installed")
    print(f"\nBin Directory: {status['bin_path']}")
    print(f"Base Directory: {status['base_path']}")
    print(f"Config Directory: {status['config_dir']}")
    print(f"Data Directory: {status['data_dir']}")
    
    if status['pluslibdata_testimages']:
        print(f"PlusLibData TestImages: {status['pluslibdata_testimages']}")
    else:
        print("PlusLibData TestImages: [X] Not found")
    
    if status['pluslibdata_config']:
        print(f"PlusLibData ConfigFiles: {status['pluslibdata_config']}")
    else:
        print("PlusLibData ConfigFiles: [X] Not found")
    
    print("\nExecutables:")
    for exe, exists in status['executables'].items():
        status_icon = "[OK]" if exists else "[X]"
        print(f"  {status_icon} {exe}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Print installation status when run directly
    print_installation_status()

