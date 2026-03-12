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

DEFAULT_DEVICE_CONFIG = """\
<PlusConfiguration version="2.1">

  <DataCollection StartupDelaySec="5.0">
    <DeviceSet 
      Name="PlusServer: NDI Aurora tracker"
      Description="Broadcasting tool tracking data through OpenIGTLink"
    />
    <Device
      Id="TrackerDevice" 
      Type="AuroraTracker"
      SerialPort="COM13"
      BaudRate="921600"
      ToolReferenceFrame="Tracker" >
      <DataSources>
        <DataSource Type="Tool" Id="Probe" PortName="0" />
      </DataSources>
      <OutputChannels>
        <OutputChannel Id="TrackerStream">
          <DataSource Id="Probe" />
        </OutputChannel>
      </OutputChannels>
    </Device>
    <Device
      Id="CaptureDevice"
      Type="VirtualCapture"
      BaseFilename="C:\\\\Users\\\\mclac\\\\Desktop\\\\Recordings\\\\three\\\\ElliseArmFri.igs.mha"
      EnableCapturingOnStart="TRUE" >
      <InputChannels>
        <InputChannel Id="CompleteChannel" />
      </InputChannels>
    </Device>
    <Device Id="VideoDevice"
            Type="MmfVideo"
            FrameSize="1920 1080"
            AcquisitionRate="15"
            VideoFormat="YUY2"
            CaptureDeviceId="1">
      <DataSources>
        <DataSource Type="Video" Id="Video" BufferSize="300" PortUsImageOrientation="MN"  
          ClipRectangleOrigin="480 180" ClipRectangleSize="960 700" />
      </DataSources>
      <OutputChannels>
        <OutputChannel Id="VideoChannelCrop" VideoDataSourceId="Video" />
      </OutputChannels>
    </Device>
    <Device Id="TrackedDevice" Type="VirtualMixer">
      <InputChannels>
        <InputChannel Id="TrackerStream"/>
        <InputChannel Id="VideoChannelCrop"/>
      </InputChannels>
      <OutputChannels>
        <OutputChannel Id="CompleteChannel"/>
      </OutputChannels>
    </Device>
  </DataCollection>

  <CoordinateDefinitions>
    <Transform From="Image" To="Probe"
      Matrix="-0.007 0.126 0.008 -107.47
-0.125 -0.008 0.004 75.361
0.004 -0.008 0.126 33.162
0 0 0 1"
      Error="0.0" Date="112317_141120" />
  </CoordinateDefinitions>

  <PlusOpenIGTLinkServer 
    MaxNumberOfIgtlMessagesToSend="1" 
    MaxTimeSpentWithProcessingMs="50" 
    ListeningPort="18944" 
    SendValidTransformsOnly="true" 
    OutputChannelId="CompleteChannel" > 
    <DefaultClientInfo> 
      <MessageTypes> 
        <Message Type="TRANSFORM" />
      </MessageTypes>
      <TransformNames> 
        <Transform Name="ProbeToTracker" />
      </TransformNames>
    </DefaultClientInfo>
  </PlusOpenIGTLinkServer>

</PlusConfiguration>
"""

DEFAULT_RECON_CONFIG = """\
<PlusConfiguration version="2.1">

  <VolumeReconstruction
    ImageCoordinateFrame="Image"
    ReferenceCoordinateFrame="Tracker"
    OutputSpacing="0.5 0.5 0.5"
    InterpolationMode="LINEAR"
    Optimization="FULL"
    FillHoles="ON" >
    <HoleFilling
      ApproximationMethod="DISTANCE_WEIGHT_INVERSE"
      ExtrapolationEnabled="FALSE" />
  </VolumeReconstruction>

  <CoordinateDefinitions>
    <Transform From="Image" To="Probe"
      Matrix="-0.007 0.126 0.008 -107.47
              -0.125 -0.008 0.004 75.361
              0.004 -0.008 0.126 33.162
              0 0 0 1" />
  </CoordinateDefinitions>

</PlusConfiguration>
"""

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

        # Tag names
        self.rules.append((re.compile(r'</?[\w:]+'), fmt("#569cd6", bold=True)))
        # Attribute names
        self.rules.append((re.compile(r'\b[\w:]+(?=\s*=)'), fmt("#9cdcfe")))
        # Attribute values
        self.rules.append((re.compile(r'"[^"]*"'), fmt("#ce9178")))
        # Comments
        self.rules.append((re.compile(r'<!--.*?-->', re.DOTALL), fmt("#6a9955")))
        # Closing brackets
        self.rules.append((re.compile(r'[<>/]'), fmt("#808080")))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for m in pattern.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


# ── Field extractor ────────────────────────────────────────────────────────────

def extract_attr(xml, attr):
    """Pull a single attribute value from XML string."""
    m = re.search(rf'{attr}="([^"]*)"', xml)
    return m.group(1) if m else ""

def replace_attr(xml, attr, value):
    """Replace a single attribute value in XML string."""
    return re.sub(rf'({attr}=")[^"]*(")', rf'\g<1>{value}\g<2>', xml)

def extract_matrix(xml):
    m = re.search(r'Matrix="([^"]*)"', xml, re.DOTALL)
    return m.group(1).strip() if m else ""

def replace_matrix(xml, value):
    return re.sub(r'(Matrix=")[^"]*(")', rf'\g<1>{value}\g<2>', xml, flags=re.DOTALL)


# ── Styled widgets ─────────────────────────────────────────────────────────────

DARK = "#1e1e1e"
PANEL = "#252526"
BORDER = "#3c3c3c"
TEXT = "#d4d4d4"
ACCENT = "#0e7490"
ACCENT_HOVER = "#0891b2"
MUTED = "#6b7280"
ERROR = "#ef5350"
SUCCESS = "#66bb6a"
WARNING = "#ffa726"

BASE_STYLE = f"""
    QMainWindow, QWidget {{ background-color: {PANEL}; color: {TEXT}; }}
    QTabWidget::pane {{ border: 1px solid {BORDER}; background: {PANEL}; }}
    QTabBar::tab {{
        background: {DARK}; color: {MUTED}; padding: 8px 18px;
        border: 1px solid {BORDER}; border-bottom: none; border-radius: 4px 4px 0 0;
        font-family: 'Consolas'; font-size: 11px; letter-spacing: 1px;
    }}
    QTabBar::tab:selected {{ background: {PANEL}; color: {TEXT}; border-bottom: 2px solid {ACCENT}; }}
    QTabBar::tab:hover {{ color: {TEXT}; }}
    QGroupBox {{
        color: {MUTED}; border: 1px solid {BORDER}; border-radius: 6px;
        margin-top: 10px; padding-top: 6px;
        font-family: 'Consolas'; font-size: 10px; letter-spacing: 2px;
        text-transform: uppercase;
    }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 6px; }}
    QLineEdit, QComboBox {{
        background: {DARK}; color: {TEXT}; border: 1px solid {BORDER};
        border-radius: 4px; padding: 5px 8px; font-family: 'Consolas'; font-size: 11px;
    }}
    QLineEdit:focus, QComboBox:focus {{ border-color: {ACCENT}; }}
    QLabel {{ color: {MUTED}; font-family: 'Consolas'; font-size: 10px; letter-spacing: 1px; }}
    QScrollArea {{ border: none; background: {PANEL}; }}
    QScrollBar:vertical {{
        background: {DARK}; width: 8px; border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 4px; min-height: 20px; }}
    QSplitter::handle {{ background: {BORDER}; width: 1px; }}
"""

def make_btn(text, color, hover=None, width=None):
    hover = hover or color
    btn = QPushButton(text)
    btn.setFixedHeight(34)
    if width:
        btn.setFixedWidth(width)
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {color}; color: white; border-radius: 5px;
            font-family: 'Consolas'; font-size: 11px; letter-spacing: 1px;
            border: none; padding: 0 14px;
        }}
        QPushButton:hover {{ background-color: {hover}; }}
        QPushButton:disabled {{ background-color: #333; color: #555; }}
    """)
    return btn


# ── Device Config Tab ──────────────────────────────────────────────────────────

class DeviceConfigTab(QWidget):
    xml_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.xml = DEFAULT_DEVICE_CONFIG
        self._build_ui()
        self._populate_fields()

    def _build_ui(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)

        # ── Left: form fields ──
        left = QWidget()
        left.setMinimumWidth(320)
        left.setMaximumWidth(420)
        scroll = QScrollArea()
        scroll.setWidget(left)
        scroll.setWidgetResizable(True)
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(12)
        left_layout.setContentsMargins(12, 12, 12, 12)

        # Tracker section
        tracker_group = QGroupBox("Aurora Tracker")
        tracker_form = QFormLayout(tracker_group)
        tracker_form.setSpacing(8)
        self.serial_port = QLineEdit()
        self.baud_rate = QComboBox()
        self.baud_rate.addItems(["9600", "19200", "38400", "57600", "115200", "921600"])
        self.tool_id = QLineEdit()
        self.port_name = QLineEdit()
        tracker_form.addRow("Serial Port", self.serial_port)
        tracker_form.addRow("Baud Rate", self.baud_rate)
        tracker_form.addRow("Tool ID", self.tool_id)
        tracker_form.addRow("Port Name", self.port_name)
        left_layout.addWidget(tracker_group)

        # Capture section
        capture_group = QGroupBox("Capture Device")
        capture_form = QFormLayout(capture_group)
        capture_form.setSpacing(8)
        self.capture_filename = QLineEdit()
        browse_capture = make_btn("Browse", "#37474f", "#455a64", 70)
        browse_capture.clicked.connect(lambda: self._browse_save(self.capture_filename))
        row = QHBoxLayout()
        row.addWidget(self.capture_filename)
        row.addWidget(browse_capture)
        row.setContentsMargins(0, 0, 0, 0)
        row_w = QWidget()
        row_w.setLayout(row)
        capture_form.addRow("Output File", row_w)
        left_layout.addWidget(capture_group)

        # Video section
        video_group = QGroupBox("Video Device")
        video_form = QFormLayout(video_group)
        video_form.setSpacing(8)
        self.frame_size = QLineEdit()
        self.acq_rate = QLineEdit()
        self.capture_device_id = QLineEdit()
        self.clip_origin = QLineEdit()
        self.clip_size = QLineEdit()
        video_form.addRow("Frame Size", self.frame_size)
        video_form.addRow("Acquisition Rate", self.acq_rate)
        video_form.addRow("Capture Device ID", self.capture_device_id)
        video_form.addRow("Clip Origin (X Y)", self.clip_origin)
        video_form.addRow("Clip Size (W H)", self.clip_size)
        left_layout.addWidget(video_group)

        # Calibration section
        cal_group = QGroupBox("Calibration Matrix  (Image → Probe)")
        cal_layout = QVBoxLayout(cal_group)
        cal_note = QLabel("4×4 homogeneous transform  |  values in mm")
        cal_note.setStyleSheet(f"color: {MUTED}; font-size: 10px;")
        self.matrix_edit = QTextEdit()
        self.matrix_edit.setFixedHeight(90)
        self.matrix_edit.setFont(QFont("Consolas", 10))
        self.matrix_edit.setStyleSheet(f"""
            QTextEdit {{ background: {DARK}; color: #9cdcfe;
                border: 1px solid {BORDER}; border-radius: 4px; padding: 4px; }}
        """)
        cal_layout.addWidget(cal_note)
        cal_layout.addWidget(self.matrix_edit)
        left_layout.addWidget(cal_group)

        # IGTLink section
        igt_group = QGroupBox("OpenIGTLink Server")
        igt_form = QFormLayout(igt_group)
        igt_form.setSpacing(8)
        self.igt_port = QLineEdit()
        self.igt_transform = QLineEdit()
        igt_form.addRow("Listening Port", self.igt_port)
        igt_form.addRow("Transform Name", self.igt_transform)
        left_layout.addWidget(igt_group)

        # Buttons
        btn_row = QHBoxLayout()
        apply_btn = make_btn("▶  Apply to XML", ACCENT, ACCENT_HOVER)
        apply_btn.clicked.connect(self._apply_fields)
        reset_btn = make_btn("↺  Reset", "#37474f", "#455a64")
        reset_btn.clicked.connect(self._reset)
        btn_row.addWidget(apply_btn)
        btn_row.addWidget(reset_btn)
        left_layout.addLayout(btn_row)
        left_layout.addStretch()

        # ── Right: XML editor ──
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.setSpacing(6)

        xml_label = QLabel("XML PREVIEW  /  DIRECT EDIT")
        xml_label.setStyleSheet(f"color: {MUTED}; font-size: 10px; letter-spacing: 2px;")
        right_layout.addWidget(xml_label)

        self.xml_edit = QTextEdit()
        self.xml_edit.setFont(QFont("Consolas", 10))
        self.xml_edit.setStyleSheet(f"""
            QTextEdit {{ background: {DARK}; color: {TEXT};
                border: 1px solid {BORDER}; border-radius: 4px; padding: 8px; }}
        """)
        self.highlighter = XmlHighlighter(self.xml_edit.document())
        self.xml_edit.setText(self.xml)
        right_layout.addWidget(self.xml_edit)

        xml_btn_row = QHBoxLayout()
        load_btn = make_btn("📂  Load File", "#37474f", "#455a64")
        load_btn.clicked.connect(self._load_file)
        save_btn = make_btn("💾  Save File", "#2e7d32", "#388e3c")
        save_btn.clicked.connect(self._save_file)
        sync_btn = make_btn("↓  Sync Fields from XML", "#37474f", "#455a64")
        sync_btn.clicked.connect(self._sync_from_xml)
        xml_btn_row.addWidget(load_btn)
        xml_btn_row.addWidget(sync_btn)
        xml_btn_row.addStretch()
        xml_btn_row.addWidget(save_btn)
        right_layout.addLayout(xml_btn_row)

        splitter.addWidget(scroll)
        splitter.addWidget(right)
        splitter.setSizes([360, 600])

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(splitter)

        # Connect live update after all widgets are created
        self._connect_live_update()

    def _populate_fields(self):
        # Block signals during population to avoid triggering live update loop
        self._block_signals(True)
        xml = self.xml
        self.serial_port.setText(extract_attr(xml, "SerialPort"))
        baud = extract_attr(xml, "BaudRate")
        idx = self.baud_rate.findText(baud)
        if idx >= 0:
            self.baud_rate.setCurrentIndex(idx)
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
        """Connect all field change signals to live update the XML preview."""
        for w in [self.serial_port, self.tool_id, self.port_name, self.capture_filename,
                  self.frame_size, self.acq_rate, self.capture_device_id,
                  self.clip_origin, self.clip_size, self.igt_port, self.igt_transform]:
            w.textChanged.connect(self._apply_fields)
        self.baud_rate.currentTextChanged.connect(self._apply_fields)
        self.matrix_edit.textChanged.connect(self._apply_fields)

    def _apply_fields(self):
        # Use the current xml_edit content as base — preserves any custom tags/edits the user has made
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
        # Block xml_edit signals to avoid recursive updates
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
        # Always apply current field values before saving
        self._apply_fields()
        path, _ = QFileDialog.getSaveFileName(self, "Save Config", "device_config.xml", "XML Files (*.xml)")
        if path:
            with open(path, "w") as f:
                f.write(self.xml_edit.toPlainText())
            QMessageBox.information(self, "Saved", f"Config saved to:\n{path}")

    def _browse_save(self, line_edit):
        path, _ = QFileDialog.getSaveFileName(self, "Output File", "", "MHA Files (*.mha *.igs.mha)")
        if path:
            line_edit.setText(path)


# ── Reconstruction Config Tab ──────────────────────────────────────────────────

class ReconConfigTab(QWidget):
    def __init__(self):
        super().__init__()
        self.xml = DEFAULT_RECON_CONFIG
        self._build_ui()
        self._populate_fields()

    def _build_ui(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)

        # ── Left: form fields ──
        left = QWidget()
        left.setMinimumWidth(320)
        left.setMaximumWidth(420)
        scroll = QScrollArea()
        scroll.setWidget(left)
        scroll.setWidgetResizable(True)
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(12)
        left_layout.setContentsMargins(12, 12, 12, 12)

        # Volume reconstruction section
        vr_group = QGroupBox("Volume Reconstruction")
        vr_form = QFormLayout(vr_group)
        vr_form.setSpacing(8)

        self.img_frame = QLineEdit()
        self.ref_frame = QLineEdit()
        self.spacing = QLineEdit()
        self.spacing.setPlaceholderText("e.g. 0.5 0.5 0.5")

        self.interp_mode = QComboBox()
        self.interp_mode.addItems(["LINEAR", "NEAREST_NEIGHBOR"])

        self.optimization = QComboBox()
        self.optimization.addItems(["FULL", "HALF", "NONE"])

        self.fill_holes = QComboBox()
        self.fill_holes.addItems(["ON", "OFF"])

        vr_form.addRow("Image Frame", self.img_frame)
        vr_form.addRow("Reference Frame", self.ref_frame)
        vr_form.addRow("Output Spacing (mm)", self.spacing)
        vr_form.addRow("Interpolation Mode", self.interp_mode)
        vr_form.addRow("Optimization", self.optimization)
        vr_form.addRow("Fill Holes", self.fill_holes)

        # Spacing helper
        spacing_note = QLabel("↑  smaller = finer detail, larger file  |  min ~0.2mm")
        spacing_note.setStyleSheet(f"color: {MUTED}; font-size: 10px; font-style: italic;")
        vr_form.addRow("", spacing_note)

        left_layout.addWidget(vr_group)

        # Hole filling section
        hf_group = QGroupBox("Hole Filling")
        hf_form = QFormLayout(hf_group)
        hf_form.setSpacing(8)
        self.approx_method = QComboBox()
        self.approx_method.addItems([
            "DISTANCE_WEIGHT_INVERSE",
            "GAUSSIAN",
            "GAUSSIAN_ACCUMULATION",
            "STICK",
            "NEAREST_NEIGHBOR"
        ])
        self.extrapolation = QComboBox()
        self.extrapolation.addItems(["FALSE", "TRUE"])
        hf_form.addRow("Approximation Method", self.approx_method)
        hf_form.addRow("Extrapolation Enabled", self.extrapolation)
        left_layout.addWidget(hf_group)

        # Calibration matrix
        cal_group = QGroupBox("Calibration Matrix  (Image → Probe)")
        cal_layout = QVBoxLayout(cal_group)
        cal_note = QLabel("4×4 homogeneous transform  |  values in mm")
        cal_note.setStyleSheet(f"color: {MUTED}; font-size: 10px;")
        self.matrix_edit = QTextEdit()
        self.matrix_edit.setFixedHeight(90)
        self.matrix_edit.setFont(QFont("Consolas", 10))
        self.matrix_edit.setStyleSheet(f"""
            QTextEdit {{ background: {DARK}; color: #9cdcfe;
                border: 1px solid {BORDER}; border-radius: 4px; padding: 4px; }}
        """)
        cal_layout.addWidget(cal_note)
        cal_layout.addWidget(self.matrix_edit)
        left_layout.addWidget(cal_group)

        # Buttons
        btn_row = QHBoxLayout()
        apply_btn = make_btn("▶  Apply to XML", ACCENT, ACCENT_HOVER)
        apply_btn.clicked.connect(self._apply_fields)
        reset_btn = make_btn("↺  Reset", "#37474f", "#455a64")
        reset_btn.clicked.connect(self._reset)
        btn_row.addWidget(apply_btn)
        btn_row.addWidget(reset_btn)
        left_layout.addLayout(btn_row)
        left_layout.addStretch()

        # ── Right: XML editor ──
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.setSpacing(6)

        xml_label = QLabel("XML PREVIEW  /  DIRECT EDIT")
        xml_label.setStyleSheet(f"color: {MUTED}; font-size: 10px; letter-spacing: 2px;")
        right_layout.addWidget(xml_label)

        self.xml_edit = QTextEdit()
        self.xml_edit.setFont(QFont("Consolas", 10))
        self.xml_edit.setStyleSheet(f"""
            QTextEdit {{ background: {DARK}; color: {TEXT};
                border: 1px solid {BORDER}; border-radius: 4px; padding: 8px; }}
        """)
        self.highlighter = XmlHighlighter(self.xml_edit.document())
        self.xml_edit.setText(self.xml)
        right_layout.addWidget(self.xml_edit)

        xml_btn_row = QHBoxLayout()
        load_btn = make_btn("📂  Load File", "#37474f", "#455a64")
        load_btn.clicked.connect(self._load_file)
        save_btn = make_btn("💾  Save File", "#2e7d32", "#388e3c")
        save_btn.clicked.connect(self._save_file)
        sync_btn = make_btn("↓  Sync Fields from XML", "#37474f", "#455a64")
        sync_btn.clicked.connect(self._sync_from_xml)
        xml_btn_row.addWidget(load_btn)
        xml_btn_row.addWidget(sync_btn)
        xml_btn_row.addStretch()
        xml_btn_row.addWidget(save_btn)
        right_layout.addLayout(xml_btn_row)

        splitter.addWidget(scroll)
        splitter.addWidget(right)
        splitter.setSizes([360, 600])

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(splitter)

        # Connect live update after all widgets are created
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

        interp = extract_attr(xml, "InterpolationMode")
        idx = self.interp_mode.findText(interp)
        if idx >= 0: self.interp_mode.setCurrentIndex(idx)

        opt = extract_attr(xml, "Optimization")
        idx = self.optimization.findText(opt)
        if idx >= 0: self.optimization.setCurrentIndex(idx)

        fh = extract_attr(xml, "FillHoles")
        idx = self.fill_holes.findText(fh)
        if idx >= 0: self.fill_holes.setCurrentIndex(idx)

        am = extract_attr(xml, "ApproximationMethod")
        idx = self.approx_method.findText(am)
        if idx >= 0: self.approx_method.setCurrentIndex(idx)

        ex = extract_attr(xml, "ExtrapolationEnabled")
        idx = self.extrapolation.findText(ex)
        if idx >= 0: self.extrapolation.setCurrentIndex(idx)

        self.matrix_edit.blockSignals(True)
        self.matrix_edit.setText(extract_matrix(xml))
        self.matrix_edit.blockSignals(False)
        self._block_signals(False)

    def _apply_fields(self):
        # Use the current xml_edit content as base — preserves any custom tags/edits the user has made
        xml = self.xml_edit.toPlainText()
        xml = replace_attr(xml, "ImageCoordinateFrame", self.img_frame.text())
        xml = replace_attr(xml, "ReferenceCoordinateFrame", self.ref_frame.text())
        xml = replace_attr(xml, "OutputSpacing", self.spacing.text())
        xml = replace_attr(xml, "InterpolationMode", self.interp_mode.currentText())
        xml = replace_attr(xml, "Optimization", self.optimization.currentText())
        xml = replace_attr(xml, "FillHoles", self.fill_holes.currentText())
        xml = replace_attr(xml, "ApproximationMethod", self.approx_method.currentText())
        xml = replace_attr(xml, "ExtrapolationEnabled", self.extrapolation.currentText())
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
        self.xml = DEFAULT_RECON_CONFIG
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
        # Always apply current field values before saving
        self._apply_fields()
        path, _ = QFileDialog.getSaveFileName(self, "Save Config", "reconstruction_config.xml", "XML Files (*.xml)")
        if path:
            with open(path, "w") as f:
                f.write(self.xml_edit.toPlainText())
            QMessageBox.information(self, "Saved", f"Config saved to:\n{path}")


# ── Main Window ────────────────────────────────────────────────────────────────

class ConfigEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plus Config Editor")
        self.resize(1000, 680)
        self.setStyleSheet(BASE_STYLE)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar
        header = QWidget()
        header.setFixedHeight(48)
        header.setStyleSheet(f"background-color: {DARK}; border-bottom: 1px solid {BORDER};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)

        self.btn_back = QPushButton("←")
        self.btn_back.setFixedSize(30, 30)
        self.btn_back.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; color: {TEXT};
                font-size: 18px; border: none; font-weight: bold;
            }}
            QPushButton:hover {{ color: {ACCENT}; }}
        """)
        header_layout.addWidget(self.btn_back)

        title = QLabel("PLUS  CONFIG  EDITOR")
        title.setStyleSheet(f"""
            color: {TEXT}; font-family: 'Consolas';
            font-size: 13px; font-weight: bold; letter-spacing: 3px;
        """)
        subtitle = QLabel("device setup  ·  volume reconstruction")
        subtitle.setStyleSheet(f"color: {MUTED}; font-family: 'Consolas'; font-size: 10px; letter-spacing: 1px;")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_layout.addStretch()
        layout.addWidget(header)

        # Tabs
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.addTab(DeviceConfigTab(), "  DEVICE CONFIG  ")
        tabs.addTab(ReconConfigTab(), "  RECONSTRUCTION CONFIG  ")
        layout.addWidget(tabs)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ConfigEditorWindow()
    window.show()
    sys.exit(app.exec())