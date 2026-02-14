"""
Test script to run ProbeCalibration with simulated configs.
These configs use simulated ultrasound and phantom data, so no .mha file is needed.
"""

import sys
from pathlib import Path
import os
import subprocess
import argparse
from datetime import datetime

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import PlusToolkit config utility
try:
    from plus_toolkit_config import (
        get_plus_toolkit_path,
        get_plus_config_dir,
        get_pluslibdata_config_dir,
        get_pluslibdata_testimages_dir
    )
except ImportError:
    # Fallback functions if module not found
    def get_plus_toolkit_path():
        env_path = os.getenv('PLUS_TOOLKIT_PATH')
        if env_path and os.path.exists(env_path):
            return os.path.abspath(env_path)
        default = r"C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin"
        return os.path.abspath(default) if os.path.exists(default) else None
    
    def get_plus_config_dir():
        bin_path = get_plus_toolkit_path()
        if bin_path:
            config_dir = os.path.join(bin_path, "..", "config")
            return os.path.abspath(config_dir) if os.path.exists(config_dir) else None
        return None
    
    def get_pluslibdata_config_dir():
        bin_path = get_plus_toolkit_path()
        if bin_path:
            config_dir = os.path.join(bin_path, "..", "data", "PlusLibData", "ConfigFiles")
            return os.path.abspath(config_dir) if os.path.exists(config_dir) else None
        return None
    
    def get_pluslibdata_testimages_dir():
        bin_path = get_plus_toolkit_path()
        if bin_path:
            testimages_dir = os.path.join(bin_path, "..", "data", "PlusLibData", "TestImages")
            return os.path.abspath(testimages_dir) if os.path.exists(testimages_dir) else None
        return None

def run_simulated_calibration(config_file_path: str, sequence_file: str = None, calibration_type: str = "auto"):
    """
    Run ProbeCalibration with a simulated config file.
    
    Args:
        config_file_path: Path to PLUS ToolKit simulated config file
        sequence_file: Optional path to sequence file. If None, tries to find it from config.
        calibration_type: Type of calibration - "spatial", "temporal", "pivot", or "auto" (detected from config filename)
    """
    # Detect calibration type from filename if auto
    if calibration_type == "auto":
        config_name = Path(config_file_path).name.lower()
        if "temporal" in config_name:
            calibration_type = "temporal"
        elif "pivot" in config_name:
            calibration_type = "pivot"
        elif "spatial" in config_name:
            calibration_type = "spatial"
        else:
            calibration_type = "unknown"
    
    print("=" * 80)
    print(f"TESTING WITH {calibration_type.upper()} CALIBRATION CONFIG")
    print("=" * 80)
    print()
    
    # Check config file exists
    config_file = Path(config_file_path).resolve()
    if not config_file.exists():
        print(f"[ERROR] Config file not found: {config_file}")
        return
    
    print(f"[OK] Using config file: {config_file}")
    
    # Parse config to find sequence file if needed
    import xml.etree.ElementTree as ET
    try:
        tree = ET.parse(config_file)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"[ERROR] Failed to parse config file as XML: {e}")
        return
    except Exception as e:
        print(f"[ERROR] Error reading config file: {e}")
        return
    
    # Analyze config file structure
    print("\n[INFO] Analyzing config file structure...")
    has_phantom = root.find(".//PhantomDefinition") is not None
    has_data_collection = root.find(".//DataCollection") is not None
    has_device_set = root.find(".//DeviceSet") is not None
    
    # Check for calibration algorithm based on type
    if calibration_type == "temporal":
        has_cal_algo = root.find(".//vtkTemporalCalibrationAlgo") is not None
        algo_name = "vtkTemporalCalibrationAlgo"
    elif calibration_type == "pivot":
        has_cal_algo = root.find(".//vtkPlusPivotCalibrationAlgo") is not None
        algo_name = "vtkPlusPivotCalibrationAlgo"
    else:  # spatial or unknown
        has_cal_algo = root.find(".//vtkPlusProbeCalibrationAlgo") is not None
        algo_name = "vtkPlusProbeCalibrationAlgo"
    
    print(f"  [{'OK' if has_phantom else 'MISSING'}] PhantomDefinition: {'Found' if has_phantom else 'MISSING'}")
    print(f"  [{'OK' if has_cal_algo else 'MISSING'}] {algo_name}: {'Found' if has_cal_algo else 'MISSING'}")
    print(f"  [{'OK' if has_data_collection else 'MISSING'}] DataCollection: {'Found' if has_data_collection else 'MISSING'}")
    print(f"  [{'OK' if has_device_set else 'MISSING'}] DeviceSet: {'Found' if has_device_set else 'MISSING'}")
    
    if not has_phantom and calibration_type != "temporal":
        print("  [WARNING] PhantomDefinition missing - this may cause calibration to fail")
    if not has_cal_algo:
        print(f"  [WARNING] {algo_name} missing - this may cause calibration to fail")
    print()
    
    # Find SequenceFile(s) in config
    # Temporal calibration may have multiple sequence files (one for tracking, one for video)
    seq_files_from_config = []
    temporal_fixed_seq = None  # Video sequence (fixed)
    temporal_moving_seq = None  # Tracking sequence (moving)
    temporal_fixed_source = None  # Source ID for fixed (usually "Video")
    temporal_moving_source = None  # Transform name for moving (e.g., "ProbeToTracker")
    
    # For temporal calibration, also get the source IDs from vtkTemporalCalibrationAlgo
    # Also check for working Synthetic files from PlusLibData
    if calibration_type == "temporal":
        temporal_algo = root.find(".//vtkTemporalCalibrationAlgo")
        if temporal_algo is not None:
            temporal_fixed_source = temporal_algo.get("FixedSourceId")
            temporal_moving_source = temporal_algo.get("MovingSourceId")
        
        # Try to use working Synthetic files from PlusLibData if available
        # These are known to work with TemporalCalibration.exe
        # Note: plus_toolkit_path is defined later, so we'll check after it's defined
    
    for device in root.findall(".//Device[@Type='SavedDataSource']"):
        seq_file_attr = device.get("SequenceFile")
        use_data = device.get("UseData", "")
        device_id = device.get("Id", "")
        
        if seq_file_attr:
            seq_files_from_config.append(seq_file_attr)
            
            # For temporal calibration, identify which is video (fixed) and which is tracking (moving)
            if calibration_type == "temporal":
                if use_data == "IMAGE" or "Video" in device_id:
                    temporal_fixed_seq = seq_file_attr  # Video is the fixed sequence
                elif use_data == "TRANSFORM" or "Tracker" in device_id:
                    temporal_moving_seq = seq_file_attr  # Tracking is the moving sequence
    
    # For temporal calibration, we need to identify fixed and moving sequences
    if calibration_type == "temporal":
        # Check for working files from PlusLibData (tested and verified to work)
        pluslibdata_testimages = get_pluslibdata_testimages_dir()
        
        # Try files in order of preference (best working first - verified by testing)
        # Option 1: ShortTrackedUltrasoundCapture (works best - completes with results, only warnings)
        short_tracked = os.path.join(pluslibdata_testimages, "ShortTrackedUltrasoundCapture.igs.mha")
        # Option 2: fCal file (works but may have signal detection issues)
        fcal_file = os.path.join(pluslibdata_testimages, "fCal_Test_Calibration_3NWires_fCal2.0.igs.mha")
        # Option 3: Combined file (may have issues with signal detection)
        combined_file = os.path.join(pluslibdata_testimages, "WaterTankBottomTranslationCombined.igs.mha")
        
        if os.path.exists(short_tracked):
            print("[INFO] Found ShortTrackedUltrasoundCapture file in PlusLibData")
            print("[INFO] Using: ShortTrackedUltrasoundCapture.igs.mha")
            print("[INFO] Verified to work with TemporalCalibration.exe - completes successfully")
            print("[INFO] Note: May show line segmentation warnings but calibration completes")
            temporal_fixed_seq = "ShortTrackedUltrasoundCapture.igs.mha"
            temporal_moving_seq = "ShortTrackedUltrasoundCapture.igs.mha"  # Same file for both
            temporal_moving_source = None
        elif os.path.exists(fcal_file):
            print("[INFO] Found fCal sequence file in PlusLibData")
            print("[INFO] Using: fCal_Test_Calibration_3NWires_fCal2.0.igs.mha")
            temporal_fixed_seq = "fCal_Test_Calibration_3NWires_fCal2.0.igs.mha"
            temporal_moving_seq = "fCal_Test_Calibration_3NWires_fCal2.0.igs.mha"  # Same file for both
            temporal_moving_source = None
        elif os.path.exists(combined_file):
            print("[INFO] Found combined sequence file in PlusLibData")
            print("[INFO] Using: WaterTankBottomTranslationCombined.igs.mha")
            temporal_fixed_seq = "WaterTankBottomTranslationCombined.igs.mha"
            temporal_moving_seq = "WaterTankBottomTranslationCombined.igs.mha"  # Same file for both
            temporal_moving_source = None
        else:
            print(f"[INFO] Temporal calibration detected - found {len(seq_files_from_config)} sequence file(s) in config")
            if temporal_fixed_seq:
                print(f"  Fixed sequence (video): {temporal_fixed_seq}")
            if temporal_moving_seq:
                print(f"  Moving sequence (tracking): {temporal_moving_seq}")
            if temporal_fixed_source:
                print(f"  Fixed source ID: {temporal_fixed_source}")
            if temporal_moving_source:
                print(f"  Moving source ID (transform): {temporal_moving_source}")
            if not temporal_fixed_seq or not temporal_moving_seq:
                print("  [WARNING] Could not identify fixed/moving sequences from config")
                print("     Will try to use first sequence as fixed, second as moving")
                if len(seq_files_from_config) >= 2:
                    temporal_fixed_seq = seq_files_from_config[0]
                    temporal_moving_seq = seq_files_from_config[1]
        print()
        seq_file_from_config = None
    else:
        # For spatial/pivot calibration, use the first sequence file found
        seq_file_from_config = seq_files_from_config[0] if seq_files_from_config else None
    
    # Find the correct calibration executable based on type
    plus_toolkit_path = get_plus_toolkit_path()
    if not plus_toolkit_path:
        print("[ERROR] PLUS ToolKit not found. Please install PLUS ToolKit and set PLUS_TOOLKIT_PATH environment variable.")
        print("        See INSTALLATION.md for instructions.")
        return
    
    plus_config_dir = get_plus_config_dir()
    
    # Choose the correct executable
    if calibration_type == "temporal":
        cal_exe_name = "TemporalCalibration.exe"
    else:  # spatial, pivot, or unknown
        cal_exe_name = "ProbeCalibration.exe"
    
    cal_exe_path = os.path.join(plus_toolkit_path, cal_exe_name)
    
    if not os.path.exists(cal_exe_path):
        print(f"[ERROR] {cal_exe_name} not found at: {cal_exe_path}")
        print(f"       Expected location: {plus_toolkit_path}")
        return
    
    print(f"[OK] Found {cal_exe_name}: {cal_exe_path}\n")
    
    # Check if sequence file exists
    if seq_file_from_config:
        # Try to find the sequence file (check data folder, config folder, etc.)
        plus_data_dir = os.path.join(plus_toolkit_path, "..", "data")
        plus_data_dir = os.path.abspath(plus_data_dir)
        
        possible_locations = [
            os.path.join(plus_data_dir, seq_file_from_config),  # data folder
            os.path.join(plus_config_dir, seq_file_from_config),  # config folder
            os.path.join(plus_toolkit_path, seq_file_from_config),  # bin folder
            os.path.join(plus_toolkit_path, "..", seq_file_from_config),  # parent folder
            seq_file_from_config  # Absolute path
        ]
        
        found_seq_file = None
        for loc in possible_locations:
            if os.path.exists(loc):
                found_seq_file = os.path.abspath(loc)
                break
        
        if found_seq_file:
            print(f"[OK] Found sequence file from config: {found_seq_file}")
            sequence_file = found_seq_file
        else:
            print(f"[WARNING] Sequence file from config not found: {seq_file_from_config}")
            print(f"          Tried locations: {possible_locations[:2]}")
            print(f"          Will try without --calibration-seq-file\n")
    
    # Run ProbeCalibration
    # Create output directory in current script directory
    script_dir = Path(__file__).parent
    output_dir = script_dir / "calibration_output"
    output_dir.mkdir(exist_ok=True)
    
    # Create timestamped output filename with calibration type
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_config = output_dir / f"{calibration_type}_calibration_result_{timestamp}.xml"
    
    # Build command - TemporalCalibration.exe has different arguments than ProbeCalibration.exe
    if calibration_type == "temporal":
        # TemporalCalibration.exe uses --fixed-seq-file and --moving-seq-file
        # It does NOT use --config-file or --output-config-file
        cmd = [cal_exe_path]
        
        # Find the sequence files
        plus_data_dir = os.path.join(plus_toolkit_path, "..", "data")
        plus_data_dir = os.path.abspath(plus_data_dir)
        
        def find_seq_file(seq_file_name):
            """Find a sequence file in common locations"""
            pluslibdata_testimages = os.path.join(plus_toolkit_path, "..", "data", "PlusLibData", "TestImages")
            possible_locations = [
                os.path.join(pluslibdata_testimages, seq_file_name),  # PlusLibData TestImages (preferred)
                os.path.join(plus_data_dir, seq_file_name),  # Regular data folder
                os.path.join(plus_config_dir, seq_file_name),  # Config folder
                os.path.join(plus_toolkit_path, seq_file_name),  # Bin folder
                os.path.join(plus_toolkit_path, "..", seq_file_name),  # Parent folder
                seq_file_name  # Absolute path
            ]
            for loc in possible_locations:
                if os.path.exists(loc):
                    return os.path.abspath(loc)
            return None
        
        # Use sequences as specified (no swapping needed for working files)
        fixed_seq_to_use = temporal_fixed_seq
        moving_seq_to_use = temporal_moving_seq
        
        if fixed_seq_to_use == moving_seq_to_use:
            print("[INFO] Using combined sequence file (contains both video and tracking):")
            print(f"       File: {fixed_seq_to_use}")
        else:
            print("[INFO] Using separate sequence files:")
            print(f"       Fixed (video): {fixed_seq_to_use}")
            print(f"       Moving (tracking): {moving_seq_to_use}")
        
        # Add fixed sequence file
        if fixed_seq_to_use:
            fixed_seq_path = find_seq_file(fixed_seq_to_use)
            if fixed_seq_path:
                cmd.append(f"--fixed-seq-file={fixed_seq_path}")
                print(f"[OK] Found fixed sequence file: {fixed_seq_path}")
            else:
                print(f"[WARNING] Fixed sequence file not found: {fixed_seq_to_use}")
                cmd.append(f"--fixed-seq-file={fixed_seq_to_use}")  # Try anyway
        
        # Add moving sequence file (should have images if swapped)
        if moving_seq_to_use:
            moving_seq_path = find_seq_file(moving_seq_to_use)
            if moving_seq_path:
                cmd.append(f"--moving-seq-file={moving_seq_path}")
                print(f"[OK] Found moving sequence file: {moving_seq_path}")
            else:
                print(f"[WARNING] Moving sequence file not found: {moving_seq_to_use}")
                cmd.append(f"--moving-seq-file={moving_seq_to_use}")  # Try anyway
        
        # Add transform parameters based on config
        # Config shows: FixedSourceId="Video", MovingSourceId="ProbeToTracker"
        # This means: Fixed=Video, Moving=Tracking (with ProbeToTracker transform)
        if temporal_moving_source and temporal_moving_source != "Video":
            # Moving sequence contains tracking data - specify the transform
            cmd.append(f"--moving-probe-to-reference-transform={temporal_moving_source}")
            print(f"[INFO] Moving sequence contains TRACKING data")
            print(f"[INFO] Using transform '{temporal_moving_source}' from moving sequence")
        else:
            # Moving sequence contains video data - no transform parameter needed
            print(f"[INFO] Moving sequence contains VIDEO data (no transform parameter)")
        
        # Also check fixed sequence - if it's not "Video", it might need transform too
        if temporal_fixed_source and temporal_fixed_source != "Video":
            cmd.append(f"--fixed-probe-to-reference-transform={temporal_fixed_source}")
            print(f"[INFO] Fixed sequence contains TRACKING data")
            print(f"[INFO] Using transform '{temporal_fixed_source}' from fixed sequence")
        
        # Also check if fixed sequence might need transform parameter
        if temporal_fixed_source and temporal_fixed_source != "Video":
            # If fixed source is not "Video", it might be tracking data
            cmd.append(f"--fixed-probe-to-reference-transform={temporal_fixed_source}")
            print(f"[INFO] Using transform '{temporal_fixed_source}' from fixed sequence")
        
        # Note: TemporalCalibration.exe doesn't have --output-config-file
        # Results may be written to stdout or a default location
        print(f"[INFO] TemporalCalibration.exe will output results (check stdout for time offset)")
        print()
        print("[NOTE] If you get 'no valid images' error, try:")
        print("  1. The sequence files might need to be swapped (fixed <-> moving)")
        print("  2. Or use a combined sequence file with both images and tracking")
        print("  3. Or the sequence files might not be in the correct format")
        
    else:
        # ProbeCalibration.exe uses --config-file and --output-config-file
        cmd = [
            cal_exe_path,
            f"--config-file={config_file}",
            f"--output-config-file={output_config}"
        ]
        
        # Add sequence file if provided
        if sequence_file:
            cmd.append(f"--calibration-seq-file={sequence_file}")
    
    print("=" * 80)
    print("COMMAND:")
    print("=" * 80)
    print(" ".join(cmd))
    print()
    
    print("=" * 80)
    print("RUNNING CALIBRATION...")
    print("=" * 80)
    print()
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    
    # Save output to log files for debugging
    log_dir = script_dir / "calibration_output" / "logs"
    log_dir.mkdir(exist_ok=True)
    stdout_log = log_dir / f"stdout_{timestamp}.txt"
    stderr_log = log_dir / f"stderr_{timestamp}.txt"
    
    with open(stdout_log, 'w', encoding='utf-8') as f:
        f.write(result.stdout)
    if result.stderr:
        with open(stderr_log, 'w', encoding='utf-8') as f:
            f.write(result.stderr)
    
    print("STDOUT:")
    print(result.stdout)
    print()
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
        print()
    
    if result.returncode == 0:
        print("=" * 80)
        print("[SUCCESS] Calibration completed successfully!")
        print("=" * 80)
        
        if calibration_type == "temporal":
            # TemporalCalibration.exe outputs to stdout, not a file
            print("Temporal calibration results are in the stdout above.")
            print("Look for the time offset value (in seconds) in the output.")
            print(f"Full output saved to: {stdout_log}")
        else:
            print(f"Output config: {output_config}")
            print(f"Output directory: {output_dir}")
            
            if os.path.exists(output_config):
                print(f"[OK] Calibration result file exists")
                print(f"     You can find it at: {output_config}")
    else:
        print("=" * 80)
        print(f"[ERROR] Calibration failed (exit code: {result.returncode})")
        print("=" * 80)
        print()
        print("ERROR ANALYSIS:")
        print("-" * 80)
        
        # Analyze common error patterns
        error_output = result.stderr + result.stdout
        
        if "Unable to find" in error_output or "not found" in error_output.lower():
            print("[ERROR] Missing file or element error detected")
            # Try to extract what's missing
            import re
            missing = re.search(r"(?:Unable to find|not found|does not exist)[^\n]*", error_output, re.IGNORECASE)
            if missing:
                print(f"   Missing: {missing.group()}")
        
        if "phantom" in error_output.lower() and "definition" in error_output.lower():
            print("[ERROR] Phantom definition error detected")
            print("   The config file may be missing PhantomDefinition section")
        
        if "vtkPlusProbeCalibrationAlgo" in error_output or "vtkTemporalCalibrationAlgo" in error_output:
            print("[ERROR] Calibration algorithm element missing")
            if calibration_type == "temporal":
                print("   The config file may be missing vtkTemporalCalibrationAlgo section")
            else:
                print("   The config file may be missing vtkPlusProbeCalibrationAlgo section")
        
        if "sequence" in error_output.lower() or "seq-file" in error_output.lower():
            print("[ERROR] Sequence file error detected")
            print("   Check if the sequence file exists and is in the correct format")
        
        if "temporal" in error_output.lower():
            print("[WARNING] Temporal calibration specific error")
            print("   Temporal calibration may require different parameters than spatial calibration")
        
        print()
        print(f"Full error logs saved to:")
        print(f"  STDOUT: {stdout_log}")
        if result.stderr:
            print(f"  STDERR: {stderr_log}")
        print()
        print("To debug further:")
        print("1. Check the log files above for detailed error messages")
        print("2. Verify the config file exists and is valid XML")
        print("3. Compare with a working spatial calibration config")
        print("4. Check if temporal calibration requires different command-line arguments")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run PLUS ToolKit calibration with simulated configs")
    parser.add_argument(
        "--type", 
        choices=["spatial", "temporal", "pivot"],
        default="spatial",
        help="Type of calibration to run (default: spatial)"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to config file (overrides --type)"
    )
    
    args = parser.parse_args()
    
    # Determine config file
    if args.config:
        config_file = args.config
        calibration_type = "auto"  # Auto-detect from filename
    else:
        # Try PlusLibData first (has working examples), fall back to regular config
        plus_config_dir = get_plus_config_dir()
        pluslibdata_config_dir = get_pluslibdata_config_dir()
        
        if not plus_config_dir:
            print("[ERROR] PLUS ToolKit config directory not found.")
            print("        Please install PLUS ToolKit and set PLUS_TOOLKIT_PATH environment variable.")
            print("        See INSTALLATION.md for instructions.")
            sys.exit(1)
        
        config_files = {
            "spatial": "PlusDeviceSet_fCal_Sim_SpatialCalibration_2.0.xml",
            "temporal": "PlusDeviceSet_fCal_Sim_TemporalCalibration.xml",
            "pivot": "PlusDeviceSet_fCal_Sim_PivotCalibration.xml"
        }
        
        # Check PlusLibData first (has working test data)
        pluslibdata_config = os.path.join(pluslibdata_config_dir, config_files[args.type])
        regular_config = os.path.join(plus_config_dir, config_files[args.type])
        
        if os.path.exists(pluslibdata_config):
            config_file = pluslibdata_config
            print(f"[INFO] Using PlusLibData config (has working test data)")
            print(f"       Config: {config_file}")
        elif os.path.exists(regular_config):
            config_file = regular_config
            print(f"[INFO] Using regular config (PlusLibData not found)")
            print(f"       Config: {config_file}")
        else:
            config_file = regular_config  # Will show error later
            print(f"[WARNING] Config file not found, will try: {config_file}")
        
        calibration_type = args.type
    
    print(f"Running {calibration_type} calibration...")
    print(f"Config file: {config_file}")
    print()
    
    run_simulated_calibration(config_file, calibration_type=calibration_type)
    
    print("\n" + "=" * 80)
    print("Usage examples:")
    print("  python test_simulated_calibration.py --type spatial")
    print("  python test_simulated_calibration.py --type temporal")
    print("  python test_simulated_calibration.py --type pivot")
    print("  python test_simulated_calibration.py --config path/to/custom_config.xml")
    print("=" * 80)

