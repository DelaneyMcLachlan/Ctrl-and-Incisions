import subprocess
import threading
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QTextEdit, QLineEdit,
    QFileDialog, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor

VOLUME_RECONSTRUCTOR_EXE = r"C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin\VolumeReconstructor.exe"

class LogEmitter(QObject):
    new_line = pyqtSignal(str)


class VolumeReconstructorUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.process = None
        self.emitter = LogEmitter()
        self.emitter.new_line.connect(self.append_log)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Volume Reconstructor")
        self.resize(800, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        nav_bar = QHBoxLayout()
        self.btn_back = QPushButton("← Back to Menu")
        self.btn_back.setFixedWidth(120)
        self.btn_back.setStyleSheet("background-color: #333; color: white; border-radius: 4px; padding: 5px; margin: 5px;")
        nav_bar.addWidget(self.btn_back)
        nav_bar.addStretch()
        layout.addLayout(nav_bar)

        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        # --- File paths group ---
        file_group = QGroupBox("File Paths")
        file_group.setStyleSheet("""
            QGroupBox {
                color: #d4d4d4;
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 8px;
                font-size: 12px;
                font-weight: bold;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
        """)
        file_layout = QVBoxLayout(file_group)
        file_layout.setSpacing(8)

        # Config file
        self.config_input = self._make_file_row(
            file_layout,
            "Config File (.xml):",
            "Select reconstruction config XML",
            "XML Files (*.xml)"
        )
        self.config_input.setText(
            r"C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin\reconstruction_config.xml"
        )

        # Source sequence file
        self.source_input = self._make_file_row(
            file_layout,
            "Source Sequence (.igs.mha):",
            "Select recorded sequence file",
            "MHA Files (*.mha *.igs.mha)"
        )

        # Output volume file
        self.output_input = self._make_file_row(
            file_layout,
            "Output Volume (.mha):",
            "Save output volume as",
            "MHA Files (*.mha)",
            save=True
        )
        self.output_input.setText(r"C:\Users\mclac\Desktop\outputfile.mha")

        layout.addWidget(file_group)

        # --- Run button ---
        btn_layout = QHBoxLayout()

        self.run_btn = QPushButton("▶  Run Reconstruction")
        self.run_btn.setFixedHeight(38)
        self.run_btn.setStyleSheet("""
            QPushButton { background-color: #2e7d32; color: white; border-radius: 5px; font-size: 13px; }
            QPushButton:hover { background-color: #388e3c; }
            QPushButton:disabled { background-color: #555; color: #999; }
        """)
        self.run_btn.clicked.connect(self.run_reconstruction)

        self.clear_btn = QPushButton("🗑  Clear Log")
        self.clear_btn.setFixedHeight(38)
        self.clear_btn.setStyleSheet("""
            QPushButton { background-color: #37474f; color: white; border-radius: 5px; font-size: 13px; }
            QPushButton:hover { background-color: #455a64; }
        """)
        self.clear_btn.clicked.connect(self.clear_log)

        btn_layout.addWidget(self.run_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.clear_btn)
        layout.addLayout(btn_layout)

        # --- Status label ---
        self.status_label = QLabel("Ready.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #d4d4d4; font-size: 12px;")
        layout.addWidget(self.status_label)

        # --- Log terminal ---
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFont(QFont("Courier New", 9))
        self.log_box.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        layout.addWidget(self.log_box)

        self.setStyleSheet("QMainWindow { background-color: #2b2b2b; } QWidget { background-color: #2b2b2b; }")

    def _make_file_row(self, parent_layout, label_text, dialog_title, file_filter, save=False):
        """Helper to create a label + text input + browse button row."""
        row_widget = QWidget()
        row = QHBoxLayout(row_widget)
        row.setContentsMargins(0, 0, 0, 0)

        label = QLabel(label_text)
        label.setFixedWidth(200)
        label.setStyleSheet("color: #d4d4d4; font-size: 11px;")

        line_edit = QLineEdit()
        line_edit.setStyleSheet("""
            QLineEdit {
                background-color: #3c3c3c;
                color: #d4d4d4;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px;
            }
        """)

        browse_btn = QPushButton("Browse")
        browse_btn.setFixedWidth(70)
        browse_btn.setStyleSheet("""
            QPushButton { background-color: #455a64; color: white; border-radius: 4px; }
            QPushButton:hover { background-color: #546e7a; }
        """)

        if save:
            browse_btn.clicked.connect(
                lambda: self._browse_save(line_edit, dialog_title, file_filter)
            )
        else:
            browse_btn.clicked.connect(
                lambda: self._browse_open(line_edit, dialog_title, file_filter)
            )

        row.addWidget(label)
        row.addWidget(line_edit)
        row.addWidget(browse_btn)
        parent_layout.addWidget(row_widget)
        return line_edit

    def _browse_open(self, line_edit, title, file_filter):
        path, _ = QFileDialog.getOpenFileName(self, title, "", file_filter)
        if path:
            line_edit.setText(path)

    def _browse_save(self, line_edit, title, file_filter):
        path, _ = QFileDialog.getSaveFileName(self, title, "", file_filter)
        if path:
            line_edit.setText(path)

    def run_reconstruction(self):
        config = self.config_input.text().strip()
        source = self.source_input.text().strip()
        output = self.output_input.text().strip()

        if not config or not source or not output:
            self.status_label.setText("Please fill in all file paths.")
            self.status_label.setStyleSheet("color: #ffa726; font-size: 12px;")
            return

        self.run_btn.setEnabled(False)
        self.status_label.setText("Reconstructing...")
        self.status_label.setStyleSheet("color: #66bb6a; font-size: 12px;")
        self.append_log("--- Starting Volume Reconstruction ---\n")

        cmd = [
            VOLUME_RECONSTRUCTOR_EXE,
            f"--config-file={config}",
            f"--source-seq-file={source}",
            f"--output-volume-file={output}"
        ]

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        for stream in [self.process.stdout, self.process.stderr]:
            thread = threading.Thread(target=self.read_stream, args=(stream,), daemon=True)
            thread.start()

        # Watch for completion in background
        thread = threading.Thread(target=self.watch_completion, daemon=True)
        thread.start()

    def watch_completion(self):
        self.process.wait()
        returncode = self.process.returncode
        if returncode == 0:
            self.emitter.new_line.emit("--- Reconstruction complete! ---\n")
            self.status_label.setText("Done! Volume saved.")
            self.status_label.setStyleSheet("color: #66bb6a; font-size: 12px;")
        else:
            self.emitter.new_line.emit(f"--- Reconstruction failed (exit code {returncode}) ---\n")
            self.status_label.setText(f"Failed. Exit code: {returncode}")
            self.status_label.setStyleSheet("color: #ef5350; font-size: 12px;")
        self.run_btn.setEnabled(True)

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VolumeReconstructorUI()
    window.show()
    sys.exit(app.exec())