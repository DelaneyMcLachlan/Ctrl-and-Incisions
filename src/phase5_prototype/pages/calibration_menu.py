import sys
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox

from pages.calibration_navigation_page import CalibrationNavigationPage


class CalibrationMenuPage(QWidget):

    def __init__(self, go_back=None, go_to_results=None):

        super().__init__()

        self.go_back = go_back
        self.go_to_results = go_to_results

        self.main_layout = QVBoxLayout(self)

        self.nav_page = CalibrationNavigationPage()
        self.main_layout.addWidget(self.nav_page)

        self.nav_page.btn_back.clicked.connect(self.handle_back)
        self.nav_page.btn_calibrate.clicked.connect(self.launch_hand_eye_calibration)
        self.nav_page.btn_results.clicked.connect(self.open_results_page)

    def handle_back(self):
        if self.go_back:
            self.go_back()

    def launch_hand_eye_calibration(self):

        try:

            src_dir = Path(__file__).resolve().parents[2]

            script_path = src_dir / "sprint2_prototype" / "hand-eye-calibration" / "run_hand_eye_calibration.py"

            if not script_path.exists():
                QMessageBox.critical(self, "File Not Found", f"Could not find:\n{script_path}")
                return

            subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(script_path.parent)
            )

        except Exception as e:
            QMessageBox.critical(self, "Launch Error", f"Failed to launch calibration:\n{e}")

    def open_results_page(self):
        if self.go_to_results:
            self.go_to_results()
            