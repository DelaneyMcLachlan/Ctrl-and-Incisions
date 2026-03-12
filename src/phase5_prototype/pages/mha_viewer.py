"""
VTK Viewer for .mha Volume Files

This script loads and displays 3D volume data from .mha (MetaImage) files.
It can display volumes from PlusLibData or any other .mha file.

Usage:
    python view_mha_volume.py                    # List all available files
    python view_mha_volume.py <number>          # View file by number (1-N)
    python view_mha_volume.py <path_to_file.mha> # View specific file
    
If no file is specified, it will list all available .mha files with numbers.
You can then run the script again with a number to view that file.
"""

import sys
import os
from pathlib import Path
import vtk
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk
import numpy as np

# Import PlusToolkit config utility
try:
    from plus_toolkit_config import get_pluslibdata_testimages_dir
except ImportError:
    # Fallback if module not found
    def get_pluslibdata_testimages_dir():
        plus_toolkit_path = os.getenv('PLUS_TOOLKIT_PATH', r"C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin")
        if os.path.exists(plus_toolkit_path):
            testimages_dir = os.path.join(plus_toolkit_path, "..", "data", "PlusLibData", "TestImages")
            if os.path.exists(testimages_dir):
                return os.path.abspath(testimages_dir)
        return None


def find_available_mha_files():
    """Find available .mha files in common locations, prioritizing 3D volumes."""
    available_files = []
    reconstructed_files = []  # Prioritize reconstructed volumes
    
    # Check PlusLibData TestImages directory (using config utility)
    pluslibdata_testimages = get_pluslibdata_testimages_dir()
    
    if pluslibdata_testimages and os.path.exists(pluslibdata_testimages):
        for file in os.listdir(pluslibdata_testimages):
            if file.endswith(('.mha', '.igs.mha')):
                full_path = os.path.join(pluslibdata_testimages, file)
                # Prioritize files that are likely 3D volumes
                if 'reconstructed' in file.lower() or 'volume' in file.lower():
                    reconstructed_files.append(full_path)
                else:
                    available_files.append(full_path)
    
    # Check current directory
    script_dir = Path(__file__).parent
    elbow_file = script_dir / "ElbowUltrasoundSweep.mha"
    if elbow_file.exists():
        available_files.insert(0, str(elbow_file))  # Put local file first
    
    # Return reconstructed files first, then others
    return reconstructed_files + available_files


def load_mha_file(file_path, verbose=True):
    """Load a .mha file using VTK's MetaImage reader."""
    if verbose:
        print(f"Loading .mha file: {file_path}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Create MetaImage reader
    reader = vtk.vtkMetaImageReader()
    reader.SetFileName(file_path)
    reader.Update()
    
    image_data = reader.GetOutput()
    
    # Get volume information
    dims = image_data.GetDimensions()
    spacing = image_data.GetSpacing()
    origin = image_data.GetOrigin()
    scalar_range = image_data.GetScalarRange()
    
    if verbose:
        print(f"  Dimensions: {dims[0]} x {dims[1]} x {dims[2]}")
        print(f"  Spacing: {spacing[0]:.4f} x {spacing[1]:.4f} x {spacing[2]:.4f}")
        print(f"  Origin: {origin[0]:.4f}, {origin[1]:.4f}, {origin[2]:.4f}")
        print(f"  Scalar range: {scalar_range[0]:.2f} to {scalar_range[1]:.2f}")
    
    # Check if this is a 3D volume or 2D image
    is_3d = dims[2] > 1
    if verbose and not is_3d:
        print(f"  Note: This appears to be a 2D image (single slice), not a 3D volume")
    
    return image_data, is_3d


def create_volume_renderer(image_data, is_3d=True):
    """Create a volume renderer for the image data."""
    if not is_3d:
        # For 2D images, use image actor instead
        image_actor = vtk.vtkImageActor()
        image_actor.SetInputData(image_data)
        return image_actor
    
    # Create volume mapper
    volume_mapper = vtk.vtkSmartVolumeMapper()
    volume_mapper.SetInputData(image_data)
    
    # Create volume property
    volume_property = vtk.vtkVolumeProperty()
    volume_property.ShadeOn()
    volume_property.SetInterpolationTypeToLinear()
    
    # Create opacity transfer function
    opacity_transfer_function = vtk.vtkPiecewiseFunction()
    scalar_range = image_data.GetScalarRange()
    
    # Set opacity based on intensity (adjust these values based on your data)
    # For ultrasound data, typically we want to see brighter regions
    if scalar_range[1] > 255:
        # 16-bit data
        opacity_transfer_function.AddPoint(scalar_range[0], 0.0)
        opacity_transfer_function.AddPoint(scalar_range[1] * 0.3, 0.0)
        opacity_transfer_function.AddPoint(scalar_range[1] * 0.5, 0.1)
        opacity_transfer_function.AddPoint(scalar_range[1] * 0.7, 0.3)
        opacity_transfer_function.AddPoint(scalar_range[1] * 0.9, 0.6)
        opacity_transfer_function.AddPoint(scalar_range[1], 1.0)
    else:
        # 8-bit data
        opacity_transfer_function.AddPoint(scalar_range[0], 0.0)
        opacity_transfer_function.AddPoint(scalar_range[1] * 0.3, 0.0)
        opacity_transfer_function.AddPoint(scalar_range[1] * 0.5, 0.2)
        opacity_transfer_function.AddPoint(scalar_range[1] * 0.7, 0.5)
        opacity_transfer_function.AddPoint(scalar_range[1], 1.0)
    
    volume_property.SetScalarOpacity(opacity_transfer_function)
    
    # Create color transfer function
    color_transfer_function = vtk.vtkColorTransferFunction()
    color_transfer_function.AddRGBPoint(scalar_range[0], 0.0, 0.0, 0.0)  # Black for low values
    color_transfer_function.AddRGBPoint(scalar_range[1] * 0.5, 0.0, 0.0, 1.0)  # Blue
    color_transfer_function.AddRGBPoint(scalar_range[1] * 0.7, 0.0, 1.0, 1.0)  # Cyan
    color_transfer_function.AddRGBPoint(scalar_range[1] * 0.9, 1.0, 1.0, 0.0)  # Yellow
    color_transfer_function.AddRGBPoint(scalar_range[1], 1.0, 1.0, 1.0)  # White for high values
    
    volume_property.SetColor(color_transfer_function)
    
    # Create volume
    volume = vtk.vtkVolume()
    volume.SetMapper(volume_mapper)
    volume.SetProperty(volume_property)
    
    return volume


def create_slice_viewer(image_data, renderer, orientation='axial'):
    """Create orthogonal slice viewers for the volume."""
    dims = image_data.GetDimensions()
    
    # Determine slice index based on orientation
    if orientation == 'axial':
        slice_idx = dims[2] // 2
        extractor = vtk.vtkImageExtractComponents()
        extractor.SetInputData(image_data)
        extractor.SetComponents(0)
        extractor.Update()
        
        extract_slice = vtk.vtkExtractVOI()
        extract_slice.SetInputConnection(extractor.GetOutputPort())
        extract_slice.SetVOI(0, dims[0]-1, 0, dims[1]-1, slice_idx, slice_idx)
        extract_slice.Update()
        
        slice_data = extract_slice.GetOutput()
    elif orientation == 'coronal':
        slice_idx = dims[1] // 2
        extract_slice = vtk.vtkExtractVOI()
        extract_slice.SetInputData(image_data)
        extract_slice.SetVOI(0, dims[0]-1, slice_idx, slice_idx, 0, dims[2]-1)
        extract_slice.Update()
        slice_data = extract_slice.GetOutput()
    else:  # sagittal
        slice_idx = dims[0] // 2
        extract_slice = vtk.vtkExtractVOI()
        extract_slice.SetInputData(image_data)
        extract_slice.SetVOI(slice_idx, slice_idx, 0, dims[1]-1, 0, dims[2]-1)
        extract_slice.Update()
        slice_data = extract_slice.GetOutput()
    
    # Create mapper and actor for slice
    slice_mapper = vtk.vtkImageMapper()
    slice_mapper.SetInputData(slice_data)
    slice_mapper.SetColorWindow(255)
    slice_mapper.SetColorLevel(127.5)
    
    slice_actor = vtk.vtkActor2D()
    slice_actor.SetMapper(slice_mapper)
    
    return slice_actor


class FileScrollerInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    """Custom interactor style that allows scrolling through files with keyboard."""
    
    def __init__(self, available_files, current_index, renderer, render_window):
        # Call parent constructor
        vtk.vtkInteractorStyleTrackballCamera.__init__(self)
        
        self.available_files = available_files
        self.current_index = current_index
        self.renderer = renderer
        self.render_window = render_window
        self.current_volume = None
        self.current_actor = None
        self.current_axes = None
        
        # Add observer for keypress events
        self.AddObserver("KeyPressEvent", self.key_press_event)
    
    def key_press_event(self, obj, event):
        """Handle keypress events for file navigation."""
        key = self.GetInteractor().GetKeySym()
        
        if key == 'Right' or key == 'Down' or key == 'n':  # Next file
            self.load_next_file()
        elif key == 'Left' or key == 'Up' or key == 'p':  # Previous file
            self.load_previous_file()
        elif key == 'Home':  # First file
            self.current_index = 0
            self.load_file_at_index()
        elif key == 'End':  # Last file
            self.current_index = len(self.available_files) - 1
            self.load_file_at_index()
        elif key == 'r':  # Reset camera
            self.renderer.ResetCamera()
            self.render_window.Render()
        elif key == 'q' or key == 'Escape':  # Quit
            self.GetInteractor().ExitCallback()
    
    def load_file_at_index(self):
        """Load and display the file at the current index."""
        if self.current_index < 0 or self.current_index >= len(self.available_files):
            return
        
        file_path = self.available_files[self.current_index]
        file_name = os.path.basename(file_path)
        
        try:
            # Clear current actors/volumes
            self.renderer.RemoveAllViewProps()
            
            # Load new file (suppress verbose output for faster scrolling)
            print(f"[{self.current_index + 1}/{len(self.available_files)}] Loading: {file_name}...", end=" ", flush=True)
            image_data, is_3d = load_mha_file(file_path, verbose=False)
            print("Done!")
            
            # Create new volume/actor
            volume_or_actor = create_volume_renderer(image_data, is_3d)
            
            if is_3d:
                self.renderer.AddVolume(volume_or_actor)
                self.current_volume = volume_or_actor
                self.current_actor = None
            else:
                self.renderer.AddActor(volume_or_actor)
                self.current_actor = volume_or_actor
                self.current_volume = None
            
            # Add axes for reference
            axes = vtk.vtkAxesActor()
            axes.SetXAxisLabelText("X")
            axes.SetYAxisLabelText("Y")
            axes.SetZAxisLabelText("Z")
            dims = image_data.GetDimensions()
            max_dim = max(dims[0], dims[1], dims[2])
            axes_length = max_dim * 0.1
            axes.SetTotalLength(axes_length, axes_length, axes_length)
            self.renderer.AddActor(axes)
            self.current_axes = axes
            
            # Update window title
            viewer_type = "3D Volume" if is_3d else "2D Image"
            self.render_window.SetWindowName(
                f"{viewer_type} Viewer - [{self.current_index + 1}/{len(self.available_files)}] {file_name}"
            )
            
            # Reset camera and render
            self.renderer.ResetCamera()
            self.render_window.Render()
            
            print(f"\n[{self.current_index + 1}/{len(self.available_files)}] Loaded: {file_name}")
            
        except Exception as e:
            print(f"Error loading file {file_path}: {e}")
            import traceback
            traceback.print_exc()
    
    def load_next_file(self):
        """Load the next file in the list."""
        if self.current_index < len(self.available_files) - 1:
            self.current_index += 1
            self.load_file_at_index()
        else:
            print("Already at last file. Press 'Home' to go to first file.")
    
    def load_previous_file(self):
        """Load the previous file in the list."""
        if self.current_index > 0:
            self.current_index -= 1
            self.load_file_at_index()
        else:
            print("Already at first file. Press 'End' to go to last file.")


def create_3d_viewer(image_data, is_3d=True, available_files=None, current_index=0):
    """Create a 3D viewer window with volume rendering and file scrolling capability."""
    # Create renderer
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.1, 0.1, 0.2)  # Dark blue background
    
    # Create volume renderer or image actor
    volume_or_actor = create_volume_renderer(image_data, is_3d)
    
    if is_3d:
        renderer.AddVolume(volume_or_actor)
    else:
        renderer.AddActor(volume_or_actor)
    
    # Add axes for reference
    axes = vtk.vtkAxesActor()
    axes.SetXAxisLabelText("X")
    axes.SetYAxisLabelText("Y")
    axes.SetZAxisLabelText("Z")
    dims = image_data.GetDimensions()
    # Scale axes appropriately
    max_dim = max(dims[0], dims[1], dims[2])
    axes_length = max_dim * 0.1
    axes.SetTotalLength(axes_length, axes_length, axes_length)
    renderer.AddActor(axes)
    
    # Create render window
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)
    render_window.SetSize(1200, 800)
    
    # Set initial window title
    viewer_type = "3D Volume" if is_3d else "2D Image"
    if available_files:
        file_name = os.path.basename(available_files[current_index])
        render_window.SetWindowName(
            f"{viewer_type} Viewer - [{current_index + 1}/{len(available_files)}] {file_name}"
        )
    else:
        render_window.SetWindowName(f"{viewer_type} Viewer - .mha File")
    
    # Create interactor
    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)
    
    # Add style for interaction (with file scrolling if files are available)
    if available_files and len(available_files) > 1:
        style = FileScrollerInteractorStyle(available_files, current_index, renderer, render_window)
        interactor.SetInteractorStyle(style)
    else:
        style = vtk.vtkInteractorStyleTrackballCamera()
        interactor.SetInteractorStyle(style)
    
    # Reset camera to show entire volume
    renderer.ResetCamera()
    
    return render_window, interactor


def list_available_files(available_files):
    """List all available files with numbers."""
    if not available_files:
        print("No .mha files found in common locations.")
        print("\nPlease specify a file path:")
        print("  python view_mha_volume.py <path_to_file.mha>")
        print("\nOr place a .mha file in one of these locations:")
        print("  - PlusLibData/TestImages directory")
        print("  - Current directory (ultrasound-calibration)")
        return
    
    print(f"\nFound {len(available_files)} available .mha file(s):")
    print("=" * 80)
    
    # Group files by directory for better organization
    files_by_dir = {}
    for f in available_files:
        dir_path = os.path.dirname(f)
        if dir_path not in files_by_dir:
            files_by_dir[dir_path] = []
        files_by_dir[dir_path].append(f)
    
    file_num = 1
    for dir_path, files in files_by_dir.items():
        # Show directory name (shortened if too long)
        if len(dir_path) > 70:
            display_dir = "..." + dir_path[-67:]
        else:
            display_dir = dir_path
        print(f"\n[{display_dir}]")
        
        for f in files:
            file_size = os.path.getsize(f) / (1024 * 1024)  # Size in MB
            file_name = os.path.basename(f)
            # Mark reconstructed/volume files
            marker = " [3D VOLUME]" if ('reconstructed' in file_name.lower() or 'volume' in file_name.lower()) else ""
            print(f"  {file_num:3d}. {file_name:<60} ({file_size:6.2f} MB){marker}")
            file_num += 1
    
    print("\n" + "=" * 80)
    print(f"Usage: python view_mha_volume.py <number>")
    print(f"Example: python view_mha_volume.py 1")
    print("=" * 80)


def main():
    """Main function to load and display .mha file."""
    # Find all available files first
    available_files = find_available_mha_files()
    
    # Determine which file to load and current index
    current_index = 0
    file_path = None
    
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        # Check if argument is a number
        try:
            file_number = int(arg)
            if file_number < 1 or file_number > len(available_files):
                print(f"Error: File number {file_number} is out of range.")
                print(f"Please choose a number between 1 and {len(available_files)}")
                print("\nAvailable files:")
                list_available_files(available_files)
                return
            
            current_index = file_number - 1  # Convert to 0-based index
            file_path = available_files[current_index]
            print(f"Selected file #{file_number}: {os.path.basename(file_path)}")
            
        except ValueError:
            # Not a number, treat as file path
            file_path = arg
            # Try to find this file in the available_files list
            if available_files:
                try:
                    current_index = available_files.index(os.path.abspath(file_path))
                except ValueError:
                    # File not in list, try to match by basename
                    file_basename = os.path.basename(file_path)
                    for i, f in enumerate(available_files):
                        if os.path.basename(f) == file_basename:
                            current_index = i
                            break
    else:
        # No argument provided - list all files
        list_available_files(available_files)
        return
    
    try:
        # Load the .mha file
        image_data, is_3d = load_mha_file(file_path)
        
        viewer_type = "3D volume" if is_3d else "2D image"
        print(f"\nCreating {viewer_type} viewer...")
        
        # Create and show viewer (with file scrolling if multiple files available)
        render_window, interactor = create_3d_viewer(
            image_data, 
            is_3d, 
            available_files=available_files if len(available_files) > 1 else None,
            current_index=current_index
        )
        
        print("\n" + "="*60)
        print(f"{viewer_type.upper()} Viewer Controls:")
        print("="*60)
        print("  Mouse Controls:")
        print("    Left Mouse Button + Drag: Rotate")
        print("    Right Mouse Button + Drag: Zoom")
        print("    Middle Mouse Button + Drag: Pan")
        print("  Keyboard Controls:")
        if available_files and len(available_files) > 1:
            print(f"    Right Arrow / Down Arrow / 'n': Next file ({len(available_files)} files available)")
            print(f"    Left Arrow / Up Arrow / 'p': Previous file")
            print(f"    Home: First file")
            print(f"    End: Last file")
        print("    'r' key: Reset camera")
        print("    'q' or Escape: Quit")
        print("="*60)
        print(f"\nDisplaying {viewer_type}...")
        
        # Show the window
        render_window.Render()
        interactor.Start()
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading or displaying file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

