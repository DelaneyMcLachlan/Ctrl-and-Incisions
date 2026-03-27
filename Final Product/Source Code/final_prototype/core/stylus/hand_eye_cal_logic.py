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
    """
    Orchestrator: Coordination between images, user input, and math.
    Called by QVTKViewer.py -> runHECal()
    """
    points_3d = []
    points_2d = []
    
    for i, frame_path in enumerate(frames):
        img = cv2.imread(frame_path)
        if img is None:
            print(f"Error: Could not read image {frame_path}")
            continue

        # 1. Try Automatic Detection (using the new image_processing module)
        center, radius = detect_green_stylus_circle(img, intMtx, distCoeffs)
        
        # 2. If Automatic fails, fallback to Manual (original code behavior)
        if center is None:
            print(f"No circles detected in frame {i}. Switching to manual segmentation.")
            
            # --- Manual Click Logic ---
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
                if k == 27: # Escape key
                    break
            cv2.destroyAllWindows()
            
            if manual_points:
                # Use the last clicked point
                center = manual_points[-1]

        # 3. Store valid points
        if center is not None:
            points_2d.append(center)
            # transforms[i] is [x, y, z] of the stylus from the tracker
            points_3d.append(transforms[i])
        else:
            print(f"Skipping frame {i}: No point defined.")

    if not points_2d:
        print("Error: No valid points collected. Cannot calibrate.")
        # Return identity/zeros to prevent crash, or raise error
        return np.eye(4), [], [], [], []

    # Convert lists to NumPy arrays for the solver (Expected format: 3xN and 2xN)
    points_3d = np.array(points_3d).T 
    points_2d = np.array(points_2d).T 
    
    # 4. Solve (using the new calibration_solver module)
    R, t = solve_hand_eye_p2l(points_3d, points_2d, intMtx)
    extrinsic_matrix = np.vstack((np.hstack((R, t)), [0, 0, 0, 1]))
    
    # 5. Validate
    # We use the solver's validation function to get pixel errors
    projected_px, px_errs = compute_reprojection_error(extrinsic_matrix, points_3d, points_2d, intMtx)

    # Distance Error
    dist_errs = compute_distance_error(extrinsic_matrix, points_3d, points_2d, intMtx)
    
    # Angular Error
    ang_errs = compute_angular_error(extrinsic_matrix, points_3d, points_2d, intMtx)

    return extrinsic_matrix, points_2d, px_errs, dist_errs, ang_errs
    
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
    # Termination criteria
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    # Prepare object points (0,0,0), (1,0,0), ... based on 9x6 board
    # 23mm square size assumed from original code
    objp = np.zeros((9 * 6, 3), np.float32)
    objp[:, :2] = np.mgrid[0:9, 0:6].T.reshape(-1, 2) * 23 

    objPts = [] # 3D points in real world space
    imgPts = [] # 2D points in image plane
    
    print(f"Processing {len(chessboardFiles)} images for intrinsic calibration...")

    for fpath in chessboardFiles:
        img = cv2.imread(fpath)
        if img is None: 
            continue
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Find checkerboard corners
        ret, corners = cv2.findChessboardCorners(gray, (9, 6), None)
        
        if ret:
            objPts.append(objp)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            imgPts.append(corners)
        else:
            print(f"Warning: Chessboard not found in {os.path.basename(fpath)}")

    if not imgPts:
        print("Error: No valid chessboards found. Cannot calibrate.")
        return np.eye(3), np.zeros((1, 5))

    # Calibrate
    ret, intMtx, distCoeffs, rvecs, tvecs = cv2.calibrateCamera(objPts, imgPts, gray.shape[::-1], None, None)
    
    print("Intrinsic Matrix:\n", intMtx)
    print("Distortion Coefficients:\n", distCoeffs)
    
    return intMtx, distCoeffs