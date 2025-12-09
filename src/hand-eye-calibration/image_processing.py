import cv2
import numpy as np

def detect_green_stylus_circle(img, int_mtx, dist_coeffs):
    """
    Detects the green stylus tip in a single image.
    Returns center (x, y) and radius, or None if failed.
    """
    h, w = img.shape[:2]
    new_cam_mtx, _ = cv2.getOptimalNewCameraMatrix(int_mtx, dist_coeffs, (w, h), 1, (w, h))
    undistorted = cv2.undistort(img, int_mtx, dist_coeffs, None, new_cam_mtx)

    # Color segmentation
    hsv = cv2.cvtColor(undistorted, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (30, 50, 0), (80, 255, 255))
    target = cv2.bitwise_and(undistorted, undistorted, mask=mask)
    
    gray = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY)
    blurred = cv2.medianBlur(binary, 25)
    blurred = cv2.blur(blurred, (10, 10))

    circles = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT, 0.1, 1000, 
        param1=50, param2=30, minRadius=0, maxRadius=50
    )

    if circles is not None:
        # Return the first detected circle (x, y, r)
        c = circles[0, 0]
        return (c[0], c[1]), c[2]
    
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