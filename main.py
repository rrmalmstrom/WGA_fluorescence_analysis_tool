#!/usr/bin/env python3
"""
Simplified Fluorescence Data Analysis Tool
Main application entry point

This is a clean, desktop-based fluorescence analysis tool designed to replace
the overly complex existing system with a simple, reliable solution.
"""

import sys
from pathlib import Path

# Add the package to Python path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """Main application entry point."""
    try:
        # Import GUI components
        from fluorescence_tool.gui.main_window import MainWindow

        # Create and run the application
        app = MainWindow()
        app.run()

    except ImportError as e:
        print(f"Error importing application components: {e}")
        print("Please ensure all dependencies are installed.")
        sys.exit(1)
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
