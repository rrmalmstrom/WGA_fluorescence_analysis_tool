#!/usr/bin/env python3
"""
Debug script to test analysis results generation.

This script tests if the curve fitting and threshold analysis are working
and generating the expected data structures.
"""

import sys
from pathlib import Path
import numpy as np

# Add the fluorescence_tool to the path
sys.path.insert(0, str(Path(__file__).parent))

def test_analysis_components():
    """Test the analysis components directly."""
    print("=== Testing Analysis Components ===")
    
    try:
        # Import analysis components
        from fluorescence_tool.algorithms.curve_fitting import CurveFitter
        from fluorescence_tool.algorithms.threshold_analysis import ThresholdAnalyzer
        from fluorescence_tool.parsers.bmg_parser import BMGOmega3Parser
        from fluorescence_tool.parsers.layout_parser import LayoutParser
        
        print("✓ All analysis components imported successfully")
        
        # Test with real data files
        data_file = "test_data/RM5097.96HL.BNCT.1.CSV"
        layout_file = "test_data/RM5097_layout.csv"
        
        # Parse data
        bmg_parser = BMGOmega3Parser()
        layout_parser = LayoutParser()
        
        print(f"Loading data from {data_file}...")
        fluorescence_data = bmg_parser.parse_file(data_file)
        print(f"✓ Loaded {len(fluorescence_data.wells)} wells")
        
        print(f"Loading layout from {layout_file}...")
        layout_data = layout_parser.parse_file(layout_file)
        print(f"✓ Loaded layout for {len(layout_data)} wells")
        
        # Initialize analysis components
        curve_fitter = CurveFitter(timeout_seconds=2)
        threshold_analyzer = ThresholdAnalyzer(baseline_percentage=0.10)
        
        # Test analysis on wells that are likely to have data (not unused)
        time_points = np.array(fluorescence_data.time_points)
        
        # Find some non-unused wells to test
        test_wells = []
        for well_id in fluorescence_data.wells:
            if well_id in layout_data and layout_data[well_id].well_type != "unused":
                test_wells.append(well_id)
                if len(test_wells) >= 3:  # Test 3 non-unused wells
                    break
        
        if not test_wells:
            print("No non-unused wells found, testing first 3 wells anyway")
            test_wells = fluorescence_data.wells[:3]
        
        print(f"\nTesting analysis on wells: {test_wells}")
        
        for i, well_id in enumerate(test_wells):
            print(f"\n--- Analyzing well {well_id} ---")
            
            # Get well type from layout
            well_type = "unknown"
            if well_id in layout_data:
                well_type = layout_data[well_id].well_type
            print(f"Well type: {well_type}")
            
            # Skip unused wells
            if well_type == "unused":
                print("Skipping unused well")
                continue
            
            # Extract fluorescence values
            fluo_values = fluorescence_data.measurements[i, :]
            print(f"Fluorescence range: {np.min(fluo_values):.1f} - {np.max(fluo_values):.1f}")
            
            # Test curve fitting
            print("Running curve fitting...")
            curve_result = curve_fitter.fit_curve(time_points, fluo_values)
            print(f"Curve fit success: {curve_result.success}")
            if curve_result.success:
                print(f"R-squared: {curve_result.r_squared:.4f}")
                print(f"Fitted curve length: {len(curve_result.fitted_curve) if curve_result.fitted_curve is not None else 'None'}")
            else:
                print(f"Curve fit error: {curve_result.error_message}")
            
            # Test threshold analysis
            print("Running threshold analysis...")
            threshold_result = threshold_analyzer.analyze_threshold_crossing(
                time_points, fluo_values, method="linear")
            print(f"Threshold analysis success: {threshold_result.success}")
            if threshold_result.success:
                print(f"Crossing time: {threshold_result.crossing_time:.2f} hours")
                print(f"Threshold value: {threshold_result.threshold_value:.1f}")
            else:
                print(f"Threshold analysis error: {threshold_result.error_message}")
        
        return True
        
    except Exception as e:
        print(f"✗ Analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run analysis debugging tests."""
    print("Starting Analysis Results Debugging")
    print("=" * 50)
    
    success = test_analysis_components()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Analysis components are working correctly!")
        print("The issue is likely in the GUI integration or plot display.")
    else:
        print("❌ Analysis components have issues that need to be fixed.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)