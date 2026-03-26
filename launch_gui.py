#!/usr/bin/env python3
"""
GUI Launcher for Fluorescence Analysis Tool

Simple script to launch the GUI for manual testing and debugging.
"""

import sys
from pathlib import Path

# Add the fluorescence_tool to the path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Launch the GUI application."""
    try:
        from fluorescence_tool.gui.main_window import MainWindow
        
        print("Launching Fluorescence Analysis Tool GUI...")
        print("Available test files:")
        print("  - Data: example_input_files/RM5097.96HL.BNCT.1.CSV")
        print("  - Layout: example_input_files/RM5097_layout.csv")
        print("  - BioRad Data: example_input_files/TEST01.BIORAD.FORMAT.1.txt")
        print("  - BioRad Layout: example_input_files/TEST01.BIORAD_layout.csv")
        print()
        
        # Create and run the application
        app = MainWindow()
        app.run()
        
    except KeyboardInterrupt:
        print("\nApplication closed by user.")
    except Exception as e:
        print(f"Error launching GUI: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())