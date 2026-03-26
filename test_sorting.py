#!/usr/bin/env python3
"""
Test script for CSV export sorting functionality.
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


def test_sorting():
    """Test the CSV export sorting functionality."""
    print("Testing CSV export sorting...")
    
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
        
        # Export without unused wells to see sorting more clearly
        print("Exporting with sorting (excluding unused wells)...")
        export_manager.export_analysis_data(
            analysis_results, 
            "test_sorted_export.csv", 
            include_unused=False
        )
        
        # Read and check the sorting
        df = pd.read_csv("test_sorted_export.csv")
        
        print(f"Total wells exported: {len(df)}")
        print("\nFirst 10 wells in sorted order:")
        for i in range(min(10, len(df))):
            well = df.iloc[i]['Well']
            well_type = df.iloc[i]['Type']
            print(f"  {i+1:2d}. {well} ({well_type})")
        
        print("\nLast 10 wells in sorted order:")
        for i in range(max(0, len(df)-10), len(df)):
            well = df.iloc[i]['Well']
            well_type = df.iloc[i]['Type']
            print(f"  {i+1:2d}. {well} ({well_type})")
        
        # Check if sorting is correct (should start with column 1, then 2, etc.)
        first_wells = df['Well'].head(10).tolist()
        print(f"\nFirst 10 wells: {first_wells}")
        
        # Verify no temporary columns remain
        temp_cols = [col for col in df.columns if col.startswith('_Well_')]
        if temp_cols:
            print(f"✗ Error: Temporary columns found: {temp_cols}")
            return False
        else:
            print("✓ No temporary sorting columns in final export")
        
        return True
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_sorting()
    if success:
        print("\n✓ Sorting test completed!")
    else:
        print("\n✗ Sorting test failed!")
        sys.exit(1)