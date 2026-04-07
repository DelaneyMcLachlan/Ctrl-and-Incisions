import threading
import time
import numpy as np
import math


class FakeTracker:
    """
    Continuously generates fake stylus motion in a background thread.

    Supports:
    - get_point(): old translation-only interface
    - get_stylus_matrix(): full 4x4 pivot-like stylus pose
    """
    def __init__(self, update_rate=0.05):  # update every 50 ms
        self.running = False
        self.update_rate = update_rate
        self.current_point = np.array([0.0, 0.0, 0.0])
        self.current_stylus_matrix = np.eye(4)
        self.thread = None
        self.t = 0.0

        # Known fake pivot offset in stylus coordinates (mm)
        # This is what pivot calibration should recover approximately.
        self.tip_offset = np.array([[12.5], [-8.0], [145.0]])

        # Fixed world point that the stylus tip stays on during fake pivoting
        self.fixed_tip_world = np.array([[250.0], [100.0], [300.0]])

    def start(self):
        """Start generating fake data."""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the tracker."""
        self.running = False
        if self.thread:
            self.thread.join()

    def _rotation_matrix_from_euler(self, rx_deg, ry_deg, rz_deg):
        rx = np.deg2rad(rx_deg)
        ry = np.deg2rad(ry_deg)
        rz = np.deg2rad(rz_deg)

        Rx = np.array([
            [1, 0, 0],
            [0, np.cos(rx), -np.sin(rx)],
            [0, np.sin(rx),  np.cos(rx)]
        ])

        Ry = np.array([
            [ np.cos(ry), 0, np.sin(ry)],
            [0, 1, 0],
            [-np.sin(ry), 0, np.cos(ry)]
        ])

        Rz = np.array([
            [np.cos(rz), -np.sin(rz), 0],
            [np.sin(rz),  np.cos(rz), 0],
            [0, 0, 1]
        ])

        return Rz @ Ry @ Rx

    def _run(self):
        """Background loop that updates fake pivot-like stylus data."""
        while self.running:
            self.t += self.update_rate

            # Smooth changing orientation
            rx = 25.0 * math.sin(0.8 * self.t)
            ry = 35.0 * math.sin(0.6 * self.t + 0.5)
            rz = 20.0 * math.sin(1.0 * self.t + 1.2)

            R = self._rotation_matrix_from_euler(rx, ry, rz)

            # Compute translation so the stylus tip stays fixed in world
            t = self.fixed_tip_world - R @ self.tip_offset

            T = np.eye(4)
            T[:3, :3] = R
            T[:3, 3] = t.reshape(3)

            self.current_stylus_matrix = T
            self.current_point = T[:3, 3].copy()

            time.sleep(self.update_rate)

    def get_point(self):
        """Return translation-only point for older code paths."""
        return self.current_point.copy()

    def get_stylus_matrix(self):
        """Return the latest 4x4 stylus pose."""
        return self.current_stylus_matrix.copy()