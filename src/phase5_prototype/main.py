import sys
from pathlib import Path

from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QApplication, QWidget, QStackedWidget, QVBoxLayout

from pages.landing_page import LandingPage
from pages.calibration_menu import CalibrationMenuPage
from pages.calibration_results import CalibrationResultsPage
from pages.ultrasound_menu import UltrasoundSequenceMenuPage


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ctrl+Incision")
        self.stack = QStackedWidget()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

        self.landing_page = LandingPage(
            go_to_calibration=self.show_calibration_menu,
            go_to_sequence_menu=self.show_ultrasound_menu,
        )

        self.calibration_menu_page = CalibrationMenuPage(
            go_back=self.show_landing_page,
            go_to_results=self.show_calibration_results,
        )

        self.calibration_results_page = CalibrationResultsPage(
            go_back=self.show_calibration_menu
        )

        self.ultrasound_sequence_menu_page = UltrasoundSequenceMenuPage(
            go_back=self.show_landing_page
        )

        self.stack.addWidget(self.landing_page)
        self.stack.addWidget(self.calibration_menu_page)
        self.stack.addWidget(self.calibration_results_page)
        self.stack.addWidget(self.ultrasound_sequence_menu_page)

        self.stack.setCurrentWidget(self.landing_page)

        self.set_initial_window_size()

    def set_initial_window_size(self):
        screen = QGuiApplication.primaryScreen()
        available = screen.availableGeometry()

        screen_width = available.width()
        screen_height = available.height()

        window_width = int(screen_width * 0.92)
        window_height = int(screen_height * 0.88)

        self.resize(window_width, window_height)
        self.setMinimumSize(
            max(900, int(screen_width * 0.55)),
            max(550, int(screen_height * 0.55))
        )

        x = available.x() + (screen_width - window_width) // 2
        y = available.y() + (screen_height - window_height) // 2
        self.move(x, y)

    def show_landing_page(self):
        self.stack.setCurrentWidget(self.landing_page)

    def show_calibration_menu(self):
        self.stack.setCurrentWidget(self.calibration_menu_page)

    def show_calibration_results(self):
        self.stack.setCurrentWidget(self.calibration_results_page)

    def show_ultrasound_menu(self):
        self.stack.setCurrentWidget(self.ultrasound_sequence_menu_page)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
	