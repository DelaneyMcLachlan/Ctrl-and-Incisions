"""
Script to use existing .mha sequence file for calibration.
"""

import sys
from pathlib import Path
import xml.etree.ElementTree as ET

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from axial_calibration import AxialCalibration

def create_config_for_existing_mha(mha_file_path: str, output_config_path: str):
    """
    Create a PLUS ToolKit config file that uses an existing .mha sequence file.
    
    Args:
        mha_file_path: Path to existing .mha file
        output_config_path: Where to save the config file
    """
    root = ET.Element("PlusConfiguration")
    root.set("version", "2.1")
    
    # DataCollection with DeviceSet
    data_collection = ET.SubElement(root, "DataCollection")
    data_collection.set("StartupDelaySec", "1.0")
    
    device_set = ET.SubElement(data_collection, "DeviceSet")
    device_set.set("Name", "Calibration: Elbow Sweep")
    device_set.set("Description", "Calibration using existing elbow sweep sequence")
    
    # Device for reading sequence file
    tracked_video_device = ET.SubElement(device_set, "Device")
    tracked_video_device.set("Id", "TrackedVideoDevice")
    tracked_video_device.set("Type", "SavedDataSource")
    tracked_video_device.set("SequenceFile", mha_file_path)
    tracked_video_device.set("UseData", "IMAGE_AND_TRANSFORM")
    tracked_video_device.set("UseOriginalTimestamps", "TRUE")
    tracked_video_device.set("RepeatEnabled", "TRUE")
    
    # Data sources
    data_sources = ET.SubElement(tracked_video_device, "DataSources")
    video_source = ET.SubElement(data_sources, "DataSource")
    video_source.set("Type", "Video")
    video_source.set("Id", "Video")
    
    # Output channels
    output_channels = ET.SubElement(tracked_video_device, "OutputChannels")
    output_channel = ET.SubElement(output_channels, "OutputChannel")
    output_channel.set("Id", "TrackedVideoStream")
    output_channel.set("VideoDataSourceId", "Video")
    
    # PhantomDefinition (required)
    # Note: For elbow sweep, this might not be a calibration phantom
    # But ProbeCalibration requires it, so we'll add a basic definition
    # You may need to adjust this based on your actual calibration setup
    phantom_def = ET.SubElement(root, "PhantomDefinition")
    description = ET.SubElement(phantom_def, "Description")
    description.set("Name", "WirePhantom")
    description.set("Type", "Wire")
    description.set("Version", "1.0")
    
    geometry = ET.SubElement(phantom_def, "Geometry")
    pattern = ET.SubElement(geometry, "Pattern")
    pattern.set("Type", "Wire")
    # Basic wire definition (you may need to adjust based on your phantom)
    wire = ET.SubElement(pattern, "Wire")
    wire.set("Name", "Wire1")
    wire.set("EndPointFront", "30.0 0.0 20.0")
    wire.set("EndPointBack", "30.0 40.0 20.0")
    
    # Note: If this is an elbow sweep (not a calibration phantom), 
    # you might need a different calibration approach
    
    # Segmentation section (required - based on example config)
    segmentation = ET.SubElement(root, "Segmentation")
    segmentation.set("ApproximateSpacingMmPerPixel", "0.078")
    segmentation.set("MorphologicalOpeningCircleRadiusMm", "0.27")
    segmentation.set("MorphologicalOpeningBarSizeMm", "2.0")
    segmentation.set("ClipRectangleOrigin", "27 27")
    segmentation.set("ClipRectangleSize", "766 562")
    segmentation.set("MaxLinePairDistanceErrorPercent", "10")
    segmentation.set("AngleToleranceDegrees", "10")
    segmentation.set("MaxAngleDifferenceDegrees", "10")
    segmentation.set("MinThetaDegrees", "-70")
    segmentation.set("MaxThetaDegrees", "70")
    segmentation.set("MaxLineShiftMm", "10.0")
    segmentation.set("ThresholdImagePercent", "10")
    segmentation.set("CollinearPointsMaxDistanceFromLineMm", "0.6")
    segmentation.set("UseOriginalImageIntensityForDotIntensityScore", "FALSE")
    segmentation.set("NumberOfMaximumFiducialPointCandidates", "20")
    
    # vtkPlusProbeCalibrationAlgo (required)
    probe_cal_algo = ET.SubElement(root, "vtkPlusProbeCalibrationAlgo")
    probe_cal_algo.set("ImageCoordinateFrame", "Image")
    probe_cal_algo.set("ProbeCoordinateFrame", "Probe")
    probe_cal_algo.set("PhantomCoordinateFrame", "Phantom")
    probe_cal_algo.set("ReferenceCoordinateFrame", "Reference")
    
    # Write config file
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(output_config_path, encoding="utf-8", xml_declaration=True)
    
    print(f"[OK] Created config file: {output_config_path}")
    return output_config_path

def run_calibration_with_mha(mha_file_path: str, config_file_path: str = None):
    """
    Run calibration using existing .mha file.
    
    Args:
        mha_file_path: Path to .mha sequence file
        config_file_path: Path to PLUS ToolKit config file. If None, uses the default one.
    """
    import tempfile
    import os
    
    print("=== Running Calibration with Existing .mha File ===\n")
    
    # Get absolute path to .mha file
    mha_path = Path(mha_file_path).resolve()
    if not mha_path.exists():
        print(f"[ERROR] .mha file not found: {mha_path}")
        return
    
    print(f"[OK] Found .mha file: {mha_path}")
    print(f"     File size: {mha_path.stat().st_size / 1024 / 1024:.2f} MB\n")
    
    # Use real config file from PLUS ToolKit installation
    if config_file_path is None:
        config_file_path = r"C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\config\PlusDeviceSet_fCal_Sim_SpatialCalibration_2.0.xml"
    
    config_file = Path(config_file_path).resolve()
    if not config_file.exists():
        print(f"[ERROR] Config file not found: {config_file}")
        return
    
    print(f"[OK] Using config file: {config_file}\n")
    
    # Initialize calibrator
    calibrator = AxialCalibration(
        plus_toolkit_path=r"C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin"
    )
    
    # Run ProbeCalibration
    probe_cal_path = os.path.join(calibrator.plus_toolkit_path, "ProbeCalibration.exe")
    if not os.path.exists(probe_cal_path):
        print(f"[ERROR] ProbeCalibration.exe not found at: {probe_cal_path}")
        return
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        output_config = os.path.join(output_dir, "calibration_result.xml")
        
        import subprocess
        # Use --calibration-seq-file argument as per PLUS docs
        # This overrides the SequenceFile in the config
        cmd = [
            probe_cal_path,
            f"--config-file={config_file}",
            f"--calibration-seq-file={mha_path}",
            f"--output-config-file={output_config}"
        ]
        
        print(f"Running: {' '.join(cmd)}\n")
        print("Config file:", config_file)
        print("Sequence file (--calibration-seq-file):", mha_path)
        print()
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"\n[OK] Calibration completed successfully!")
            print(f"     Output config: {output_config}")
            
            # Try to read calibration result
            if os.path.exists(output_config):
                print(f"\n[OK] Calibration result file exists")
                # Parse and extract calibration matrix
                # (Implementation depends on output format)
        else:
            print(f"\n[ERROR] Calibration failed (exit code: {result.returncode})")

if __name__ == "__main__":
    # Use the elbow sweep .mha file
    mha_file = Path(__file__).parent / "ElbowUltrasoundSweep.mha"
    
    if mha_file.exists():
        run_calibration_with_mha(str(mha_file))
    else:
        print(f"[ERROR] .mha file not found: {mha_file}")
        print("Please ensure 'ElbowUltrasoundSweep.mha' is in the ultrasound-calibration directory")

