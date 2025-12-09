import numpy as np

def solve_hand_eye_p2l(X, Q, A, tol=0.001):
    """
    Solves for the extrinsic matrix using Point-to-Line registration.
    
    Args:
        X (3xn): 3D coordinates (tracker space)
        Q (2xn): 2D pixel locations (image space)
        A (3x3): Camera intrinsic matrix
        tol: Tolerance for convergence
        
    Returns:
        R, t: Rotation matrix (3x3) and translation vector (3x1)
    """

    n = Q.shape[1]
    e = np.ones(n)
    J = np.identity(n) - (np.divide((np.transpose(e) * e), n))
    
    # Normalize 2D pixel coordinates
    Q_norm = np.linalg.inv(A) @ np.vstack((Q, e))
    
    Y = np.empty((3, 0))
    for i in range(n):
        x = Q_norm[:, i]
        y = np.linalg.norm(x)
        z = x / y
        Y = np.hstack((Y, z.reshape(3, 1)))

    Q_vectors = Y
    err = np.inf
    E_old = 1000 * np.ones((3, n))
    
    while err > tol:
        a = Y @ J @ X.T.conj()
        U, S, V, = np.linalg.svd(a)

        # Get rotation
        R = U @ np.array([[1, 0, 0], [0, 1, 0], [0, 0, np.linalg.det(U @ V)]]) @ V 

        # Get translation
        T = Y - R @ X
        t = ([])
        for i in range(np.shape(Y)[0]): # could use n?
            t = np.append(t, np.mean(T[i]))
        t = np.reshape(t, (np.shape(Y)[0], 1))

        # Reprojection
        h = R @ X + t * e
        H = ([])
        for i in range(np.shape(Q)[1]):
            H = np.append(H, np.dot(h[:, i], Q[:, i]))
        Y = np.matlib.repmat(H, 3, 1) * Q

        # Get reprojection error
        E = Y - R @ X - t * e
        err = np.linalg.norm(E - E_old, 'fro')
        E_old = E
    
    return R, t

def compute_reprojection_error(ext_mtx, pts3d, pts2d, int_mtx):
    """Calculates pixel error for validation."""
    n = pts3d.shape[1]
    px_errs = []
    projected_px = []

    for k in range(n):
        pt_3d = np.vstack((pts3d[:, k].reshape(3,1), 1))
        
        # Transform to camera space
        cam_pt = ext_mtx @ pt_3d
        cam_pt = cam_pt[:3] / cam_pt[2] # Normalize Z
        
        # Project to pixels
        proj = int_mtx @ cam_pt
        
        # Calculate error
        actual = pts2d[:, k].reshape(2, 1)
        # Note: proj is 3x1 (homogeneous), actual is 2x1
        err_vec = proj[0:2] - actual
        error = np.linalg.norm(err_vec)
        
        px_errs.append(error)
        projected_px.append(proj)
        
    return projected_px, np.array(px_errs)

def compute_distance_error(ext_mtx, pts3d, pts2d, int_mtx):
    """
    Computes the distance error between the projected 3D point and the 3D ray 
    from the camera center through the 2D pixel.
    """
    n = pts3d.shape[1]
    
    # 1. Convert 2D pixels to 3D rays (in camera frame)
    # Append 1 to make homogeneous [u, v, 1]
    pts2d_h = np.vstack((pts2d, np.ones(n)))
    # Apply inverse intrinsic matrix: K_inv @ [u, v, 1]
    rays_cam = np.linalg.inv(int_mtx) @ pts2d_h
    # Normalize rays to be unit vectors
    rays_cam_norm = rays_cam / np.linalg.norm(rays_cam, axis=0)

    # 2. Transform 3D tracker points to Camera Frame
    pts3d_h = np.vstack((pts3d, np.ones(n))) # [x, y, z, 1]
    pts3d_cam = ext_mtx @ pts3d_h # 4xN
    pts3d_cam = pts3d_cam[:3, :] # Drop 4th row -> 3xN

    # 3. Compute Error
    dist_errs = []
    for i in range(n):
        # Vector P (point in space)
        P = pts3d_cam[:, i]
        P_mag = np.linalg.norm(P)
        
        # Unit Vector r (ray direction)
        r = rays_cam_norm[:, i]
        
        # Angle between P and r
        # dot product: a . b = |a||b|cos(theta) -> cos(theta) = (P . r) / |P| (since |r|=1)
        dot_val = np.dot(P, r)
        cos_theta = np.clip(dot_val / P_mag, -1.0, 1.0)
        theta = np.arccos(cos_theta)
        
        # Distance error = |P| * tan(theta)
        # (The perpendicular distance from the point to the ray)
        d_err = P_mag * np.tan(theta)
        dist_errs.append(d_err)

    return np.array(dist_errs)

def compute_angular_error(ext_mtx, pts3d, pts2d, int_mtx):
    """
    Computes the angular error (in degrees) between the vector to the 
    3D point and the ray through the 2D pixel.
    """
    n = pts3d.shape[1]
    
    # 1. Get Rays (same as above)
    pts2d_h = np.vstack((pts2d, np.ones(n)))
    rays_cam = np.linalg.inv(int_mtx) @ pts2d_h
    rays_cam_norm = rays_cam / np.linalg.norm(rays_cam, axis=0)

    # 2. Get Transformed Points (same as above)
    pts3d_h = np.vstack((pts3d, np.ones(n)))
    pts3d_cam = ext_mtx @ pts3d_h
    pts3d_cam = pts3d_cam[:3, :]

    # 3. Compute Angle
    ang_errs = []
    for i in range(n):
        P = pts3d_cam[:, i]
        r = rays_cam_norm[:, i]
        
        cos_theta = np.dot(P, r) / (np.linalg.norm(P) * 1.0)
        cos_theta = np.clip(cos_theta, -1.0, 1.0)
        theta = np.arccos(cos_theta)
        
        ang_errs.append(np.degrees(theta))

    return np.array(ang_errs)