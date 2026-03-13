import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont, QGuiApplication
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QSizePolicy,
    QGraphicsDropShadowEffect,
)


class LandingPage(QWidget):
    def __init__(self, go_to_calibration=None, go_to_sequence_menu=None):
        super().__init__()

        self.go_to_calibration = go_to_calibration
        self.go_to_sequence_menu = go_to_sequence_menu

        self.setWindowTitle("Landing Page")

        base_dir = Path(__file__).resolve().parent.parent
        assets_dir = base_dir / "assets"

        self.logo_path = assets_dir / "logo.png"
        self.icon_path = assets_dir / "ultrasound_icon.png"
        self.bg_path = assets_dir / "surgery_background.png"

        self.logo_pixmap_original = QPixmap(str(self.logo_path)) if self.logo_path.exists() else None
        self.icon_pixmap_original = QPixmap(str(self.icon_path)) if self.icon_path.exists() else None
        self.bg_pixmap_original = QPixmap(str(self.bg_path)) if self.bg_path.exists() else None

        self.setup_ui()
        self.update_responsive_ui()

    def setup_shadow(self, widget, blur=18, x_offset=0, y_offset=3, color_alpha=55):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(blur)
        shadow.setOffset(x_offset, y_offset)
        shadow.setColor(Qt.GlobalColor.black)
        shadow.setEnabled(True)
        widget.setGraphicsEffect(shadow)
        shadow.setColor(shadow.color().fromRgb(0, 0, 0, color_alpha))

    def setup_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # LEFT PANEL
        self.left_panel = QFrame()
        self.left_panel.setObjectName("leftPanel")
        self.left_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.left_panel.setStyleSheet("""
            QFrame#leftPanel {
                background-color: #E9E9EE;
                border-top-right-radius: 28px;
                border-bottom-right-radius: 28px;
            }
        """)

        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(26, 28, 26, 22)
        self.left_layout.setSpacing(18)

        # Logo container
        self.logo_container = QFrame()
        self.logo_container.setObjectName("logoContainer")
        self.logo_container.setStyleSheet("""
            QFrame#logoContainer {
                background-color: white;
                border-radius: 12px;
            }
        """)
        self.logo_container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setup_shadow(self.logo_container, blur=16, y_offset=3, color_alpha=45)

        logo_container_layout = QVBoxLayout(self.logo_container)
        logo_container_layout.setContentsMargins(10, 10, 10, 10)
        logo_container_layout.setSpacing(0)

        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if self.logo_pixmap_original and not self.logo_pixmap_original.isNull():
            self.logo_label.setPixmap(self.logo_pixmap_original)
        else:
            self.logo_label.setText("Logo")

        logo_container_layout.addWidget(self.logo_label)
        self.left_layout.addWidget(self.logo_container, alignment=Qt.AlignmentFlag.AlignLeft)
        self.left_layout.addSpacing(40)

        # Card
        self.card = QFrame()
        self.card.setObjectName("card")
        self.card.setMaximumWidth(420)
        self.card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.card.setStyleSheet("""
            QFrame#card {
                background-color: #FCFCFD;
                border-radius: 18px;
            }
        """)
        self.setup_shadow(self.card, blur=22, y_offset=4, color_alpha=38)

        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(20, 16, 20, 16)
        self.card_layout.setSpacing(10)

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        if self.icon_pixmap_original and not self.icon_pixmap_original.isNull():
            self.icon_label.setPixmap(self.icon_pixmap_original)
        else:
            self.icon_label.setText("Ultrasound Icon")

        self.title_label = QLabel("Spatial Ultrasound Calibration\nand Reconstruction")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #2948A3;
                font-weight: 600;
                line-height: 1.2;
                background: transparent;
            }
        """)

        self.card_layout.addSpacing(6)
        self.card_layout.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.card_layout.addSpacing(4)
        self.card_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.card_layout.addSpacing(6)

        self.left_layout.addWidget(self.card, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.left_layout.addSpacing(8)

        # Buttons
        self.calibration_button = QPushButton("Calibration Menu")
        self.sequence_button = QPushButton("Ultrasound Sequence Menu")

        self.calibration_button.clicked.connect(self.open_calibration)
        self.sequence_button.clicked.connect(self.open_ultrasound_sequence_menu)

        self.left_layout.addWidget(self.calibration_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.left_layout.addWidget(self.sequence_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.left_layout.addStretch()

        # RIGHT SIDE
        self.bg_label = QLabel()
        self.bg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bg_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        if not self.bg_pixmap_original or self.bg_pixmap_original.isNull():
            self.bg_label.setText("Background Image Missing")
            self.bg_label.setStyleSheet("background-color: black; color: white;")

        self.main_layout.addWidget(self.left_panel, stretch=3)
        self.main_layout.addWidget(self.bg_label, stretch=5)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_responsive_ui()

    def update_responsive_ui(self):
        window_width = max(1, self.width())
        window_height = max(1, self.height())

        left_width = max(320, min(int(window_width * 0.38), 470))
        self.left_panel.setMinimumWidth(left_width)
        self.left_panel.setMaximumWidth(left_width)

        margin = max(18, min(30, window_width // 48))
        spacing = max(10, min(18, window_height // 40))
        self.left_layout.setContentsMargins(margin, margin, margin, margin - 4)
        self.left_layout.setSpacing(spacing)

        logo_box = max(82, min(102, left_width // 4))
        self.logo_container.setFixedSize(logo_box, logo_box)

        if self.logo_pixmap_original and not self.logo_pixmap_original.isNull():
            logo_img = int(logo_box * 0.82)
            logo_pixmap = self.logo_pixmap_original.scaled(
                logo_img,
                logo_img,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.logo_label.setPixmap(logo_pixmap)

        card_width = int(left_width * 0.78)
        self.card.setFixedWidth(card_width)

        card_pad_h = max(16, min(24, left_width // 18))
        card_pad_v = max(12, min(20, window_height // 36))
        self.card_layout.setContentsMargins(card_pad_h, card_pad_v, card_pad_h, card_pad_v)

        if self.icon_pixmap_original and not self.icon_pixmap_original.isNull():
            icon_size = max(130, min(210, int(left_width * 0.46)))
            icon_pixmap = self.icon_pixmap_original.scaled(
                icon_size,
                icon_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.icon_label.setPixmap(icon_pixmap)

        title_font_size = max(11, min(15, left_width // 26))
        self.title_label.setFont(QFont("Arial", title_font_size, QFont.Weight.DemiBold))

        button_height = max(42, min(52, window_height // 15))
        button_font_size = max(11, min(15, left_width // 28))
        radius = button_height // 2
        button_width = int(left_width * 0.68)

        self.calibration_button.setFixedWidth(button_width)
        self.sequence_button.setFixedWidth(button_width)

        button_style = f"""
            QPushButton {{
                background-color: #FFFFFF;
                color: #2948A3;
                border: 1px solid #D6D6DB;
                border-radius: {radius}px;
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

        self.calibration_button.setStyleSheet(button_style)
        self.sequence_button.setStyleSheet(button_style)

        if self.bg_pixmap_original and not self.bg_pixmap_original.isNull():
            target_width = max(1, self.bg_label.width())
            target_height = max(1, self.bg_label.height())
            bg_pixmap = self.bg_pixmap_original.scaled(
                target_width,
                target_height,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self.bg_label.setPixmap(bg_pixmap)

    def open_calibration(self):
        if self.go_to_calibration:
            self.go_to_calibration()
        else:
            print("Calibration clicked")

    def open_ultrasound_sequence_menu(self):
        if self.go_to_sequence_menu:
            self.go_to_sequence_menu()
        else:
            print("Ultrasound Sequence Menu clicked")
