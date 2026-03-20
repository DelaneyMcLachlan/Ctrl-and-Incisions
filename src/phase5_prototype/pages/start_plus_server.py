import subprocess
import threading
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QTextEdit,
    QLineEdit, QFileDialog, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor

# ── Theme Colors ──────────────────────────────────────────────────────────────
BG_LIGHT     = "#F0F2F5"
PANEL_WHITE  = "#FFFFFF"
NAVY         = "#132B50"
ACCENT       = "#3A66B7"
ACCENT_HOVER = "#4A7DE0"
BORDER_LIGHT = "#D1D5DB"
MUTED_TEXT   = "#64748B"
ERROR_RED    = "#EF4444"
SUCCESS_GREEN= "#22C55E"

DEFAULT_EXE    = r"C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin\PlusServer.exe"
DEFAULT_CONFIG = r"C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\config\PlusDeviceSet_Server_NDIAurora.xml"


class LogEmitter(QObject):
    """Signals must live in a QObject — lets background threads post to the UI safely."""
    new_line = pyqtSignal(str)


class PlusServerLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.process = None
        self.emitter = LogEmitter()
        self.emitter.new_line.connect(self.append_log)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Sequence Recorder")
        self.resize(800, 650)
        self.setStyleSheet(f"QMainWindow {{ background-color: {BG_LIGHT}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # ── Navigation ────────────────────────────────────────────────────────
        nav_bar = QHBoxLayout()
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
        nav_bar.addWidget(self.btn_back)
        nav_bar.addStretch()
        layout.addLayout(nav_bar)

        # ── Configuration Group ───────────────────────────────────────────────
        file_group = QGroupBox("Configuration and System Overview")
        file_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {PANEL_WHITE};
                color: {NAVY}; border: 1px solid {BORDER_LIGHT}; border-radius: 12px;
                margin-top: 5px; padding-top: 0px; font-weight: bold; font-size: 12px;
            }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 15px; padding: 0 5px; }}
        """)
        
        file_layout = QFormLayout(file_group)
        file_layout.setSpacing(12)
        file_layout.setContentsMargins(15, 20, 15, 15)

        # ── New Educational Text ──
        description_text = QLabel(
            "The Sequence Recorder initializes a background process that executes a Bash-style "
            "command to launch the PlusServer executable. This server manages the data stream "
            "and records the sequence to your local disk.\n\n"
            "IMPORTANT: The Config File must be customized to match your specific hardware "
            "setup (e.g., Tracker type, COM ports, and Calibration matrices) to ensure "
            "accurate data capture."
        )
        description_text.setWordWrap(True)
        description_text.setStyleSheet(f"""
            color: {MUTED_TEXT}; 
            font-size: 11px; 
            font-weight: 400; 
            line-height: 14px; 
            padding-bottom: 10px;
            border-bottom: 1px solid {BG_LIGHT};
        """)
        # Add the description at the very top of the form
        file_layout.addRow(description_text)

        input_style = f"""
            QLineEdit {{
                background: {BG_LIGHT}; color: {NAVY}; border: 1px solid {BORDER_LIGHT};
                border-radius: 6px; padding: 6px 10px; font-family: 'Segoe UI'; font-size: 12px;
            }}
            QLineEdit:focus {{ border-color: {ACCENT}; }}
        """
        browse_style = f"""
            QPushButton {{
                background-color: {MUTED_TEXT}; color: white; border-radius: 6px;
                font-size: 11px; font-weight: bold; padding: 6px 12px; border: none;
            }}
            QPushButton:hover {{ background-color: #475569; }}
        """
        label_style = f"color: {NAVY}; font-weight: 600; font-size: 11px; background: transparent; border: none;"

        # PlusServer.exe row
        self.exe_input = QLineEdit(DEFAULT_EXE)
        self.exe_input.setStyleSheet(input_style)
        exe_browse = QPushButton("Browse")
        exe_browse.setFixedWidth(80)
        exe_browse.setStyleSheet(browse_style)
        exe_browse.clicked.connect(self._browse_exe)
        
        exe_row = QHBoxLayout()
        exe_row.addWidget(self.exe_input)
        exe_row.addWidget(exe_browse)
        exe_row_w = QWidget()
        exe_row_w.setLayout(exe_row)
        exe_row_w.setStyleSheet("background: transparent; border: none;")

        exe_label = QLabel("PlusServer.exe")
        exe_label.setStyleSheet(label_style)
        file_layout.addRow(exe_label, exe_row_w)

        # Config XML row
        self.config_input = QLineEdit(DEFAULT_CONFIG)
        self.config_input.setStyleSheet(input_style)
        cfg_browse = QPushButton("Browse")
        cfg_browse.setFixedWidth(80)
        cfg_browse.setStyleSheet(browse_style)
        cfg_browse.clicked.connect(self._browse_config)

        cfg_row = QHBoxLayout()
        cfg_row.addWidget(self.config_input)
        cfg_row.addWidget(cfg_browse)
        cfg_row_w = QWidget()
        cfg_row_w.setLayout(cfg_row)
        cfg_row_w.setStyleSheet("background: transparent; border: none;")

        cfg_label = QLabel("Config File")
        cfg_label.setStyleSheet(label_style)
        file_layout.addRow(cfg_label, cfg_row_w)

        layout.addWidget(file_group)

        # ── Status label ─────────────────────────────────────────────────────
        self.status_label = QLabel("PlusServer not running")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(f"color: {ERROR_RED}; font-weight: 800; font-size: 14px; background: transparent;")
        layout.addWidget(self.status_label)

        # ── Buttons ──────────────────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.start_btn = QPushButton("Start Recording")
        self.start_btn.setFixedHeight(40)
        self.start_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {ACCENT}; color: white; border-radius: 8px; font-weight: bold; font-size: 13px; border: none; }}
            QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}
            QPushButton:disabled {{ background-color: {BORDER_LIGHT}; color: {MUTED_TEXT}; }}
        """)
        self.start_btn.clicked.connect(self.start_server)

        self.stop_btn = QPushButton("Stop Recording")
        self.stop_btn.setFixedHeight(40)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {ERROR_RED}; color: white; border-radius: 8px; font-weight: bold; font-size: 13px; border: none; }}
            QPushButton:hover {{ background-color: #DC2626; }}
            QPushButton:disabled {{ background-color: {BORDER_LIGHT}; color: {MUTED_TEXT}; }}
        """)
        self.stop_btn.clicked.connect(self.stop_server)

        self.clear_btn = QPushButton("Clear Log")
        self.clear_btn.setFixedHeight(40)
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {PANEL_WHITE}; color: {NAVY}; border-radius: 8px; font-weight: bold; border: 1px solid {BORDER_LIGHT}; }}
            QPushButton:hover {{ background-color: {BG_LIGHT}; }}
        """)
        self.clear_btn.clicked.connect(self.clear_log)

        btn_layout.addWidget(self.start_btn, 2)
        btn_layout.addWidget(self.stop_btn, 2)
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.clear_btn, 1)
        layout.addLayout(btn_layout)

        # ── Log terminal ─────────────────────────────────────────────────────
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFont(QFont("Consolas", 10))
        self.log_box.setStyleSheet(f"""
            QTextEdit {{
                background-color: {PANEL_WHITE}; color: {NAVY};
                border: 1px solid {BORDER_LIGHT}; border-radius: 12px; padding: 12px;
            }}
        """)
        layout.addWidget(self.log_box)

    # ── File browse helpers ───────────────────────────────────────────────────

    def _browse_exe(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select PlusServer.exe", "", "Executable (*.exe)")
        if path: self.exe_input.setText(path)

    def _browse_config(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select PlusServer Config", "", "XML Files (*.xml)")
        if path: self.config_input.setText(path)

    # ── Server control ────────────────────────────────────────────────────────

    def start_server(self):
        exe    = self.exe_input.text().strip()
        config = self.config_input.text().strip()

        if not exe or not config:
            self.status_label.setText("Set paths before starting")
            self.status_label.setStyleSheet(f"color: {ACCENT}; font-weight: 800; font-size: 14px;")
            return

        if self.process is None:
            self.process = subprocess.Popen(
                [exe, f"--config-file={config}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.status_label.setText("PlusServer running")
            self.status_label.setStyleSheet(f"color: {SUCCESS_GREEN}; font-weight: 800; font-size: 14px;")
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.append_log(f"--- PlusServer started ---\nEXE:    {exe}\nCONFIG: {config}\n\n")

            for stream in [self.process.stdout, self.process.stderr]:
                thread = threading.Thread(target=self.read_stream, args=(stream,), daemon=True)
                thread.start()

    def stop_server(self):
        if self.process:
            self.process.terminate()
            self.process = None
            self.status_label.setText("PlusServer stopped")
            self.status_label.setStyleSheet(f"color: {ERROR_RED}; font-weight: 800; font-size: 14px;")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.append_log("\n--- PlusServer stopped ---\n")

    def read_stream(self, stream):
        for line in iter(stream.readline, b''):
            self.emitter.new_line.emit(line.decode('utf-8', errors='replace'))

    def append_log(self, text):
        if "|ERROR|" in text:
            self.log_box.setTextColor(QColor(ERROR_RED))
        elif "|WARNING|" in text:
            self.log_box.setTextColor(QColor("#B45309")) # Amber/Orange
        elif "---" in text:
            self.log_box.setTextColor(QColor(ACCENT))
        else:
            self.log_box.setTextColor(QColor(NAVY))

        self.log_box.insertPlainText(text)
        self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())

    def clear_log(self):
        self.log_box.clear()

    def closeEvent(self, event):
        self.stop_server()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = PlusServerLauncher()
    window.show()
    sys.exit(app.exec())