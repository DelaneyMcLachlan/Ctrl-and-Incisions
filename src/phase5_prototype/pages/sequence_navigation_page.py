# NavigationPage.py
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QApplication, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# --- THEME COLORS ---
LEFT_BG = "#E8E8F2"            # Page background
NAVY = "#132B50"
WHITE = "#FFFFFF"
ACCENT = "#3A66B7"
ACCENT_HOVER = "#4A7DE0"
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
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {ACCENT_HOVER};
            color: white;
        }}
    """)
    return btn


class NavigationPage(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet(f"background-color: {LEFT_BG};")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # ------------------------------------------------------
        # Top Bar With Back Button
        # ------------------------------------------------------
        top_bar = QHBoxLayout()
        back_btn = QPushButton("←")
        back_btn.setFixedSize(32, 32)
        back_btn.setStyleSheet(f"""
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
        """)

        top_title = QLabel("Menu")
        top_title.setStyleSheet(f"color:{NAVY}; font-size:11pt; font-weight:600;")
        top_title.setContentsMargins(10, 0, 0, 0)

        top_bar.addWidget(back_btn)
        top_bar.addWidget(top_title)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        # ------------------------------------------------------
        # Center Buttons
        # ------------------------------------------------------
        center_wrapper = QVBoxLayout()
        center_wrapper.setAlignment(Qt.AlignmentFlag.AlignCenter)

        center_wrapper.addItem(QSpacerItem(20, 120, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.btn_config = make_nav_button("Configure Hardware")
        self.btn_record = make_nav_button("Record Sequence")
        self.btn_recon  = make_nav_button("Perform Volume Reconstruction")
        self.btn_view3d = make_nav_button("View 3D Reconstruction")

        # self.btn_config.clicked.connect(self.open_config_editor)
        # self.btn_record.clicked.connect(self.open_record_page)
        # self.btn_view3d.clicked.connect(self.open_volume_viewer)    


        center_wrapper.addWidget(self.btn_config)
        center_wrapper.addSpacing(15)
        center_wrapper.addWidget(self.btn_record)
        center_wrapper.addSpacing(15)
        center_wrapper.addWidget(self.btn_recon)
        center_wrapper.addSpacing(15)
        center_wrapper.addWidget(self.btn_view3d)

        center_wrapper.addItem(QSpacerItem(20, 120, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        layout.addLayout(center_wrapper)

        # ------------------------------------------------------
        # Help Button (bottom-right)
        # ------------------------------------------------------
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch()

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
        """)
        bottom_bar.addWidget(help_btn)

        layout.addLayout(bottom_bar)


# Standalone test
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = NavigationPage()
    w.resize(1100, 680)
    w.show()
    sys.exit(app.exec())
