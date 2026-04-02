# WGA Fluorescence Analysis Tool — Lab Distribution Guide

This document explains how lab members get the tool, set it up once, and keep it updated.

---

## 1. Overview

This guide is for lab members who need to install and run the WGA Fluorescence Analysis Tool on their own machine. Setup only needs to be done once. After that, launching the app is a single double-click on macOS, or two terminal commands on any platform.

**Terminology used in this guide:**
- **Tool folder** — the cloned git repository (`WGA_fluorescence_analysis_tool/`) containing all the code
- **Data folder** — the folder on your machine where your plate reader output files (`.CSV`, `.xlsx`, layout `.csv`) are stored. This is completely separate from the tool folder. Legacy Bio-Rad `.txt` files are also supported.

---

## 2. First-Time Setup

### Prerequisites

- **Anaconda** or **Miniconda** must be installed on your machine.
  - Download: https://www.anaconda.com/download or https://docs.conda.io/en/latest/miniconda.html
- **Git** must be installed.
  - Download: https://git-scm.com/downloads

### Steps

1. **Clone the repository:**

   ```bash
   git clone https://github.com/rrmalmstrom/WGA_fluorescence_analysis_tool.git
   ```

2. **Enter the project directory:**

   ```bash
   cd WGA_fluorescence_analysis_tool
   ```

3. **Run the setup script:**

   ```bash
   bash setup.sh
   ```

   `setup.sh` will verify that `conda` and `git` are available, then create the conda environment automatically. If the environment already exists it will tell you how to update it instead of failing.

4. **Launch the app — choose one method:**

   **macOS — double-click launcher (recommended):**
   Double-click `run.command` in Finder. It will open a Terminal, activate the conda environment automatically, prompt you for your **data folder** path, and launch the GUI.

   **Any platform — terminal:**
   ```bash
   conda activate wga-fluorescence-gui
   python launch_gui.py
   ```

---

## 3. Running the App (After First Setup)

**macOS — double-click launcher (recommended):**
Double-click `run.command` in Finder (inside the tool folder). It will:
1. Open a Terminal window
2. Activate the `wga-fluorescence-gui` conda environment automatically
3. Ask you to provide the path to your **data folder** (type it or drag-and-drop the folder into the Terminal)
4. Check GitHub for updates
5. Launch the GUI with all file dialogs defaulting to your data folder

**Any platform — terminal:**
```bash
conda activate wga-fluorescence-gui
python launch_gui.py
```

Each time the app launches, `launch_gui.py` automatically:
1. Confirms the correct conda environment is active
2. Checks GitHub for updates — if your local branch is behind the remote, you will see a prompt like:

```
🔄 A new version is available on GitHub.
Pull updates now? [y/N]:
```

Enter `y` to download and apply the latest changes before the GUI opens, or press Enter to skip and continue with the current version. This means you no longer need to run `git pull` manually before each session.

> **Data folder tip:** When you provide a data folder path, all file-open dialogs (Load Data File, Load Layout File) and export dialogs (Save CSV, Export Plot) will default to that folder — no more navigating through your file system each time.

---

## 4. Keeping the Tool Up to Date

The lab owner pushes updates to GitHub. You should pull the latest changes before each session, or whenever you are notified that an update is available.

```bash
cd WGA_fluorescence_analysis_tool
git pull origin main
conda activate wga-fluorescence-gui
python launch_gui.py
```

> **If `environment.yml` was updated** (e.g., new packages were added), also run:
>
> ```bash
> conda env update -f environment.yml --prune
> ```
>
> You will be notified when this is necessary.

---

## 5. Checking for Updates Without Pulling

To check whether updates are available without downloading them yet:

```bash
git fetch origin
git status
```

If the output says **"Your branch is behind"**, there are updates available. Run `git pull origin main` to apply them.

---

## 6. Test Data

The `test_data/` directory contains sample input files (BMG and Bio-Rad formats) that you can use to verify the tool is working correctly after setup. Load these files through the app interface to confirm everything runs as expected.

---

## 7. Troubleshooting

| Problem | Solution |
|---|---|
| App won't launch | Make sure the conda environment is activated: `conda activate wga-fluorescence-gui` |
| Import errors on startup | Run `conda env update -f environment.yml --prune` to sync the environment |
| `git pull` fails with conflicts | **Do not attempt to resolve conflicts yourself.** Contact the lab owner before doing anything. |

---

## 8. Who to Contact

Contact [Lab Owner] for access to the GitHub repository or for help with setup.
