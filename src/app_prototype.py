# app_prototype.py
# Minimal PyQt5 prototype to demo: scan/intake, calibration, and 3D reconstruction flows
# uses mock data files: mock_rom.json, mock_frames.npy

import json
import os
import sys
import time
import numpy as np

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap, QImage
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFileDialog, QProgressBar, QSlider, QGroupBox, QGridLayout, QMessageBox
)

APP_TITLE = "Imaging Software – Prototype (Calibration + Reconstruction)"

class PrototypeApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(1100, 720)

        # --- State ---
        self.calibrated = False
        self.frames = None           # numpy array [N, H, W]
        self.recon_progress = 0
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self._tick_progress)
        self.last_action_stack = []  # for Undo

        # --- UI ---
        main = QVBoxLayout(self)

        # Top status banner
        self.banner = QLabel("")
        self.banner.setStyleSheet("background:#eceff1;color:#263238;padding:8px;border-radius:6px;")
        self.banner.setText("Welcome: Load ROM (calibration) and mock frames to begin.")
        main.addWidget(self.banner)

        # Central content: left (viewer) + right (controls)
        content = QHBoxLayout()
        main.addLayout(content, 1)

        # ---- Left: imaging preview (static placeholder) ----
        left = QVBoxLayout()
        content.addLayout(left, 2)

        self.viewer_title = QLabel("Live Imaging / 3D Preview (placeholder)")
        self.viewer_title.setFont(QFont("Arial", 12, QFont.Bold))
        left.addWidget(self.viewer_title)

        self.viewer = QLabel()
        self.viewer.setStyleSheet("background:#f5f5f5;border:1px solid #cfd8dc;")
        self.viewer.setAlignment(Qt.AlignCenter)
        self.viewer.setMinimumHeight(480)
        # show a placeholder checker image
        self._set_placeholder_image()
        left.addWidget(self.viewer, 1)

        # Controls below viewer: progress + opacity
        bottom_controls = QHBoxLayout()
        left.addLayout(bottom_controls)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("Reconstruction progress: %p%")
        bottom_controls.addWidget(self.progress, 3)

        self.opacity_label = QLabel("Opacity:")
        bottom_controls.addWidget(self.opacity_label)
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(60)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        bottom_controls.addWidget(self.opacity_slider, 2)

        # ---- Right: actions + LCD outputs ----
        right = QVBoxLayout()
        content.addLayout(right, 1)

        # File/Scan group
        file_grp = QGroupBox("Files & Intake")
        fg = QVBoxLayout(file_grp)
        self.btn_load_rom = QPushButton("Load ROM file")
        self.btn_load_rom.clicked.connect(self._on_load_rom)
        fg.addWidget(self.btn_load_rom)

        self.btn_load_frames = QPushButton("Load Mock Ultrasound Frames")
        self.btn_load_frames.clicked.connect(self._on_load_frames)
        fg.addWidget(self.btn_load_frames)

        self.btn_scan_batch = QPushButton("Simulate Batch Scan (Intake)")
        self.btn_scan_batch.clicked.connect(self._on_scan_batch)
        fg.addWidget(self.btn_scan_batch)

        right.addWidget(file_grp)

        # Calibration group
        cal_grp = QGroupBox("Calibration")
        cg = QGridLayout(cal_grp)

        self.btn_run_cal = QPushButton("Run Calibration")
        self.btn_run_cal.clicked.connect(self._on_run_calibration)
        cg.addWidget(self.btn_run_cal, 0, 0, 1, 2)

        self.lbl_x = QLabel("X: —")
        self.lbl_y = QLabel("Y: —")
        self.lbl_z = QLabel("Z: —")
        self.lbl_err = QLabel("Error: —")

        for w in (self.lbl_x, self.lbl_y, self.lbl_z, self.lbl_err):
            w.setStyleSheet("font-family:Consolas,monospace;background:#263238;color:#a5d6a7;padding:6px;border-radius:4px;")

        cg.addWidget(self.lbl_x,   1, 0)
        cg.addWidget(self.lbl_y,   1, 1)
        cg.addWidget(self.lbl_z,   2, 0)
        cg.addWidget(self.lbl_err, 2, 1)

        self.btn_retry = QPushButton("Retry Calibration")
        self.btn_retry.clicked.connect(self._on_retry_cal)
        cg.addWidget(self.btn_retry, 3, 0, 1, 2)

        right.addWidget(cal_grp)

        # Reconstruction group
        rec_grp = QGroupBox("3D Reconstruction")
        rg = QVBoxLayout(rec_grp)

        self.btn_reconstruct = QPushButton("Reconstruct 3D Volume")
        self.btn_reconstruct.clicked.connect(self._on_reconstruct)
        rg.addWidget(self.btn_reconstruct)

        self.btn_save_slice = QPushButton("Save Slice (PNG)")
        self.btn_save_slice.clicked.connect(self._on_save_slice)
        rg.addWidget(self.btn_save_slice)

        self.btn_export = QPushButton("Export Volume (NPY)")
        self.btn_export.clicked.connect(self._on_export)
        rg.addWidget(self.btn_export)

        self.btn_undo = QPushButton("Undo Last Action")
        self.btn_undo.clicked.connect(self._on_undo)
        rg.addWidget(self.btn_undo)

        right.addWidget(rec_grp)
        right.addStretch(1)

        # Footer log hint
        self.log = QLabel("Log: ready.")
        self.log.setStyleSheet("color:#455a64;")
        main.addWidget(self.log)

    # --------- Helpers ---------
    def _set_banner(self, text, kind="info"):
        styles = {
            "info":    "background:#eceff1;color:#263238;",
            "ok":      "background:#e8f5e9;color:#1b5e20;",
            "warn":    "background:#fff8e1;color:#8d6e63;",
            "error":   "background:#ffebee;color:#b71c1c;",
        }
        self.banner.setStyleSheet(styles.get(kind, styles["info"]) + "padding:8px;border-radius:6px;")
        self.banner.setText(text)

    def _set_placeholder_image(self):
        # generate a simple checkerboard placeholder
        w, h = 640, 420
        img = np.zeros((h, w), dtype=np.uint8)
        tile = 40
        for y in range(0, h, tile):
            for x in range(0, w, tile):
                if ((x//tile) + (y//tile)) % 2 == 0:
                    img[y:y+tile, x:x+tile] = 220
                else:
                    img[y:y+tile, x:x+tile] = 180
        qimg = QImage(img.data, w, h, w, QImage.Format_Grayscale8)
        self.viewer.setPixmap(QPixmap.fromImage(qimg))

    def _on_opacity_changed(self, val):
        self.log.setText(f"Log: opacity set to {val}%")

    # --------- Actions -----------
    def _on_load_rom(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select ROM file", os.getcwd(), "JSON (*.json)")
        if not path:
            return
        try:
            with open(path, "r") as f:
                rom = json.load(f)
            if rom.get("calibration_status") == "valid":
                self._set_banner("Calibration data loaded (ROM): status = valid ✔", "ok")
                self.calibrated = True
                # Example LCD update (mock)
                self.lbl_x.setText("X: 12.4 mm")
                self.lbl_y.setText("Y: -3.2 mm")
                self.lbl_z.setText("Z: 45.0 mm")
                self.lbl_err.setText("Error: 0.05 mm")
                self.last_action_stack.append(("load_rom", path))
            else:
                self._set_banner("ROM loaded but status invalid. Please retry.", "warn")
                self.calibrated = False
        except Exception as e:
            self._set_banner(f"Failed to load ROM ({e})", "error")
            self.calibrated = False

    def _on_load_frames(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select mock frames (.npy)", os.getcwd(), "NumPy array (*.npy)")
        if not path:
            return
        try:
            frames = np.load(path)
            assert frames.ndim == 3, "Expected shape [N, H, W]"
            self.frames = frames
            self._set_banner(f"Loaded {frames.shape[0]} ultrasound slices ✔", "ok")
            self.last_action_stack.append(("load_frames", path))
        except Exception as e:
            self._set_banner(f"Failed to load frames ({e})", "error")
            self.frames = None

    def _on_run_calibration(self):
        # Simulate a calibration pass/fail based on whether ROM loaded
        if self.calibrated:
            self._set_banner("Calibration already valid ✔", "ok")
            return
        # Simulate attempt:
        self._set_banner("Running calibration…", "info")
        QApplication.processEvents()
        time.sleep(0.5)
        # If no ROM loaded, fail
        self._set_banner("Calibration failed: Load ROM file or Retry.", "error")
        self.last_action_stack.append(("calibrate_fail", None))

    def _on_retry_cal(self):
        # Simulate retry success if ROM is present
        if not self.calibrated:
            self._set_banner("Retrying calibration…", "info")
            QApplication.processEvents()
            time.sleep(0.5)
            # If ROM file was loaded earlier, mark success; else keep failing
            self.calibrated = True
            self.lbl_x.setText("X: 12.4 mm")
            self.lbl_y.setText("Y: -3.2 mm")
            self.lbl_z.setText("Z: 45.0 mm")
            self.lbl_err.setText("Error: 0.05 mm")
            self._set_banner("Calibration complete ✔", "ok")
            self.last_action_stack.append(("retry_calibration", None))
        else:
            self._set_banner("Calibration already valid ✔", "ok")

    def _on_scan_batch(self):
        # Simulate batch intake with a progress bump
        for p in range(0, 101, 20):
            self.progress.setValue(p)
            QApplication.processEvents()
            time.sleep(0.05)
        self._set_banner("Batch scan simulated (intake complete).", "ok")
        self.last_action_stack.append(("scan_batch", None))

    def _on_reconstruct(self):
        if self.frames is None:
            self._set_banner("Insufficient data: load ultrasound frames to reconstruct volume.", "error")
            return
        n_slices = self.frames.shape[0]
        if n_slices < 20:
            self._set_banner("Frame count below minimum threshold for 3D reconstruction.", "error")
            return
        # Simulate reconstruction progress
        self._set_banner("Reconstruction started…", "info")
        self.recon_progress = 0
        self.progress.setValue(0)
        self.progress_timer.start(40)  # ticks _tick_progress
        self.last_action_stack.append(("reconstruct", n_slices))

    def _tick_progress(self):
        self.recon_progress += 3
        self.progress.setValue(min(self.recon_progress, 100))
        if self.recon_progress >= 100:
            self.progress_timer.stop()
            self._set_banner("Reconstruction completed successfully ✔", "ok")
            # Show a slice as a “preview” (center slice)
            mid = self.frames.shape[0] // 2
            img = self.frames[mid]
            # apply opacity-like effect as a brightness scale
            alpha = max(0.1, self.opacity_slider.value() / 100.0)
            img = (img.astype(np.float32) * alpha).clip(0, 255).astype(np.uint8)
            qimg = QImage(img.data, img.shape[1], img.shape[0], img.shape[1], QImage.Format_Grayscale8)
            self.viewer.setPixmap(QPixmap.fromImage(qimg))

    def _on_save_slice(self):
        if self.frames is None:
            self._set_banner("No frames loaded to save slice.", "error")
            return
        mid = self.frames.shape[0] // 2
        img = self.frames[mid]
        path, _ = QFileDialog.getSaveFileName(self, "Save slice as PNG", os.getcwd(), "PNG (*.png)")
        if not path:
            return
        # save with Pillow if available; else use Qt
        try:
            from PIL import Image
            Image.fromarray(img).save(path)
        except Exception:
            # fallback via Qt
            qimg = QImage(img.data, img.shape[1], img.shape[0], img.shape[1], QImage.Format_Grayscale8)
            QPixmap.fromImage(qimg).save(path, "PNG")
        self._set_banner(f"Slice saved to {os.path.basename(path)} ✔", "ok")
        self.last_action_stack.append(("save_slice", path))

    def _on_export(self):
        if self.frames is None:
            self._set_banner("No volume to export.", "error")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export volume (NPY)", os.getcwd(), "NumPy array (*.npy)")
        if not path:
            return
        np.save(path, self.frames)
        self._set_banner(f"Volume exported to {os.path.basename(path)} ✔", "ok")
        self.last_action_stack.append(("export_volume", path))

    def _on_undo(self):
        if not self.last_action_stack:
            self._set_banner("Nothing to undo.", "warn")
            return
        action, payload = self.last_action_stack.pop()
        if action in ("load_rom", "retry_calibration"):
            self.calibrated = False
            self.lbl_x.setText("X: —")
            self.lbl_y.setText("Y: —")
            self.lbl_z.setText("Z: —")
            self.lbl_err.setText("Error: —")
            self._set_banner("Calibration undone.", "info")
        elif action == "load_frames":
            self.frames = None
            self._set_placeholder_image()
            self._set_banner("Frames unloaded.", "info")
        elif action == "reconstruct":
            self.progress.setValue(0)
            self._set_placeholder_image()
            self._set_banner("Reconstruction undone.", "info")
        elif action in ("save_slice", "export_volume", "scan_batch", "calibrate_fail"):
            self._set_banner("Undid last action.", "info")
        else:
            self._set_banner("Undo: no handler.", "warn")


def main():
    app = QApplication(sys.argv)
    w = PrototypeApp()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
