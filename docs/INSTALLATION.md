# Installation Guide - Fluorescence Data Analysis Tool

Complete installation and setup instructions for the simplified fluorescence analysis tool.

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

**Operating System**
- Windows 10 or later
- macOS 10.14 (Mojave) or later
- Linux (Ubuntu 18.04+, CentOS 7+, or equivalent)

**Hardware**
- 4 GB RAM (8 GB recommended)
- 2 GB free disk space
- Display resolution: 1024x768 minimum (1920x1080 recommended)
- Graphics: Basic graphics card with OpenGL support

**Software Prerequisites**
- Python 3.9 or later (3.11 recommended)
- Conda package manager (Anaconda or Miniconda)

### Recommended Specifications

**For Optimal Performance**
- 8+ GB RAM for large datasets (384-well plates)
- SSD storage for faster file loading
- Multi-core processor for analysis performance
- High-resolution display for detailed visualization

**For High-Throughput Use**
- 16+ GB RAM for batch processing
- Fast CPU (Intel i7/AMD Ryzen 7 or better)
- Dedicated graphics card (optional, for better GUI performance)

---

## Quick Installation

For users familiar with Python and conda environments:

```bash
# 1. Clone or download the project
git clone <repo-url>
cd WGA_fluorescence_analysis_tool

# 2. Create conda environment
conda env create -f environment.yml

# 3. Activate environment
conda activate wga-fluorescence-gui

# 4. Launch application
python launch_gui.py
```

**That's it!** Skip to [Verification and Testing](#verification-and-testing) to confirm everything works.

---

## Detailed Installation Steps

### Step 1: Install Python and Conda

#### Option A: Install Anaconda (Recommended for Beginners)

1. **Download Anaconda**
   - Visit: https://www.anaconda.com/products/distribution
   - Choose your operating system (Windows, macOS, or Linux)
   - Download the Python 3.11 version

2. **Install Anaconda**
   - **Windows**: Run the downloaded `.exe` file and follow the installer
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
   - Choose your operating system and Python 3.11 version

2. **Install Miniconda**
   - Follow the same process as Anaconda above

3. **Verify Installation**
   ```bash
   conda --version
   python --version
   ```

### Step 2: Download the Fluorescence Tool

#### Option A: Download ZIP File

1. **Download** the project as a ZIP file from the repository
2. **Extract** to a convenient location (e.g., `Documents/WGA_fluorescence_analysis_tool`)
3. **Navigate** to the extracted folder

#### Option B: Clone with Git (If Available)

```bash
# Navigate to desired directory
cd ~/Documents  # or C:\Users\YourName\Documents on Windows

# Clone the repository
git clone <repo-url>
cd WGA_fluorescence_analysis_tool
```

### Step 3: Create the Conda Environment

1. **Open Terminal/Command Prompt**
   - **Windows**: Open "Anaconda Prompt" from Start Menu
   - **macOS**: Open Terminal application
   - **Linux**: Open your terminal emulator

2. **Navigate to Project Directory**
   ```bash
   cd path/to/WGA_fluorescence_analysis_tool
   ```

3. **Create Environment from File**
   ```bash
   conda env create -f environment.yml
   ```

   This will:
   - Create a new environment called "wga-fluorescence-gui"
   - Install Python 3.9–3.12 and all required packages
   - Set up the correct versions for compatibility

4. **Wait for Installation**
   - This may take 5-15 minutes depending on your internet connection
   - You'll see progress messages as packages are downloaded and installed

### Step 4: Activate the Environment

```bash
conda activate wga-fluorescence-gui
```

**Important**: You must activate this environment every time you want to use the tool.

### Step 5: Launch the Application

```bash
python launch_gui.py
```

`launch_gui.py` will confirm the conda environment is active, check GitHub for updates, then open the application window.

---

## Environment Setup

### Understanding the Conda Environment

The tool uses a dedicated conda environment to ensure:
- **Dependency Isolation**: No conflicts with other Python projects
- **Version Control**: Exact package versions for reproducibility
- **Easy Management**: Simple activation/deactivation

### Environment Contents

The `environment.yml` file specifies:

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
  - pip
```

> **Note:** tkinter is built into Python — no separate install is needed on most systems. See troubleshooting below if you encounter `tkinter not available` on Linux.

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

#### Update Environment (if needed)
```bash
conda env update -f environment.yml
```

#### Remove Environment (if needed)
```bash
conda env remove -n wga-fluorescence-gui
```

---

## Verification and Testing

### Basic Functionality Test

1. **Launch the Application**
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
   - Load `RM5097.96HL.BNCT.1.CSV` as data file
   - Load `RM5097_layout.csv` as layout file
   - Click "Process Files"
   - Verify plate view shows colored wells

### Running Automated Tests

The tool includes a comprehensive test suite:

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
- Missing dependencies (check environment.yml)
- Graphics/display issues (update drivers)
- File permission problems (check write access)

### Performance Verification

Test with the included verification script:

```bash
python tests/verification/end_to_end_verification.py
```

This will:
- Process real laboratory data
- Generate analysis results
- Create output plots
- Validate against expected results

---

## Troubleshooting Installation

### Common Issues and Solutions

#### "conda: command not found"

**Problem**: Conda is not in your system PATH
**Solutions**:
1. Restart terminal after installing Anaconda/Miniconda
2. On Windows, use "Anaconda Prompt" instead of regular Command Prompt
3. Add conda to PATH manually (advanced users)

#### "Environment creation failed"

**Problem**: Network issues or package conflicts
**Solutions**:
1. Check internet connection
2. Try again (temporary server issues)
3. Clear conda cache: `conda clean --all`
4. Use different conda channels: `conda config --add channels conda-forge`

#### "tkinter not available"

**Problem**: GUI toolkit not installed (rare on most systems)
**Solutions**:
1. **Linux**: Install tkinter package
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3-tk
   
   # CentOS/RHEL
   sudo yum install tkinter
   ```
2. **macOS**: Usually included, try reinstalling Python
3. **Windows**: Usually included with Anaconda

#### "Permission denied" errors

**Problem**: Insufficient file permissions
**Solutions**:
1. Run terminal as administrator (Windows) or use sudo (Linux/macOS)
2. Install in user directory instead of system directory
3. Check antivirus software isn't blocking installation

#### "Import errors" when running

**Problem**: Environment not activated or incomplete installation
**Solutions**:
1. Ensure environment is activated: `conda activate wga-fluorescence-gui`
2. Reinstall environment: `conda env remove -n wga-fluorescence-gui` then recreate
3. Check Python version: `python --version` (should be 3.9+)

### Platform-Specific Issues

#### Windows

**Graphics Issues**
- Update graphics drivers
- Try running with `python -m tkinter` to test GUI

**Path Issues**
- Use forward slashes or raw strings for file paths
- Avoid spaces in installation directory

#### macOS

**Security Warnings**
- Allow Python in System Preferences > Security & Privacy
- Grant file access permissions when prompted

**M1/M2 Macs**
- Use native conda packages when available
- Some packages may need Rosetta 2 translation

#### Linux

**Display Issues**
- Ensure X11 forwarding if using SSH: `ssh -X`
- Install GUI libraries: `sudo apt-get install python3-tk`

**Package Manager Conflicts**
- Use conda instead of pip when possible
- Avoid mixing system Python with conda

---

## Alternative Installation Methods

### Method 1: Manual Dependency Installation

If conda is not available:

```bash
# Create virtual environment
python -m venv fluorescence_env

# Activate environment
# Windows:
fluorescence_env\Scripts\activate
# macOS/Linux:
source fluorescence_env/bin/activate

# Install dependencies
pip install "numpy>=2.0,<3.0" "scipy>=1.13,<2.0" "pandas>=2.0,<3.0" "matplotlib>=3.9,<4.0" pytest
```

### Method 2: Docker Installation (Advanced)

For containerized deployment:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

CMD ["python", "launch_gui.py"]
```

### Method 3: System Python (Not Recommended)

Only if virtual environments are not possible:

```bash
pip install --user numpy scipy pandas matplotlib pytest
python launch_gui.py
```

**Warning**: This may cause conflicts with other Python projects.

---

## Updating and Maintenance

### Updating the Tool

When new versions are available:

1. **Pull Latest Changes**
   ```bash
   git pull origin main
   ```

2. **Update Environment** (only if `environment.yml` changed)
   ```bash
   conda env update -f environment.yml
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
The conda environment uses approximately 1-2 GB of disk space.

### Backup and Recovery

#### Backup Environment
```bash
conda env export -n wga-fluorescence-gui > wga_fluorescence_backup.yml
```

#### Restore Environment
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
3. Test with provided sample data
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

- Check the project documentation
- Review the test data and examples
- Examine the verification scripts for usage patterns

---

**Installation Complete!** 

Once installed successfully, refer to the [USER_GUIDE.md](USER_GUIDE.md) for detailed usage instructions and the [README.md](README.md) for project overview.

*For technical details about the implementation, see [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md).*