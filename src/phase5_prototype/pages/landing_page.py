import sys
import subprocess
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget

# 1. Imports from your files
from sequence_navigation_page import NavigationPage
from edit_config import ConfigEditorWindow
from start_plus_server import PlusServerLauncher 
from start_volume_reconstruction import VolumeReconstructorUI

class MainApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Surgical System Control")
        self.resize(1200, 800)

        # Main switcher
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # 2. Initialize the page instances
        self.nav_page = NavigationPage()
        self.config_page = ConfigEditorWindow()
        self.record_page = PlusServerLauncher()
        self.recon_page = VolumeReconstructorUI()

        # 3. Add them to the stack
        # Index 0 = Home, Index 1 = Config, Index 2 = Record
        self.stack.addWidget(self.nav_page)    
        self.stack.addWidget(self.config_page) 
        self.stack.addWidget(self.record_page) 
        self.stack.addWidget(self.recon_page)

        # 4. Connect Buttons from NavigationPage
        self.nav_page.btn_config.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.nav_page.btn_record.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.nav_page.btn_recon.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        # Launching the PySide6 viewer as a separate window (process)
        self.nav_page.btn_view3d.clicked.connect(self.launch_ultrasound_viewer)

        # 5. Connect back buttons 
        self.config_page.btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.record_page.btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.recon_page.btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        

    def launch_ultrasound_viewer(self):
        """Launches the PySide6 viewer as a standalone external window."""
        try:
            subprocess.Popen([sys.executable, "./src/phase5_prototype/pages/ultrasound_viewer_page.py"])
        except Exception as e:
            print(f"Error launching viewer: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApplication()
    window.show()
    sys.exit(app.exec())