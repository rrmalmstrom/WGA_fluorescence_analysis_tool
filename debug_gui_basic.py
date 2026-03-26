#!/usr/bin/env python3
"""
Basic GUI debugging script to test import and initialization.

This script tests the fundamental GUI functionality:
1. Import all GUI components
2. Initialize main window
3. Check for basic errors
4. Test component creation
"""

import sys
import traceback
from pathlib import Path

# Add the fluorescence_tool to the path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test importing all GUI components."""
    print("=== Testing GUI Component Imports ===")
    
    try:
        print("Importing core models...")
        from fluorescence_tool.core.models import FluorescenceData, WellInfo, FileFormat
        print("✓ Core models imported successfully")
        
        print("Importing parsers...")
        from fluorescence_tool.parsers.bmg_parser import BMGOmega3Parser
        from fluorescence_tool.parsers.biorad_parser import BioRadParser
        from fluorescence_tool.parsers.layout_parser import LayoutParser
        print("✓ Parsers imported successfully")
        
        print("Importing analysis pipeline...")
        from fluorescence_tool.algorithms.analysis_pipeline import FluorescenceAnalysisPipeline
        print("✓ Analysis pipeline imported successfully")
        
        print("Importing GUI components...")
        from fluorescence_tool.gui.components.file_loader import FileLoader
        from fluorescence_tool.gui.components.plate_view import PlateView
        from fluorescence_tool.gui.components.plot_panel import PlotPanel
        from fluorescence_tool.gui.components.dialogs import ExportDialog
        print("✓ GUI components imported successfully")
        
        print("Importing main window...")
        from fluorescence_tool.gui.main_window import MainWindow
        print("✓ Main window imported successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        traceback.print_exc()
        return False

def test_gui_initialization():
    """Test GUI initialization without showing the window."""
    print("\n=== Testing GUI Initialization ===")
    
    try:
        from fluorescence_tool.gui.main_window import MainWindow
        
        print("Creating main window instance...")
        app = MainWindow()
        print("✓ Main window created successfully")
        
        print("Testing window properties...")
        print(f"  - Title: {app.root.title()}")
        print(f"  - Geometry: {app.root.geometry()}")
        print(f"  - Min size: {app.root.minsize()}")
        
        print("Testing component references...")
        print(f"  - File loader: {type(app.file_loader).__name__}")
        print(f"  - Plate view: {type(app.plate_view).__name__}")
        print(f"  - Plot panel: {type(app.plot_panel).__name__}")
        
        print("Testing parser initialization...")
        print(f"  - BMG parser: {type(app.bmg_parser).__name__}")
        print(f"  - BioRad parser: {type(app.biorad_parser).__name__}")
        print(f"  - Layout parser: {type(app.layout_parser).__name__}")
        print(f"  - Analysis pipeline: {type(app.analysis_pipeline).__name__}")
        
        print("Testing application state...")
        print(f"  - Fluorescence data: {app.fluorescence_data}")
        print(f"  - Layout data: {len(app.layout_data)} entries")
        print(f"  - Analysis results: {len(app.analysis_results)} entries")
        print(f"  - Selected wells: {len(app.selected_wells)} wells")
        
        # Don't start the main loop, just test initialization
        print("✓ GUI initialization completed successfully")
        
        # Clean up
        app.root.destroy()
        return True
        
    except Exception as e:
        print(f"✗ GUI initialization failed: {e}")
        traceback.print_exc()
        return False

def test_component_creation():
    """Test individual component creation."""
    print("\n=== Testing Individual Component Creation ===")
    
    try:
        import tkinter as tk
        from fluorescence_tool.gui.components.file_loader import FileLoader
        from fluorescence_tool.gui.components.plate_view import PlateView
        from fluorescence_tool.gui.components.plot_panel import PlotPanel
        
        # Create a test root window
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Mock main window for component testing
        class MockMainWindow:
            def __init__(self):
                self.fluorescence_data = None
                self.layout_data = {}
                self.analysis_results = {}
                self.selected_wells = []
                
            def _load_data_file(self):
                pass
                
            def _load_layout_file(self):
                pass
                
            def _run_analysis(self):
                pass
                
            def on_well_selection_changed(self, wells):
                pass
                
            def update_status(self, message):
                pass
        
        mock_main = MockMainWindow()
        
        print("Testing FileLoader component...")
        file_loader = FileLoader(root, mock_main)
        print("✓ FileLoader created successfully")
        
        print("Testing PlateView component...")
        plate_view = PlateView(root, mock_main)
        print("✓ PlateView created successfully")
        
        print("Testing PlotPanel component...")
        plot_panel = PlotPanel(root, mock_main)
        print("✓ PlotPanel created successfully")
        
        # Clean up
        root.destroy()
        return True
        
    except Exception as e:
        print(f"✗ Component creation failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all basic GUI tests."""
    print("Starting Basic GUI Debugging Tests")
    print("=" * 50)
    
    # Test 1: Imports
    import_success = test_imports()
    
    # Test 2: GUI initialization
    init_success = test_gui_initialization() if import_success else False
    
    # Test 3: Component creation
    component_success = test_component_creation() if import_success else False
    
    # Summary
    print("\n" + "=" * 50)
    print("BASIC GUI TEST SUMMARY")
    print("=" * 50)
    print(f"Import test: {'✓ PASS' if import_success else '✗ FAIL'}")
    print(f"Initialization test: {'✓ PASS' if init_success else '✗ FAIL'}")
    print(f"Component creation test: {'✓ PASS' if component_success else '✗ FAIL'}")
    
    if import_success and init_success and component_success:
        print("\n🎉 All basic GUI tests PASSED!")
        print("The GUI framework appears to be working correctly.")
        return True
    else:
        print("\n❌ Some basic GUI tests FAILED!")
        print("Issues need to be resolved before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)