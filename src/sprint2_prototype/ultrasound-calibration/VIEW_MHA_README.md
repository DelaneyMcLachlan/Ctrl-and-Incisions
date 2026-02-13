# VTK .mha Volume Viewer

This script allows you to visualize 3D volume data from .mha (MetaImage) files using VTK.

## Usage

### List All Available Files
```bash
python view_mha_volume.py
```
This will list all available .mha files with numbers (1-89). Files are organized by directory, and 3D volumes are marked with `[3D VOLUME]`.

### Select File by Number (Recommended)
```bash
python view_mha_volume.py <number>
```
Select a file by its number from the list. This is the easiest way to view files!

**Examples:**
```bash
# List all files first
python view_mha_volume.py

# Then select a file by number (e.g., file #2)
python view_mha_volume.py 2

# Or select file #89 (ElbowUltrasoundSweep.mha)
python view_mha_volume.py 89
```

### Specify a File by Path
```bash
python view_mha_volume.py "path/to/file.mha"
```
You can also specify a file path directly if you know the exact location.

**Examples:**
```bash
# View a reconstructed volume from PlusLibData
python view_mha_volume.py "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\data\PlusLibData\TestImages\SpinePhantomFreehandReconstructed.mha"

# View the elbow sweep file in current directory
python view_mha_volume.py "ElbowUltrasoundSweep.mha"
```

## Recommended Files for 3D Visualization

The script automatically prioritizes files with "reconstructed" or "volume" in their names. Here are some good 3D volume files from PlusLibData:

### Reconstructed Volumes (Best for 3D viewing)
- `SpinePhantomFreehandReconstructed.mha` - 147 x 106 x 104 (0.5mm spacing)
- `NwirePhantomFreehandReconstructed.mha` - Reconstructed N-wire phantom
- `vtkVolumeReconstructorTest*volumeRef.mha` - Various test volumes from VolumeReconstructor

### Other 3D Volumes
- `ElbowUltrasoundSweep.mha` - In your current directory (if it's a 3D volume)

### Note on 2D Files
Many .mha files in PlusLibData are 2D images (single slice) or sequence files with tracking data. These will display as 2D images rather than 3D volumes.

## Viewer Controls

### Mouse Controls
- **Left Mouse Button + Drag**: Rotate the view
- **Right Mouse Button + Drag**: Zoom in/out
- **Middle Mouse Button + Drag**: Pan the view

### Keyboard Controls

#### File Navigation (when viewing files from the numbered list)
- **Right Arrow / Down Arrow / 'n'**: Load next file
- **Left Arrow / Up Arrow / 'p'**: Load previous file
- **Home**: Jump to first file
- **End**: Jump to last file

#### General Controls
- **'r' key**: Reset camera to default view
- **'q' key or Escape**: Quit the viewer

### File Scrolling Feature

When you open a file using a number (e.g., `python view_mha_volume.py 2`), the viewer enables **file scrolling mode**. This allows you to browse through all 89 available files without closing and reopening the viewer:

1. Open any file by number: `python view_mha_volume.py 2`
2. Use arrow keys to scroll through files:
   - Right/Down arrow or 'n' → Next file
   - Left/Up arrow or 'p' → Previous file
   - Home → First file
   - End → Last file
3. The window title shows the current file number: `[2/89] filename.mha`
4. Each file loads automatically when you scroll

This makes it easy to quickly browse and compare different volumes!

## Features

- **Automatic file detection**: Finds .mha files in PlusLibData and current directory
- **3D volume rendering**: Uses VTK's volume rendering with opacity and color transfer functions
- **2D image support**: Also handles 2D images (single slice)
- **Volume information**: Displays dimensions, spacing, origin, and scalar range
- **Interactive viewing**: Full 3D rotation, zoom, and pan controls

## Requirements

- VTK (installed via `pip install vtk`)
- Python 3.x
- PlusToolkit PlusLibData (optional, for sample files)

## Integration with VolumeReconstructor.exe

This viewer is designed to display the output from `VolumeReconstructor.exe`. After running VolumeReconstructor to create a 3D volume from tracked ultrasound data, you can use this script to visualize the result:

```bash
# After running VolumeReconstructor.exe to create output.mha
python view_mha_volume.py output.mha
```

