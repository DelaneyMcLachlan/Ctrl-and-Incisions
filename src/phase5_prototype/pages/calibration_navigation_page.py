from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt

LEFT_BG = "#E8E8F2"
NAVY = "#132B50"
WHITE = "#FFFFFF"
ACCENT = "#3A66B7"
ACCENT_HOVER = "#4A7DE0"
PRESSED = "#7FA6E4"
SHADOW = "#C8CCDD"


def make_nav_button(text):
    btn = QPushButton(text)
    btn.setFixedSize(260, 36)

    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {WHITE};
            color: {NAVY};
            border-radius: 18px;
            border: 1px solid {SHADOW};
            font-size: 11pt;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {ACCENT_HOVER};
            color: white;
        }}
        QPushButton:pressed {{
                background-color: {PRESSED};
            }}
    """)
    return btn


class CalibrationNavigationPage(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet(f"background-color: {LEFT_BG};")
        self._build_ui()

    def _build_ui(self):

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # --------------------------
        # Top Bar
        # --------------------------

        top_bar = QHBoxLayout()

        self.btn_back = QPushButton("←")
        self.btn_back.setFixedSize(32, 32)

        self.btn_back.setStyleSheet(f"""
            QPushButton {{
                background-color: {WHITE};
                border-radius: 6px;
                border: 1px solid #D5D7DD;
                color: {NAVY};
                font-size: 14pt;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {ACCENT};
                color: white;
            }}
            QPushButton:pressed {{
                background-color: {PRESSED};
            }}
        """)

        title = QLabel("Calibration Menu  ")
        title.setStyleSheet(f"color:{NAVY}; font-size:11pt; font-weight:600;")
        title.setContentsMargins(10, 0, 0, 0)

        top_bar.addWidget(self.btn_back)
        top_bar.addWidget(title)
        top_bar.addStretch()

        layout.addLayout(top_bar)

        # --------------------------
        # Center Buttons
        # --------------------------

        center = QVBoxLayout()
        center.setAlignment(Qt.AlignmentFlag.AlignCenter)

        center.addItem(QSpacerItem(20, 120, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.btn_calibrate = make_nav_button("Perform Calibration")
        self.btn_results = make_nav_button("View Previous Results")

        center.addWidget(self.btn_calibrate)
        center.addSpacing(15)
        center.addWidget(self.btn_results)

        center.addItem(QSpacerItem(20, 120, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        layout.addLayout(center)

        # --------------------------
        # Bottom Help Button
        # --------------------------

        bottom = QHBoxLayout()
        bottom.addStretch()

        help_btn = QPushButton("?")
        help_btn.setFixedSize(32, 32)

        help_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {WHITE};
                border-radius: 6px;
                border: 1px solid #D5D7DD;
                font-weight: 900;
                color: {NAVY};
            }}
            QPushButton:hover {{
                background-color: {ACCENT};
                color: white;
            }}
            QPushButton:pressed {{
                background-color: {PRESSED};
            }}
        """)

        bottom.addWidget(help_btn)

        layout.addLayout(bottom)
