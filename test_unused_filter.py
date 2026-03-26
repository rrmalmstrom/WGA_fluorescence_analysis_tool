#!/usr/bin/env python3
"""
Test script for unused well filtering in CSV export.
"""

import sys
import os
from pathlib import Path

# Add the fluorescence_tool to the path
sys.path.insert(0, str(Path(__file__).parent))

from fluorescence_tool.parsers.bmg_parser import BMGOmega3Parser
from fluorescence_tool.parsers.layout_parser import LayoutParser
from fluorescence_tool.core.export_manager import ExportManager
import pandas as pd


def test_unused_filter():
    """Test the unused well filtering functionality."""
    print("Testing unused well filtering...")
    
    # Load test data
    data_file = "../example_input_files/RM5097.96HL.BNCT.1.CSV"
    layout_file = "../example_input_files/RM5097_layout.csv"
    
    if not os.path.exists(data_file) or not os.path.exists(layout_file):
        print("Error: Test files not found")
        return False
    
    try:
        # Parse data files
        bmg_parser = BMGOmega3Parser()
        fluorescence_data = bmg_parser.parse_file(data_file)
        
        layout_parser = LayoutParser()
        layout_data = layout_parser.parse_file(layout_file)
        
        # Create minimal analysis results
        analysis_results = {
            'fluorescence_data': fluorescence_data,
            'layout_data': list(layout_data.values()),
            'curve_fits': {}  # Empty for this test
        }
        
        export_manager = ExportManager()
        
        # Test 1: Export with unused wells included
        print("Test 1: Export WITH unused wells...")
        export_manager.export_analysis_data(
            analysis_results, 
            "test_with_unused.csv", 
            include_unused=True
        )
        
        df_with_unused = pd.read_csv("test_with_unused.csv")
        unused_count_with = len(df_with_unused[df_with_unused['Type'] == 'unused'])
        total_with = len(df_with_unused)
        
        print(f"  Total wells: {total_with}")
        print(f"  Unused wells: {unused_count_with}")
        
        # Test 2: Export without unused wells
        print("\nTest 2: Export WITHOUT unused wells...")
        export_manager.export_analysis_data(
            analysis_results, 
            "test_without_unused.csv", 
            include_unused=False
        )
        
        df_without_unused = pd.read_csv("test_without_unused.csv")
        unused_count_without = len(df_without_unused[df_without_unused['Type'] == 'unused'])
        total_without = len(df_without_unused)
        
        print(f"  Total wells: {total_without}")
        print(f"  Unused wells: {unused_count_without}")
        
        # Verify results
        print(f"\nResults:")
        print(f"  Wells filtered out: {total_with - total_without}")
        print(f"  Unused wells in filtered export: {unused_count_without}")
        
        if unused_count_without == 0 and total_without < total_with:
            print("✓ Unused well filtering works correctly!")
            return True
        else:
            print("✗ Unused well filtering failed!")
            return False
            
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_unused_filter()
    if success:
        print("\n✓ Unused well filtering test passed!")
    else:
        print("\n✗ Unused well filtering test failed!")
        sys.exit(1)