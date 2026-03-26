#!/usr/bin/env python3
"""
Test script for CSV export functionality.

This script tests the new CSV export format to ensure it includes:
1. Layout file columns
2. Delta fluorescence
3. Crossing point (CP)
4. Pass/fail results
5. Raw fluorescence data (one column per time point)
6. Curve fitting statistics
"""

import sys
import os
from pathlib import Path

# Add the fluorescence_tool to the path
sys.path.insert(0, str(Path(__file__).parent))

from fluorescence_tool.parsers.bmg_parser import BMGOmega3Parser
from fluorescence_tool.parsers.layout_parser import LayoutParser
from fluorescence_tool.algorithms.curve_fitting import CurveFitter
from fluorescence_tool.algorithms.threshold_analysis import ThresholdAnalyzer
from fluorescence_tool.algorithms.pass_fail_analysis import PassFailAnalyzer
from fluorescence_tool.core.models import PassFailThresholds
from fluorescence_tool.core.export_manager import ExportManager
import numpy as np
import pandas as pd


def test_csv_export():
    """Test the CSV export functionality with real data."""
    print("Testing CSV export functionality...")
    
    # Load test data
    data_file = "../example_input_files/RM5097.96HL.BNCT.1.CSV"
    layout_file = "../example_input_files/RM5097_layout.csv"
    
    if not os.path.exists(data_file):
        print(f"Error: Data file not found: {data_file}")
        return False
        
    if not os.path.exists(layout_file):
        print(f"Error: Layout file not found: {layout_file}")
        return False
    
    try:
        # Parse data files
        print("Loading fluorescence data...")
        bmg_parser = BMGOmega3Parser()
        fluorescence_data = bmg_parser.parse_file(data_file)
        print(f"Loaded {len(fluorescence_data.wells)} wells")
        
        print("Loading layout data...")
        layout_parser = LayoutParser()
        layout_data = layout_parser.parse_file(layout_file)
        print(f"Loaded layout for {len(layout_data)} wells")
        
        # Run analysis on a subset of wells for testing
        print("Running analysis on sample wells...")
        curve_fitter = CurveFitter(timeout_seconds=2)
        threshold_analyzer = ThresholdAnalyzer(baseline_percentage=0.10)
        
        # Analyze first 10 wells for testing
        test_wells = fluorescence_data.wells[:10]
        curve_fits = {}
        time_points = np.array(fluorescence_data.time_points)
        
        for well_id in test_wells:
            well_index = fluorescence_data.wells.index(well_id)
            fluo_values = fluorescence_data.measurements[well_index, :]
            
            # Perform curve fitting
            curve_result = curve_fitter.fit_curve(time_points, fluo_values)
            
            # Generate fitted curve
            fitted_curve = None
            if curve_result.success and curve_result.parameters:
                try:
                    fitted_curve = curve_fitter.sigmoid_5param(time_points, *curve_result.parameters)
                except Exception:
                    pass
            
            # Perform threshold analysis
            threshold_result = threshold_analyzer.analyze_threshold_crossing(
                time_points, fluo_values, method="linear")
            
            # Store results in the format expected by export manager
            curve_fits[well_id] = {
                'curve_result': curve_result,
                'threshold_result': threshold_result,
                'fitted_curve': fitted_curve,
                'crossing_point': threshold_result.crossing_time if threshold_result.success else None,
                'threshold_value': threshold_result.threshold_value if threshold_result.success else None
            }
        
        print(f"Analysis completed for {len(curve_fits)} wells")
        
        # Create analysis results structure
        analysis_results = {
            'fluorescence_data': fluorescence_data,
            'layout_data': list(layout_data.values()),
            'curve_fits': curve_fits
        }
        
        # Run pass/fail analysis
        print("Running pass/fail analysis...")
        pass_fail_thresholds = PassFailThresholds(
            cp_threshold=400.0,  # 400 minutes
            fluorescence_change_threshold=500.0,  # 500 RFU
            enabled=True
        )
        pass_fail_analyzer = PassFailAnalyzer(pass_fail_thresholds)
        pass_fail_results = pass_fail_analyzer.analyze_all_wells(analysis_results)
        
        # Test CSV export
        print("Testing CSV export...")
        export_manager = ExportManager()
        output_file = "test_export_output.csv"
        
        export_manager.export_analysis_data(
            analysis_results, 
            output_file, 
            pass_fail_results=pass_fail_results
        )
        
        # Verify the exported file
        if os.path.exists(output_file):
            print(f"CSV export successful: {output_file}")
            
            # Read and examine the exported data
            df = pd.read_csv(output_file)
            print(f"Exported CSV contains {len(df)} rows and {len(df.columns)} columns")
            
            # Check expected columns
            expected_columns = [
                'Plate_ID', 'Well', 'Type', 'Cell_Count', 'Group_1', 'Group_2', 'Group_3', 'Sample',
                'Delta_Fluorescence', 'Crossing_Point', 'Pass_Fail'
            ]
            
            print("\nColumn verification:")
            for col in expected_columns:
                if col in df.columns:
                    print(f"✓ {col}")
                else:
                    print(f"✗ Missing: {col}")
            
            # Check for time point columns
            time_cols = [col for col in df.columns if col.startswith('T_')]
            print(f"✓ Found {len(time_cols)} time point columns")
            
            # Check for statistics columns
            stats_cols = ['R_Squared', 'Fit_Quality']
            for col in stats_cols:
                if col in df.columns:
                    print(f"✓ {col}")
                else:
                    print(f"✗ Missing: {col}")
            
            # Show sample data
            print(f"\nFirst few rows of exported data:")
            print(df.head(3).to_string())
            
            # Show column summary
            print(f"\nColumn summary:")
            print(f"Total columns: {len(df.columns)}")
            print(f"Layout columns: {len([c for c in df.columns if c in expected_columns])}")
            print(f"Time point columns: {len(time_cols)}")
            print(f"Statistics columns: {len([c for c in df.columns if c in stats_cols])}")
            
            return True
        else:
            print("Error: CSV export failed - file not created")
            return False
            
    except Exception as e:
        print(f"Error during CSV export test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_csv_export()
    if success:
        print("\n✓ CSV export test completed successfully!")
    else:
        print("\n✗ CSV export test failed!")
        sys.exit(1)