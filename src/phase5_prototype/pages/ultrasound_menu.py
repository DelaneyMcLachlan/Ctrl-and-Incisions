import sys
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QStackedWidget,
)

from pages.sequence_navigation_page import NavigationPage
from pages.edit_config import ConfigEditorWindow
from pages.start_plus_server import PlusServerLauncher
from pages.start_volume_reconstruction import VolumeReconstructorUI


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

        self.nav_page = NavigationPage()
        self.config_page = ConfigEditorWindow()
        self.record_page = PlusServerLauncher()
        self.recon_page = VolumeReconstructorUI()

        # Add them to the internal stack
        self.stack.addWidget(self.nav_page)      # index 0
        self.stack.addWidget(self.config_page)   # index 1
        self.stack.addWidget(self.record_page)   # index 2
        self.stack.addWidget(self.recon_page)    # index 3

        self.nav_page.btn_config.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.nav_page.btn_record.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.nav_page.btn_recon.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        self.nav_page.btn_view3d.clicked.connect(self.launch_ultrasound_viewer)

        self.config_page.btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.record_page.btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.recon_page.btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        self.nav_page.btn_back.clicked.connect(self.handle_back)

    def handle_back(self):
        if self.go_back:
            self.go_back()

    def launch_ultrasound_viewer(self):
        try:
            project_root = Path(__file__).resolve().parent.parent
            viewer_path = project_root / "pages" / "ultrasound_viewer_page.py"

            subprocess.Popen([sys.executable, str(viewer_path)])
        except Exception as e:
            print(f"Error launching viewer: {e}")
            
			