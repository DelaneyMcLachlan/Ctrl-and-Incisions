import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QSplitter,
    QHBoxLayout, QPushButton, QLabel, QFileDialog, QTextEdit,
    QSlider, QMessageBox, QComboBox, QGroupBox, QListWidget, QGridLayout
)
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPalette
import vtkmodules.vtkInteractionWidgets as vtkWidgets

from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkChartsCore import vtkChartXY, vtkPiecewiseControlPointsItem
from vtkmodules.vtkViewsContext2D import vtkContextView

import vtk

from view_mha_volume import find_available_mha_files, load_mha_file


class MHAViewerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tracked Ultrasound Viewer")
        self.setGeometry(100, 100, 1500, 900)

        # --- State ---
        self.available_files = find_available_mha_files()
        self.current_file = None
        self.volume = None
        self.prop = None

        # --- Main Layout ---
        main_layout = QHBoxLayout(self)
        self.setLayout(main_layout)

        # ==============================
        # Sidebar setup
        # ==============================
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setAlignment(Qt.AlignTop)

        lbl_title = QLabel("<h2>Tracked Ultrasound Viewer</h2>")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_subtitle = QLabel("<i>Select file source:</i>")
        lbl_subtitle.setAlignment(Qt.AlignLeft)

        self.btn_open = QPushButton("📂 Open Local .mha File")
        self.btn_open.clicked.connect(self.select_file)

        self.lbl_samples = QLabel("<b>Or choose a sample file:</b>")
        self.file_list = QListWidget()
        self.file_list.addItems([os.path.basename(f) for f in self.available_files])
        self.file_list.itemClicked.connect(self.select_sample_file)
        # self.file_list.setMaximumHeight(150)


        self.sidebar_info = QTextEdit()
        self.sidebar_info.setReadOnly(True)
        self.sidebar_info.setSizeAdjustPolicy(QTextEdit.AdjustToContents)
        self.sidebar_info.setMaximumHeight(150)
        self.sidebar_info.setMinimumHeight(20)


        # Visualization control sliders
        vis_controls = QGroupBox("Visualization Controls")
        vis_layout = QVBoxLayout()

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self.adjust_opacity)

        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(-50, 50)
        self.brightness_slider.setValue(0)
        self.brightness_slider.valueChanged.connect(self.adjust_brightness)

        vis_layout.addWidget(QLabel("Opacity"))
        vis_layout.addWidget(self.opacity_slider)
        vis_layout.addWidget(QLabel("Brightness"))
        vis_layout.addWidget(self.brightness_slider)

        # --- Robust Opacity Controls ---
        vis_layout.addWidget(QLabel("<b>Volume Opacity Mapping</b>"))
        
        # Slider to cut out background noise (Lower Threshold)
        # vis_layout.addWidget(QLabel("Lower Threshold (Hide Noise):"))
        # self.threshold_slider = QSlider(Qt.Horizontal)
        # self.threshold_slider.setRange(0, 100)
        # self.threshold_slider.setValue(20) # Start with a little noise reduction
        # self.threshold_slider.valueChanged.connect(self.update_opacity_function)
        # vis_layout.addWidget(self.threshold_slider)

        # # Slider to control overall peak opacity
        # vis_layout.addWidget(QLabel("Peak Opacity (Density):"))
        # self.peak_slider = QSlider(Qt.Horizontal)
        # self.peak_slider.setRange(0, 100)
        # self.peak_slider.setValue(100)
        # self.peak_slider.valueChanged.connect(self.update_opacity_function)
        # vis_layout.addWidget(self.peak_slider)

        vis_controls.setLayout(vis_layout)

        # ---------------- Opacity Preset Dropdown ----------------
        self.opacity_preset_label = QLabel("Opacity Preset")
        vis_layout.addWidget(self.opacity_preset_label)

        self.opacity_preset_combo = QComboBox()
        self.opacity_preset_combo.addItems([
            "Ultrasound - Soft",
            "Ultrasound - High Contrast",
            "Bright Structures Only",
            "Hide Background",
            "CT - Air",
            "CT - Bone",
            "CT - Soft Tissue",
            "CT - Chest",
            "MRI - Brain",
            "MRI - Bone"
        ])
        vis_layout.addWidget(self.opacity_preset_combo)
        self.opacity_preset_combo.currentTextChanged.connect(self.apply_opacity_preset)
        self.opacity_preset_combo.currentTextChanged.connect(self.apply_color_preset)



        # --- Inside your sidebar layout code ---
        self.color_dropdown = QComboBox()
        self.color_dropdown.addItems(["Grayscale", "Thermal (Red-Yellow)", "Ocean (Blue-Cyan)", "Tissue-Bone"])
        self.color_dropdown.currentIndexChanged.connect(self.update_color_function)
        vis_layout.addWidget(QLabel("Color Preset:"))
        vis_layout.addWidget(self.color_dropdown)

        sidebar_layout.addWidget(lbl_title)
        sidebar_layout.addWidget(lbl_subtitle)
        sidebar_layout.addWidget(self.btn_open)
        sidebar_layout.addSpacing(20)
        sidebar_layout.addWidget(self.lbl_samples)
        sidebar_layout.addWidget(self.file_list)
        sidebar_layout.addSpacing(15)
        sidebar_layout.addWidget(QLabel("<b>File Details:</b>"))
        sidebar_layout.addWidget(self.sidebar_info)
        sidebar_layout.addSpacing(10)
        sidebar_layout.addWidget(vis_controls)

        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar_layout)

        # ==============================
        # VTK Viewer Area
        # ==============================
        self.vtk_widget = QVTKRenderWindowInteractor(self)
        self.render_window = self.vtk_widget.GetRenderWindow()
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.1, 0.1, 0.15)
        self.render_window.AddRenderer(self.renderer)

        # Floating control widget (anchored bottom-left)
        self.control_overlay = QWidget(self.vtk_widget)
        self._setup_control_panel()

        viewer_layout = QVBoxLayout()
        viewer_layout.addWidget(self.vtk_widget)
        viewer_widget = QWidget()
        viewer_widget.setLayout(viewer_layout)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(sidebar_widget)
        splitter.addWidget(viewer_widget)
        splitter.setSizes([380, 1120])
        main_layout.addWidget(splitter)

        # Handle resizing to keep overlay anchored bottom-left
        self.vtk_widget.resizeEvent = self._on_vtk_resized

        # Prepare interactor
        self.interactor = self.vtk_widget
        self.interactor.Initialize()
        self.interactor.Start()

        # Setting a slower camera interaction style
        style = vtk.vtkInteractorStyleTrackballCamera()
        if hasattr(style, "SetMotionFactor"):
            style.SetMotionFactor(7)
        if hasattr(style, "SetRotationFactor"):
            style.SetRotationFactor(7)
        self.interactor.SetInteractorStyle(style)


        if not self.available_files:
            self.sidebar_info.setText("⚠️ No PlusToolKit sample files found.\nClick 'Open Local .mha File' to select one manually.")
        else:
            self.sidebar_info.setText(f"Found {len(self.available_files)} sample file(s).\nSelect one from the list to view.")

    # ==============================
    # Floating Control Panel Setup
    # ==============================
    def _setup_control_panel(self):
        self.overlay_size = QPoint(240, 250)
        self.control_overlay.resize(self.overlay_size.x(), self.overlay_size.y())

        app_palette = QApplication.palette()
        is_dark = app_palette.color(QPalette.Window).value() < 128

        font_color = "#FFFFFF" if is_dark else "#202020"
        panel_bg = "rgba(40,40,40,180)" if is_dark else "rgba(255,255,255,230)"
        button_bg = "#555555" if is_dark else "#f4f4f4"
        button_hover = "#707070" if is_dark else "#e0e0e0"
        button_pressed = "#808080" if is_dark else "#c8c8c8"
        border_color = "#999999" if is_dark else "#b0b0b0"

        self.control_overlay.setStyleSheet(f"""
            QWidget {{
                background-color: {panel_bg};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
            QPushButton {{
                background-color: {button_bg};
                color: {font_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                min-width: 54px;
                min-height: 54px;
                font-size: 22px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {button_hover};
            }}
            QPushButton:pressed {{
                background-color: {button_pressed};
            }}
        """)

        grid = QGridLayout(self.control_overlay)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setSpacing(6)

        # Create holdable buttons (auto-repeat)
        def make_button(text, func):
            btn = QPushButton(text)
            btn.pressed.connect(lambda: self._start_holding(func))
            btn.released.connect(self._stop_holding)
            return btn

        self.hold_timer = QTimer()
        self.hold_timer.timeout.connect(lambda: self._holding_action())

        # Movement and rotation bindings
        self.hold_action_func = None

        self.btn_up = make_button("↑", lambda: self.translate_view(0, 10, 0))
        self.btn_down = make_button("↓", lambda: self.translate_view(0, -10, 0))
        self.btn_left = make_button("←", lambda: self.translate_view(-10, 0, 0))
        self.btn_right = make_button("→", lambda: self.translate_view(10, 0, 0))

        self.btn_rot_ul = make_button("⤺", lambda: self.rotate_camera('up_left'))
        self.btn_rot_ur = make_button("⤻", lambda: self.rotate_camera('up_right'))
        self.btn_rot_dl = make_button("⟳", lambda: self.rotate_camera('down_left'))
        self.btn_rot_dr = make_button("⟲", lambda: self.rotate_camera('down_right'))

        self.btn_reset = QPushButton("Reset")
        self.btn_reset.clicked.connect(self.reset_camera)
        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_out = QPushButton("–")
        self.btn_zoom_in.pressed.connect(lambda: self._start_holding(lambda: self.zoom_camera(1.05)))
        self.btn_zoom_out.pressed.connect(lambda: self._start_holding(lambda: self.zoom_camera(0.95)))
        self.btn_zoom_in.released.connect(self._stop_holding)
        self.btn_zoom_out.released.connect(self._stop_holding)

        # Layout grid
        grid.addWidget(self.btn_rot_ul, 0, 0)
        grid.addWidget(self.btn_up, 0, 1)
        grid.addWidget(self.btn_rot_ur, 0, 2)
        grid.addWidget(self.btn_left, 1, 0)
        grid.addWidget(self.btn_reset, 1, 1)
        grid.addWidget(self.btn_right, 1, 2)
        grid.addWidget(self.btn_rot_dl, 2, 0)
        grid.addWidget(self.btn_down, 2, 1)
        grid.addWidget(self.btn_rot_dr, 2, 2)
        grid.addWidget(self.btn_zoom_in, 3, 0, 1, 1)
        grid.addWidget(self.btn_zoom_out, 3, 2, 1, 1)

        self.btn_up.setToolTip("Move view up")
        self.btn_down.setToolTip("Move view down")
        self.btn_left.setToolTip("Move view left")
        self.btn_right.setToolTip("Move view right")

        self.btn_rot_ul.setToolTip("Rotate up-left")
        self.btn_rot_ur.setToolTip("Rotate up-right")
        self.btn_rot_dl.setToolTip("Rotate down-left")
        self.btn_rot_dr.setToolTip("Rotate down-right")

        self.btn_reset.setToolTip("Reset camera view")
        self.btn_zoom_in.setToolTip("Zoom in")
        self.btn_zoom_out.setToolTip("Zoom out")


    def _on_vtk_resized(self, event):
        """Ensure overlay stays anchored to bottom-left on resize."""
        new_height = self.vtk_widget.height()
        self.control_overlay.move(20, new_height - self.overlay_size.y() - 20)
        event.accept()

    # ==============================
    # Button Hold Logic
    # ==============================
    def _start_holding(self, func):
        self.hold_action_func = func
        func()  # run once immediately
        self.hold_timer.start(50)  # repeat every 50 ms

    def _stop_holding(self):
        self.hold_timer.stop()
        self.hold_action_func = None

    def _holding_action(self):
        if self.hold_action_func:
            self.hold_action_func()

    # ==============================
    # File loading and rendering
    # ==============================
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select .mha File", "", "MetaImage Files (*.mha)")
        if file_path:
            self.load_and_display(file_path)

    def select_sample_file(self, item):
        idx = self.file_list.row(item)
        file_path = self.available_files[idx]
        self.load_and_display(file_path)

    def load_and_display(self, file_path):
        try:
            image_data, is_3d = load_mha_file(file_path)

            # Verify VTK actually produced a valid image
            if not image_data or not isinstance(image_data, vtk.vtkImageData):
                raise ValueError("Not a valid image volume (unsupported data type).")

            dims = image_data.GetDimensions()
            if dims[0] == 0 or dims[1] == 0 or dims[2] == 0:
                raise ValueError("File does not contain volumetric image data.")

            # --- 1. Clear previous 3D objects ---
            self.renderer.RemoveAllViewProps()

            # --- 2. Setup Volume Rendering Pipeline ---
            mapper = vtk.vtkSmartVolumeMapper()
            mapper.SetInputData(image_data)

            self.prop = vtk.vtkVolumeProperty()
            self.prop.ShadeOn()
            self.prop.SetInterpolationTypeToLinear()

            # Set up default Color Transfer Function (Grayscale)
            smin, smax = image_data.GetScalarRange()
            color_func = vtk.vtkColorTransferFunction()
            color_func.AddRGBPoint(smin, 0.0, 0.0, 0.0)
            color_func.AddRGBPoint(smax, 1.0, 1.0, 1.0)
            self.prop.SetColor(color_func)

            self.is_hu_volume = (smin < -500 and smax > 1500) 

            # Create and add volume to renderer
            self.volume = vtk.vtkVolume()
            self.volume.SetMapper(mapper)
            self.volume.SetProperty(self.prop)
            self.renderer.AddVolume(self.volume)
            
            # Add helper axes
            self.renderer.AddActor(vtk.vtkAxesActor())

            # --- 3. Initialize Opacity via Sliders ---
            # Save the current file path so the slider method can access it
            self.current_file = file_path
            
            # This replaces the entire "Section 4 & 5" from your old code
            # It builds the PiecewiseFunction based on the current slider positions
            # self.update_opacity_function()

            # --- 4. Update UI Info Text ---
            spacing = image_data.GetSpacing()
            origin = image_data.GetOrigin()
            self.sidebar_info.setHtml(
                f"<b>File:</b> {os.path.basename(file_path)}<br>"
                f"<b>Dimensions:</b> {dims}<br>"
                f"<b>Spacing:</b> {spacing}<br>"
                f"<b>Origin:</b> {origin}<br>"
                f"<b>Scalar Range:</b> {(smin, smax)}<br>"
                f"<b>Type:</b> {'3D Volume' if is_3d else '2D Image'}"
            )

            # Final visual refresh
            self.renderer.ResetCamera()
            self.update_color_function() # Ensure colors match the dropdown
            self.render_window.Render()

        except Exception as e:
            self.renderer.RemoveAllViewProps()
            self.render_window.Render()
            QMessageBox.warning(
                self,
                "Error Loading File",
                f"Cannot load this file:\n{file_path}\n\nReason:\n{e}"
            )

    # def update_opacity_function(self):
    #     if not self.prop or not self.current_file:
    #         return

    #     # Get the range of the current data (e.g., 0 to 255)
    #     # We need to fetch this from the actual volume data
    #     image_data = self.volume.GetMapper().GetInput()
    #     smin, smax = image_data.GetScalarRange()
    #     s_range = smax - smin

    #     # Calculate values based on sliders
    #     # Threshold: Move the "start" of the ramp
    #     thresh_val = smin + (self.threshold_slider.value() / 100.0) * s_range
    #     # Peak: How opaque is the brightest point?
    #     peak_opacity = self.peak_slider.value() / 100.0

    #     # Create a new function
    #     new_opacity = vtk.vtkPiecewiseFunction()
        
    #     # 1. Everything below threshold is invisible (0.0)
    #     new_opacity.AddPoint(smin, 0.0)
    #     new_opacity.AddPoint(thresh_val, 0.0)
        
    #     # 2. Ramp up to the peak opacity at the max scalar value
    #     new_opacity.AddPoint(smax, peak_opacity)

    #     # Apply to volume
    #     self.prop.SetScalarOpacity(new_opacity)
    #     self.render_window.Render()

    def apply_opacity_preset(self, preset):
        if not self.prop or not self.volume:
            return

        smin, smax = self.volume.GetMapper().GetInput().GetScalarRange()
        func = vtk.vtkPiecewiseFunction()

        # Detect HU scan automatically
        isHU = (smin < -500 and smax > 1500)

        # -------------------------
        # HU-BASED PRESETS (Slicer)
        # -------------------------
        if preset == "CT - Bone" and isHU:
            # SlicerBone: hard bone = +700–3000
            func.AddPoint(-1024, 0.00)   # air
            func.AddPoint(  150, 0.00)   # soft tissue cutoff
            func.AddPoint(  300, 0.10)   # trabecular bone
            func.AddPoint(  700, 0.40)   # cortical start
            func.AddPoint( 1200, 0.80)   # dense cortical
            func.AddPoint( 3000, 1.00)
        
        elif preset == "CT - Soft Tissue" and isHU:
            func.AddPoint(-1024, 0.00)
            func.AddPoint(  -200, 0.00)
            func.AddPoint(    50, 0.15)
            func.AddPoint(   300, 0.50)
            func.AddPoint(  1000, 1.00)

        elif preset == "CT - Air" and isHU:
            func.AddPoint(-1024, 1.00)
            func.AddPoint(  -900, 0.80)
            func.AddPoint(  -700, 0.50)
            func.AddPoint(   300, 0.00)
            func.AddPoint(  1500, 0.00)

        elif preset == "CT - Chest" and isHU:
            func.AddPoint(-1024, 0.00)
            func.AddPoint(  -700, 0.20)
            func.AddPoint(  -100, 0.50)
            func.AddPoint(   300, 0.70)
            func.AddPoint(  2000, 1.00)

        elif preset == "MRI - Brain" and isHU:
            # MRI-like appearance (not true HU)
            func.AddPoint(smin, 0.00)
            func.AddPoint(smin + (smax - smin)*0.20, 0.15)
            func.AddPoint(smin + (smax - smin)*0.50, 0.35)
            func.AddPoint(smin + (smax - smin)*0.85, 0.80)
            func.AddPoint(smax, 1.00)

        elif preset == "MRI - Bone" and isHU:
            func.AddPoint(-1024, 0.00)
            func.AddPoint(  100, 0.00)
            func.AddPoint(  400, 0.10)
            func.AddPoint( 1000, 0.50)
            func.AddPoint( 2500, 1.00)

        # ----------------------------------------------
        # Generic presets for NON-HU (0–255 volumes)
        # ----------------------------------------------
        elif preset == "Ultrasound - Soft":
            func.AddPoint(smin, 0.0)
            func.AddPoint(smin + (smax-smin)*0.3, 0.1)
            func.AddPoint(smin + (smax-smin)*0.6, 0.3)
            func.AddPoint(smax, 1.0)

        elif preset == "Ultrasound - High Contrast":
            func.AddPoint(smin, 0.0)
            func.AddPoint(smin + (smax-smin)*0.4, 0.0)
            func.AddPoint(smin + (smax-smin)*0.6, 0.5)
            func.AddPoint(smax, 1.0)

        elif preset == "Bright Structures Only":
            func.AddPoint(smin, 0.0)
            func.AddPoint(smin + (smax-smin)*0.8, 0.0)
            func.AddPoint(smax, 1.0)

        elif preset == "Hide Background":
            func.AddPoint(smin, 0.0)
            func.AddPoint(smin + (smax-smin)*0.2, 0.0)
            func.AddPoint(smin + (smax-smin)*0.5, 0.3)
            func.AddPoint(smax, 1.0)

        self.prop.SetScalarOpacity(func)
        self.render_window.Render()


    def apply_color_preset(self, preset):
        if not self.prop or not self.volume:
            return

        smin, smax = self.volume.GetMapper().GetInput().GetScalarRange()
        color = vtk.vtkColorTransferFunction()

        isHU = (smin < -500 and smax > 1500)

        # -------------------------
        # HU-BASED COLOR PRESETS
        # -------------------------
        if preset == "CT - Bone" and isHU:
            # Light yellow-white bone colors like Slicer
            color.AddRGBPoint(-1024, 0.00, 0.00, 0.00)
            color.AddRGBPoint(   300, 0.90, 0.85, 0.75)
            color.AddRGBPoint(   700, 0.95, 0.92, 0.80)
            color.AddRGBPoint(  1200, 1.00, 0.98, 0.90)
            color.AddRGBPoint(  3000, 1.00, 1.00, 1.00)

        elif preset == "CT - Soft Tissue" and isHU:
            color.AddRGBPoint(-1024, 0.00, 0.00, 0.00)
            color.AddRGBPoint(  -200, 0.50, 0.30, 0.20)
            color.AddRGBPoint(    50, 0.80, 0.55, 0.40)
            color.AddRGBPoint(   300, 0.95, 0.80, 0.70)
            color.AddRGBPoint(  1500, 1.00, 0.95, 0.90)

        elif preset == "CT - Chest" and isHU:
            color.AddRGBPoint(-1024, 0.00, 0.00, 0.00)
            color.AddRGBPoint(  -700, 0.20, 0.40, 0.80)    # blue-ish for air spaces
            color.AddRGBPoint(  -100, 0.80, 0.60, 0.50)
            color.AddRGBPoint(   300, 0.95, 0.80, 0.70)
            color.AddRGBPoint(  2000, 1.00, 0.95, 0.90)

        elif preset == "CT - Air" and isHU:
            color.AddRGBPoint(smin, 1.00, 1.00, 1.00)
            color.AddRGBPoint(-900, 0.80, 0.80, 0.80)
            color.AddRGBPoint(-700, 0.40, 0.40, 0.40)
            color.AddRGBPoint( 300, 0.00, 0.00, 0.00)
            color.AddRGBPoint(1500, 0.00, 0.00, 0.00)

        elif preset == "MRI - Brain" and isHU:
            # MRI-like grayscale
            color.AddRGBPoint(smin, 0.00, 0.00, 0.00)
            color.AddRGBPoint(smin + (smax-smin)*0.30, 0.25, 0.25, 0.25)
            color.AddRGBPoint(smin + (smax-smin)*0.60, 0.55, 0.55, 0.55)
            color.AddRGBPoint(smax, 1.00, 1.00, 1.00)

        elif preset == "MRI - Bone" and isHU:
            color.AddRGBPoint(-1024, 0.00, 0.00, 0.00)
            color.AddRGBPoint(  100, 0.20, 0.20, 0.20)
            color.AddRGBPoint( 1000, 0.75, 0.75, 0.75)
            color.AddRGBPoint( 2500, 1.00, 1.00, 1.00)

        # ----------------------------------------------
        # NON-HU / ULTRASOUND COLOR PRESETS
        # ----------------------------------------------
        elif preset == "Ultrasound - Soft":
            color.AddRGBPoint(smin, 0.00, 0.00, 0.00)
            color.AddRGBPoint(smax, 1.00, 1.00, 1.00)

        elif preset == "Ultrasound - High Contrast":
            color.AddRGBPoint(smin, 0.00, 0.00, 0.00)
            color.AddRGBPoint(smax, 1.00, 1.00, 1.00)

        elif preset == "Bright Structures Only":
            color.AddRGBPoint(smin, 0.00, 0.00, 0.00)
            color.AddRGBPoint(smax, 1.00, 1.00, 1.00)

        elif preset == "Hide Background":
            color.AddRGBPoint(smin, 0.00, 0.00, 0.00)
            color.AddRGBPoint(smax, 1.00, 1.00, 1.00)

        self.prop.SetColor(color)
        self.render_window.Render()


    def update_color_function(self):
        if not self.prop or not self.volume:
            return

        image_data = self.volume.GetMapper().GetInput()
        smin, smax = image_data.GetScalarRange()
        
        color_func = vtk.vtkColorTransferFunction()
        preset = self.color_dropdown.currentText()

        if preset == "Grayscale":
            color_func.AddRGBPoint(smin, 0.0, 0.0, 0.0)
            color_func.AddRGBPoint(smax, 1.0, 1.0, 1.0)

        elif preset == "Thermal (Red-Yellow)":
            # Dark Red -> Bright Orange -> Yellow
            color_func.AddRGBPoint(smin, 0.2, 0.0, 0.0)
            color_func.AddRGBPoint(smin + (smax-smin)*0.5, 1.0, 0.5, 0.0)
            color_func.AddRGBPoint(smax, 1.0, 1.0, 0.0)

        elif preset == "Ocean (Blue-Cyan)":
            # Deep Blue -> Cyan -> White
            color_func.AddRGBPoint(smin, 0.0, 0.0, 0.2)
            color_func.AddRGBPoint(smin + (smax-smin)*0.5, 0.0, 0.8, 1.0)
            color_func.AddRGBPoint(smax, 1.0, 1.0, 1.0)

        elif preset == "Tissue-Bone":
            # Purple (Fluid) -> Pink (Tissue) -> White (Bone)
            color_func.AddRGBPoint(smin, 0.3, 0.0, 0.3)
            color_func.AddRGBPoint(smin + (smax-smin)*0.4, 0.9, 0.6, 0.6)
            color_func.AddRGBPoint(smax, 1.0, 1.0, 1.0)

        self.prop.SetColor(color_func)
        self.render_window.Render()

    # ==============================
    # Opacity / Brightness Controls
    # ==============================
    def adjust_opacity(self):
        """Global opacity adjustment — visually effective scaling."""
        if not self.volume:
            return

        # Map slider range (0–100) → scaling factor range (2.0 → 0.1)
        # Lower value = denser opacity
        slider_value = self.opacity_slider.value()
        scaled_value = 2.0 - (slider_value / 100.0) * 1.9  # 2.0 → 0.1

        self.volume.GetProperty().SetScalarOpacityUnitDistance(scaled_value)
        self.render_window.Render()


    def adjust_brightness(self):
        if not self.prop:
            return
        val = self.brightness_slider.value() / 100.0
        color = self.prop.GetRGBTransferFunction()
        smin, smax = color.GetRange()
        color.RemoveAllPoints()
        low = max(0.0, 0.2 + val)
        high = min(1.0, 1.0 + val)
        color.AddRGBPoint(smin, low, low, low)
        color.AddRGBPoint(smax, high, high, high)
        self.render_window.Render()

    # ==============================
    # Camera Controls
    # ==============================
    def get_camera(self):
        return self.renderer.GetActiveCamera()

    def translate_view(self, dx, dy, dz):
        cam = self.get_camera()
        fp = list(cam.GetFocalPoint())
        pos = list(cam.GetPosition())
        fp[0] += dx
        fp[1] += dy
        fp[2] += dz
        pos[0] += dx
        pos[1] += dy
        pos[2] += dz
        cam.SetFocalPoint(fp)
        cam.SetPosition(pos)
        self.render_window.Render()

    def rotate_camera(self, direction):
        cam = self.get_camera()
        if direction == 'up_left':
            cam.Azimuth(-10)
            cam.Elevation(10)
        elif direction == 'up_right':
            cam.Azimuth(10)
            cam.Elevation(10)
        elif direction == 'down_left':
            cam.Azimuth(-10)
            cam.Elevation(-10)
        elif direction == 'down_right':
            cam.Azimuth(10)
            cam.Elevation(-10)
        cam.OrthogonalizeViewUp()
        self.renderer.ResetCameraClippingRange()
        self.render_window.Render()

    def zoom_camera(self, factor):
        cam = self.get_camera()
        cam.Zoom(factor)
        self.renderer.ResetCameraClippingRange()
        self.render_window.Render()

    def reset_camera(self):
        self.renderer.ResetCamera()
        self.render_window.Render()


def main():
    app = QApplication(sys.argv)
    viewer = MHAViewerApp()
    viewer.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
