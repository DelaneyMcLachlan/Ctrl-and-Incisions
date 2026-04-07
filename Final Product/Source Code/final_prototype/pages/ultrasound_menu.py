import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QStackedWidget,
)

current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

from sequence_navigation_page import NavigationPage
from edit_config import ConfigEditorWindow
from start_plus_server import PlusServerLauncher
from start_volume_reconstruction import VolumeReconstructorUI
from ultrasound_viewer_page import TrackedUltrasoundViewer

class UltrasoundSequenceMenuPage(QWidget):
    def __init__(self, go_back=None):
        super().__init__()
        self.go_back = go_back

        self.setWindowTitle("Ultrasound Sequence Menu")

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        # Instantiate all pages
        self.nav_page = NavigationPage()
        self.config_page = ConfigEditorWindow()
        self.record_page = PlusServerLauncher()
        # self.recon_page = VolumeReconstructorUI()
        self.viewer_page = TrackedUltrasoundViewer() # New instance

        # Add them to the internal stack
        self.stack.addWidget(self.nav_page)      # index 0
        self.stack.addWidget(self.config_page)   # index 1
        self.stack.addWidget(self.record_page)   # index 2
        # self.stack.addWidget(self.recon_page)    # index 3
        self.stack.addWidget(self.viewer_page)   # index 4

        # Navigation button connections
        self.nav_page.btn_config.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.nav_page.btn_record.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        # self.nav_page.btn_recon.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        self.nav_page.btn_view3d.clicked.connect(lambda: (print("Switching to Index 3"), self.stack.setCurrentIndex(3)))

        # "Back" button connections for all sub-pages
        self.config_page.btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.record_page.btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        # self.recon_page.btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.viewer_page.btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        self.nav_page.btn_back.clicked.connect(self.handle_back)

    def handle_back(self):
        if self.go_back:
            self.go_back()