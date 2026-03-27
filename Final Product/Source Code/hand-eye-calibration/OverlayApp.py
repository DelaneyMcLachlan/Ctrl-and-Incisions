from sksurgeryutils.common_overlay_apps import OverlayBaseWidget
import cv2
import numpy as np

from CameraController import CameraController
from OverlayRenderer import OverlayRenderer
from ArucoStylusTracker import ArucoStylusTracker


class OverlayApp(OverlayBaseWidget):
    def __init__(self, video_source: int, parentViewer):
        super().__init__(video_source)
        self.parentViewer = parentViewer

        # Sprint 2 modules
        self.camera = CameraController(self.video_source.source)
        self.renderer = OverlayRenderer(self.vtk_overlay_window)

        # Calibration matrices
        self.intMat = None
        self.distCoeffs = None
        self.newCamMat = None

        # -----------------------------
        # ArUco settings
        # -----------------------------
        self.stylus_target_id = 6       # example: 17
        self.valid_stylus_ids = None       # example: [17, 18, 19]

        self.aruco_tracker = ArucoStylusTracker(
            dict_name="DICT_4X4_50",
            marker_length_mm=25.0,
            target_id=self.stylus_target_id,
            valid_ids=self.valid_stylus_ids,
        )

        # Stylus tip offset in marker coordinates
        self.tip_offset_marker = np.array([0.0, 0.0, 0.03], dtype=np.float64)

        # Crosshair appearance
        self.crosshair_size = 18
        self.crosshair_color = (0, 255, 0)
        self.crosshair_thickness = 2

        # Crosshair smoothing
        self.prev_uv = None
        self.smooth_alpha = 0.18
        self.deadband_px = 3

        # Detection throttling
        self.frame_count = 0
        self.detect_every_n_frames = 2

        # Cache last successful marker detection to avoid blinking
        self.last_T_marker_to_cam = None
        self.last_rvec = None
        self.last_tvec = None
        self.last_corners = None
        self.last_ids = None

        # Camera initialization
        try:
            self.camera.open_settings()
        except Exception:
            pass

        try:
            self.camera.set_focus(0)
        except Exception:
            pass

        width = int(self.video_source.source.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.video_source.source.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if width <= 0:
            width = 640
        if height <= 0:
            height = 480

        self.setFixedWidth(width)
        self.setFixedHeight(height)

    def update_view(self):
        image = self.camera.read()

        if image is None:
            image = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(
                image,
                "Webcam not available",
                (120, 240),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 0, 255),
                2,
                cv2.LINE_AA,
            )
        else:
            if (
                self.newCamMat is not None
                and self.intMat is not None
                and self.distCoeffs is not None
            ):
                image = cv2.undistort(
                    image, self.intMat, self.distCoeffs, None, self.newCamMat
                )

            image = self.process_aruco_and_draw_crosshair(image)

        self.renderer.render_frame(image)
        self.handle_capture()

    def process_aruco_and_draw_crosshair(self, image):
        if self.intMat is None or self.distCoeffs is None:
            return image

        self.frame_count += 1
        run_detection = (self.frame_count % self.detect_every_n_frames == 0)

        self.aruco_tracker.set_intrinsics(self.intMat, self.distCoeffs)
        self.aruco_tracker.set_target_id(self.stylus_target_id)
        self.aruco_tracker.set_valid_ids(self.valid_stylus_ids)

        if run_detection:
            (
                image,
                T_marker_to_cam,
                corners,
                ids,
                chosen_corners,
                rvec,
                tvec,
            ) = self.aruco_tracker.process(image)

            # Save last valid marker outlines so boxes remain visible
            if corners is not None and len(corners) > 0:
                self.last_corners = corners
                self.last_ids = ids
            else:
                self.last_corners = None
                self.last_ids = None

            # Save last pose so axes remain visible and do not blink
            if T_marker_to_cam is not None:
                self.last_T_marker_to_cam = T_marker_to_cam
                self.last_rvec = rvec
                self.last_tvec = tvec
            
            else:
            # Active stylus marker disappeared -> clear old pose/crosshair
                self.last_T_marker_to_cam = None
                self.last_rvec = None
                self.last_tvec = None
                self.prev_uv = None

        else:
            # Redraw cached overlays on skipped frames
            if self.last_corners is not None and len(self.last_corners) > 0:
                cv2.aruco.drawDetectedMarkers(image, self.last_corners)

            if self.last_rvec is not None and self.last_tvec is not None:
                cv2.drawFrameAxes(
                    image,
                    self.intMat,
                    self.distCoeffs,
                    self.last_rvec,
                    self.last_tvec,
                    self.aruco_tracker.marker_length * 0.75,
                )

        if self.last_T_marker_to_cam is None:
            return image

        try:
            self.parentViewer.updateArucoPose(self.last_T_marker_to_cam)
        except Exception:
            pass

        tip_marker_h = np.array(
            [
                self.tip_offset_marker[0],
                self.tip_offset_marker[1],
                self.tip_offset_marker[2],
                1.0,
            ],
            dtype=np.float64,
        )

        tip_cam_h = self.last_T_marker_to_cam @ tip_marker_h
        tip_cam = tip_cam_h[:3]

        uv = self.aruco_tracker.project_point(tip_cam)

        if uv is not None:
            uv = np.array(uv, dtype=np.float64)

            if self.prev_uv is None:
                self.prev_uv = uv
            else:
                if np.linalg.norm(uv - self.prev_uv) < self.deadband_px:
                    uv = self.prev_uv

                self.prev_uv = (
                    (1.0 - self.smooth_alpha) * self.prev_uv
                    + self.smooth_alpha * uv
                )

            smooth_uv = (int(self.prev_uv[0]), int(self.prev_uv[1]))
            self.draw_crosshair(image, smooth_uv)

        return image

    def draw_crosshair(self, image, uv):
        u, v = uv
        s = self.crosshair_size
        c = self.crosshair_color
        t = self.crosshair_thickness

        cv2.line(image, (u - s, v), (u + s, v), c, t, cv2.LINE_AA)
        cv2.line(image, (u, v - s), (u, v + s), c, t, cv2.LINE_AA)
        cv2.circle(image, (u, v), 4, c, -1, cv2.LINE_AA)

    def handle_capture(self):
        if not self.parentViewer.capture:
            return

        self.parentViewer.capture = False
        self.parentViewer.handleCapture(self.get_output_frame())

    def open_camera_settings(self):
        try:
            self.video_source.source.set(cv2.CAP_PROP_SETTINGS, 1)
        except Exception:
            pass

    def get_output_frame(self):
        output_frame = self.renderer.get_rendered_numpy()
        output_frame = cv2.cvtColor(output_frame, cv2.COLOR_RGB2BGR)
        return output_frame

    def closeEvent(self, QCloseEvent) -> None:
        super().closeEvent(QCloseEvent)
        self.stop()

    def set_camera_matrix(self, intMat, distCoeffs):
        w = max(1, self.width())
        h = max(1, self.height())

        self.intMat = np.array(intMat, dtype=np.float64)
        self.distCoeffs = np.array(distCoeffs, dtype=np.float64)

        self.newCamMat, _ = cv2.getOptimalNewCameraMatrix(
            self.intMat, self.distCoeffs, (w, h), 1, (w, h)
        )

        self.camera.set_camera_matrix(self.intMat, self.distCoeffs, (w, h))
        self.aruco_tracker.set_intrinsics(self.intMat, self.distCoeffs)

    # -----------------------------------------
    # Easy setters for stylus / valid IDs
    # -----------------------------------------
    def set_stylus_target_id(self, marker_id):
        self.stylus_target_id = marker_id
        self.aruco_tracker.set_target_id(marker_id)

        # Reset pose cache if target changes
        self.last_T_marker_to_cam = None
        self.last_rvec = None
        self.last_tvec = None
        self.prev_uv = None

    def set_valid_stylus_ids(self, valid_ids):
        self.valid_stylus_ids = valid_ids
        self.aruco_tracker.set_valid_ids(valid_ids)

        # Reset corner cache if valid marker set changes
        self.last_corners = None
        self.last_ids = None

    def set_stylus_ids(self, target_id=None, valid_ids=None):
        self.stylus_target_id = target_id
        self.valid_stylus_ids = valid_ids

        self.aruco_tracker.set_target_id(target_id)
        self.aruco_tracker.set_valid_ids(valid_ids)

        # Reset caches
        self.last_T_marker_to_cam = None
        self.last_rvec = None
        self.last_tvec = None
        self.last_corners = None
        self.last_ids = None
        self.prev_uv = None