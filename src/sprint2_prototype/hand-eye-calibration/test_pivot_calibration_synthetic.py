import numpy as np
import vtk


def rotation_matrix_from_euler(rx_deg, ry_deg, rz_deg):
    rx = np.deg2rad(rx_deg)
    ry = np.deg2rad(ry_deg)
    rz = np.deg2rad(rz_deg)

    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(rx), -np.sin(rx)],
        [0, np.sin(rx),  np.cos(rx)]
    ])

    Ry = np.array([
        [ np.cos(ry), 0, np.sin(ry)],
        [0, 1, 0],
        [-np.sin(ry), 0, np.cos(ry)]
    ])

    Rz = np.array([
        [np.cos(rz), -np.sin(rz), 0],
        [np.sin(rz),  np.cos(rz), 0],
        [0, 0, 1]
    ])

    return Rz @ Ry @ Rx


def make_transform(R, t):
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = t.reshape(3)
    return T


class SyntheticPivotTester:
    def __init__(self):
        self.pivotCalArray = vtk.vtkDoubleArray()
        self.pivotCalArray.SetNumberOfComponents(16)

        self.pivotCalMat = np.eye(4)
        self.minimizer = vtk.vtkAmoebaMinimizer()
        self.minimizer.SetFunction(self.minimizerFunc)

    def minimizerFunc(self):
        """
        Same style as your QVTKViewer minimizer function.
        Minimizes spread of transformed tip points.
        """
        n = self.pivotCalArray.GetNumberOfTuples()

        x = self.minimizer.GetParameterValue("x")
        y = self.minimizer.GetParameterValue("y")
        z = self.minimizer.GetParameterValue("z")

        sx = sy = sz = 0.0
        sxx = syy = szz = 0.0

        for i in range(n):
            mat = self.pivotCalArray.GetTuple(i)
            mat = np.reshape(mat, (4, 4))

            nx = mat[0, 0] * x + mat[0, 1] * y + mat[0, 2] * z + mat[0, 3]
            ny = mat[1, 0] * x + mat[1, 1] * y + mat[1, 2] * z + mat[1, 3]
            nz = mat[2, 0] * x + mat[2, 1] * y + mat[2, 2] * z + mat[2, 3]

            sx += nx
            sy += ny
            sz += nz

            sxx += nx * nx
            syy += ny * ny
            szz += nz * nz

        if n > 1:
            r = np.sqrt(
                (sxx - sx * sx / n) / (n - 1) +
                (syy - sy * sy / n) / (n - 1) +
                (szz - sz * sz / n) / (n - 1)
            )
        else:
            r = 0.0

        self.minimizer.SetFunctionValue(r)

    def doPivotCal(self):
        self.pivotCalMat = np.eye(4)

        self.minimizer.SetParameterValue("x", 0.0)
        self.minimizer.SetParameterScale("x", 1000.0)

        self.minimizer.SetParameterValue("y", 0.0)
        self.minimizer.SetParameterScale("y", 1000.0)

        self.minimizer.SetParameterValue("z", 0.0)
        self.minimizer.SetParameterScale("z", 1000.0)

        self.minimizer.Minimize()
        minimum = self.minimizer.GetFunctionValue()

        self.pivotCalMat[0, 3] = self.minimizer.GetParameterValue("x")
        self.pivotCalMat[1, 3] = self.minimizer.GetParameterValue("y")
        self.pivotCalMat[2, 3] = self.minimizer.GetParameterValue("z")

        return minimum


def generate_synthetic_pivot_data(
    true_tip_offset,
    fixed_tip_world,
    num_samples=40,
    translation_noise_mm=0.0
):
    """
    Generate tracker transforms T_i such that:
        R_i * true_tip_offset + t_i = fixed_tip_world

    This simulates pivoting the stylus around a fixed tip point.
    """
    transforms = []

    # A mix of different rotations
    angle_sets = [
        (-40, -30, -20), (-35, -10, 15), (-30, 20, 40), (-25, 35, -10),
        (-20, -25, 25), (-15, 10, -35), (-10, 25, 15), (-5, -35, 5),
        (0, 0, 0), (5, 15, -20), (10, -20, 35), (15, 30, -15),
        (20, -15, 10), (25, 5, 25), (30, -30, -25), (35, 20, 30),
        (40, 10, -5), (45, -10, 20), (50, 25, -30), (55, -25, 10),
    ]

    while len(angle_sets) < num_samples:
        angle_sets.extend(angle_sets)

    angle_sets = angle_sets[:num_samples]

    for rx, ry, rz in angle_sets:
        R = rotation_matrix_from_euler(rx, ry, rz)

        # enforce fixed tip world position
        t = fixed_tip_world.reshape(3, 1) - R @ true_tip_offset.reshape(3, 1)

        if translation_noise_mm > 0.0:
            t += np.random.normal(0.0, translation_noise_mm, size=(3, 1))

        T = make_transform(R, t)
        transforms.append(T)

    return transforms


def verify_fixed_tip_points(transforms, estimated_tip):
    pts = []
    for T in transforms:
        p = T[:3, :3] @ estimated_tip.reshape(3, 1) + T[:3, 3].reshape(3, 1)
        pts.append(p.reshape(3))
    pts = np.array(pts)

    mean_pt = pts.mean(axis=0)
    rms = np.sqrt(np.mean(np.sum((pts - mean_pt) ** 2, axis=1)))
    return pts, mean_pt, rms


def main():
    np.set_printoptions(suppress=True, precision=6)

    print("=" * 70)
    print("SYNTHETIC PIVOT CALIBRATION TEST")
    print("=" * 70)

    # Known ground truth tip offset in stylus coordinates (mm)
    true_tip_offset = np.array([[12.5], [-8.0], [145.0]])

    # Fixed pivot point in world coordinates (mm)
    fixed_tip_world = np.array([[250.0], [100.0], [300.0]])

    print("\nGround truth:")
    print("True stylus tip offset [x, y, z] (mm):")
    print(true_tip_offset.reshape(3))
    print("Fixed world pivot point [x, y, z] (mm):")
    print(fixed_tip_world.reshape(3))

    transforms = generate_synthetic_pivot_data(
        true_tip_offset=true_tip_offset,
        fixed_tip_world=fixed_tip_world,
        num_samples=40,
        translation_noise_mm=0.0
    )

    print(f"\nGenerated {len(transforms)} synthetic tracker transforms.")

    print("\nFirst 3 synthetic transforms:")
    for i, T in enumerate(transforms[:3]):
        print(f"\nTransform {i + 1}:")
        print(T)

    tester = SyntheticPivotTester()

    for T in transforms:
        tester.pivotCalArray.InsertNextTuple(T.reshape(16))

    print("\nInserted samples into pivotCalArray:")
    print("Number of tuples:", tester.pivotCalArray.GetNumberOfTuples())

    minimum = tester.doPivotCal()

    estimated_tip = tester.pivotCalMat[:3, 3].reshape(3, 1)
    tip_error = np.linalg.norm(estimated_tip - true_tip_offset)

    print("\nSolved pivot calibration matrix:")
    print(tester.pivotCalMat)

    print("\nRecovered stylus tip offset [x, y, z] (mm):")
    print(estimated_tip.reshape(3))

    print("\nError compared to ground truth:")
    print("Absolute vector error (mm):", (estimated_tip - true_tip_offset).reshape(3))
    print("Euclidean tip error (mm):", tip_error)

    print("\nMinimizer residual:")
    print(minimum)

    pts, mean_pt, rms = verify_fixed_tip_points(transforms, estimated_tip)

    print("\nBack-projected world tip points using recovered offset:")
    print("Mean world tip position (mm):", mean_pt)
    print("RMS spread around mean (mm):", rms)

    print("\nExpected fixed world tip position (mm):")
    print(fixed_tip_world.reshape(3))

    world_tip_error = np.linalg.norm(mean_pt.reshape(3, 1) - fixed_tip_world)
    print("Mean fixed-point error (mm):", world_tip_error)

    print("\nPASS / FAIL CHECKS")
    pass_tip = tip_error < 1e-3
    pass_rms = rms < 1e-3
    pass_world = world_tip_error < 1e-3

    print("Tip offset recovered correctly:", pass_tip)
    print("Recovered tip stays fixed in world:", pass_rms)
    print("Recovered fixed world point is correct:", pass_world)

    if pass_tip and pass_rms and pass_world:
        print("\nRESULT: PASS")
        print("Your pivot calibration math is working correctly on synthetic data.")
    else:
        print("\nRESULT: FAIL")
        print("The pivot calibration math did not recover the expected result.")


if __name__ == "__main__":
    main()