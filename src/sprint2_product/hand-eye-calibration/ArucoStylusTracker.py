import cv2
import numpy as np

class ArucoStylusTracker:

    def __init__(self,
                 dict_name="DICT_4X4_50",
                 marker_length_mm=25.0,
                 target_id=None):

        self.marker_length = marker_length_mm / 1000.0  # meters
        self.target_id = target_id

        self.K = None
        self.dist = None

        aruco = cv2.aruco
        dictionary = aruco.getPredefinedDictionary(getattr(aruco, dict_name))
        params = aruco.DetectorParameters()
        self.detector = aruco.ArucoDetector(dictionary, params)

    def set_intrinsics(self, K, dist):
        self.K = np.array(K, dtype=np.float64)
        self.dist = np.array(dist, dtype=np.float64)

    def process(self, frame):

        if self.K is None:
            return frame, None

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = self.detector.detectMarkers(gray)

        if ids is None:
            return frame, None

        ids = ids.flatten()
        idx = 0

        if self.target_id is not None:
            matches = np.where(ids == self.target_id)[0]
            if len(matches) == 0:
                return frame, None
            idx = matches[0]

        chosen_corners = corners[idx]
        rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
            [chosen_corners],
            self.marker_length,
            self.K,
            self.dist
        )

        rvec = rvecs[0]
        tvec = tvecs[0]

        # Draw marker + axes
        cv2.aruco.drawDetectedMarkers(frame, [chosen_corners])
        cv2.drawFrameAxes(frame, self.K, self.dist, rvec, tvec, self.marker_length * 0.75)

        # Convert to 4x4 transform
        R, _ = cv2.Rodrigues(rvec)
        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = tvec.flatten()

        return frame, T

    def project_point(self, pt_cam):

        X, Y, Z = pt_cam
        if Z <= 0:
            return None

        fx = self.K[0,0]
        fy = self.K[1,1]
        cx = self.K[0,2]
        cy = self.K[1,2]

        u = fx * X/Z + cx
        v = fy * Y/Z + cy

        return int(u), int(v)

