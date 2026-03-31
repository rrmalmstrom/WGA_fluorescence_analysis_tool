# Installation Guide — WGA Fluorescence Analysis Tool

Complete installation and setup instructions for the WGA fluorescence analysis tool.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Installation](#quick-installation)
3. [Detailed Installation Steps](#detailed-installation-steps)
4. [Environment Setup](#environment-setup)
5. [Verification and Testing](#verification-and-testing)
6. [Troubleshooting Installation](#troubleshooting-installation)
7. [Alternative Installation Methods](#alternative-installation-methods)
8. [Updating and Maintenance](#updating-and-maintenance)

---

## System Requirements

### Minimum Requirements

**Software Prerequisites**
- Python 3.9–3.12
- Conda package manager (Anaconda or Miniconda)
- Git (required for the update-check feature in `launch_gui.py`)

### Recommended Specifications

**For Optimal Performance**
- 8+ GB RAM for large datasets (384-well plates)
- SSD storage for faster file loading
- Multi-core processor for analysis performance
- High-resolution display for detailed visualization

**For High-Throughput Use**
- 16+ GB RAM for batch processing
- Fast CPU (Apple M-series, Intel i7, or AMD Ryzen 7 / better)

---

## Quick Installation

For users familiar with Python and conda environments:

```bash
# 1. Clone the repository
git clone https://github.com/rrmalmstrom/WGA_fluorescence_analysis_tool.git
cd WGA_fluorescence_analysis_tool

# 2. Run the first-time setup script (creates the conda environment)
bash setup.sh

# 3. Launch the application
#    macOS (recommended): double-click run.command in Finder
#    Terminal (alternative):
#      conda activate wga-fluorescence-gui
#      python launch_gui.py
```

**That's it!** Skip to [Verification and Testing](#verification-and-testing) to confirm everything works.

---

## Detailed Installation Steps

### Step 1: Install Python and Conda

#### Option A: Install Anaconda (Recommended for Beginners)

1. **Download Anaconda**
   - Visit: https://www.anaconda.com/download
   - Download the Python 3.11 version for your platform

2. **Install Anaconda**
   - **macOS**: Run the downloaded `.pkg` file and follow the installer
   - **Linux**: Run `bash Anaconda3-*.sh` and follow the prompts

3. **Verify Installation**
   ```bash
   conda --version
   python --version
   ```

#### Option B: Install Miniconda (Lightweight Alternative)

1. **Download Miniconda**
   - Visit: https://docs.conda.io/en/latest/miniconda.html
   - Choose your platform and Python 3.11 version

2. **Install Miniconda**
   - Follow the same process as Anaconda above

3. **Verify Installation**
   ```bash
   conda --version
   python --version
   ```

### Step 2: Download the Tool

#### Option A: Clone with Git (Recommended)

```bash
# Navigate to desired directory
cd ~/Documents

# Clone the repository
git clone https://github.com/rrmalmstrom/WGA_fluorescence_analysis_tool.git
cd WGA_fluorescence_analysis_tool
```

#### Option B: Download ZIP File

1. **Download** the project as a ZIP file from the repository
2. **Extract** to a convenient location (e.g., `~/Documents/WGA_fluorescence_analysis_tool`)
3. **Navigate** to the extracted folder in your terminal

> **Note:** Cloning with Git is preferred — `launch_gui.py` uses `git fetch` / `git status` to check for updates automatically on each launch. Without a git repository, the update check is skipped gracefully.

### Step 3: Create the Conda Environment

Run the provided setup script from inside the project folder:

```bash
bash setup.sh
```

`setup.sh` will:
- Verify that `conda` and `git` are available on your PATH
- Run `conda env create -f environment.yml` to create the `wga-fluorescence-gui` environment
- Print next-step instructions when complete

> **Already ran setup before?** If the environment already exists, `setup.sh` will tell you and suggest `conda env update -f environment.yml --prune` instead.

This may take **5–10 minutes** depending on your internet connection.

### Step 4: Activate the Environment

```bash
conda activate wga-fluorescence-gui
```

> **Important:** `launch_gui.py` checks that the correct conda environment is active and exits with an error if it is not. You must activate `wga-fluorescence-gui` before running the launcher from the terminal.

### Step 5: Launch the Application

#### Recommended: double-click `run.command` (macOS)

Double-click `run.command` in Finder (inside the tool folder). It will:
1. Open a Terminal window
2. Locate and source your conda installation automatically
3. Activate the `wga-fluorescence-gui` environment
4. Prompt you for your **data folder** path (type or drag-and-drop the folder)
5. Launch the GUI via `python launch_gui.py --data-folder <path>`

> **Data folder:** When a data folder is provided, all file-open dialogs (Load Data File, Load Layout File) and export dialogs (Save CSV, Export Plot) default to that folder.

#### Alternative: terminal launch (macOS / Linux)

If you prefer the terminal, or are on Linux:

```bash
conda activate wga-fluorescence-gui
python launch_gui.py
```

You can also pass a data folder directly:

```bash
python launch_gui.py --data-folder /path/to/your/data
```

In both cases, `launch_gui.py` confirms the conda environment is active, checks GitHub for updates (prompting you to pull if a new version is available), then opens the application window.

---

## Environment Setup

### Understanding the Conda Environment

The tool uses a dedicated conda environment to ensure:
- **Dependency Isolation**: No conflicts with other Python projects
- **Version Control**: Exact package versions for reproducibility
- **Easy Management**: Simple activation/deactivation

### Environment Contents

The [`environment.yml`](../environment.yml) file specifies:

```yaml
name: wga-fluorescence-gui
channels:
  - conda-forge
  - defaults
dependencies:
  - python >=3.9,<3.13
  - numpy >=2.0,<3.0
  - scipy >=1.13,<2.0
  - pandas >=2.0,<3.0
  - matplotlib >=3.9,<4.0
  - pytest >=7.0
  - pip
```

> **Note:** `tkinter` is built into Python — no separate install is needed on most systems. See troubleshooting below if you encounter `tkinter not available` on Linux.

### Managing the Environment

#### Activate Environment
```bash
conda activate wga-fluorescence-gui
```

#### Deactivate Environment
```bash
conda deactivate
```

#### List Installed Packages
```bash
conda list
```

#### Update Environment (if `environment.yml` changed)
```bash
conda env update -f environment.yml --prune
```

#### Remove Environment (if needed)
```bash
conda env remove -n wga-fluorescence-gui
```

---

## Verification and Testing

### Basic Functionality Test

1. **Launch the Application**

   **macOS (recommended):** double-click `run.command` in Finder.

   **Terminal (alternative):**
   ```bash
   conda activate wga-fluorescence-gui
   python launch_gui.py
   ```

2. **Check Interface Elements**
   - File loading panel at the top
   - Plate view on the left
   - Plot panel on the right
   - All buttons and controls visible

3. **Test with Sample Data**
   - Use files in the `test_data/` directory
   - Load `test_data/RM5097.96HL.BNCT.1.CSV` as data file
   - Load `test_data/RM5097_layout.csv` as layout file
   - Click "Process Files"
   - Verify plate view shows colored wells

### Running Automated Tests

The tool includes a test suite under `tests/`:

```bash
# Activate environment
conda activate wga-fluorescence-gui

# Run all tests
pytest -v

# Run specific test categories
pytest tests/unit/ -v          # Unit tests
pytest tests/integration/ -v   # Integration tests
```

### Expected Test Results

**Successful Installation Shows**:
- ✅ All tests pass
- ✅ No import errors
- ✅ GUI launches without errors
- ✅ Sample data loads correctly

**Common Test Failures**:
- Missing dependencies (check `environment.yml` and re-run `bash setup.sh`)
- Environment not activated (`conda activate wga-fluorescence-gui`)
- File permission problems (check read access to `test_data/`)

### Verification Scripts

Additional standalone verification scripts are available:

```bash
python tests/verification/end_to_end_verification.py
python tests/verification/simple_verification.py
python tests/verification/verify_curve_fitting.py
```

These scripts process real laboratory data, generate analysis results, and validate against expected outputs without requiring the GUI.

---

## Troubleshooting Installation

### Common Issues and Solutions

#### "conda: command not found"

**Problem**: Conda is not in your system PATH.  
**Solutions**:
1. Restart your terminal after installing Anaconda/Miniconda
2. On macOS, ensure the installer added conda to your shell profile (`~/.zshrc` or `~/.bash_profile`)
3. Add conda to PATH manually (advanced users)

#### "Environment creation failed"

**Problem**: Network issues or package conflicts.  
**Solutions**:
1. Check internet connection
2. Try again (temporary server issues)
3. Clear conda cache: `conda clean --all`
4. Ensure `conda-forge` channel is available: `conda config --add channels conda-forge`

#### "❌ Wrong conda environment" or "❌ No conda environment is active"

**Problem**: `launch_gui.py` detected that `wga-fluorescence-gui` is not the active environment.  
**Solution**:
```bash
conda activate wga-fluorescence-gui
python launch_gui.py
```

#### "❌ Could not activate the 'wga-fluorescence-gui' conda environment" (run.command)

**Problem**: The environment hasn't been created yet.  
**Solution**: Run the setup script first:
```bash
bash setup.sh
```
Then double-click `run.command` again.

#### "tkinter not available"

**Problem**: GUI toolkit not installed (rare on most systems).  
**Solutions**:
1. **Linux**: Install tkinter package
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3-tk

   # CentOS/RHEL
   sudo yum install python3-tkinter
   ```
2. **macOS**: Usually included with Python from conda; try recreating the environment

#### "Import errors" when running

**Problem**: Environment not activated or incomplete installation.  
**Solutions**:
1. Ensure environment is activated: `conda activate wga-fluorescence-gui`
2. Reinstall environment:
   ```bash
   conda env remove -n wga-fluorescence-gui
   bash setup.sh
   ```
3. Check Python version: `python --version` (should be 3.9–3.12)

### Platform-Specific Notes

#### macOS

**Security Warnings (Gatekeeper)**
- If macOS blocks `run.command`, right-click it in Finder and choose **Open**, then confirm
- Allow Python in **System Settings → Privacy & Security** if prompted
- Grant file access permissions when prompted by the OS

**Apple Silicon (M1/M2/M3)**
- `conda-forge` packages are natively compiled for Apple Silicon — no Rosetta 2 needed for the dependencies in `environment.yml`

#### Linux

**Display Issues**
- Ensure a display is available; if using SSH, enable X11 forwarding: `ssh -X user@host`
- Install GUI libraries if missing: `sudo apt-get install python3-tk`

**`run.command` is macOS-only**
- On Linux, always launch via the terminal:
  ```bash
  conda activate wga-fluorescence-gui
  python launch_gui.py
  ```

---

## Alternative Installation Methods

### Method 1: Manual Dependency Installation (pip / venv)

If conda is not available:

```bash
# Create virtual environment
python -m venv fluorescence_env

# Activate environment
# macOS/Linux:
source fluorescence_env/bin/activate

# Install dependencies
pip install "numpy>=2.0,<3.0" "scipy>=1.13,<2.0" "pandas>=2.0,<3.0" "matplotlib>=3.9,<4.0" "pytest>=7.0"
```

Then launch with:
```bash
python launch_gui.py
```

> **Note:** The conda environment check in `launch_gui.py` will report that no conda environment is active, but the tool will still exit — you would need to run `python -c "from fluorescence_tool.gui.main_window import MainWindow; MainWindow().run()"` directly, or modify the launcher. Using conda is strongly recommended.

### Method 2: System Python (Not Recommended)

Only if virtual environments are not possible:

```bash
pip install --user numpy scipy pandas matplotlib pytest
python launch_gui.py
```

**Warning**: This may cause conflicts with other Python projects.

---

## Updating and Maintenance

### Updating the Tool

`launch_gui.py` checks for updates automatically on each launch. When a new version is available on GitHub, it will prompt:

```
🔄 A new version is available on GitHub.
Pull updates now? [y/N]:
```

Type `y` to pull and automatically restart with the new version.

To update manually:

1. **Pull Latest Changes**
   ```bash
   git pull origin main
   ```

2. **Update Environment** (only if `environment.yml` changed)
   ```bash
   conda env update -f environment.yml --prune
   ```

3. **Test Updated Installation**
   ```bash
   pytest -v
   ```

### Regular Maintenance

#### Keep Conda Updated
```bash
conda update conda
```

#### Clean Conda Cache
```bash
conda clean --all
```

#### Monitor Disk Space
The conda environment uses approximately 1–2 GB of disk space.

### Backup and Recovery

#### Export Environment Snapshot
```bash
conda env export -n wga-fluorescence-gui > wga_fluorescence_backup.yml
```

#### Restore from Snapshot
```bash
conda env create -f wga_fluorescence_backup.yml
```

#### Backup Analysis Results
- Export important results as CSV files
- Keep copies of layout files and protocols
- Document analysis parameters used

---

## Getting Help

### Installation Support

**Before Seeking Help**:
1. Check this installation guide thoroughly
2. Try the troubleshooting steps above
3. Test with provided sample data in `test_data/`
4. Run the verification scripts

**When Reporting Issues**:
- Include your operating system and version
- Provide the exact error message
- Describe what you were trying to do
- Include output from `conda list` and `python --version`

### Useful Commands for Diagnostics

```bash
# System information
python --version
conda --version
conda info

# Environment information
conda activate wga-fluorescence-gui
conda list
python -c "import tkinter; print('GUI available')"

# Test basic functionality
python -c "import numpy, scipy, pandas, matplotlib; print('All packages imported successfully')"
```

### Community Resources

- Check the project documentation in `docs/`
- Review the test data and examples in `test_data/`
- Examine the verification scripts in `tests/verification/` for usage patterns

---

**Installation Complete!**

Once installed successfully, refer to the [USER_GUIDE.md](USER_GUIDE.md) for detailed usage instructions and the [README.md](../README.md) for project overview.

*For technical details about the implementation, see [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md).*
