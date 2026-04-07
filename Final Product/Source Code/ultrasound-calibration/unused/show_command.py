"""
Show the exact command that will be run for ProbeCalibration.
"""

from pathlib import Path
import os

# Paths
plus_toolkit_path = r"C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin"
mha_file = Path(__file__).parent / "ElbowUltrasoundSweep.mha"
mha_path = mha_file.resolve()

# Build the command
probe_cal_path = os.path.join(plus_toolkit_path, "ProbeCalibration.exe")
config_file = "calibration_config.xml"  # This will be a temp file in actual execution
output_config = "calibration_result.xml"  # This will be in temp/output/ in actual execution

cmd = [
    probe_cal_path,
    f"--config-file={config_file}",
    f"--calibration-seq-file={mha_path}",
    f"--output-config-file={output_config}"
]

print("=" * 80)
print("EXACT COMMAND THAT WILL BE RUN:")
print("=" * 80)
print()
print(" ".join(cmd))
print()
print("=" * 80)
print("BREAKDOWN:")
print("=" * 80)
print(f"  Executable: {probe_cal_path}")
print(f"  --config-file: {config_file}")
print(f"  --calibration-seq-file: {mha_path}")
print(f"  --output-config-file: {output_config}")
print()
print("=" * 80)
print("MATCHES PLUS DOCS FORMAT:")
print("=" * 80)
print("  ProbeCalibration --config-file=... --calibration-seq-file=...mha")
print("=" * 80)



