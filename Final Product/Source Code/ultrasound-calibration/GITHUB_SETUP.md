# GitHub Setup Checklist

This document ensures the codebase is ready for GitHub submission with no hardcoded user-specific paths.

## ✅ Completed Changes

### 1. Configuration System
- ✅ Created `plus_toolkit_config.py` utility module
- ✅ All scripts now use configurable paths via environment variables
- ✅ Fallback to default location if environment variable not set
- ✅ No hardcoded user-specific paths remain in active code

### 2. Updated Scripts
- ✅ `view_mha_volume.py` - Uses `get_pluslibdata_testimages_dir()` from config
- ✅ `test_simulated_calibration.py` - Uses config utility functions
- ✅ Both scripts have fallback functions if config module not found

### 3. Documentation
- ✅ `INSTALLATION.md` - Complete installation guide
- ✅ `README.md` - Main project documentation
- ✅ `VIEW_MHA_README.md` - Volume viewer documentation
- ✅ All documentation uses generic paths and examples

## Files Modified

### Active Code Files
1. `plus_toolkit_config.py` - NEW: Configuration utility
2. `view_mha_volume.py` - UPDATED: Uses config utility
3. `test_simulated_calibration.py` - UPDATED: Uses config utility

### Documentation Files
1. `INSTALLATION.md` - NEW: Installation instructions
2. `README.md` - NEW: Main documentation
3. `VIEW_MHA_README.md` - EXISTS: Volume viewer docs

## Files with Hardcoded Paths (Documentation Only)

These files contain hardcoded paths but are either:
- Documentation files (examples)
- Unused/legacy files in `unused/` directory

**No action needed** - these are for reference only:
- `CALIBRATION_EXECUTABLES.md` - Contains example paths
- `TEMPORAL_CALIBRATION_GUIDE.md` - Contains example paths
- `REQUIRED_FILES_FROM_ADVISOR.md` - Contains example paths
- `run_calibration.md` - Contains example paths
- Files in `unused/` directory - Legacy code

## Environment Variable Setup

Users must set `PLUS_TOOLKIT_PATH` environment variable:

**Windows PowerShell:**
```powershell
[Environment]::SetEnvironmentVariable("PLUS_TOOLKIT_PATH", "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin", "User")
```

**Windows Command Prompt:**
```cmd
setx PLUS_TOOLKIT_PATH "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin"
```

## Testing Before Commit

1. ✅ Verify config utility works:
   ```bash
   python plus_toolkit_config.py
   ```

2. ✅ Test with environment variable:
   ```powershell
   $env:PLUS_TOOLKIT_PATH = "C:\PlusToolkit\PlusApp-2.8.0.20190617-Win64\bin"
   python plus_toolkit_config.py
   ```

3. ✅ Test viewer script:
   ```bash
   python view_mha_volume.py
   ```

4. ✅ Test calibration script:
   ```bash
   python test_simulated_calibration.py --type spatial
   ```

## What Users Need to Do

1. Install PLUS ToolKit (see `INSTALLATION.md`)
2. Set `PLUS_TOOLKIT_PATH` environment variable
3. Install Python dependencies: `pip install -r requirements.txt`
4. Run verification: `python plus_toolkit_config.py`

## Git Considerations

### Files to Include
- ✅ All Python scripts in root directory
- ✅ `requirements.txt`
- ✅ All `.md` documentation files
- ✅ `plus_toolkit_config.py`

### Files to Exclude (if not already in .gitignore)
- `__pycache__/` directories
- `*.pyc` files
- `calibration_output/` (user-generated output)
- `unused/` directory (optional - contains legacy code)

### Recommended .gitignore Additions

```
# Python
__pycache__/
*.py[cod]
*$py.class

# Calibration output
calibration_output/
*.xml

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

## Summary

✅ **All active code uses configurable paths**
✅ **No user-specific hardcoded paths in production code**
✅ **Complete installation documentation provided**
✅ **Configuration utility for easy setup verification**
✅ **Ready for GitHub submission**

The codebase is now portable and can be used by anyone who:
1. Installs PLUS ToolKit
2. Sets the environment variable (or uses default location)
3. Installs Python dependencies

