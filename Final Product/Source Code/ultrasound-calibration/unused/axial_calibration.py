"""
Axial Calibration Module

Provides axial calibration functionality using PLUS ToolKit.
Axial calibration determines the relationship between ultrasound image coordinates
and the physical probe coordinate system.
"""

import numpy as np
from typing import List, Optional, Dict
import os
import subprocess
import json
from pathlib import Path


class AxialCalibration:
    """
    Axial calibration for ultrasound probes using PLUS ToolKit.
    
    Axial calibration computes the transformation from ultrasound image space
    to probe/tool coordinate space. This is essential for accurate 3D reconstruction.
    """
    
    def __init__(self, plus_toolkit_path: Optional[str] = None):
        """
        Initialize axial calibration.
        
        Args:
            plus_toolkit_path: Optional path to PLUS ToolKit installation directory.
                              Can be the bin directory or the root PLUS directory.
                              If None, checks environment variable PLUS_TOOLKIT_PATH or system PATH.
                              Example: "C:\\PlusToolkit\\PlusApp-2.8.0.20190617-Win64\\bin"
        """
        # Check environment variable if path not provided
        if plus_toolkit_path is None:
            plus_toolkit_path = os.environ.get('PLUS_TOOLKIT_PATH', None)
        
        # Normalize the path
        if plus_toolkit_path:
            plus_toolkit_path = os.path.normpath(plus_toolkit_path)
            # If it's the root directory, append 'bin'
            if not plus_toolkit_path.endswith('bin'):
                bin_path = os.path.join(plus_toolkit_path, 'bin')
                if os.path.exists(bin_path):
                    plus_toolkit_path = bin_path
        
        self.plus_toolkit_path = plus_toolkit_path
        self.calibration_matrix = None
        self.calibration_status = "not_calibrated"
        
    def calibrate(
        self,
        probe_poses: List[np.ndarray] = None,
        ultrasound_images: List[np.ndarray] = None,
        calibration_phantom: str = "wire_phantom",
        phantom_parameters: Optional[Dict] = None,
        sequence_file: Optional[str] = None
    ) -> np.ndarray:
        """
        Perform axial calibration using tracked probe poses and ultrasound images.
        
        Args:
            probe_poses: List of 4x4 transformation matrices (probe poses from tracker).
                        Optional if sequence_file is provided.
            ultrasound_images: List of ultrasound image arrays (2D grayscale images).
                             Optional if sequence_file is provided.
            calibration_phantom: Type of calibration phantom ("wire_phantom", "n_wire", "plane", etc.)
            phantom_parameters: Optional dictionary with phantom-specific parameters
                               (e.g., wire positions, spacing, etc.)
            sequence_file: Optional path to existing .mha sequence file.
                          If provided, probe_poses and ultrasound_images are ignored.
        
        Returns:
            4x4 transformation matrix from image space to probe space
        """
        # If sequence file is provided, use it directly
        if sequence_file:
            if not os.path.exists(sequence_file):
                raise FileNotFoundError(f"Sequence file not found: {sequence_file}")
            return self._calibrate_with_sequence_file(sequence_file, calibration_phantom, phantom_parameters)
        
        # Otherwise, use provided poses and images
        if probe_poses is None or ultrasound_images is None:
            raise ValueError("Either sequence_file or both probe_poses and ultrasound_images must be provided")
        
        if len(probe_poses) != len(ultrasound_images):
            raise ValueError("Number of probe poses must match number of ultrasound images")
        
        if len(probe_poses) < 3:
            raise ValueError("At least 3 calibration images are required")
        
        # TODO: Implement actual PLUS ToolKit integration
        # For now, this is a placeholder structure
        
        # Option 1: Use PLUS ToolKit Python bindings (if available)
        try:
            calibration_matrix = self._calibrate_with_plus_bindings(
                probe_poses, ultrasound_images, calibration_phantom, phantom_parameters
            )
        except ImportError:
            # Option 2: Use PLUS ToolKit command-line tools via subprocess
            try:
                calibration_matrix = self._calibrate_with_plus_cli(
                    probe_poses, ultrasound_images, calibration_phantom, phantom_parameters
                )
            except FileNotFoundError:
                raise RuntimeError(
                    "PLUS ToolKit not found. Please install PLUS ToolKit and ensure it's in PATH, "
                    "or install Python bindings."
                )
        
        self.calibration_matrix = calibration_matrix
        self.calibration_status = "calibrated"
        
        return calibration_matrix
    
    def _calibrate_with_plus_bindings(
        self,
        probe_poses: List[np.ndarray],
        ultrasound_images: List[np.ndarray],
        calibration_phantom: str,
        phantom_parameters: Optional[Dict]
    ) -> np.ndarray:
        """
        Calibrate using PLUS ToolKit Python bindings.
        
        This method will be implemented once PLUS ToolKit Python bindings are available.
        """
        # Placeholder for future implementation
        # import plustoolkit
        # return plustoolkit.axial_calibration(...)
        
        raise ImportError("PLUS ToolKit Python bindings not available")
    
    def _calibrate_with_plus_cli(
        self,
        probe_poses: List[np.ndarray],
        ultrasound_images: List[np.ndarray],
        calibration_phantom: str,
        phantom_parameters: Optional[Dict]
    ) -> np.ndarray:
        """
        Calibrate using PLUS ToolKit via PlusServer with XML configuration.
        
        PLUS ToolKit uses XML configuration files rather than command-line arguments.
        This method creates a configuration file and runs PlusServer.
        """
        import tempfile
        import xml.etree.ElementTree as ET
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save probe poses and images to temporary files
            images_dir = os.path.join(temp_dir, "images")
            os.makedirs(images_dir, exist_ok=True)
            
            # Save ultrasound images
            image_files = []
            for i, img in enumerate(ultrasound_images):
                import cv2
                img_file = os.path.join(images_dir, f"image_{i:04d}.png")
                cv2.imwrite(img_file, img)
                image_files.append(img_file)
            
            # Create PLUS ToolKit configuration XML file
            config_file = os.path.join(temp_dir, "calibration_config.xml")
            self._create_plus_config_xml(
                config_file, probe_poses, image_files, calibration_phantom, phantom_parameters
            )
            
            # Find ProbeCalibration executable (this is the calibration tool, not PlusServer)
            probe_cal_cmd = None
            if self.plus_toolkit_path:
                # Try ProbeCalibration.exe first (Windows)
                exe_path = os.path.join(self.plus_toolkit_path, "ProbeCalibration.exe")
                if os.path.exists(exe_path):
                    probe_cal_cmd = exe_path
                else:
                    # Try without .exe (Linux/macOS)
                    exe_path = os.path.join(self.plus_toolkit_path, "ProbeCalibration")
                    if os.path.exists(exe_path):
                        probe_cal_cmd = exe_path
            else:
                # Try to find in system PATH
                if self._find_executable("ProbeCalibration.exe"):
                    probe_cal_cmd = "ProbeCalibration.exe"
                elif self._find_executable("ProbeCalibration"):
                    probe_cal_cmd = "ProbeCalibration"
            
            if probe_cal_cmd is None:
                raise FileNotFoundError(
                    "ProbeCalibration executable not found. "
                    "Please specify plus_toolkit_path or set PLUS_TOOLKIT_PATH environment variable."
                )
            
            # Run ProbeCalibration with configuration file
            # ProbeCalibration may use different command-line syntax
            output_dir = os.path.join(temp_dir, "output")
            os.makedirs(output_dir, exist_ok=True)
            
            # Try different command formats for ProbeCalibration
            # Format 1: --config-file=path
            cmd = [
                probe_cal_cmd,
                f"--config-file={config_file}"
            ]
            
            # Alternative formats to try if first fails:
            # cmd = [probe_cal_cmd, config_file]  # Direct file argument
            # cmd = [probe_cal_cmd, "-c", config_file]  # Short form
            
            # ProbeCalibration requires a sequence metafile, not just a config file
            # We need to create a sequence metafile from images and poses
            seq_file = self._create_sequence_metafile(
                temp_dir, probe_poses, image_files
            )
            
            # Update command to include sequence file
            cmd = [
                probe_cal_cmd,
                f"--config-file={config_file}",
                f"--calibration-seq-file={seq_file}"
            ]
            
            # Add output config file
            output_config = os.path.join(output_dir, "calibration_result.xml")
            cmd.append(f"--output-config-file={output_config}")
            
            print(f"Running: {' '.join(cmd)}")
            print(f"Config file: {config_file}")
            print(f"Sequence file: {seq_file}")
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=temp_dir, timeout=60)
            
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else result.stdout
                raise RuntimeError(
                    f"PLUS ToolKit calibration failed (exit code {result.returncode}):\n{error_msg}"
                )
            
            # Look for calibration result in output directory
            # PLUS ToolKit typically outputs calibration matrices in XML format
            result_file = self._find_plus_calibration_output(output_dir)
            
            if result_file is None:
                # If no specific output file, try to parse from PlusServer output
                # or use a default location
                result_file = os.path.join(output_dir, "CalibrationResult.xml")
                if not os.path.exists(result_file):
                    # Try alternative locations
                    alt_locations = [
                        os.path.join(output_dir, "Calibration.xml"),
                        os.path.join(temp_dir, "CalibrationResult.xml"),
                    ]
                    for alt_path in alt_locations:
                        if os.path.exists(alt_path):
                            result_file = alt_path
                            break
            
            # Read calibration result
            if os.path.exists(result_file):
                calibration_matrix = self._read_plus_calibration_result(result_file)
            else:
                # If no output file found, try to extract from PlusServer output
                # or return identity matrix as fallback (with warning)
                print("Warning: Calibration output file not found. Using identity matrix.")
                print("You may need to check PLUS ToolKit output format and update parsing.")
                calibration_matrix = np.eye(4)
            
            return calibration_matrix
    
    def _find_executable(self, name: str) -> bool:
        """
        Check if an executable exists in system PATH.
        
        Args:
            name: Name of executable to find
        
        Returns:
            True if executable found, False otherwise
        """
        import shutil
        return shutil.which(name) is not None
    
    def _create_plus_config_xml(
        self,
        config_file: str,
        probe_poses: List[np.ndarray],
        image_files: List[str],
        calibration_phantom: str,
        phantom_parameters: Optional[Dict]
    ):
        """
        Create PLUS ToolKit configuration XML file.
        
        Args:
            config_file: Path to save configuration XML
            probe_poses: List of probe poses (4x4 matrices)
            image_files: List of paths to ultrasound images
            calibration_phantom: Type of calibration phantom
            phantom_parameters: Optional phantom-specific parameters
        """
        import xml.etree.ElementTree as ET
        
        # Create root element
        root = ET.Element("PlusConfiguration")
        root.set("version", "2.8")
        
        # CRITICAL: PlusServer requires a DataCollection element
        data_collection = ET.SubElement(root, "DataCollection")
        
        # Add device section inside DataCollection
        devices = ET.SubElement(data_collection, "Devices")
        
        # Add tracking device (probe poses)
        # PLUS ToolKit requires proper device configuration
        tracking_device = ET.SubElement(devices, "Device")
        tracking_device.set("id", "Tracker")
        tracking_device.set("type", "VirtualDevice")
        
        # Add device configuration (required for device to be created)
        device_config = ET.SubElement(tracking_device, "DeviceConfiguration")
        # VirtualDevice may need specific configuration
        # For now, add minimal required elements
        
        # Add ultrasound device
        us_device = ET.SubElement(devices, "Device")
        us_device.set("id", "Ultrasound")
        us_device.set("type", "VirtualDevice")
        us_device_config = ET.SubElement(us_device, "DeviceConfiguration")
        # Minimal configuration
        
        # Note: Calibration section may need to be handled separately
        # For now, we'll add it at root level, but it might need to be
        # in DataCollection or handled by a different tool
        calibration = ET.SubElement(root, "Calibration")
        calibration.set("type", calibration_phantom)
        
        # Add image sequence
        image_sequence = ET.SubElement(calibration, "ImageSequence")
        for i, img_file in enumerate(image_files):
            image = ET.SubElement(image_sequence, "Image")
            image.set("index", str(i))
            image.set("file", img_file)
        
        # Add pose sequence
        pose_sequence = ET.SubElement(calibration, "PoseSequence")
        for i, pose in enumerate(probe_poses):
            pose_elem = ET.SubElement(pose_sequence, "Pose")
            pose_elem.set("index", str(i))
            # Convert 4x4 matrix to string representation
            pose_str = " ".join([str(pose[i, j]) for i in range(4) for j in range(4)])
            pose_elem.text = pose_str
        
        # Add phantom parameters if provided
        if phantom_parameters:
            phantom_params = ET.SubElement(calibration, "PhantomParameters")
            for key, value in phantom_parameters.items():
                param = ET.SubElement(phantom_params, "Parameter")
                param.set("name", key)
                param.text = str(value)
        
        # Write XML file
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(config_file, encoding="utf-8", xml_declaration=True)
    
    def _create_sequence_metafile(
        self,
        temp_dir: str,
        probe_poses: List[np.ndarray],
        image_files: List[str]
    ) -> str:
        """
        Create PLUS ToolKit sequence metafile from poses and images.
        
        Sequence metafile format is an XML file that references images and contains
        tracking data in PLUS ToolKit's format.
        
        Args:
            temp_dir: Temporary directory for files
            probe_poses: List of probe poses (4x4 matrices)
            image_files: List of paths to ultrasound images
        
        Returns:
            Path to created sequence metafile
        """
        import xml.etree.ElementTree as ET
        
        seq_file = os.path.join(temp_dir, "calibration_sequence.mha")
        # Actually, sequence metafile is typically .mha or .mhd + .raw
        # But PLUS also uses .mha for sequences with embedded data
        # For now, create an XML metafile that references the images
        
        # Create sequence metafile XML
        root = ET.Element("Sequence")
        root.set("version", "1.0")
        
        # Add tracking data
        tracking = ET.SubElement(root, "Tracking")
        for i, pose in enumerate(probe_poses):
            frame = ET.SubElement(tracking, "Frame")
            frame.set("index", str(i))
            transform = ET.SubElement(frame, "Transform")
            transform.set("type", "Matrix4x4")
            # Convert 4x4 matrix to string (row-major, space-separated)
            pose_str = " ".join([str(pose[i, j]) for i in range(4) for j in range(4)])
            transform.text = pose_str
        
        # Add image references
        images = ET.SubElement(root, "Images")
        for i, img_file in enumerate(image_files):
            image = ET.SubElement(images, "Image")
            image.set("index", str(i))
            image.set("file", img_file)
        
        # Write sequence file
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        seq_xml = os.path.join(temp_dir, "calibration_sequence.xml")
        tree.write(seq_xml, encoding="utf-8", xml_declaration=True)
        
        # Note: PLUS ToolKit may require .mha format instead
        # This is a simplified version - may need adjustment based on actual format
        return seq_xml
    
    def _calibrate_with_sequence_file(
        self,
        sequence_file: str,
        calibration_phantom: str,
        phantom_parameters: Optional[Dict],
        config_file_path: Optional[str] = None
    ) -> np.ndarray:
        """
        Calibrate using an existing .mha sequence file.
        
        Args:
            sequence_file: Path to .mha sequence file
            calibration_phantom: Type of calibration phantom (ignored if config_file_path provided)
            phantom_parameters: Optional phantom parameters (ignored if config_file_path provided)
            config_file_path: Optional path to PLUS ToolKit config file. 
                            If None, uses the default PLUS config file.
        
        Returns:
            4x4 calibration matrix
        """
        import tempfile
        
        sequence_path = Path(sequence_file).resolve()
        if not sequence_path.exists():
            raise FileNotFoundError(f"Sequence file not found: {sequence_path}")
        
        # Use real config file from PLUS ToolKit installation
        if config_file_path is None:
            # Default to the fCal config file
            plus_config_dir = os.path.join(self.plus_toolkit_path, "..", "config")
            config_file_path = os.path.join(plus_config_dir, "PlusDeviceSet_fCal_Sim_SpatialCalibration_2.0.xml")
            config_file_path = os.path.abspath(config_file_path)
        
        config_file = Path(config_file_path).resolve()
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Find ProbeCalibration executable
            probe_cal_cmd = None
            if self.plus_toolkit_path:
                exe_path = os.path.join(self.plus_toolkit_path, "ProbeCalibration.exe")
                if os.path.exists(exe_path):
                    probe_cal_cmd = exe_path
            
            if probe_cal_cmd is None:
                raise FileNotFoundError("ProbeCalibration.exe not found")
            
            # Run ProbeCalibration
            output_dir = os.path.join(temp_dir, "output")
            os.makedirs(output_dir, exist_ok=True)
            output_config = os.path.join(output_dir, "calibration_result.xml")
            
            cmd = [
                probe_cal_cmd,
                f"--config-file={config_file}",
                f"--calibration-seq-file={sequence_path}",
                f"--output-config-file={output_config}"
            ]
            
            print(f"Running calibration with sequence file: {sequence_path}")
            print(f"Command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else result.stdout
                raise RuntimeError(
                    f"PLUS ToolKit calibration failed (exit code {result.returncode}):\n{error_msg}"
                )
            
            # Read calibration result
            if os.path.exists(output_config):
                calibration_matrix = self._read_plus_calibration_result(output_config)
            else:
                # Try to find result in other locations
                result_file = self._find_plus_calibration_output(output_dir)
                if result_file:
                    calibration_matrix = self._read_plus_calibration_result(result_file)
                else:
                    print("Warning: Calibration output file not found. Using identity matrix.")
                    calibration_matrix = np.eye(4)
            
            return calibration_matrix
    
    def _create_config_for_sequence_file(
        self,
        config_file: str,
        sequence_file: str,
        calibration_phantom: str,
        phantom_parameters: Optional[Dict]
    ):
        """
        Create config file that uses an existing .mha sequence file.
        
        Args:
            config_file: Path to save config file
            sequence_file: Path to .mha sequence file
            calibration_phantom: Type of phantom
            phantom_parameters: Optional phantom parameters
        """
        import xml.etree.ElementTree as ET
        
        root = ET.Element("PlusConfiguration")
        root.set("version", "2.1")
        
        # DataCollection with DeviceSet
        data_collection = ET.SubElement(root, "DataCollection")
        data_collection.set("StartupDelaySec", "1.0")
        
        device_set = ET.SubElement(data_collection, "DeviceSet")
        device_set.set("Name", f"Calibration: {calibration_phantom}")
        device_set.set("Description", "Calibration using existing sequence file")
        
        # Device for reading sequence file
        tracked_video_device = ET.SubElement(device_set, "Device")
        tracked_video_device.set("Id", "TrackedVideoDevice")
        tracked_video_device.set("Type", "SavedDataSource")
        tracked_video_device.set("SequenceFile", sequence_file)
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
        phantom_def = ET.SubElement(root, "PhantomDefinition")
        description = ET.SubElement(phantom_def, "Description")
        description.set("Name", calibration_phantom.replace("_", "").title())
        description.set("Type", "Multi-N" if "n" in calibration_phantom.lower() else "Wire")
        description.set("Version", "2.0")
        
        geometry = ET.SubElement(phantom_def, "Geometry")
        pattern = ET.SubElement(geometry, "Pattern")
        pattern.set("Type", "NWire" if "n" in calibration_phantom.lower() else "Wire")
        
        # Add wire definitions from phantom_parameters or defaults
        if phantom_parameters and 'wires' in phantom_parameters:
            for wire in phantom_parameters['wires']:
                wire_elem = ET.SubElement(pattern, "Wire")
                wire_elem.set("Name", wire.get('name', 'Wire'))
                wire_elem.set("EndPointFront", f"{wire['front'][0]} {wire['front'][1]} {wire['front'][2]}")
                wire_elem.set("EndPointBack", f"{wire['back'][0]} {wire['back'][1]} {wire['back'][2]}")
        else:
            # Default single wire for testing
            wire_elem = ET.SubElement(pattern, "Wire")
            wire_elem.set("Name", "Wire1")
            wire_elem.set("EndPointFront", "30.0 0.0 20.0")
            wire_elem.set("EndPointBack", "30.0 40.0 20.0")
        
        # vtkPlusProbeCalibrationAlgo (required)
        probe_cal_algo = ET.SubElement(root, "vtkPlusProbeCalibrationAlgo")
        probe_cal_algo.set("ImageCoordinateFrame", "Image")
        probe_cal_algo.set("ProbeCoordinateFrame", "Probe")
        probe_cal_algo.set("PhantomCoordinateFrame", "Phantom")
        probe_cal_algo.set("ReferenceCoordinateFrame", "Reference")
        
        # Write config file
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(config_file, encoding="utf-8", xml_declaration=True)
    
    def _find_plus_calibration_output(self, output_dir: str) -> Optional[str]:
        """
        Find calibration output file in PLUS ToolKit output directory.
        
        Args:
            output_dir: Directory where PLUS ToolKit wrote output
        
        Returns:
            Path to calibration result file, or None if not found
        """
        possible_names = [
            "CalibrationResult.xml",
            "Calibration.xml",
            "ProbeCalibration.xml",
            "ImageToProbeTransform.xml"
        ]
        
        for name in possible_names:
            file_path = os.path.join(output_dir, name)
            if os.path.exists(file_path):
                return file_path
        
        # Also check subdirectories
        for root, dirs, files in os.walk(output_dir):
            for name in possible_names:
                file_path = os.path.join(root, name)
                if os.path.exists(file_path):
                    return file_path
        
        return None
    
    def _read_plus_calibration_result(self, result_file: str) -> np.ndarray:
        """
        Read calibration result from PLUS ToolKit output file.
        
        Args:
            result_file: Path to PLUS ToolKit calibration output file
        
        Returns:
            4x4 transformation matrix
        """
        # TODO: Implement parsing of PLUS ToolKit output format
        # This will depend on the actual output format (XML, JSON, etc.)
        
        # Placeholder: return identity matrix
        return np.eye(4)
    
    def image_to_probe(self, image_coords: np.ndarray) -> np.ndarray:
        """
        Transform image coordinates to probe coordinate space.
        
        Args:
            image_coords: Nx2 array of image coordinates (u, v) in pixels
        
        Returns:
            Nx3 array of coordinates in probe space (x, y, z) in mm
        """
        if self.calibration_matrix is None:
            raise RuntimeError("Calibration not performed. Call calibrate() first.")
        
        # Convert 2D image coordinates to 3D homogeneous coordinates
        n_points = image_coords.shape[0]
        coords_3d = np.ones((n_points, 4))
        coords_3d[:, :2] = image_coords
        
        # Apply calibration transformation
        probe_coords = (self.calibration_matrix @ coords_3d.T).T
        
        return probe_coords[:, :3]
    
    def get_calibration_matrix(self) -> Optional[np.ndarray]:
        """Get the current calibration matrix."""
        return self.calibration_matrix
    
    def save_calibration(self, filepath: str):
        """
        Save calibration matrix to file.
        
        Args:
            filepath: Path to save calibration file (XML or JSON format)
        """
        if self.calibration_matrix is None:
            raise RuntimeError("No calibration to save. Perform calibration first.")
        
        if filepath.endswith('.json'):
            data = {
                'calibration_matrix': self.calibration_matrix.tolist(),
                'calibration_status': self.calibration_status
            }
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            # Save as XML (similar to existing calibration_io.py format)
            from PySide6 import QtCore
            qfile = QtCore.QFile(filepath)
            if qfile.open(QtCore.QIODevice.WriteOnly):
                stream = QtCore.QXmlStreamWriter(qfile)
                stream.writeStartDocument()
                stream.writeStartElement("AxialCalibration")
                stream.writeStartElement("CalibrationMatrix")
                for i in range(4):
                    stream.writeStartElement("Row")
                    for j in range(4):
                        stream.writeTextElement("Element", str(self.calibration_matrix[i, j]))
                    stream.writeEndElement()
                stream.writeEndElement()
                stream.writeEndElement()
                stream.writeEndDocument()
            qfile.close()
    
    def load_calibration(self, filepath: str):
        """
        Load calibration matrix from file.
        
        Args:
            filepath: Path to calibration file
        """
        if filepath.endswith('.json'):
            with open(filepath, 'r') as f:
                data = json.load(f)
            self.calibration_matrix = np.array(data['calibration_matrix'])
            self.calibration_status = data.get('calibration_status', 'loaded')
        else:
            # Load from XML
            from PySide6 import QtCore
            qfile = QtCore.QFile(filepath)
            calibration_matrix = np.empty((4, 4))
            if qfile.open(QtCore.QIODevice.ReadOnly):
                reader = QtCore.QXmlStreamReader()
                reader.setDevice(qfile)
                reader.readNextStartElement()  # AxialCalibration
                reader.readNextStartElement()  # CalibrationMatrix
                for i in range(4):
                    reader.readNextStartElement()  # Row
                    for j in range(4):
                        reader.readNextStartElement()  # Element
                        calibration_matrix[i, j] = float(reader.readElementText())
                qfile.close()
            self.calibration_matrix = calibration_matrix
            self.calibration_status = 'loaded'

