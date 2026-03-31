# WGA Fluorescence Analysis Tool

> **Documentation:** [User Guide](docs/USER_GUIDE.md) · [Installation](docs/INSTALLATION.md) · [Algorithms](docs/ALGORITHM_DOCUMENTATION.md) · [Technical Reference](docs/TECHNICAL_DOCUMENTATION.md)

A desktop GUI application for analyzing WGA (Whole Genome Amplification) fluorescence data from 96-well plate readers. Designed for laboratory scientists who need reliable sigmoid curve fitting, crossing-point detection, and pass/fail assessment without complex setup.

**Version:** 1.0.0

---

## Overview

This tool reads fluorescence time-series data exported from plate reader instruments, fits a 5-parameter sigmoid model to each well, detects the amplification crossing point (CP), and evaluates each well against configurable pass/fail thresholds. Results can be exported as a CSV summary.

Supported instruments:
- **BMG Omega3** — `.CSV` format (time encoded as "X h Y min")
- **Bio-Rad CFX** — `.txt` format (cycle-based, user specifies cycle time in minutes)

---

## Features

- Load fluorescence data and plate layout files via a point-and-click GUI
- Interactive 96-well plate visualization with color-coded well types
- 5-parameter sigmoid curve fitting with multiple fitting strategies and timeout protection
- Crossing-point (CP) detection via threshold crossing (10% above early-timepoint baseline)
- Pass/fail assessment using dual criteria: CP time and total fluorescence change
- Statistical summary by well group
- CSV export of all analysis results
- PDF export of publication-quality plots

---

## Installation

**Requirements:** [conda](https://docs.conda.io/en/latest/miniconda.html) (Miniconda or Anaconda)

```bash
git clone <repo-url>
cd WGA_fluorescence_analysis_tool
conda env create -f environment.yml
conda activate wga-fluorescence-gui
```

**Dependencies** (managed by `environment.yml`):

| Package    | Version         |
|------------|-----------------|
| Python     | >=3.9, <3.13    |
| numpy      | >=2.0, <3.0     |
| scipy      | >=1.13, <2.0    |
| pandas     | >=2.0, <3.0     |
| matplotlib | >=3.9, <4.0     |
| tkinter    | built into Python — no install needed |

---

## Usage

```bash
python main.py
```

Or, for verbose debug output to the terminal:

```bash
python launch_gui.py
```

### Workflow

1. **Load Data File** — select a BMG `.CSV` or Bio-Rad `.txt` file
2. **Load Layout File** — select the matching layout `.csv` file
   - Layout must include a `Sample` column; optional grouping columns (`Group_1`, `Group_2`, `Group_3`) are supported
   - For Bio-Rad files, enter the cycle time in minutes when prompted
3. **Process Files** — validates and parses both files
4. **Select Wells** — click wells on the plate visualization to select them
5. **Analyze Selected** — runs curve fitting and threshold analysis on selected wells
6. **Export** — save results as CSV or plots as PDF

### Pass/Fail Thresholds (defaults)

| Criterion              | Default Threshold |
|------------------------|-------------------|
| Crossing Point (CP)    | ≤ 6.5 hours       |
| Fluorescence change    | > 500 RFU         |

Both criteria must be met for a well to pass. Thresholds are configurable in the GUI.

### Sigmoid Model

```
y = a / (1 + exp(-b * (x - c))) + d + e * x
```

Parameters: `a` (amplitude), `b` (steepness), `c` (inflection point / CP), `d` (baseline offset), `e` (linear drift correction)

---

## Updating

The intended lab workflow is to clone once and pull updates as needed:

```bash
git pull origin main
python main.py
```

No reinstallation of the conda environment is needed unless `environment.yml` changes.

---

## Project Structure

```
WGA_fluorescence_analysis_tool/
├── environment.yml              # Conda environment specification
├── main.py                      # Primary entry point
├── launch_gui.py                # Alternate launcher with debug output
├── pytest.ini                   # Test configuration
├── README.md
├── fluorescence_tool/
│   ├── __init__.py              # Package version (1.0.0)
│   ├── core/
│   │   ├── models.py            # FluorescenceData, WellInfo, PassFailThresholds,
│   │   │                        #   PassFailResult, CurveFitResult
│   │   └── export_manager.py    # CSV and PDF export logic
│   ├── algorithms/
│   │   ├── curve_fitting.py     # 5-parameter sigmoid fitting
│   │   ├── threshold_analysis.py
│   │   ├── statistical_analysis.py
│   │   ├── pass_fail_analysis.py
│   │   └── analysis_pipeline.py # Orchestrates full analysis workflow
│   ├── parsers/
│   │   ├── bmg_parser.py        # BMG Omega3 .CSV parser
│   │   ├── biorad_parser.py     # Bio-Rad CFX .txt parser
│   │   └── layout_parser.py     # Plate layout .csv parser
│   └── gui/
│       ├── main_window.py       # Main application window
│       └── components/
│           ├── file_loader.py
│           ├── plate_view.py
│           ├── plot_panel.py
│           └── dialogs.py
├── test_data/                   # Sample input files for manual testing
│   ├── RM5097.96HL.BNCT.1.CSV
│   ├── RM5097_layout.csv
│   ├── TEST01.BIORAD.FORMAT.1.txt
│   ├── TEST01.BIORAD_layout.csv
│   └── tinyTEST01.BIORAD_layout.csv
└── tests/
    ├── unit/                    # Unit tests for parsers, models, algorithms
    ├── integration/             # End-to-end pipeline tests
    └── verification/            # Manual verification scripts
```

---

## Running Tests

```bash
pytest
```

To run with verbose output:

```bash
pytest -v
```

---

## Known Issues

- **Performance:** Analyzing a full 96-well plate may take 1–2 minutes due to the curve fitting optimization step. This is a known limitation currently being addressed.
