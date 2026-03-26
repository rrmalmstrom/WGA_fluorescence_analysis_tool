# Simplified Fluorescence Data Analysis Tool

A clean, reliable desktop application for fluorescence data analysis that replaces overly complex systems with a simple, user-friendly solution.

## Features

- **Dual File Format Support**: BMG Omega3 (.csv) and BioRad (.txt) formats
- **Interactive GUI**: tkinter-based desktop application with real-time visualization
- **Advanced Analysis**: 5-parameter sigmoid curve fitting with threshold detection
- **Export Capabilities**: Publication-ready PDF plots and comprehensive CSV data exports
- **Test-Driven Development**: Comprehensive test suite ensuring reliability

## Quick Start

### Prerequisites

- Python 3.9+
- Conda (recommended for environment management)

### Installation

1. Clone or download this project
2. Create the conda environment:
   ```bash
   conda env create -f environment.yml
   ```
3. Activate the environment:
   ```bash
   conda activate fluorescence-tool
   ```
4. Run the application:
   ```bash
   python main.py
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=fluorescence_tool --cov-report=html

# Run specific test categories
pytest tests/unit/ -v          # Unit tests only
pytest tests/integration/ -v   # Integration tests only
```

## Project Structure

```
fluorescence_tool_simplified/
├── main.py                    # Application entry point
├── environment.yml            # Conda environment specification
├── fluorescence_tool/         # Main package
│   ├── gui/                  # GUI components
│   ├── core/                 # Core business logic
│   ├── parsers/              # File format parsers
│   ├── algorithms/           # Analysis algorithms
│   └── utils/                # Utility functions
├── tests/                    # Test suite
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── performance/         # Performance tests
└── test_data/               # Sample data files
```

## Supported File Formats

### BMG Omega3 Format (.csv)
- Automatic time parsing from "X h Y min" format
- Metadata extraction from header rows
- Well identification from row/column data

### BioRad Format (.txt)
- Tab-separated cycle-based data
- User-specified cycle time conversion
- Support for 96-well and 384-well plates

### Layout Files (.csv)
- Well type classification (sample, control, unused)
- Grouping information for analysis
- Cell count metadata

## Development

This project follows Test-Driven Development (TDD) methodology:

1. Write failing tests first
2. Implement minimal code to pass tests
3. Refactor and improve
4. Repeat

### Contributing

1. Ensure all tests pass: `pytest`
2. Follow code style: `black fluorescence_tool/`
3. Check linting: `flake8 fluorescence_tool/`
4. Add tests for new features

## License

[Add your license here]

## Support

[Add support information here]