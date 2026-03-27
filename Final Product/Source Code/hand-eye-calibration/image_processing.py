import cv2
import numpy as np

def detect_green_stylus_circle(img, int_mtx, dist_coeffs):
    h, w = img.shape[:2]
    new_cam_mtx, _ = cv2.getOptimalNewCameraMatrix(
        int_mtx, dist_coeffs, (w, h), 1, (w, h)
    )
    undistorted = cv2.undistort(img, int_mtx, dist_coeffs, None, new_cam_mtx)

    hsv = cv2.cvtColor(undistorted, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (30, 50, 0), (80, 255, 255))
    target = cv2.bitwise_and(undistorted, undistorted, mask=mask)

    gray = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY)
    blurred = cv2.medianBlur(binary, 25)
    blurred = cv2.blur(blurred, (10, 10))

    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        0.1,
        1000,
        param1=50,
        param2=30,
        minRadius=0,
        maxRadius=50
    )

    if circles is not None:
        center = None
        radius = None

        for c in circles[0, :]:
            center = (float(c[0]), float(c[1]))
            radius = float(c[2])

        # Sprint 1 style overlay
        draw_img = undistorted.copy()
        cx = int(round(center[0]))
        cy = int(round(center[1]))
        r = int(round(radius))

        cv2.circle(draw_img, (cx, cy), r, (255, 0, 255), 2)
        cv2.circle(draw_img, (cx, cy), 2, (0, 255, 255), -1)

        cv2.imshow("circle overlay", draw_img)
        cv2.waitKey(0)

        return center, radius

    return None, None

def detect_chessboard(img_path, pattern_size=(9, 6)):
    """
    Finds chessboard corners in an image file.
    """
    img = cv2.imread(img_path)
    if img is None:
        return None, None
        
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(gray, pattern_size, None)
    
    if ret:
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        return corners_refined, gray.shape[::-1]
    
    return None, None