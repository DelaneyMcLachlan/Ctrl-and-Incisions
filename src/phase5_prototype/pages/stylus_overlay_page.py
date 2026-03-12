from sksurgeryutils.common_overlay_apps import OverlayBaseWidget
import cv2
import numpy as np

from CameraController import CameraController
from OverlayRenderer import OverlayRenderer
from ArucoStylusTracker import ArucoStylusTracker   # NEW


# Defines video feed widget with VTK overlay
class OverlayApp(OverlayBaseWidget):

    def __init__(self, video_source: int, parentViewer):
        super().__init__(video_source)
        self.parentViewer = parentViewer

        # modules
        self.camera = CameraController(self.video_source.source)
        self.renderer = OverlayRenderer(self.vtk_overlay_window)

        # ArUco tracker
        self.aruco = ArucoStylusTracker()

        self.K = None
        self.dist = None

        # camera initialization
        self.camera.open_settings()
        self.camera.set_focus(0)

        # set widget size
        w = int(self.video_source.source.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.video_source.source.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.setFixedWidth(w)
        self.setFixedHeight(h)

    def update_view(self):
        """
        Reads, processes, and displays video frames
        """
        frame = self.camera.read()
        if frame is None:
            return

        T = None

        # ---------- PART 2 & 3: ARUCO TRACKING + SHAPES ----------
        if self.K is not None:
            frame, T = self.aruco.process(frame)
            


            if T is not None:
                # Update VTK stylus transform
                self.parentViewer.updateArucoPose(T)

                # Project stylus tip and draw crosshair
                tip_cam = self.parentViewer.getStylusTipInCameraFrame(T)
                
                if tip_cam is not None:
                    uv = self.aruco.project_point(tip_cam)
                    if uv is not None:
                        cv2.drawMarker(
                            frame,
                            uv,
                            (0, 255, 0),
                            cv2.MARKER_CROSS,
                            markerSize = 20,
                            thickness =2
                            
                        )
        # -------------------------------------------------------

        self.renderer.render_frame(frame)
        self.handle_capture()

    def handle_capture(self):
        """
        Triggered capture from parent viewer
        """
        if not self.parentViewer.capture:
            return

        self.parentViewer.capture = False
        frame = self.get_output_frame()
        self.parentViewer.handleCapture(frame)

    def set_camera_matrix(self, intMat, distCoeffs):
        """
        Pass calibration matrices to CameraController and ArUco
        """
        size = (self.width(), self.height())
        self.camera.set_camera_matrix(intMat, distCoeffs, size)

        self.K = intMat
        self.dist = distCoeffs
        self.aruco.set_intrinsics(intMat, distCoeffs)

    def get_output_frame(self):
        """
        Converts frame to NumPy array and returns it
        """
        frame = self.renderer.get_rendered_numpy()
        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    def closeEvent(self, QCloseEvent) -> None:
        """Handles window close"""
        super().closeEvent(QCloseEvent)
        self.stop()
