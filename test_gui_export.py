#!/usr/bin/env python3
"""
Test script for GUI export functionality.

This script tests the export functionality through the GUI to ensure
the integration works correctly.
"""

import sys
import os
from pathlib import Path

# Add the fluorescence_tool to the path
sys.path.insert(0, str(Path(__file__).parent))

from fluorescence_tool.gui.main_window import MainWindow
import tkinter as tk


def test_gui_export():
    """Test export functionality through the GUI."""
    print("Testing GUI export functionality...")
    
    # Create main window
    app = MainWindow()
    
    # Test data files
    data_file = "../example_input_files/RM5097.96HL.BNCT.1.CSV"
    layout_file = "../example_input_files/RM5097_layout.csv"
    
    if not os.path.exists(data_file) or not os.path.exists(layout_file):
        print("Error: Test files not found")
        return False
    
    try:
        # Load data programmatically
        print("Loading test data...")
        app._process_data_file(data_file)
        app._process_layout_file(layout_file)
        
        # Run analysis
        print("Running analysis...")
        app._run_analysis()
        
        # Test CSV export
        print("Testing CSV export...")
        test_csv_file = "gui_test_export.csv"
        
        # Simulate export
        from fluorescence_tool.core.export_manager import ExportManager
        export_manager = ExportManager()
        
        # Get pass/fail results from plot panel if available
        pass_fail_data = getattr(app.plot_panel, 'pass_fail_results', None)
        
        export_manager.export_analysis_data(
            app.analysis_results, 
            test_csv_file, 
            pass_fail_results=pass_fail_data
        )
        
        if os.path.exists(test_csv_file):
            print(f"✓ GUI CSV export successful: {test_csv_file}")
            
            # Quick validation
            import pandas as pd
            df = pd.read_csv(test_csv_file)
            print(f"✓ Exported {len(df)} rows with {len(df.columns)} columns")
            
            # Check for key columns
            required_cols = ['Well', 'Delta_Fluorescence', 'Crossing_Point', 'Pass_Fail']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if not missing_cols:
                print("✓ All required columns present")
                return True
            else:
                print(f"✗ Missing columns: {missing_cols}")
                return False
        else:
            print("✗ CSV export failed")
            return False
            
    except Exception as e:
        print(f"Error during GUI export test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        try:
            app.root.destroy()
        except:
            pass


if __name__ == "__main__":
    success = test_gui_export()
    if success:
        print("\n✓ GUI export test completed successfully!")
    else:
        print("\n✗ GUI export test failed!")
        sys.exit(1)