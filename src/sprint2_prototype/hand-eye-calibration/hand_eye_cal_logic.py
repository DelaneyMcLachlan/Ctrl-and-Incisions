import numpy as np
import cv2
import os

try:
    from .core.image_processing import detect_green_stylus_circle
    from .core.calibration_solver import (
        solve_hand_eye_p2l, 
        compute_reprojection_error,
        compute_distance_error,
        compute_angular_error   
    )
except ImportError:
    # Fallback if files are not found
    from calibration_solver import (
        solve_hand_eye_p2l, 
        compute_reprojection_error,
        compute_distance_error,
        compute_angular_error
    )
    from image_processing import detect_green_stylus_circle

def analyzeFrames(frames, transforms, intMtx, distCoeffs):
    points_3d = []
    points_2d = []

    if len(frames) == 0:
        print("Error: No frames provided.")
        return np.eye(4), [], [], [], []

    sample_img = cv2.imread(frames[0])
    if sample_img is None:
        print(f"Error: Could not read first image {frames[0]}")
        return np.eye(4), [], [], [], []

    h, w = sample_img.shape[:2]
    newCameraMtx, roi = cv2.getOptimalNewCameraMatrix(
        intMtx, distCoeffs, (w, h), 1, (w, h)
    )

    for i, frame_path in enumerate(frames):
        img = cv2.imread(frame_path)
        if img is None:
            print(f"Error: Could not read image {frame_path}")
            continue

        center, radius = detect_green_stylus_circle(img, intMtx, distCoeffs)

        if center is None:
            print(f"No circles detected in frame {i}. Switching to manual segmentation.")

            manual_points = []

            def click_event(event, x, y, flags, param):
                if event == cv2.EVENT_LBUTTONDOWN:
                    cv2.circle(img, (x, y), 2, (0, 255, 255), -1)
                    manual_points.append((x, y))
                    cv2.imshow("Segment Image", img)

            cv2.namedWindow("Segment Image")
            cv2.setMouseCallback("Segment Image", click_event)

            print("Click the center of the sphere. Press ESC when done.")
            while True:
                cv2.imshow("Segment Image", img)
                k = cv2.waitKey(1) & 0xFF
                if k == 27:
                    break
            cv2.destroyAllWindows()

            if manual_points:
                circle = cv2.minEnclosingCircle(np.array(manual_points, dtype=np.float32))
                center = circle[0]

        if center is not None:
            # Sprint 1 tracking-loss skip
            if len(points_3d) > 0 and points_3d[-1][0] == transforms[i][0]:
                print(f"Spatial tracking lost in frame {i}")
            else:
                points_2d.append(center)
                points_3d.append(transforms[i])
        else:
            print(f"Skipping frame {i}: No point defined.")

    if not points_2d:
        print("Error: No valid points collected. Cannot calibrate.")
        return np.eye(4), [], [], [], []

    points_3d = np.array(points_3d).T
    points_2d = np.array(points_2d).T

    # Sprint 1 math: solve with newCameraMtx
    R, t = solve_hand_eye_p2l(points_3d, points_2d, newCameraMtx)
    extrinsic_matrix = np.vstack((np.hstack((R, t)), [0, 0, 0, 1]))

    print("Extrinsic Matrix:", extrinsic_matrix)

    projected_px, px_errs = compute_reprojection_error(
        extrinsic_matrix, points_3d, points_2d, intMtx
    )
    dist_errs = compute_distance_error(
        extrinsic_matrix, points_3d, points_2d, intMtx
    )
    ang_errs = compute_angular_error(
        extrinsic_matrix, points_3d, points_2d, intMtx
    )

    px_errs = np.array(px_errs).reshape(-1, 1)
    dist_errs = np.array(dist_errs).reshape(-1, 1)
    ang_errs = np.array(ang_errs).reshape(-1, 1)

    # IMPORTANT: return projected pixels, not points_2d
    return extrinsic_matrix, projected_px, px_errs, dist_errs, ang_errs
    
    # Thw following is for testing if needed, the distance and angular error calculations are defaulted to zero so the UI continues to work

    # Generate placeholder errors for Distance and Angular to match original return signature
    # (The original code calculated these. If you need them for your CSV output, 
    # we can move those functions to the solver as well. For now, we return zeros to keep the UI running.)
    # dist_errs = np.zeros(len(px_errs)) 
    # ang_errs = np.zeros(len(px_errs))

    # return extrinsic_matrix, points_2d, px_errs, dist_errs, ang_errs

def distortionCalibration(chessboardFiles):
    """
    Runs intrinsic calibration on a set of chessboard image files.
    Called by QVTKViewer.py -> runIntCal()
    """
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    objp = np.zeros((9 * 6, 3), np.float32)
    objp[:, :2] = np.mgrid[0:9, 0:6].T.reshape(-1, 2) * 23

    objPts = []
    imgPts = []

    for fpath in chessboardFiles:
        img = cv2.imread(fpath)
        if img is None:
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, (9, 6), None)

        if ret:
            objPts.append(objp)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            imgPts.append(corners2)

            # Sprint 1 style visual behaviour
            cornersdrawn = cv2.drawChessboardCorners(img.copy(), (9, 6), corners2, ret)
            cv2.imshow(f"Chessbaord - {fpath[-13:]}", cornersdrawn)
            cv2.waitKey(0)
        else:
            print(f"Warning: Chessboard not found in {os.path.basename(fpath)}")

    if not imgPts:
        print("Error: No valid chessboards found. Cannot calibrate.")
        return np.eye(3), np.zeros((1, 5))

    ret, intMtx, distCoeffs, rvecs, tvecs = cv2.calibrateCamera(
        objPts, imgPts, gray.shape[::-1], None, None
    )

    # Match Sprint 1 print style
    print("distortion coefficients:", distCoeffs)
    print("intMtx:", intMtx)
    print("distCoeffs:", distCoeffs)

    return intMtx, distCoeffs