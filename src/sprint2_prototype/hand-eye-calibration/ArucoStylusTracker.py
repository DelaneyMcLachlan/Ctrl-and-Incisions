import cv2
import numpy as np


class ArucoStylusTracker:
    def __init__(
        self,
        dict_name="DICT_4X4_50",
        marker_length_mm=25.0,
        target_id=None,
        valid_ids=None,
    ):
        self.marker_length = marker_length_mm / 1000.0  # meters
        self.target_id = target_id
        self.valid_ids = set(valid_ids) if valid_ids is not None else None

        self.K = None
        self.dist = None

        aruco = cv2.aruco
        dictionary = aruco.getPredefinedDictionary(getattr(aruco, dict_name))
        params = aruco.DetectorParameters()
        self.detector = aruco.ArucoDetector(dictionary, params)

    def set_intrinsics(self, K, dist):
        self.K = np.array(K, dtype=np.float64)
        self.dist = np.array(dist, dtype=np.float64)

    def set_target_id(self, target_id):
        self.target_id = target_id

    def set_valid_ids(self, valid_ids):
        self.valid_ids = set(valid_ids) if valid_ids is not None else None

    def process(self, frame):
        """
        Detect markers, draw boxes for all valid markers, and draw axes only
        for the selected target marker.

        Returns:
            frame,
            T_marker_to_cam,
            filtered_corners,
            filtered_ids,
            chosen_corners,
            rvec,
            tvec
        """

        if self.K is None:
            return frame, None, None, None, None, None, None

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = self.detector.detectMarkers(gray)

        if ids is None or len(corners) == 0:
            return frame, None, None, None, None, None, None

        ids = ids.flatten()

        # Keep only allowed markers if valid_ids is provided
        filtered_corners = []
        filtered_ids = []

        for c, marker_id in zip(corners, ids):
            if self.valid_ids is None or marker_id in self.valid_ids:
                filtered_corners.append(c)
                filtered_ids.append(int(marker_id))

        if len(filtered_corners) == 0:
            return frame, None, None, None, None, None, None

        filtered_ids = np.array(filtered_ids, dtype=np.int32)

        # Draw boxes only. No text IDs are manually drawn.
        cv2.aruco.drawDetectedMarkers(frame, filtered_corners)

        # Select marker for pose
        idx = 0
        if self.target_id is not None:
            matches = np.where(filtered_ids == self.target_id)[0]
            if len(matches) == 0:
                return frame, None, filtered_corners, filtered_ids, None, None, None
            idx = matches[0]

        chosen_corners = filtered_corners[idx]

        rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
            [chosen_corners],
            self.marker_length,
            self.K,
            self.dist,
        )

        rvec = rvecs[0]
        tvec = tvecs[0]

        # Draw axes only for chosen target
        cv2.drawFrameAxes(
            frame,
            self.K,
            self.dist,
            rvec,
            tvec,
            self.marker_length * 0.75,
        )

        # Convert to 4x4 transform
        R, _ = cv2.Rodrigues(rvec)
        T = np.eye(4, dtype=np.float64)
        T[:3, :3] = R
        T[:3, 3] = tvec.flatten()

        return frame, T, filtered_corners, filtered_ids, chosen_corners, rvec, tvec

    def project_point(self, pt_cam):
        if self.K is None:
            return None

        X, Y, Z = pt_cam
        if Z <= 0:
            return None

        fx = self.K[0, 0]
        fy = self.K[1, 1]
        cx = self.K[0, 2]
        cy = self.K[1, 2]

        u = fx * X / Z + cx
        v = fy * Y / Z + cy

        return int(u), int(v)