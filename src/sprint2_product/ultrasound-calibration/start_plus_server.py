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
        self.setWindowTitle("PlusServer Launcher")
        self.resize(800, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        # ── File path group ──────────────────────────────────────────────────
        file_group = QGroupBox("Configuration")
        file_group.setStyleSheet("""
            QGroupBox {
                color: #888; border: 1px solid #3c3c3c; border-radius: 5px;
                margin-top: 8px; font-family: Consolas; font-size: 10px;
                letter-spacing: 1px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
        """)
        file_layout = QFormLayout(file_group)
        file_layout.setSpacing(6)
        file_layout.setContentsMargins(10, 14, 10, 10)

        input_style = """
            QLineEdit {
                background: #1e1e1e; color: #d4d4d4; border: 1px solid #3c3c3c;
                border-radius: 4px; padding: 4px 8px;
                font-family: Consolas; font-size: 11px;
            }
            QLineEdit:focus { border-color: #0e7490; }
        """
        browse_style = """
            QPushButton {
                background-color: #37474f; color: white; border-radius: 4px;
                font-size: 11px; padding: 4px 10px;
            }
            QPushButton:hover { background-color: #455a64; }
        """
        label_style = "color: #888; font-family: Consolas; font-size: 10px; letter-spacing: 1px;"

        # PlusServer.exe row
        exe_row = QWidget()
        exe_layout = QHBoxLayout(exe_row)
        exe_layout.setContentsMargins(0, 0, 0, 0)
        exe_layout.setSpacing(6)
        self.exe_input = QLineEdit(DEFAULT_EXE)
        self.exe_input.setStyleSheet(input_style)
        exe_browse = QPushButton("Browse")
        exe_browse.setFixedWidth(70)
        exe_browse.setStyleSheet(browse_style)
        exe_browse.clicked.connect(self._browse_exe)
        exe_layout.addWidget(self.exe_input)
        exe_layout.addWidget(exe_browse)
        exe_label = QLabel("PlusServer.exe")
        exe_label.setStyleSheet(label_style)
        file_layout.addRow(exe_label, exe_row)

        # Config XML row
        cfg_row = QWidget()
        cfg_layout = QHBoxLayout(cfg_row)
        cfg_layout.setContentsMargins(0, 0, 0, 0)
        cfg_layout.setSpacing(6)
        self.config_input = QLineEdit(DEFAULT_CONFIG)
        self.config_input.setStyleSheet(input_style)
        cfg_browse = QPushButton("Browse")
        cfg_browse.setFixedWidth(70)
        cfg_browse.setStyleSheet(browse_style)
        cfg_browse.clicked.connect(self._browse_config)
        cfg_layout.addWidget(self.config_input)
        cfg_layout.addWidget(cfg_browse)
        cfg_label = QLabel("Config File")
        cfg_label.setStyleSheet(label_style)
        file_layout.addRow(cfg_label, cfg_row)

        layout.addWidget(file_group)

        # ── Status label ─────────────────────────────────────────────────────
        self.status_label = QLabel("PlusServer not running.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #e05555; font-weight: bold; font-size: 13px;")
        layout.addWidget(self.status_label)

        # ── Buttons ──────────────────────────────────────────────────────────
        btn_layout = QHBoxLayout()

        self.start_btn = QPushButton("▶  Start PlusServer")
        self.start_btn.setFixedHeight(36)
        self.start_btn.setStyleSheet("""
            QPushButton { background-color: #2e7d32; color: white; border-radius: 5px; font-size: 13px; }
            QPushButton:hover { background-color: #388e3c; }
            QPushButton:disabled { background-color: #555; color: #999; }
        """)
        self.start_btn.clicked.connect(self.start_server)

        self.stop_btn = QPushButton("■  Stop PlusServer")
        self.stop_btn.setFixedHeight(36)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton { background-color: #c62828; color: white; border-radius: 5px; font-size: 13px; }
            QPushButton:hover { background-color: #d32f2f; }
            QPushButton:disabled { background-color: #555; color: #999; }
        """)
        self.stop_btn.clicked.connect(self.stop_server)

        self.clear_btn = QPushButton("🗑  Clear Log")
        self.clear_btn.setFixedHeight(36)
        self.clear_btn.setStyleSheet("""
            QPushButton { background-color: #37474f; color: white; border-radius: 5px; font-size: 13px; }
            QPushButton:hover { background-color: #455a64; }
        """)
        self.clear_btn.clicked.connect(self.clear_log)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.clear_btn)
        layout.addLayout(btn_layout)

        # ── Log terminal ─────────────────────────────────────────────────────
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFont(QFont("Courier New", 9))
        self.log_box.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e; color: #d4d4d4;
                border: 1px solid #444; border-radius: 4px; padding: 6px;
            }
        """)
        layout.addWidget(self.log_box)

        self.setStyleSheet("QMainWindow { background-color: #2b2b2b; } QWidget { background-color: #2b2b2b; }")

    # ── File browse helpers ───────────────────────────────────────────────────

    def _browse_exe(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select PlusServer.exe", "", "Executable (*.exe)"
        )
        if path:
            self.exe_input.setText(path)

    def _browse_config(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select PlusServer Config", "", "XML Files (*.xml)"
        )
        if path:
            self.config_input.setText(path)

    # ── Server control ────────────────────────────────────────────────────────

    def start_server(self):
        exe    = self.exe_input.text().strip()
        config = self.config_input.text().strip()

        if not exe or not config:
            self.status_label.setText("Please set both paths before starting.")
            self.status_label.setStyleSheet("color: #ffa726; font-weight: bold; font-size: 13px;")
            return

        if self.process is None:
            self.process = subprocess.Popen(
                [exe, f"--config-file={config}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.status_label.setText("PlusServer running...")
            self.status_label.setStyleSheet("color: #66bb6a; font-weight: bold; font-size: 13px;")
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
            self.status_label.setText("PlusServer stopped.")
            self.status_label.setStyleSheet("color: #e05555; font-weight: bold; font-size: 13px;")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.append_log("--- PlusServer stopped ---\n")

    def read_stream(self, stream):
        for line in iter(stream.readline, b''):
            self.emitter.new_line.emit(line.decode('utf-8', errors='replace'))

    def append_log(self, text):
        if "|ERROR|" in text:
            self.log_box.setTextColor(QColor("#ef5350"))
        elif "|WARNING|" in text:
            self.log_box.setTextColor(QColor("#ffa726"))
        elif "---" in text:
            self.log_box.setTextColor(QColor("#64b5f6"))
        else:
            self.log_box.setTextColor(QColor("#d4d4d4"))

        self.log_box.insertPlainText(text)
        self.log_box.verticalScrollBar().setValue(
            self.log_box.verticalScrollBar().maximum()
        )

    def clear_log(self):
        self.log_box.clear()

    def closeEvent(self, event):
        self.stop_server()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PlusServerLauncher()
    window.show()
    sys.exit(app.exec())