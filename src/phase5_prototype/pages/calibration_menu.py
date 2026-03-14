import sys
import subprocess
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QGraphicsDropShadowEffect,
    QMessageBox,
)


class CalibrationMenuPage(QWidget):
    def __init__(self, go_back=None, go_to_results=None):
        super().__init__()
        self.go_back = go_back
        self.go_to_results = go_to_results
        self.setup_ui()
        self.update_responsive_ui()

    def setup_shadow(self, widget, blur=18, x_offset=0, y_offset=3, color_alpha=55):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(blur)
        shadow.setOffset(x_offset, y_offset)
        shadow.setEnabled(True)
        color = shadow.color().fromRgb(0, 0, 0, color_alpha)
        shadow.setColor(color)
        widget.setGraphicsEffect(shadow)

    def setup_ui(self):
        self.setStyleSheet("background-color: #E9E9EE;")

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(18, 18, 18, 18)
        self.main_layout.setSpacing(0)

        # top row with back button
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(0)

        self.back_button = QPushButton("←")
        self.back_button.clicked.connect(self.handle_back)
        self.back_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setup_shadow(self.back_button, blur=16, y_offset=3, color_alpha=35)

        top_row.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        top_row.addStretch()

        self.main_layout.addLayout(top_row)
        self.main_layout.addStretch()

        # center buttons
        self.center_layout = QVBoxLayout()
        self.center_layout.setSpacing(20)

        self.camera_button = QPushButton("Perform Calibration")
        self.results_button = QPushButton("View Previous Results")

        self.camera_button.clicked.connect(self.launch_hand_eye_calibration)
        self.results_button.clicked.connect(self.open_results_page)

        self.center_layout.addWidget(self.camera_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.center_layout.addWidget(self.results_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addLayout(self.center_layout)
        self.main_layout.addStretch()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_responsive_ui()

    def update_responsive_ui(self):
        width = max(1, self.width())
        height = max(1, self.height())

        back_size = max(42, min(58, width // 18))
        back_font_size = max(16, min(24, width // 45))

        self.back_button.setFixedSize(back_size, back_size)
        self.back_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                color: #2948A3;
                border: none;
                border-radius: 10px;
                font-size: {back_font_size}px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: #F4F7FF;
            }}
            QPushButton:pressed {{
                background-color: #E8EEFF;
            }}
        """)

        button_width = max(230, min(360, width // 4))
        button_height = max(46, min(62, height // 12))
        radius = button_height // 2
        button_font_size = max(11, min(16, width // 80))

        button_style = f"""
            QPushButton {{
                background-color: #FFFFFF;
                color: #2948A3;
                border: 1px solid #D6D6DB;
                border-radius: {radius}px;
                min-width: {button_width}px;
                max-width: {button_width}px;
                min-height: {button_height}px;
                max-height: {button_height}px;
                font-size: {button_font_size}px;
                font-weight: 600;
                padding-left: 18px;
                padding-right: 18px;
            }}
            QPushButton:hover {{
                background-color: #F4F7FF;
                border: 1px solid #C8D3F5;
            }}
            QPushButton:pressed {{
                background-color: #E8EEFF;
            }}
        """

        for button in [self.camera_button, self.results_button]:
            button.setStyleSheet(button_style)

    def launch_hand_eye_calibration(self):
        try:
            # calibration_menu.py -> pages -> project_folder -> src
            src_dir = Path(__file__).resolve().parents[2]

            script_path = src_dir / "sprint2_prototype" / "hand-eye-calibration" / "run_hand_eye_calibration.py"

            if not script_path.exists():
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self,
                    "File Not Found",
                    f"Could not find:\n{script_path}"
                )
                return

            subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(script_path.parent)
            )

        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Launch Error",
                f"Failed to launch hand-eye calibration:\n{e}"
            )

    def open_results_page(self):
        if self.go_to_results:
            self.go_to_results()

    def handle_back(self):
        if self.go_back:
            self.go_back()
