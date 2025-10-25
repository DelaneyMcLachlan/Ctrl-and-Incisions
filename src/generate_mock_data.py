# generate_mock_data.py
import json
import numpy as np

# ---- Create mock ROM (calibration) file ----
rom = {
    "camera_id": "CAM_1234",
    "probe_id": "PROBE_42",
    "calibration_status": "valid",
    "hand_eye_matrix": [
        [0.9998, 0.0012, 0.019,  0.5],
        [-0.0011, 0.9999, 0.012, 0.2],
        [-0.019, -0.012, 0.9997, 0.1],
        [0, 0, 0, 1]
    ]
}
with open("mock_rom.json", "w") as f:
    json.dump(rom, f, indent=2)

# ---- Create mock ultrasound frames (grayscale) ----
# 50 slices, enough to "succeed" reconstruction; change to < 15 to force failure
slices = 50
H, W = 256, 256
frames = np.random.randint(0, 255, (slices, H, W), dtype=np.uint8)
np.save("mock_frames.npy", frames)

print("✔ mock_rom.json and mock_frames.npy created.")
