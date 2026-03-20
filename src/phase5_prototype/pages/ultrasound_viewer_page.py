import sys
import os
import vtk
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QSplitter,
    QHBoxLayout, QPushButton, QLabel, QFileDialog, QTextEdit,
    QSlider, QMessageBox, QComboBox, QGroupBox, QListWidget, 
    QGridLayout, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QColor

from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

# Import logic from your helper file
from mha_viewer import find_available_mha_files, load_mha_file

# --- THEME COLORS ---
BG_LIGHT = "#F0F2F5"
PANEL_WHITE = "#FFFFFF"
NAVY = "#132B50"
ACCENT = "#3A66B7"
ACCENT_HOVER = "#4A7DE0"
BORDER_LIGHT = "#D1D5DB"
MUTED_TEXT = "#64748B"

BASE_STYLE = f"""
    QWidget {{ background-color: {BG_LIGHT}; color: {NAVY}; }}
    
    QGroupBox {{
        color: {NAVY}; border: 1px solid {BORDER_LIGHT}; border-radius: 8px;
        margin-top: 15px; padding-top: 10px; font-weight: bold; font-size: 11px;
        background-color: {PANEL_WHITE};
    }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}

    QListWidget {{
        background: {BG_LIGHT}; border: 1px solid {BORDER_LIGHT};
        border-radius: 6px; padding: 5px; color: {NAVY}; font-size: 10px;
    }}
    QListWidget::item {{ padding: 4px; border-radius: 4px; }}
    QListWidget::item:selected {{ background: {ACCENT}; color: white; }}

    /* COMBOBOX STYLING */
    QComboBox {{
        background: {PANEL_WHITE} !important; 
        color: {NAVY}; 
        border: 1px solid {BORDER_LIGHT};
        border-radius: 6px; 
        padding: 5px; 
        font-size: 11px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {PANEL_WHITE} !important;
        border: 1px solid {BORDER_LIGHT};
        selection-background-color: {ACCENT};
        selection-color: white;
        outline: none;
    }}
    
    QLabel {{ background: transparent; border: none; color: {NAVY}; font-size: 11px; }}
"""

class TrackedUltrasoundViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tracked Ultrasound Viewer")
        self.resize(1500, 900)
        self.setStyleSheet(BASE_STYLE)

        # --- State ---
        try:
            self.available_files = find_available_mha_files()
        except Exception:
            self.available_files = []
            
        self.current_file = None
        self.volume = None
        self.prop = None
        self.hold_action_func = None
        self.hold_timer = QTimer()
        self.hold_timer.timeout.connect(self._holding_action)

        self._build_ui()

    def _build_ui(self):
        # FIX: Single main vertical layout for the whole widget
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ==============================
        # HEADER BAR
        # ==============================
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet(f"background-color: {PANEL_WHITE}; border-bottom: 1px solid {BORDER_LIGHT};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        self.btn_back = QPushButton("←  Back to Menu")
        self.btn_back.setFixedSize(130, 40)
        self.btn_back.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG_LIGHT}; color: {NAVY};
                font-size: 12px; border-radius: 10px; border: none; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {BORDER_LIGHT}; }}
        """)
        header_layout.addWidget(self.btn_back)

        title_vbox = QVBoxLayout()
        header_title = QLabel("TRACKED ULTRASOUND VIEWER")
        header_title.setStyleSheet(f"color: {NAVY}; font-size: 14px; font-weight: 800; letter-spacing: 1px;")
        title_vbox.addWidget(header_title)
        header_layout.addLayout(title_vbox)
        header_layout.addStretch()
        
        self.main_layout.addWidget(header)

        # ==============================
        # BODY AREA
        # ==============================
        body_content = QWidget()
        body_layout = QHBoxLayout(body_content)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {BORDER_LIGHT}; }}")

        # --- SIDEBAR ---
        sidebar_container = QWidget()
        sidebar_container.setStyleSheet(f"background-color: {PANEL_WHITE}; border-top-right-radius: 25px; border-bottom-right-radius: 25px;")
        sidebar_layout = QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        inner_scroll = QWidget()
        inner_scroll.setStyleSheet("background: transparent;")
        inner_layout = QVBoxLayout(inner_scroll)
        inner_layout.setContentsMargins(20, 20, 20, 20)
        inner_layout.setSpacing(5)

        # 1. Source
        src_group = QGroupBox("File Source")
        src_layout = QVBoxLayout(src_group)
        self.btn_open = QPushButton("Open Local .mha File")
        self.btn_open.setFixedHeight(34)
        self.btn_open.setStyleSheet(f"background: {ACCENT}; color: white; border-radius: 6px; font-weight: bold;")
        self.btn_open.clicked.connect(self.select_file)
        
        self.file_list = QListWidget()
        self.file_list.setFixedHeight(120)
        self.file_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.file_list.addItems([os.path.basename(f) for f in self.available_files])
        self.file_list.itemClicked.connect(self.select_sample_file)

        src_layout.addWidget(self.btn_open)
        src_layout.addWidget(QLabel("Sample files:"))
        src_layout.addWidget(self.file_list)
        inner_layout.addWidget(src_group)

        # 2. Details
        det_group = QGroupBox("File Details")
        det_layout = QVBoxLayout(det_group)
        self.sidebar_info = QTextEdit()
        self.sidebar_info.setReadOnly(True)
        self.sidebar_info.setFixedHeight(150)
        self.sidebar_info.setStyleSheet(f"background: {BG_LIGHT}; border: 1px solid {BORDER_LIGHT}; border-radius: 6px;")
        det_layout.addWidget(self.sidebar_info)
        inner_layout.addWidget(det_group)

        # 3. Controls
        vis_group = QGroupBox("Visualization Controls")
        vis_layout = QVBoxLayout(vis_group)
        
        vis_layout.addWidget(QLabel("Opacity"))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self.adjust_opacity)
        vis_layout.addWidget(self.opacity_slider)

        vis_layout.addWidget(QLabel("Brightness"))
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(-50, 50)
        self.brightness_slider.setValue(0)
        self.brightness_slider.valueChanged.connect(self.adjust_brightness)
        vis_layout.addWidget(self.brightness_slider)

        vis_layout.addWidget(QLabel("Opacity Preset"))
        self.opacity_preset_combo = QComboBox()
        self.opacity_preset_combo.addItems([
            "Ultrasound - Soft", "Ultrasound - High Contrast", "Bright Structures Only",
            "Hide Background", "CT - Air", "CT - Bone", "CT - Soft Tissue",
            "CT - Chest", "MRI - Brain", "MRI - Bone"
        ])
        self.opacity_preset_combo.currentTextChanged.connect(self.apply_opacity_preset)
        self.opacity_preset_combo.currentTextChanged.connect(self.apply_color_preset)
        self.opacity_preset_combo.setStyleSheet(f"background: {BG_LIGHT} !important; background-color: {PANEL_WHITE} !important ;color: {NAVY}; border: 1px solid {BORDER_LIGHT}; border-radius: 6px; padding: 5px; font-size: 11px;")
        vis_layout.addWidget(self.opacity_preset_combo)

        vis_layout.addWidget(QLabel("Color Mapping"))
        self.color_dropdown = QComboBox()
        self.color_dropdown.addItems(["Grayscale", "Thermal", "Ocean"])
        self.color_dropdown.currentTextChanged.connect(self.update_color_function)
        self.color_dropdown.setStyleSheet(f"background: {BG_LIGHT} !important; background-color: {PANEL_WHITE} !important ;color: {NAVY}; border: 1px solid {BORDER_LIGHT}; border-radius: 6px; padding: 5px; font-size: 11px;")
        vis_layout.addWidget(self.color_dropdown)
        
        inner_layout.addWidget(vis_group)
        inner_layout.addStretch()

        scroll.setWidget(inner_scroll)
        sidebar_layout.addWidget(scroll)

        # --- VTK VIEWER AREA ---
        self.vtk_container = QWidget()
        vtk_vbox = QVBoxLayout(self.vtk_container)
        vtk_vbox.setContentsMargins(15, 15, 15, 15)

        self.vtk_widget = QVTKRenderWindowInteractor(self.vtk_container)
        self.vtk_widget.setStyleSheet(f"border: 1px solid {BORDER_LIGHT}; border-radius: 15px; background: black;")
        
        self.render_window = self.vtk_widget.GetRenderWindow()
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0, 0, 0) # Black placeholder
        self.render_window.AddRenderer(self.renderer)

        self.control_overlay = QFrame(self.vtk_widget)
        self._setup_control_panel()

        style = vtk.vtkInteractorStyleTrackballCamera()
        style.SetMotionFactor(6.0) # Slower rotation
        self.vtk_widget.SetInteractorStyle(style)

        vtk_vbox.addWidget(self.vtk_widget)
        
        splitter.addWidget(sidebar_container)
        splitter.addWidget(self.vtk_container)
        splitter.setSizes([380, 1120])
        
        body_layout.addWidget(splitter)
        self.main_layout.addWidget(body_content)

        # Force render so the black square appears immediately
        self.render_window.Render() 
        self.vtk_widget.Initialize()
        self.vtk_widget.resizeEvent = self._on_vtk_resized

    def _setup_control_panel(self):
        self.overlay_size = QPoint(220, 240)
        self.control_overlay.resize(self.overlay_size.x(), self.overlay_size.y())
        self.control_overlay.setStyleSheet(f"""
            QFrame {{ background: {PANEL_WHITE}; border: 1px solid {BORDER_LIGHT}; border-radius: 12px; }}
            QPushButton {{
                background: {BG_LIGHT}; color: {NAVY}; border: 1px solid {BORDER_LIGHT};
                border-radius: 6px; font-size: 18px; min-width: 45px; min-height: 45px;
            }}
            QPushButton:hover {{ background: {BORDER_LIGHT}; }}
        """)

        grid = QGridLayout(self.control_overlay)
        grid.setSpacing(5)

        def make_btn(text, func):
            btn = QPushButton(text)
            btn.pressed.connect(lambda: self._start_holding(func))
            btn.released.connect(self._stop_holding)
            return btn

        grid.addWidget(make_btn("⤺", lambda: self.rotate_camera('up_left')), 0, 0)
        grid.addWidget(make_btn("↑", lambda: self.translate_view(0, 10, 0)), 0, 1)
        grid.addWidget(make_btn("⤻", lambda: self.rotate_camera('up_right')), 0, 2)
        grid.addWidget(make_btn("←", lambda: self.translate_view(-10, 0, 0)), 1, 0)
        
        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setStyleSheet("font-size: 10px; font-weight: bold; text-transform: uppercase;")
        self.btn_reset.clicked.connect(self.reset_camera)
        grid.addWidget(self.btn_reset, 1, 1)

        grid.addWidget(make_btn("→", lambda: self.translate_view(10, 0, 0)), 1, 2)
        grid.addWidget(make_btn("⟳", lambda: self.rotate_camera('down_left')), 2, 0)
        grid.addWidget(make_btn("↓", lambda: self.translate_view(0, -10, 0)), 2, 1)
        grid.addWidget(make_btn("⟲", lambda: self.rotate_camera('down_right')), 2, 2)

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
            if not image_data or not isinstance(image_data, vtk.vtkImageData):
                raise ValueError("Not a valid image volume.")

            dims = image_data.GetDimensions()
            self.renderer.RemoveAllViewProps()

            mapper = vtk.vtkSmartVolumeMapper()
            mapper.SetInputData(image_data)

            self.prop = vtk.vtkVolumeProperty()
            self.prop.ShadeOn()
            self.prop.SetInterpolationTypeToLinear()

            smin, smax = image_data.GetScalarRange()
            color_func = vtk.vtkColorTransferFunction()
            color_func.AddRGBPoint(smin, 0.0, 0.0, 0.0)
            color_func.AddRGBPoint(smax, 1.0, 1.0, 1.0)
            self.prop.SetColor(color_func)

            self.volume = vtk.vtkVolume()
            self.volume.SetMapper(mapper)
            self.volume.SetProperty(self.prop)
            self.renderer.AddVolume(self.volume)
            self.renderer.AddActor(vtk.vtkAxesActor())

            self.current_file = file_path
            spacing = image_data.GetSpacing()
            origin = image_data.GetOrigin()
            self.sidebar_info.setHtml(
                f"<b>File:</b> {os.path.basename(file_path)}<br>"
                f"<b>Dimensions:</b> {dims}<br>"
                f"<b>Spacing:</b> {spacing}<br>"
                f"<b>Scalar Range:</b> {(smin, smax)}<br>"
                f"<b>Type:</b> {'3D Volume' if is_3d else '2D Image'}"
            )

            self.renderer.ResetCamera()
            self.update_color_function()
            self.render_window.Render()
        except Exception as e:
            QMessageBox.warning(self, "Error Loading File", f"Reason: {e}")

    def apply_opacity_preset(self, preset):
        if not self.prop or not self.volume: return
        smin, smax = self.volume.GetMapper().GetInput().GetScalarRange()
        func = vtk.vtkPiecewiseFunction()
        if preset == "Ultrasound - Soft":
            func.AddPoint(smin, 0.0)
            func.AddPoint(smin + (smax-smin)*0.6, 0.3)
            func.AddPoint(smax, 1.0)
        else:
            func.AddPoint(smin, 0.0)
            func.AddPoint(smax, 1.0)
        self.prop.SetScalarOpacity(func)
        self.render_window.Render()

    def apply_color_preset(self, preset):
        if not self.prop or not self.volume: return
        smin, smax = self.volume.GetMapper().GetInput().GetScalarRange()
        color = vtk.vtkColorTransferFunction()
        color.AddRGBPoint(smin, 0.0, 0.0, 0.0)
        color.AddRGBPoint(smax, 1.0, 1.0, 1.0)
        self.prop.SetColor(color)
        self.render_window.Render()

    def update_color_function(self):
        if not self.prop or not self.volume: return
        smin, smax = self.volume.GetMapper().GetInput().GetScalarRange()
        color_func = vtk.vtkColorTransferFunction()
        preset = self.color_dropdown.currentText()
        if preset == "Thermal":
            color_func.AddRGBPoint(smin, 0.2, 0.0, 0.0)
            color_func.AddRGBPoint(smax, 1.0, 1.0, 0.0)
        else:
            color_func.AddRGBPoint(smin, 0.0, 0.0, 0.0)
            color_func.AddRGBPoint(smax, 1.0, 1.0, 1.0)
        self.prop.SetColor(color_func)
        self.render_window.Render()

    def adjust_opacity(self):
        if not self.volume: return
        val = 2.0 - (self.opacity_slider.value() / 100.0) * 1.9
        self.volume.GetProperty().SetScalarOpacityUnitDistance(val)
        self.render_window.Render()

    def adjust_brightness(self):
        if not self.prop: return
        val = self.brightness_slider.value() / 100.0
        color = self.prop.GetRGBTransferFunction()
        smin, smax = color.GetRange()
        color.RemoveAllPoints()
        color.AddRGBPoint(smin, max(0, 0.2+val), max(0, 0.2+val), max(0, 0.2+val))
        color.AddRGBPoint(smax, min(1, 1.0+val), min(1, 1.0+val), min(1, 1.0+val))
        self.render_window.Render()

    def get_camera(self): return self.renderer.GetActiveCamera()

    def translate_view(self, dx, dy, dz):
        cam = self.get_camera()
        fp, pos = list(cam.GetFocalPoint()), list(cam.GetPosition())
        for i, delta in enumerate([dx, dy, dz]):
            fp[i] += delta
            pos[i] += delta
        cam.SetFocalPoint(fp)
        cam.SetPosition(pos)
        self.render_window.Render()

    def rotate_camera(self, direction):
        cam = self.get_camera()
        if 'up' in direction: cam.Elevation(10)
        if 'down' in direction: cam.Elevation(-10)
        if 'left' in direction: cam.Azimuth(-10)
        if 'right' in direction: cam.Azimuth(10)
        cam.OrthogonalizeViewUp()
        self.renderer.ResetCameraClippingRange()
        self.render_window.Render()

    def zoom_camera(self, factor):
        self.get_camera().Zoom(factor)
        self.renderer.ResetCameraClippingRange()
        self.render_window.Render()

    def reset_camera(self):
        self.renderer.ResetCamera()
        self.render_window.Render()

    def _on_vtk_resized(self, event):
        self.control_overlay.move(20, self.vtk_widget.height() - self.overlay_size.y() - 20)
        if event: event.accept()

    def _start_holding(self, func):
        self.hold_action_func = func
        func()
        self.hold_timer.start(50)

    def _stop_holding(self):
        self.hold_timer.stop()
        self.hold_action_func = None

    def _holding_action(self):
        if self.hold_action_func: self.hold_action_func()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = TrackedUltrasoundViewer()
    viewer.show()
    print("Window opening.")
    sys.exit(app.exec())