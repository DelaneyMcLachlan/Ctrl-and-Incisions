import threading
import time
import numpy as np
import math

class FakeTracker:
    """
    Continuously generates fake (x, y, z) data in a background thread.
    """
    def __init__(self, update_rate=0.05):  # update every 50 ms
        self.running = False
        self.update_rate = update_rate
        self.current_point = np.array([0.0, 0.0, 0.0])
        self.thread = None
        self.t = 0.0

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

    def _run(self):
        """The background loop that updates fake data."""
        while self.running:
            # Example: a looping 3D Lissajous-like curve
            self.t += self.update_rate

            x = 100 * math.cos(self.t)
            y = 100 * math.sin(self.t)
            z = 50 * math.sin(self.t * 0.5)

            self.current_point = np.array([x, y, z])

            time.sleep(self.update_rate)

    def get_point(self):
        """Return the latest generated (x,y,z) point."""
        return self.current_point.copy()
# 