# Simplified Fluorescence Data Analysis Tool

A clean, reliable desktop application for fluorescence data analysis that replaces overly complex systems with a simple, user-friendly solution designed specifically for laboratory scientists.


## ✨ Features

### Core Functionality
- **Dual File Format Support**: BMG Omega3 (.csv) and BioRad (.txt) formats
- **Layout File Integration**: Dynamic grouping and well classification
- **Advanced Curve Fitting**: 5-parameter sigmoid with multiple fitting strategies
- **QC Filter System**: 10% baseline threshold with robust validation
- **Threshold Detection**: Second derivative crossing point calculation
- **Interactive GUI**: Real-time plate visualization and plot updates

### Advanced Features
- **Multi-Layer Visualization**: Type, Group_1, Group_2, Group_3 organization
- **Pass/Fail Analysis**: Dual criteria threshold system (CP + fluorescence change)
- **Interactive Well Selection**: Click-to-select with real-time plot updates
- **Comprehensive Export**: CSV data export with all analysis parameters
- **Publication Plots**: High-quality PDF export with proper formatting
- **Statistical Analysis**: Group comparisons and summary statistics

### Technical Excellence
- **Clean Architecture**: Modular design with clear separation of concerns
- **Robust Error Handling**: Graceful failure recovery and user feedback
- **Performance Optimized**: Handles 384-well plates efficiently
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Minimal Dependencies**: Scientific Python stack only

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Conda (recommended for environment management)

### Installation

1. **Clone or download this project**
   ```bash
   git clone [repository-url]
   cd fluorescence_tool_simplified
   ```

2. **Create the conda environment**
   ```bash
   conda env create -f environment.yml
   ```

3. **Activate the environment**
   ```bash
   conda activate fluorescence-tool
   ```

4. **Launch the application**
   ```bash
   python launch_gui.py
   ```

### First Analysis

1. **Load Data Files**
   - Click "Load Data File" and select your BMG (.csv) or BioRad (.txt) file
   - Click "Load Layout File" and select your layout CSV file
   - For BioRad files, specify the cycle time in minutes

2. **Process and Visualize**
   - Click "Process Files" to load and validate data
   - View the interactive plate layout with color-coded wells
   - Select wells by clicking on the plate visualization

3. **Analyze and Export**
   - Click "Analyze Selected" to perform curve fitting
   - View real-time plots with fitted curves and thresholds
   - Export results as CSV data or publication-ready PDF plots

## 📁 Project Structure

```
fluorescence_tool_simplified/
├── README.md                    # This file - project overview
├── USER_GUIDE.md               # Complete user manual
├── TECHNICAL_DOCUMENTATION.md  # Developer documentation
├── ALGORITHM_DOCUMENTATION.md  # Scientific algorithm details
├── INSTALLATION.md             # Detailed setup instructions
├── main.py                     # Application entry point
├── launch_gui.py               # GUI launcher script
├── environment.yml             # Conda environment specification
├── fluorescence_tool/          # Main package
│   ├── gui/                   # GUI components
│   │   ├── main_window.py     # Main application window
│   │   └── components/        # UI components (plate view, plots, etc.)
│   ├── core/                  # Core business logic
│   │   ├── models.py          # Data structures
│   │   └── export_manager.py  # Export functionality
│   ├── parsers/               # File format parsers
│   │   ├── bmg_parser.py      # BMG Omega3 format
│   │   ├── biorad_parser.py   # BioRad format
│   │   └── layout_parser.py   # Layout file parser
│   ├── algorithms/            # Analysis algorithms
│   │   ├── curve_fitting.py   # 5-parameter sigmoid fitting
│   │   ├── threshold_analysis.py # Threshold detection
│   │   ├── pass_fail_analysis.py # Pass/fail evaluation
│   │   └── analysis_pipeline.py  # Complete analysis workflow
│   └── utils/                 # Utility functions
├── tests/                     # Comprehensive test suite
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── performance/           # Performance tests
├── verification/              # Validation scripts and results
├── test_data/                 # Sample data files
├── docs/                      # Additional documentation
└── plans/                     # Architecture and design documents
```

## 🔬 Supported File Formats

### BMG Omega3 Format (.csv)
- **Automatic Processing**: No user input required
- **Time Parsing**: Converts "X h Y min" format to decimal hours
- **Metadata Extraction**: User, test name, date, plate ID
- **Well Identification**: Automatic from row/column data
- **Quality Validation**: Comprehensive data integrity checks

### BioRad Format (.txt)
- **Cycle-Based Data**: Tab-separated format with cycle numbers
- **Time Conversion**: User-specified cycle time (minutes) → hours
- **Plate Support**: 96-well and 384-well automatic detection
- **Flexible Input**: Handles various BioRad export formats

### Layout Files (.csv)
- **Well Classification**: sample, neg_cntrl, pos_cntrl, unused, blank
- **Multi-Level Grouping**: Group_1, Group_2, Group_3 for complex experiments
- **Cell Count Metadata**: Optional cell/capsule count information
- **Flexible Format**: Handles missing optional columns gracefully

## 🧪 Scientific Algorithms

### 5-Parameter Sigmoid Curve Fitting
- **Mathematical Model**: `y = a / (1 + exp(-b * (x - c))) + d + e * x`
- **Multiple Strategies**: Standard, steep curve, and wide range fitting
- **Robust Optimization**: Timeout protection and parameter bounds
- **Quality Assessment**: R-squared calculation and convergence analysis

### Threshold Detection
- **Baseline Method**: 10% above mean of early time points (proven approach)
- **Crossing Point**: Linear interpolation for precise time calculation
- **QC Filtering**: Automatic validation of data quality
- **Flexible Parameters**: Configurable baseline points and percentage

### Pass/Fail Analysis
- **Dual Criteria**: Crossing Point (CP) AND fluorescence change thresholds
- **Default Thresholds**: CP < 400 minutes, fluorescence change > 500 RFU
- **Configurable**: User-adjustable threshold values
- **Detailed Results**: Individual criterion results and failure reasons

## 📊 Export Capabilities

### CSV Data Export
- **Complete Analysis**: All curve fitting parameters and results
- **Raw Data**: Original time-series measurements
- **Fitted Data**: Calculated curve values at each time point
- **Metadata**: Well information, grouping, and quality metrics
- **Pass/Fail Results**: Threshold analysis outcomes

### PDF Plot Export
- **Publication Quality**: 300 DPI resolution with proper formatting
- **Customizable Views**: Raw data, fitted curves, thresholds, crossing points
- **Group Visualization**: Color-coded by well type and groups
- **Metadata Annotation**: Automatic plot annotation with analysis details
- **Professional Layout**: Proper axis labels, legends, and grid formatting

## 🛠️ Development

### Technology Stack
- **Language**: Python 3.9+
- **GUI Framework**: tkinter (built-in, cross-platform)
- **Scientific Computing**: NumPy, SciPy, Pandas
- **Visualization**: Matplotlib with tkinter backend
- **Testing**: pytest with coverage reporting
- **Environment**: Conda for dependency management

### Development Workflow
1. **Test-Driven Development**: Write tests first, implement features
2. **Modular Architecture**: Clear separation of concerns
3. **Code Quality**: Black formatting, flake8 linting
4. **Documentation**: Comprehensive docstrings and external docs
5. **Validation**: Real data testing and user feedback

### Contributing
```bash
# Setup development environment
conda env create -f environment.yml
conda activate fluorescence-tool

# Run tests
pytest tests/ -v --cov=fluorescence_tool

# Code formatting
black fluorescence_tool/

# Linting
flake8 fluorescence_tool/
```

## 📚 Documentation

- **[USER_GUIDE.md](USER_GUIDE.md)**: Complete user manual for laboratory scientists
- **[TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)**: Developer and API documentation
- **[ALGORITHM_DOCUMENTATION.md](ALGORITHM_DOCUMENTATION.md)**: Scientific algorithm details
- **[INSTALLATION.md](INSTALLATION.md)**: Detailed setup and deployment instructions
- **[plans/](plans/)**: Architecture and design documents

## 🔧 Troubleshooting

### Common Issues
- **File Loading Errors**: Check file format and encoding
- **Analysis Failures**: Verify data quality and time series length
- **Export Problems**: Ensure write permissions and disk space
- **GUI Issues**: Update graphics drivers and Python version

### Support Resources
- **User Guide**: Step-by-step instructions for all features
- **Technical Documentation**: API reference and troubleshooting
- **Test Data**: Sample files for validation and testing
- **Verification Scripts**: Tools for validating installation
