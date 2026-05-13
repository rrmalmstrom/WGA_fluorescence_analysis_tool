# Getting Started — WGA Fluorescence Analysis Tool

Everything you need to install, launch, and keep the tool up to date.

---

## Table of Contents

1. [Which setup path is mine?](#1-which-setup-path-is-mine)
2. [Prerequisites](#2-prerequisites)
3. [First-Time Setup](#3-first-time-setup)
4. [Daily Launch](#4-daily-launch)
5. [What Happens on Launch](#5-what-happens-on-launch)
6. [Keeping the Tool Up to Date](#6-keeping-the-tool-up-to-date)
7. [Test Data](#7-test-data)
8. [Troubleshooting](#8-troubleshooting)
9. [Who to Contact](#9-who-to-contact)

---

## 1. Which setup path is mine?

| I am on… | I should use… |
|---|---|
| **macOS** | conda path — `setup.sh` + `run.command` |
| **Windows 10 or 11** | pip + venv path — `setup.bat` + `run.bat` |
| **Linux** | conda path — `setup.sh` + terminal |

---

## 2. Prerequisites

### macOS / Linux

- **Anaconda or Miniconda** — the conda package manager
  - Download Anaconda: https://www.anaconda.com/download
  - Download Miniconda (lighter): https://docs.conda.io/en/latest/miniconda.html
- **Git**
  - Download: https://git-scm.com/downloads
  - macOS alternative: install Xcode Command Line Tools (`xcode-select --install`)

### Windows

- **Python 3.11** — from the official python.org installer
  - Download: https://www.python.org/downloads/
  - ⚠️ Use the **python.org installer**, not the Microsoft Store version
  - ⚠️ On the first installer screen, check **"Add Python to PATH"** before clicking Install
- **Git for Windows**
  - Download: https://git-scm.com/download/win
  - Accept all default options during installation

---

## 3. First-Time Setup

### Step 1 — Clone the repository

Open a terminal (macOS/Linux) or Command Prompt / PowerShell (Windows) and run:

```bash
git clone https://github.com/rrmalmstrom/WGA_fluorescence_analysis_tool.git
cd WGA_fluorescence_analysis_tool
```

Or download the ZIP from GitHub and extract it to a convenient location.

> **Note:** Cloning with Git is strongly recommended. The launcher uses `git fetch` / `git status` to check for updates automatically on each launch. Without a git repository the update check is skipped gracefully.

### Step 2 — Run the setup script

**macOS / Linux:**

```bash
bash setup.sh
```

`setup.sh` will:
- Verify that `conda` and `git` are on your PATH
- Create the `wga-fluorescence-gui` conda environment from `environment.yml`
- Print next-step instructions when complete

This may take **5–10 minutes** on first run.

> **Already ran setup before?** If the environment already exists, `setup.sh` will tell you and suggest `conda env update -f environment.yml --prune` to update it.

---

**Windows:**

Double-click **`setup.bat`** in File Explorer (inside the tool folder).

`setup.bat` will:
- Verify that Python and Git are on your PATH
- Create a `.venv` virtual environment inside the tool folder
- Install all pinned dependencies from `requirements.txt`
- Verify that the GUI toolkit (tkinter) is working
- Print a success message when complete

This may take **3–5 minutes** on first run.

---

## 4. Daily Launch

### macOS — double-click launcher (recommended)

Double-click **`run.command`** in Finder (inside the tool folder).

It will:
1. Open a Terminal window
2. Locate and activate the `wga-fluorescence-gui` conda environment automatically
3. Ask you to provide the path to your **data folder** (type it or drag-and-drop the folder into the Terminal window, then press Enter)
4. Check GitHub for updates
5. Launch the GUI with all file dialogs defaulting to your data folder

> **Data folder tip:** When you provide a data folder path, all file-open dialogs (Load Data File, Load Layout File) and export dialogs (Save CSV, Export Plot) will default to that folder — no more navigating through your file system each time.

### Windows — double-click launcher

Double-click **`run.bat`** in File Explorer (inside the tool folder).

It will:
1. Open a Command Prompt window
2. Activate the `.venv` virtual environment automatically
3. Ask you to provide the path to your **data folder** (type it or drag-and-drop the folder, then press Enter)
4. Check GitHub for updates
5. Launch the GUI with all file dialogs defaulting to your data folder

### macOS / Linux — terminal (alternative)

```bash
conda activate wga-fluorescence-gui
python launch_gui.py
```

You can also pass a data folder directly:

```bash
python launch_gui.py --data-folder /path/to/your/data
```

### Windows — terminal (alternative)

```
.venv\Scripts\activate
python launch_gui.py
```

---

## 5. What Happens on Launch

Each time the app launches, `launch_gui.py` automatically:

1. **Confirms the environment is active** — checks for the conda env (macOS/Linux) or active venv (Windows) and exits with instructions if neither is found
2. **Checks GitHub for updates** — fetches the latest refs from the remote. If your local branch is behind, you will see:

```
🔄 A new version is available on GitHub.
Pull updates now? [y/N]:
```

Enter `y` to download and apply the latest changes before the GUI opens. The launcher will also update your environment packages (`conda env update` on macOS, `pip install -r requirements.txt` on Windows) and restart automatically.

Press Enter (or `n`) to skip and continue with the current version.

3. **Opens the GUI** — the main application window appears

---

## 6. Keeping the Tool Up to Date

The launcher handles updates automatically on each launch (see above). To update manually:

**macOS / Linux:**

```bash
git pull origin main
conda env update -f environment.yml --prune
python launch_gui.py
```

**Windows:**

```
git pull origin main
.venv\Scripts\pip install -r requirements.txt
python launch_gui.py
```

> **When is a manual update needed?** Only if the automatic update prompt fails (e.g., no network at launch time) or if you are told by the lab owner to update immediately.

---

## 7. Test Data

The `test_data/` folder contains sample input files you can use to verify the tool is working correctly after setup:

| File | Format |
|---|---|
| `RM5097.96HL.BNCT.1.CSV` | BMG Omega3 |
| `RM5097_layout.csv` | Layout file for above |
| `TEST01.BIORAD.FORMAT.1.txt` | Bio-Rad CFX legacy |
| `TEST01.BIORAD_layout.csv` | Layout file for above |

Load these files through the app interface to confirm everything runs as expected. See [docs/USER_GUIDE.md](docs/USER_GUIDE.md) for step-by-step usage instructions.

---

## 8. Troubleshooting

### macOS / Linux

| Problem | Solution |
|---|---|
| `conda: command not found` | Restart your terminal after installing Anaconda/Miniconda. On macOS, ensure the installer added conda to `~/.zshrc` or `~/.bash_profile`. |
| `❌ Could not activate the 'wga-fluorescence-gui' conda environment` | The environment hasn't been created yet. Run `bash setup.sh` first. |
| `❌ Wrong conda environment` or `❌ No conda environment is active` | Run `conda activate wga-fluorescence-gui` before launching. |
| Environment creation failed | Check your internet connection. Try `conda clean --all` then re-run `bash setup.sh`. |
| `tkinter not available` (Linux) | Run `sudo apt-get install python3-tk` (Ubuntu/Debian) or `sudo yum install python3-tkinter` (CentOS/RHEL). |
| `git pull` fails with conflicts | **Do not attempt to resolve conflicts yourself.** Contact the lab owner. |
| macOS blocks `run.command` (Gatekeeper) | Right-click `run.command` in Finder → **Open** → confirm. |

### Windows

| Problem | Solution |
|---|---|
| `'python' is not recognized` | Python is not on your PATH. Reinstall Python 3.11 from https://www.python.org/downloads/ and check **"Add Python to PATH"** on the first screen. |
| `'git' is not recognized` | Git is not installed. Download from https://git-scm.com/download/win and use default options. |
| `ERROR: requirements.txt not found` | Run `git pull origin main` to get the latest files, then re-run `setup.bat`. |
| `ERROR: Virtual environment not found` | Re-run `setup.bat` to recreate the `.venv` environment. |
| `WARNING: tkinter is not available` | Reinstall Python 3.11 from https://www.python.org/downloads/ and ensure **"tcl/tk and IDLE"** is checked during installation. |
| Antivirus blocks `setup.bat` or `run.bat` | Right-click the file → **Run as administrator**. If your organisation's antivirus quarantines the file, contact your IT department and show them the GitHub repository. |
| Import errors on startup | Re-run `setup.bat` to reinstall dependencies. |

### Running the automated test suite

To verify the full installation programmatically:

```bash
# macOS / Linux
conda activate wga-fluorescence-gui
pytest -v

# Windows
.venv\Scripts\activate
pytest -v
```

All tests should pass. If any fail, note the error message and contact the lab owner.

---

## 9. Who to Contact

Contact the lab owner for:
- Access to the GitHub repository
- Help with setup or installation errors
- Reporting bugs or unexpected behaviour

---

*For detailed usage instructions (loading files, plate view, analysis, export), see [docs/USER_GUIDE.md](docs/USER_GUIDE.md).*
*For technical and algorithm documentation, see [docs/TECHNICAL_DOCUMENTATION.md](docs/TECHNICAL_DOCUMENTATION.md) and [docs/ALGORITHM_DOCUMENTATION.md](docs/ALGORITHM_DOCUMENTATION.md).*
