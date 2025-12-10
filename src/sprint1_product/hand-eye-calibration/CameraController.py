import cv2

class CameraController:
    def __init__(self, source):
        self.cap = source

        self.intMat = None
        self.distCoeffs = None
        self.newCamMat = None

    def open_settings(self):
        """
        Open the native camera settings window if available
        """
        self.cap.set(cv2.CAP_PROP_SETTINGS, 1)

    def set_focus(self, value=0):
        """
        Set camera focus
        """
        self.cap.set(cv2.CAP_PROP_FOCUS, value)

    def read(self):
        """
        Read a frame and undistort it if calibration is active
        """
        ok, frame = self.cap.read()
        if not ok:
            return None
        return self.undistort(frame)

    def undistort(self, frame):
        """
        Undistort frame if the calibration matrices are set
        """
        if self.newCamMat is None:
            return frame
        return cv2.undistort(
            frame, self.intMat, self.distCoeffs, None, self.newCamMat
        )
    
    def set_camera_matrix(self, intMat, distCoeffs, size):
        """
        Set intrinsics + distortion and compute optimal new camera matrix
        """
        w, h = size
        self.intMat = intMat
        self.distCoeffs = distCoeffs
        self.newCamMat, _ = cv2.getOptimalNewCameraMatrix(
            intMat, distCoeffs, (w, h), 1, (w, h)
        )

