from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QTextEdit,
    QFrame,
    QSizePolicy,
)

from data.db import (
    get_recent_capture_sessions,
    get_capture_session_details,
    get_ultrasound_streams_for_session,
    get_tracking_streams_for_session,
    get_logs_for_session,
)


class CalibrationResultsPage(QWidget):
    def __init__(self, go_back=None):
        super().__init__()
        self.go_back = go_back
        self.session_map = {}
        self.setup_ui()
        self.load_sessions()

    def setup_ui(self):
        self.setStyleSheet("background-color: #E9E9EE;")

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(18, 18, 18, 18)
        self.main_layout.setSpacing(14)

        # Top bar
        top_row = QHBoxLayout()

        self.back_button = QPushButton("←")
        self.back_button.setFixedSize(48, 48)
        self.back_button.clicked.connect(self.handle_back)

        self.title_label = QLabel("Previous Results")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_sessions)
        self.refresh_button.setFixedHeight(42)

        top_row.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignLeft)
        top_row.addStretch()
        top_row.addWidget(self.title_label)
        top_row.addStretch()
        top_row.addWidget(self.refresh_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.main_layout.addLayout(top_row)

        # Body
        body_row = QHBoxLayout()
        body_row.setSpacing(14)

        # Left: sessions list
        self.sessions_card = QFrame()
        self.sessions_card_layout = QVBoxLayout(self.sessions_card)
        self.sessions_card_layout.setContentsMargins(16, 16, 16, 16)
        self.sessions_card_layout.setSpacing(10)

        self.sessions_label = QLabel("Recent Sessions")
        self.sessions_list = QListWidget()
        self.sessions_list.currentItemChanged.connect(self.handle_session_selected)

        self.sessions_card_layout.addWidget(self.sessions_label)
        self.sessions_card_layout.addWidget(self.sessions_list)

        # Right: details
        self.details_card = QFrame()
        self.details_card_layout = QVBoxLayout(self.details_card)
        self.details_card_layout.setContentsMargins(16, 16, 16, 16)
        self.details_card_layout.setSpacing(10)

        self.details_label = QLabel("Session Details")
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)

        self.details_card_layout.addWidget(self.details_label)
        self.details_card_layout.addWidget(self.details_text)

        body_row.addWidget(self.sessions_card, 2)
        body_row.addWidget(self.details_card, 3)

        self.main_layout.addLayout(body_row)

        self.apply_styles()

    def apply_styles(self):
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #2948A3;
                border: none;
                border-radius: 10px;
                font-size: 22px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #F4F7FF;
            }
        """)

        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #2948A3;
                border: 1px solid #D6D6DB;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 600;
                padding-left: 16px;
                padding-right: 16px;
            }
            QPushButton:hover {
                background-color: #F4F7FF;
            }
        """)

        self.title_label.setStyleSheet("""
            QLabel {
                color: #2948A3;
                font-size: 24px;
                font-weight: 700;
            }
        """)

        for card in [self.sessions_card, self.details_card]:
            card.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 16px;
                }
            """)

        self.sessions_label.setStyleSheet("""
            QLabel {
                color: #2948A3;
                font-size: 18px;
                font-weight: 700;
            }
        """)

        self.details_label.setStyleSheet("""
            QLabel {
                color: #2948A3;
                font-size: 18px;
                font-weight: 700;
            }
        """)

        self.sessions_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E0E0E0;
                border-radius: 10px;
                background-color: #FAFAFA;
                padding: 6px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px;
                margin: 4px 0px;
                border-radius: 8px;
            }
            QListWidget::item:selected {
                background-color: #E8EEFF;
                color: #2948A3;
            }
        """)

        self.details_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E0E0E0;
                border-radius: 10px;
                background-color: #FAFAFA;
                padding: 8px;
                font-size: 13px;
            }
        """)

    def load_sessions(self):
        self.sessions_list.clear()
        self.session_map.clear()
        self.details_text.clear()

        sessions = get_recent_capture_sessions(limit=25)

        if not sessions:
            self.details_text.setPlainText("No previous results found.")
            return

        for row in sessions:
            session_id = row[0]
            started_at = row[1]
            status = row[3] or "UNKNOWN"
            device_name = row[6] or "Unknown Device"

            item_text = f"Session #{session_id} | {status}\n{device_name} | {started_at}"
            item = QListWidgetItem(item_text)
            self.sessions_list.addItem(item)
            self.session_map[item_text] = session_id

        self.sessions_list.setCurrentRow(0)

    def handle_session_selected(self, current, previous):
        if current is None:
            return

        session_text = current.text()
        session_id = self.session_map.get(session_text)
        if session_id is None:
            return

        details = get_capture_session_details(session_id)
        ultrasound_streams = get_ultrasound_streams_for_session(session_id)
        tracking_streams = get_tracking_streams_for_session(session_id)
        logs = get_logs_for_session(session_id, limit=20)

        if not details:
            self.details_text.setPlainText("No details found for this session.")
            return

        (
            sid,
            started_at,
            ended_at,
            status,
            output_dir,
            fps,
            device_name,
            device_type,
            connection_info,
            config_path,
            config_type,
            notes,
        ) = details

        lines = []
        lines.append(f"Session ID: {sid}")
        lines.append(f"Status: {status or 'N/A'}")
        lines.append(f"Started: {started_at or 'N/A'}")
        lines.append(f"Ended: {ended_at or 'N/A'}")
        lines.append(f"Output Directory: {output_dir or 'N/A'}")
        lines.append(f"FPS: {fps if fps is not None else 'N/A'}")
        lines.append("")
        lines.append("Device")
        lines.append(f"  Name: {device_name or 'N/A'}")
        lines.append(f"  Type: {device_type or 'N/A'}")
        lines.append(f"  Connection Info: {connection_info or 'N/A'}")
        lines.append("")
        lines.append("Configuration")
        lines.append(f"  Config Path: {config_path or 'N/A'}")
        lines.append(f"  Config Type: {config_type or 'N/A'}")
        lines.append(f"  Notes: {notes or 'N/A'}")
        lines.append("")

        lines.append("Ultrasound Streams")
        if ultrasound_streams:
            for stream in ultrasound_streams:
                _, stream_type, file_path, stream_fps, resolution, created_at = stream
                lines.append(f"  - Type: {stream_type or 'N/A'}")
                lines.append(f"    File: {file_path or 'N/A'}")
                lines.append(f"    FPS: {stream_fps if stream_fps is not None else 'N/A'}")
                lines.append(f"    Resolution: {resolution or 'N/A'}")
                lines.append(f"    Created: {created_at or 'N/A'}")
        else:
            lines.append("  No ultrasound streams found.")
        lines.append("")

        lines.append("Tracking Streams")
        if tracking_streams:
            for stream in tracking_streams:
                _, stream_type, file_path, rate_hz, created_at = stream
                lines.append(f"  - Type: {stream_type or 'N/A'}")
                lines.append(f"    File: {file_path or 'N/A'}")
                lines.append(f"    Rate: {rate_hz if rate_hz is not None else 'N/A'}")
                lines.append(f"    Created: {created_at or 'N/A'}")
        else:
            lines.append("  No tracking streams found.")
        lines.append("")

        lines.append("Recent Logs")
        if logs:
            for event_type, timestamp, level, message in logs:
                lines.append(f"  - [{timestamp}] {level} | {event_type}")
                if message:
                    lines.append(f"    {message}")
        else:
            lines.append("  No logs found.")

        self.details_text.setPlainText("\n".join(lines))

    def handle_back(self):
        if self.go_back:
            self.go_back()
            
