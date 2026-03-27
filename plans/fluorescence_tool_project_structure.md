# Fluorescence Tool Simplified - Project Structure

## Directory Structure for `../fluorescence_tool_simplified/`

```
fluorescence_tool_simplified/
├── README.md                           # User documentation and setup instructions
├── LICENSE                             # Software license
├── environment.yml                     # Conda environment specification
├── requirements.txt                    # Pip requirements (backup)
├── launcher.py                         # Cross-platform application launcher
├── main.py                            # Application entry point
├── setup.py                           # Package setup configuration
├── .gitignore                         # Git ignore patterns
├── pytest.ini                        # Pytest configuration
├── .github/                           # GitHub workflows (optional)
│   └── workflows/
│       └── tests.yml                  # CI/CD pipeline
├── docs/                              # Documentation
│   ├── user_guide.md                 # End-user documentation
│   ├── developer_guide.md            # Developer setup and contribution guide
│   ├── api_reference.md              # API documentation
│   └── troubleshooting.md            # Common issues and solutions
├── tests/                             # Test suite (TDD approach)
│   ├── __init__.py
│   ├── conftest.py                   # Pytest configuration and fixtures
│   ├── test_data/                    # Test data files
│   │   ├── bmg_sample.csv           # Sample BMG Omega3 file
│   │   ├── biorad_sample.txt        # Sample BioRad file
│   │   ├── layout_sample.csv        # Sample layout file
│   │   └── synthetic_data.py        # Synthetic data generators
│   ├── unit/                         # Unit tests
│   │   ├── __init__.py
│   │   ├── test_parsers/
│   │   │   ├── __init__.py
│   │   │   ├── test_bmg_parser.py
│   │   │   ├── test_biorad_parser.py
│   │   │   └── test_layout_parser.py
│   │   ├── test_algorithms/
│   │   │   ├── __init__.py
│   │   │   ├── test_curve_fitting.py
│   │   │   ├── test_threshold.py
│   │   │   └── test_statistics.py
│   │   ├── test_core/
│   │   │   ├── __init__.py
│   │   │   ├── test_data_manager.py
│   │   │   ├── test_analysis_engine.py
│   │   │   └── test_export_manager.py
│   │   └── test_utils/
│   │       ├── __init__.py
│   │       ├── test_validators.py
│   │       └── test_time_utils.py
│   ├── integration/                  # Integration tests
│   │   ├── __init__.py
│   │   ├── test_workflow_bmg.py     # End-to-end BMG workflow
│   │   ├── test_workflow_biorad.py  # End-to-end BioRad workflow
│   │   └── test_gui_integration.py  # GUI integration tests
│   └── performance/                  # Performance tests
│       ├── __init__.py
│       ├── test_large_datasets.py   # Large dataset performance
│       └── test_memory_usage.py     # Memory usage tests
├── fluorescence_tool/                # Main package
│   ├── __init__.py                   # Package initialization
│   ├── version.py                    # Version information
│   ├── constants.py                  # Application constants
│   ├── exceptions.py                 # Custom exception classes
│   ├── gui/                          # GUI components
│   │   ├── __init__.py
│   │   ├── main_window.py           # Main application window
│   │   ├── components/              # Reusable GUI components
│   │   │   ├── __init__.py
│   │   │   ├── file_loader.py       # File loading interface
│   │   │   ├── plate_view.py        # Interactive plate visualization
│   │   │   ├── plot_panel.py        # Plot display and controls
│   │   │   ├── progress_dialog.py   # Progress indication
│   │   │   └── dialogs.py           # Export and settings dialogs
│   │   ├── styles/                  # GUI styling
│   │   │   ├── __init__.py
│   │   │   └── themes.py            # Color themes and styling
│   │   └── utils/                   # GUI utilities
│   │       ├── __init__.py
│   │       ├── event_manager.py     # Event handling
│   │       └── state_manager.py     # Application state
│   ├── core/                        # Core business logic
│   │   ├── __init__.py
│   │   ├── data_manager.py          # Central data management
│   │   ├── analysis_engine.py       # Curve fitting and analysis
│   │   ├── export_manager.py        # File export functionality
│   │   └── models.py                # Data models and structures
│   ├── parsers/                     # File format parsers
│   │   ├── __init__.py
│   │   ├── base_parser.py           # Abstract base parser
│   │   ├── bmg_parser.py            # BMG Omega3 format parser
│   │   ├── biorad_parser.py         # BioRad format parser
│   │   ├── layout_parser.py         # Layout file parser
│   │   └── format_detector.py       # Automatic format detection
│   ├── algorithms/                  # Analysis algorithms
│   │   ├── __init__.py
│   │   ├── curve_fitting.py         # Sigmoid curve fitting
│   │   ├── threshold.py             # Threshold detection methods
│   │   ├── statistics.py            # Statistical calculations
│   │   └── quality_control.py       # Data quality assessment
│   └── utils/                       # Utility functions
│       ├── __init__.py
│       ├── validators.py            # Data validation utilities
│       ├── time_utils.py            # Time conversion utilities
│       ├── file_utils.py            # File handling utilities
│       └── math_utils.py            # Mathematical utilities
├── examples/                        # Example usage and tutorials
│   ├── __init__.py
│   ├── basic_usage.py              # Basic usage example
│   ├── advanced_analysis.py        # Advanced analysis example
│   └── batch_processing.py         # Batch processing example
├── scripts/                         # Utility scripts
│   ├── setup_environment.sh        # Environment setup script
│   ├── run_tests.sh                # Test execution script
│   ├── generate_docs.py            # Documentation generation
│   └── validate_installation.py    # Installation validation
└── output/                          # Default output directory
    ├── plots/                      # Generated plots
    ├── data/                       # Exported data files
    └── logs/                       # Application logs
```

## Key Design Principles

### 1. **Clean Separation of Concerns**
- **GUI Layer**: Pure presentation logic, no business logic
- **Core Layer**: Business logic, data management, analysis
- **Parsers Layer**: File format handling, data normalization
- **Algorithms Layer**: Mathematical computations, curve fitting
- **Utils Layer**: Shared utilities and helpers

### 2. **Test-Driven Development Structure**
- **Comprehensive Test Coverage**: Unit, integration, and performance tests
- **Test Data Management**: Dedicated test data directory with samples
- **Fixtures and Mocks**: Reusable test components in conftest.py
- **CI/CD Ready**: GitHub Actions workflow for automated testing

### 3. **Modular Architecture**
- **Independent Modules**: Each module can be tested and developed separately
- **Clear Interfaces**: Abstract base classes define contracts
- **Dependency Injection**: Core components accept dependencies
- **Plugin Architecture**: Easy to add new file formats or algorithms

### 4. **User Experience Focus**
- **Simple Installation**: Single conda environment setup
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Comprehensive Documentation**: User guides and API reference
- **Example Code**: Working examples for common use cases

### 5. **Development Workflow Support**
- **Version Control**: Git-friendly structure with proper .gitignore
- **Package Management**: Both conda and pip support
- **Documentation**: Automated documentation generation
- **Quality Assurance**: Linting, formatting, and validation scripts

## File Naming Conventions

### Python Files
- **snake_case**: All Python files use snake_case naming
- **Descriptive Names**: File names clearly indicate purpose
- **Module Prefixes**: Test files prefixed with `test_`

### Documentation
- **Markdown Format**: All documentation in Markdown
- **Lowercase**: Documentation files in lowercase with underscores
- **Descriptive**: Clear, descriptive filenames

### Configuration Files
- **Standard Names**: Use standard configuration file names
- **Environment Specific**: Separate configs for different environments
- **Version Controlled**: All configs tracked in version control

## Dependencies and Requirements

### Core Dependencies
```yaml
# environment.yml core dependencies
- python=3.9
- numpy=1.24
- scipy=1.10
- pandas=2.0
- matplotlib=3.7
```

### Development Dependencies
```yaml
# Development and testing
- pytest=7.4
- pytest-cov=4.1
- black=23.7
- flake8=6.0
- mypy=1.5
```

### Optional Dependencies
```yaml
# Optional enhancements
- jupyter=1.0  # For notebook examples
- sphinx=7.1   # For documentation generation
```

This structure provides a solid foundation for TDD development while maintaining clean architecture and supporting the simplified desktop application approach outlined in the technical specifications.