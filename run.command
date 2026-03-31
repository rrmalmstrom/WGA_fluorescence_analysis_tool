#!/usr/bin/env bash
# =============================================================================
# run.command — macOS double-click launcher for the WGA Fluorescence Analysis Tool
#
# Double-click this file in Finder to open a Terminal, activate the correct
# conda environment, and launch the analysis tool.
# =============================================================================

# -----------------------------------------------------------------------------
# Find the tool folder (the directory this script lives in)
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# -----------------------------------------------------------------------------
# Source conda so that 'conda activate' works in a non-interactive shell
# -----------------------------------------------------------------------------
# Try common conda installation locations
CONDA_INIT_SCRIPT=""
for candidate in \
    "$HOME/anaconda3/etc/profile.d/conda.sh" \
    "$HOME/miniconda3/etc/profile.d/conda.sh" \
    "$HOME/opt/anaconda3/etc/profile.d/conda.sh" \
    "$HOME/opt/miniconda3/etc/profile.d/conda.sh" \
    "/opt/anaconda3/etc/profile.d/conda.sh" \
    "/opt/miniconda3/etc/profile.d/conda.sh" \
    "/usr/local/anaconda3/etc/profile.d/conda.sh" \
    "/usr/local/miniconda3/etc/profile.d/conda.sh"
do
    if [[ -f "$candidate" ]]; then
        CONDA_INIT_SCRIPT="$candidate"
        break
    fi
done

if [[ -z "$CONDA_INIT_SCRIPT" ]]; then
    echo ""
    echo "❌ Could not find conda on this machine."
    echo "   Please install Anaconda or Miniconda:"
    echo "     • https://www.anaconda.com/download"
    echo "     • https://docs.conda.io/en/latest/miniconda.html"
    echo ""
    echo "Press Enter to close this window."
    read -r
    exit 1
fi

# shellcheck source=/dev/null
source "$CONDA_INIT_SCRIPT"

# -----------------------------------------------------------------------------
# Activate the correct conda environment
# -----------------------------------------------------------------------------
echo ""
echo "============================================================"
echo "  WGA Fluorescence Analysis Tool"
echo "============================================================"
echo ""

conda activate wga-fluorescence-gui 2>/dev/null

if [[ "$CONDA_DEFAULT_ENV" != "wga-fluorescence-gui" ]]; then
    echo "❌ Could not activate the 'wga-fluorescence-gui' conda environment."
    echo ""
    echo "   If this is your first time running the tool, please run setup first:"
    echo "     cd \"$SCRIPT_DIR\""
    echo "     bash setup.sh"
    echo ""
    echo "Press Enter to close this window."
    read -r
    exit 1
fi

echo "🐍 Conda environment: wga-fluorescence-gui ✅"
echo ""

# -----------------------------------------------------------------------------
# Ask the user for the data folder path
# -----------------------------------------------------------------------------
echo "Please enter the path to your data folder."
echo "(You can type the full path, or drag and drop the folder into this window.)"
echo ""
printf "Data folder: "
read -r DATA_FOLDER_RAW

# Strip leading/trailing whitespace and any surrounding quotes added by drag-and-drop
DATA_FOLDER="${DATA_FOLDER_RAW#"${DATA_FOLDER_RAW%%[![:space:]]*}"}"  # ltrim
DATA_FOLDER="${DATA_FOLDER%"${DATA_FOLDER##*[![:space:]]}"}"           # rtrim
DATA_FOLDER="${DATA_FOLDER%/}"                                          # remove trailing slash
# Remove surrounding single or double quotes (drag-and-drop on some macOS versions adds them)
DATA_FOLDER="${DATA_FOLDER#\'}"
DATA_FOLDER="${DATA_FOLDER%\'}"
DATA_FOLDER="${DATA_FOLDER#\"}"
DATA_FOLDER="${DATA_FOLDER%\"}"

if [[ -z "$DATA_FOLDER" ]]; then
    echo ""
    echo "⚠ No data folder provided. Launching without a default data folder."
    echo ""
elif [[ ! -d "$DATA_FOLDER" ]]; then
    echo ""
    echo "⚠ The path '$DATA_FOLDER' does not exist or is not a folder."
    echo "  Launching without a default data folder."
    echo ""
    DATA_FOLDER=""
else
    echo ""
    echo "📂 Data folder: $DATA_FOLDER"
    echo ""
fi

# -----------------------------------------------------------------------------
# Launch the tool
# -----------------------------------------------------------------------------
cd "$SCRIPT_DIR" || exit 1

if [[ -n "$DATA_FOLDER" ]]; then
    python launch_gui.py --data-folder "$DATA_FOLDER"
else
    python launch_gui.py
fi
