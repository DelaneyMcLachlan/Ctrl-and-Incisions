import sys
import re
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTabWidget, QScrollArea,
    QGroupBox, QFormLayout, QTextEdit, QFileDialog, QMessageBox,
    QSplitter, QFrame, QComboBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QSyntaxHighlighter, QTextCharFormat

# ── Default configs ────────────────────────────────────────────────────────────
# (Keeping these exactly as they were in your snippet)
DEFAULT_DEVICE_CONFIG = """<PlusConfiguration version="2.1">
  <DataCollection StartupDelaySec="5.0">
    <DeviceSet Name="PlusServer: NDI Aurora tracker" Description="Broadcasting tool tracking data through OpenIGTLink" />
    <Device Id="TrackerDevice" Type="AuroraTracker" SerialPort="COM13" BaudRate="921600" ToolReferenceFrame="Tracker" >
      <DataSources><DataSource Type="Tool" Id="Probe" PortName="0" /></DataSources>
      <OutputChannels><OutputChannel Id="TrackerStream"><DataSource Id="Probe" /></OutputChannel></OutputChannels>
    </Device>
    <Device Id="CaptureDevice" Type="VirtualCapture" BaseFilename="C:\\\\Users\\\\mclac\\\\Desktop\\\\Recordings\\\\three\\\\ElliseArmFri.igs.mha" EnableCapturingOnStart="TRUE" >
      <InputChannels><InputChannel Id="CompleteChannel" /></InputChannels>
    </Device>
    <Device Id="VideoDevice" Type="MmfVideo" FrameSize="1920 1080" AcquisitionRate="15" VideoFormat="YUY2" CaptureDeviceId="1">
      <DataSources><DataSource Type="Video" Id="Video" BufferSize="300" PortUsImageOrientation="MN" ClipRectangleOrigin="480 180" ClipRectangleSize="960 700" /></DataSources>
      <OutputChannels><OutputChannel Id="VideoChannelCrop" VideoDataSourceId="Video" /></OutputChannels>
    </Device>
    <Device Id="TrackedDevice" Type="VirtualMixer">
      <InputChannels><InputChannel Id="TrackerStream"/><InputChannel Id="VideoChannelCrop"/></InputChannels>
      <OutputChannels><OutputChannel Id="CompleteChannel"/></OutputChannels>
    </Device>
  </DataCollection>
  <CoordinateDefinitions>
    <Transform From="Image" To="Probe" Matrix="-0.007 0.126 0.008 -107.47 -0.125 -0.008 0.004 75.361 0.004 -0.008 0.126 33.162 0 0 0 1" Error="0.0" Date="112317_141120" />
  </CoordinateDefinitions>
  <PlusOpenIGTLinkServer MaxNumberOfIgtlMessagesToSend="1" MaxTimeSpentWithProcessingMs="50" ListeningPort="18944" SendValidTransformsOnly="true" OutputChannelId="CompleteChannel" > 
    <DefaultClientInfo><MessageTypes><Message Type="TRANSFORM" /></MessageTypes>
      <TransformNames><Transform Name="ProbeToTracker" /></TransformNames>
    </DefaultClientInfo>
  </PlusOpenIGTLinkServer>
</PlusConfiguration>"""

DEFAULT_RECON_CONFIG = """<PlusConfiguration version="2.1">
  <VolumeReconstruction ImageCoordinateFrame="Image" ReferenceCoordinateFrame="Tracker" OutputSpacing="0.5 0.5 0.5" InterpolationMode="LINEAR" Optimization="FULL" FillHoles="ON" >
    <HoleFilling ApproximationMethod="DISTANCE_WEIGHT_INVERSE" ExtrapolationEnabled="FALSE" />
  </VolumeReconstruction>
  <CoordinateDefinitions>
    <Transform From="Image" To="Probe" Matrix="-0.007 0.126 0.008 -107.47 -0.125 -0.008 0.004 75.361 0.004 -0.008 0.126 33.162 0 0 0 1" />
  </CoordinateDefinitions>
</PlusConfiguration>"""

# ── XML Syntax Highlighter ─────────────────────────────────────────────────────

class XmlHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rules = []

        def fmt(color, bold=False):
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(700)
            return f

        # Updated for Light Mode visibility
        self.rules.append((re.compile(r'</?[\w:]+'), fmt("#0033B3", bold=True))) # Tags
        self.rules.append((re.compile(r'\b[\w:]+(?=\s*=)'), fmt("#871094")))    # Attributes
        self.rules.append((re.compile(r'"[^"]*"'), fmt("#067D17")))             # Values
        self.rules.append((re.compile(r'', re.DOTALL), fmt("#8C8C8C")))# Comments
        self.rules.append((re.compile(r'[<>/]'), fmt("#000000")))                # Brackets

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for m in pattern.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)

# ── Field extractor functions ──────────────────────────────────────────────────
# (Functionality remains untouched as requested)
def extract_attr(xml, attr):
    m = re.search(rf'{attr}="([^"]*)"', xml)
    return m.group(1) if m else ""
def replace_attr(xml, attr, value):
    return re.sub(rf'({attr}=")[^"]*(")', rf'\g<1>{value}\g<2>', xml)
def extract_matrix(xml):
    m = re.search(r'Matrix="([^"]*)"', xml, re.DOTALL)
    return m.group(1).strip() if m else ""
def replace_matrix(xml, value):
    return re.sub(r'(Matrix=")[^"]*(")', rf'\g<1>{value}\g<2>', xml, flags=re.DOTALL)

# ── Styled widgets & Colors ────────────────────────────────────────────────────

# Theme matching the Light Grey screenshot
BG_LIGHT = "#F0F2F5"    # Overall window background
PANEL_WHITE = "#FFFFFF" # Raised panel color
NAVY = "#132B50"        # Deep blue for text
ACCENT = "#3A66B7"      # Primary button blue
ACCENT_HOVER = "#4A7DE0"
BORDER_LIGHT = "#D1D5DB"
MUTED_TEXT = "#64748B"

BASE_STYLE = f"""
    QMainWindow, QWidget {{ background-color: {BG_LIGHT}; color: {NAVY}; }}
    QTabWidget::pane {{ 
        border: none; 
        background: {PANEL_WHITE}; 
        border-top-right-radius: 20px;
        border-bottom-right-radius: 20px;
    }}
    
    /* Styling the tabs to look integrated into the panel */
    QTabBar::tab {{
        background: transparent; 
        color: {MUTED_TEXT}; 
        padding: 12px 25px;
        font-family: 'Segoe UI', sans-serif; 
        font-size: 11px; 
        font-weight: 700; 
        text-transform: uppercase;
    }}
    QTabBar::tab:selected {{ 
        color: {ACCENT}; 
        border-bottom: 3px solid {ACCENT}; 
    }}
    
    QGroupBox {{
        color: {NAVY}; border: 1px solid {BORDER_LIGHT}; border-radius: 8px;
        margin-top: 15px; padding-top: 10px; font-weight: bold;
        text-transform: none; font-size: 11px;
    }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}

    QLineEdit, QComboBox {{
        background: {PANEL_WHITE}; color: {NAVY}; border: 1px solid {BORDER_LIGHT};
        border-radius: 6px; padding: 6px; font-size: 12px;
    }}
    QLineEdit:focus, QComboBox:focus {{ border: 1px solid {ACCENT}; }}
    
    /* REMOVED BOXES FROM LABELS HERE */
    QLabel {{ 
        background-color: transparent; 
        border: none !important; 
        color: {NAVY}; 
        font-size: 11px; 
        font-weight: 500; 
    }}
    
    QScrollArea {{ border: none; background: transparent; }}
    QScrollBar:vertical {{ background: {BG_LIGHT}; width: 8px; }}
    QScrollBar::handle:vertical {{ background: {BORDER_LIGHT}; border-radius: 4px; }}
"""

def make_btn(text, color, hover=None, width=None):
    hover = hover or color
    # Remove emojis from text string
    clean_text = text.replace("▶", "").replace("↺", "").replace("📂", "").replace("💾", "").replace("↓", "").strip()
    
    btn = QPushButton(clean_text)
    btn.setFixedHeight(36)
    if width: btn.setFixedWidth(width)
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {color}; color: white; border-radius: 8px;
            font-weight: 600; font-size: 12px; border: none; padding: 0 16px;
        }}
        QPushButton:hover {{ background-color: {hover}; }}
        QPushButton:pressed {{ background-color: #000000; }}
    """)
    return btn

# ── Tab Classes ──────────────────────────────────────────────────────────

class DeviceConfigTab(QWidget):
    xml_changed = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.xml = DEFAULT_DEVICE_CONFIG
        self._build_ui()
        self._populate_fields()

    def _build_ui(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # ── Left: Raised panel ──
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(15, 15, 15, 15)

        # The Raised Panel frame
        panel_frame = QFrame()
        panel_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {PANEL_WHITE};
                border-radius: 15px;
                border: 1px solid #E5E7EB;
            }}
        """)
        # For actual drop shadow, we'd use QGraphicsDropShadowEffect, 
        # but styling gives the visual "raised" look.
        
        panel_layout = QVBoxLayout(panel_frame)
        panel_layout.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner_scroll_content = QWidget()
        inner_scroll_content.setStyleSheet("background: transparent;")
        inner_layout = QVBoxLayout(inner_scroll_content)

        # Sections
        tracker_group = QGroupBox("Aurora Tracker")
        tracker_form = QFormLayout(tracker_group)
        self.serial_port = QLineEdit()
        self.baud_rate = QComboBox()
        self.baud_rate.addItems(["9600", "19200", "38400", "57600", "115200", "921600"])
        self.tool_id = QLineEdit()
        self.port_name = QLineEdit()
        tracker_form.addRow("Serial Port", self.serial_port)
        tracker_form.addRow("Baud Rate", self.baud_rate)
        tracker_form.addRow("Tool ID", self.tool_id)
        tracker_form.addRow("Port Name", self.port_name)
        inner_layout.addWidget(tracker_group)

        capture_group = QGroupBox("Capture Device")
        capture_form = QFormLayout(capture_group)
        self.capture_filename = QLineEdit()
        browse_capture = make_btn("Browse", "#64748B", "#475569", 80)
        browse_capture.clicked.connect(lambda: self._browse_save(self.capture_filename))
        row = QHBoxLayout()
        row.addWidget(self.capture_filename)
        row.addWidget(browse_capture)
        row_w = QWidget()
        row_w.setLayout(row)
        capture_form.addRow("Output File", row_w)
        inner_layout.addWidget(capture_group)

        video_group = QGroupBox("Video Device")
        video_form = QFormLayout(video_group)
        self.frame_size = QLineEdit()
        self.acq_rate = QLineEdit()
        self.capture_device_id = QLineEdit()
        self.clip_origin = QLineEdit()
        self.clip_size = QLineEdit()
        video_form.addRow("Frame Size", self.frame_size)
        video_form.addRow("Acquisition Rate", self.acq_rate)
        video_form.addRow("Capture Device ID", self.capture_device_id)
        video_form.addRow("Clip Origin", self.clip_origin)
        video_form.addRow("Clip Size", self.clip_size)
        inner_layout.addWidget(video_group)

        cal_group = QGroupBox("Calibration Matrix")
        cal_layout = QVBoxLayout(cal_group)
        self.matrix_edit = QTextEdit()
        self.matrix_edit.setFixedHeight(90)
        self.matrix_edit.setFont(QFont("Consolas", 10))
        self.matrix_edit.setStyleSheet(f"background: {BG_LIGHT}; border: 1px solid {BORDER_LIGHT}; border-radius: 4px; color: black;")
        cal_layout.addWidget(self.matrix_edit)
        inner_layout.addWidget(cal_group)

        igt_group = QGroupBox("OpenIGTLink Server")
        igt_form = QFormLayout(igt_group)
        self.igt_port = QLineEdit()
        self.igt_transform = QLineEdit()
        igt_form.addRow("Port", self.igt_port)
        igt_form.addRow("Transform", self.igt_transform)
        inner_layout.addWidget(igt_group)

        btn_row = QHBoxLayout()
        apply_btn = make_btn("Apply to XML", ACCENT, ACCENT_HOVER)
        apply_btn.clicked.connect(self._apply_fields)
        reset_btn = make_btn("Reset", "#EF4444", "#DC2626") # Red for reset
        reset_btn.clicked.connect(self._reset)
        btn_row.addWidget(apply_btn)
        btn_row.addWidget(reset_btn)
        inner_layout.addLayout(btn_row)

        scroll.setWidget(inner_scroll_content)
        panel_layout.addWidget(scroll)
        left_layout.addWidget(panel_frame)

        # ── Right: XML ──
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(10, 15, 15, 15)

        self.xml_edit = QTextEdit()
        self.xml_edit.setFont(QFont("Consolas", 10))
        self.xml_edit.setStyleSheet(f"background: {PANEL_WHITE}; color: black; border: 1px solid {BORDER_LIGHT}; border-radius: 8px; padding: 10px;")
        self.highlighter = XmlHighlighter(self.xml_edit.document())
        self.xml_edit.setText(self.xml)
        right_layout.addWidget(self.xml_edit)

        xml_btn_row = QHBoxLayout()
        load_btn = make_btn("Load File", "#64748B", "#475569")
        load_btn.clicked.connect(self._load_file)
        sync_btn = make_btn("Sync from XML", "#64748B", "#475569")
        sync_btn.clicked.connect(self._sync_from_xml)
        save_btn = make_btn("Save File", "#22C55E", "#16A34A") # Green for save
        save_btn.clicked.connect(self._save_file)
        
        xml_btn_row.addWidget(load_btn)
        xml_btn_row.addWidget(sync_btn)
        xml_btn_row.addStretch()
        xml_btn_row.addWidget(save_btn)
        right_layout.addLayout(xml_btn_row)

        splitter.addWidget(left_container)
        splitter.addWidget(right)
        splitter.setSizes([380, 620])

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(splitter)
        self._connect_live_update()

    # (Populate, sync, and logic methods remain exactly the same as your snippet)
    def _populate_fields(self):
        self._block_signals(True)
        xml = self.xml
        self.serial_port.setText(extract_attr(xml, "SerialPort"))
        baud = extract_attr(xml, "BaudRate")
        idx = self.baud_rate.findText(baud)
        if idx >= 0: self.baud_rate.setCurrentIndex(idx)
        self.tool_id.setText(extract_attr(xml, "Id"))
        self.port_name.setText(extract_attr(xml, "PortName"))
        self.capture_filename.setText(extract_attr(xml, "BaseFilename").replace("\\\\", "\\"))
        self.frame_size.setText(extract_attr(xml, "FrameSize"))
        self.acq_rate.setText(extract_attr(xml, "AcquisitionRate"))
        self.capture_device_id.setText(extract_attr(xml, "CaptureDeviceId"))
        self.clip_origin.setText(extract_attr(xml, "ClipRectangleOrigin"))
        self.clip_size.setText(extract_attr(xml, "ClipRectangleSize"))
        self.matrix_edit.blockSignals(True)
        self.matrix_edit.setText(extract_matrix(xml))
        self.matrix_edit.blockSignals(False)
        self.igt_port.setText(extract_attr(xml, "ListeningPort"))
        m = re.search(r'<Transform Name="([^"]*)"', xml)
        self.igt_transform.setText(m.group(1) if m else "")
        self._block_signals(False)

    def _block_signals(self, block):
        for w in [self.serial_port, self.baud_rate, self.tool_id, self.port_name,
                  self.capture_filename, self.frame_size, self.acq_rate,
                  self.capture_device_id, self.clip_origin, self.clip_size,
                  self.igt_port, self.igt_transform]:
            w.blockSignals(block)

    def _connect_live_update(self):
        for w in [self.serial_port, self.tool_id, self.port_name, self.capture_filename,
                  self.frame_size, self.acq_rate, self.capture_device_id,
                  self.clip_origin, self.clip_size, self.igt_port, self.igt_transform]:
            w.textChanged.connect(self._apply_fields)
        self.baud_rate.currentTextChanged.connect(self._apply_fields)
        self.matrix_edit.textChanged.connect(self._apply_fields)

    def _apply_fields(self):
        xml = self.xml_edit.toPlainText()
        xml = replace_attr(xml, "SerialPort", self.serial_port.text())
        xml = replace_attr(xml, "BaudRate", self.baud_rate.currentText())
        xml = replace_attr(xml, "BaseFilename", self.capture_filename.text().replace("\\", "\\\\"))
        xml = replace_attr(xml, "FrameSize", self.frame_size.text())
        xml = replace_attr(xml, "AcquisitionRate", self.acq_rate.text())
        xml = replace_attr(xml, "CaptureDeviceId", self.capture_device_id.text())
        xml = replace_attr(xml, "ClipRectangleOrigin", self.clip_origin.text())
        xml = replace_attr(xml, "ClipRectangleSize", self.clip_size.text())
        xml = replace_attr(xml, "ListeningPort", self.igt_port.text())
        xml = replace_matrix(xml, self.matrix_edit.toPlainText())
        self.xml_edit.blockSignals(True)
        cursor_pos = self.xml_edit.textCursor().position()
        self.xml_edit.setText(xml)
        cursor = self.xml_edit.textCursor()
        cursor.setPosition(min(cursor_pos, len(xml)))
        self.xml_edit.setTextCursor(cursor)
        self.xml_edit.blockSignals(False)

    def _sync_from_xml(self):
        self.xml = self.xml_edit.toPlainText()
        self._populate_fields()

    def _reset(self):
        self.xml = DEFAULT_DEVICE_CONFIG
        self.xml_edit.blockSignals(True)
        self.xml_edit.setText(self.xml)
        self.xml_edit.blockSignals(False)
        self._populate_fields()

    def _load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Config", "", "XML Files (*.xml)")
        if path:
            with open(path, "r") as f:
                self.xml = f.read()
            self.xml_edit.blockSignals(True)
            self.xml_edit.setText(self.xml)
            self.xml_edit.blockSignals(False)
            self._populate_fields()

    def _save_file(self):
        self._apply_fields()
        path, _ = QFileDialog.getSaveFileName(self, "Save Config", "device_config.xml", "XML Files (*.xml)")
        if path:
            with open(path, "w") as f: f.write(self.xml_edit.toPlainText())
            QMessageBox.information(self, "Saved", f"Config saved to:\n{path}")

    def _browse_save(self, line_edit):
        path, _ = QFileDialog.getSaveFileName(self, "Output File", "", "MHA Files (*.mha *.igs.mha)")
        if path: line_edit.setText(path)


class ReconConfigTab(QWidget):
    # This tab replicates the visual logic of DeviceConfigTab
    def __init__(self):
        super().__init__()
        self.xml = DEFAULT_RECON_CONFIG
        self._build_ui()
        self.resize(1200, 800)
        self.setStyleSheet(BASE_STYLE)
        self._populate_fields()

    def _build_ui(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {BORDER_LIGHT}; }}")
        
        # ── Left: Form Fields (Flush Sidebar) ──
        left_container = QWidget()
        # Apply the flush background and right-side rounding directly to the container
        left_container.setStyleSheet(f"""
            QWidget {{
                background-color: {PANEL_WHITE};
                border-top-right-radius: 25px;
                border-bottom-right-radius: 25px;
            }}
        """)
        
        left_layout = QVBoxLayout(left_container)
        # 0 margin on left, top, and bottom to touch the window edges
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # Scroll Area for the form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        # Ensure scroll area doesn't break the background/rounding
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        inner_content = QWidget()
        inner_content.setStyleSheet("background: transparent;")
        inner_layout = QVBoxLayout(inner_content)
        # Add internal padding so the form elements aren't touching the edge
        inner_layout.setContentsMargins(20, 15, 20, 15)
        inner_layout.setSpacing(12)

        # --- FORM ELEMENTS (Unedited) ---
        vr_group = QGroupBox("Volume Reconstruction")
        vr_form = QFormLayout(vr_group)
        self.img_frame = QLineEdit()
        self.ref_frame = QLineEdit()
        self.spacing = QLineEdit()
        self.interp_mode = QComboBox()
        self.interp_mode.addItems(["LINEAR", "NEAREST_NEIGHBOR"])
        self.optimization = QComboBox()
        self.optimization.addItems(["FULL", "HALF", "NONE"])
        self.fill_holes = QComboBox()
        self.fill_holes.addItems(["ON", "OFF"])
        vr_form.addRow("Image Frame", self.img_frame)
        vr_form.addRow("Ref Frame", self.ref_frame)
        vr_form.addRow("Spacing", self.spacing)
        vr_form.addRow("Interpolation", self.interp_mode)
        vr_form.addRow("Optimization", self.optimization)
        vr_form.addRow("Fill Holes", self.fill_holes)
        inner_layout.addWidget(vr_group)

        hf_group = QGroupBox("Hole Filling")
        hf_form = QFormLayout(hf_group)
        self.approx_method = QComboBox()
        self.approx_method.addItems(["DISTANCE_WEIGHT_INVERSE", "GAUSSIAN", "GAUSSIAN_ACCUMULATION", "STICK", "NEAREST_NEIGHBOR"])
        self.extrapolation = QComboBox()
        self.extrapolation.addItems(["FALSE", "TRUE"])
        hf_form.addRow("Method", self.approx_method)
        hf_form.addRow("Extrapolation", self.extrapolation)
        inner_layout.addWidget(hf_group)

        cal_group = QGroupBox("Calibration Matrix")
        cal_layout = QVBoxLayout(cal_group)
        self.matrix_edit = QTextEdit()
        self.matrix_edit.setFixedHeight(90)
        self.matrix_edit.setFont(QFont("Consolas", 10))
        self.matrix_edit.setStyleSheet(f"background: {BG_LIGHT}; color: black; border: 1px solid {BORDER_LIGHT}; border-radius: 4px;")
        cal_layout.addWidget(self.matrix_edit)
        inner_layout.addWidget(cal_group)

        btn_row = QHBoxLayout()
        apply_btn = make_btn("Apply to XML", ACCENT, ACCENT_HOVER)
        apply_btn.clicked.connect(self._apply_fields)
        reset_btn = make_btn("Reset", "#EF4444", "#DC2626")
        reset_btn.clicked.connect(self._reset)
        btn_row.addWidget(apply_btn)
        btn_row.addWidget(reset_btn)
        inner_layout.addLayout(btn_row)
        # --- END FORM ELEMENTS ---

        scroll.setWidget(inner_content)
        left_layout.addWidget(scroll)

        # ── Right: XML ──
        right = QWidget()
        # Set background to transparent so it shows the main window's BG_LIGHT
        right.setStyleSheet("background: transparent;")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(20, 15, 15, 15)
        
        self.xml_edit = QTextEdit()
        self.xml_edit.setFont(QFont("Consolas", 10))
        self.xml_edit.setStyleSheet(f"background: {PANEL_WHITE}; color: black; border: 1px solid {BORDER_LIGHT}; border-radius: 8px; padding: 10px;")
        self.highlighter = XmlHighlighter(self.xml_edit.document())
        self.xml_edit.setText(self.xml)
        right_layout.addWidget(self.xml_edit)

        xml_btn_row = QHBoxLayout()
        load_btn = make_btn("Load File", "#64748B", "#475569")
        load_btn.clicked.connect(self._load_file)
        sync_btn = make_btn("Sync from XML", "#64748B", "#475569")
        sync_btn.clicked.connect(self._sync_from_xml)
        save_btn = make_btn("Save File", "#22C55E", "#16A34A")
        xml_btn_row.addWidget(load_btn)
        xml_btn_row.addWidget(sync_btn)
        xml_btn_row.addStretch()
        xml_btn_row.addWidget(save_btn)
        right_layout.addLayout(xml_btn_row)

        splitter.addWidget(left_container)
        splitter.addWidget(right)
        splitter.setSizes([400, 600])

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(splitter)
        self._connect_live_update()

    def _connect_live_update(self):
        for w in [self.img_frame, self.ref_frame, self.spacing]:
            w.textChanged.connect(self._apply_fields)
        for w in [self.interp_mode, self.optimization, self.fill_holes,
                  self.approx_method, self.extrapolation]:
            w.currentTextChanged.connect(self._apply_fields)
        self.matrix_edit.textChanged.connect(self._apply_fields)

    def _block_signals(self, block):
        for w in [self.img_frame, self.ref_frame, self.spacing,
                  self.interp_mode, self.optimization, self.fill_holes,
                  self.approx_method, self.extrapolation]:
            w.blockSignals(block)

    def _populate_fields(self):
        self._block_signals(True)
        xml = self.xml
        self.img_frame.setText(extract_attr(xml, "ImageCoordinateFrame"))
        self.ref_frame.setText(extract_attr(xml, "ReferenceCoordinateFrame"))
        self.spacing.setText(extract_attr(xml, "OutputSpacing"))
        for field, attr in [(self.interp_mode, "InterpolationMode"), (self.optimization, "Optimization"), (self.fill_holes, "FillHoles"), (self.approx_method, "ApproximationMethod"), (self.extrapolation, "ExtrapolationEnabled")]:
            val = extract_attr(xml, attr)
            idx = field.findText(val)
            if idx >= 0: field.setCurrentIndex(idx)
        self.matrix_edit.blockSignals(True)
        self.matrix_edit.setText(extract_matrix(xml))
        self.matrix_edit.blockSignals(False)
        self._block_signals(False)

    def _apply_fields(self):
        xml = self.xml_edit.toPlainText()
        for attr, field in [("ImageCoordinateFrame", self.img_frame), ("ReferenceCoordinateFrame", self.ref_frame), ("OutputSpacing", self.spacing)]:
            xml = replace_attr(xml, attr, field.text())
        for attr, field in [("InterpolationMode", self.interp_mode), ("Optimization", self.optimization), ("FillHoles", self.fill_holes), ("ApproximationMethod", self.approx_method), ("ExtrapolationEnabled", self.extrapolation)]:
            xml = replace_attr(xml, attr, field.currentText())
        xml = replace_matrix(xml, self.matrix_edit.toPlainText())
        self.xml_edit.blockSignals(True)
        self.xml_edit.setText(xml)
        self.xml_edit.blockSignals(False)

    def _sync_from_xml(self):
        self.xml = self.xml_edit.toPlainText()
        self._populate_fields()

    def _reset(self):
        self.xml = DEFAULT_RECON_CONFIG
        self.xml_edit.setText(self.xml)
        self._populate_fields()

    def _load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load", "", "XML (*.xml)")
        if path:
            with open(path, "r") as f: self.xml = f.read()
            self.xml_edit.setText(self.xml)
            self._populate_fields()

    def _save_file(self):
        self._apply_fields()
        path, _ = QFileDialog.getSaveFileName(self, "Save", "recon_config.xml", "XML (*.xml)")
        if path:
            with open(path, "w") as f: f.write(self.xml_edit.toPlainText())


# ── Main Window ────────────────────────────────────────────────────────────────

class ConfigEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plus Config Editor")
        self.resize(1100, 750)
        self.setStyleSheet(BASE_STYLE)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header bar matching the Navy/White theme
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet(f"background-color: {PANEL_WHITE}; border-bottom: 1px solid {BORDER_LIGHT};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        self.btn_back = QPushButton("←  Back to Menu")
        self.btn_back.setFixedWidth(140)
        self.btn_back.setFixedHeight(36)
        self.btn_back.setStyleSheet(f"""
            QPushButton {{
                background-color: {PANEL_WHITE}; color: {NAVY}; border-radius: 10px; 
                font-weight: bold; border: 1px solid {BORDER_LIGHT};
            }}
            QPushButton:hover {{ background-color: {BG_LIGHT}; }}
        """)
        header_layout.addWidget(self.btn_back)

        title_vbox = QVBoxLayout()
        title = QLabel("PLUS CONFIG EDITOR")
        title.setStyleSheet(f"color: {NAVY}; font-size: 14px; font-weight: 800; letter-spacing: 1px;")
        subtitle = QLabel("Hardware Configuration & Volume Reconstruction")
        subtitle.setStyleSheet(f"color: {MUTED_TEXT}; font-size: 10px; font-weight: 500;")
        title_vbox.addWidget(title)
        # title_vbox.addWidget(subtitle)
        header_layout.addLayout(title_vbox)
        header_layout.addStretch()
        layout.addWidget(header)

        tabs = QTabWidget()
        tabs.addTab(DeviceConfigTab(), "Device Config")
        tabs.addTab(ReconConfigTab(), "Reconstruction Config")
        layout.addWidget(tabs)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ConfigEditorWindow()
    window.show()
    sys.exit(app.exec())