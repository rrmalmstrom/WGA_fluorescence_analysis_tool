#!/usr/bin/env bash
# =============================================================================
# WGA Fluorescence Analysis Tool — First-Time Setup Script
#
# Run this script once after cloning the repository to create the conda
# environment. After setup, activate the environment and launch the app:
#
#   conda activate wga-fluorescence-gui
#   python launch_gui.py
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------
echo ""
echo "============================================================"
echo "  WGA Fluorescence Analysis Tool — First-Time Setup"
echo "============================================================"
echo ""

# -----------------------------------------------------------------------------
# Check that conda is available
# -----------------------------------------------------------------------------
if ! command -v conda &> /dev/null; then
    echo "❌ ERROR: 'conda' was not found on your PATH."
    echo ""
    echo "   Please install Anaconda or Miniconda before running this script:"
    echo "     • Anaconda:  https://www.anaconda.com/download"
    echo "     • Miniconda: https://docs.conda.io/en/latest/miniconda.html"
    echo ""
    exit 1
fi

echo "✅ conda found: $(conda --version)"

# -----------------------------------------------------------------------------
# Check that git is available
# -----------------------------------------------------------------------------
if ! command -v git &> /dev/null; then
    echo "❌ ERROR: 'git' was not found on your PATH."
    echo ""
    echo "   Please install Git before running this script:"
    echo "     • https://git-scm.com/downloads"
    echo ""
    exit 1
fi

echo "✅ git found: $(git --version)"
echo ""

# -----------------------------------------------------------------------------
# Create the conda environment from environment.yml
# -----------------------------------------------------------------------------
echo "⏳ Creating conda environment from environment.yml..."
echo "   This may take 5–10 minutes with no visible progress bar. Please wait."
echo ""

# Capture both stdout and stderr so we can inspect the output on failure
CREATE_OUTPUT=$(conda env create -f environment.yml 2>&1) || CREATE_EXIT=$?

if [[ -n "${CREATE_EXIT:-}" && "${CREATE_EXIT}" -ne 0 ]]; then
    # Check whether the failure is simply because the environment already exists
    if echo "${CREATE_OUTPUT}" | grep -q "already exists"; then
        echo "⚠  Environment already exists."
        echo ""
        echo "   To update it with any new packages, run:"
        echo "     conda env update -f environment.yml --prune"
        echo ""
    else
        # A genuine error occurred — print the output and abort
        echo "❌ ERROR: 'conda env create' failed with the following output:"
        echo ""
        echo "${CREATE_OUTPUT}"
        echo ""
        exit 1
    fi
else
    echo "${CREATE_OUTPUT}"
    echo ""
    echo "✅ Conda environment created successfully."
    echo ""
fi

# -----------------------------------------------------------------------------
# Success — print next-step instructions
# -----------------------------------------------------------------------------
echo "============================================================"
echo "  Setup complete! To launch the app:"
echo ""
echo "    1. Activate the environment:"
echo "         conda activate wga-fluorescence-gui"
echo ""
echo "    2. Launch the app:"
echo "         python launch_gui.py"
echo ""
echo "  The launcher will confirm your environment is active,"
echo "  check GitHub for updates, then open the GUI."
echo "============================================================"
echo ""
