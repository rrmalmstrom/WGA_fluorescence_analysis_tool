#!/usr/bin/env python3
"""
Test script to verify the configurable QC threshold feature.

This script tests that wells C7-C9 can now get CP values when using
a lower QC threshold (e.g., 5% instead of 10%).
"""

import sys
import os
import numpy as np

# Add the fluorescence_tool to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_configurable_qc_threshold():
    """Test the configurable QC threshold with BioRad data."""
    print("🧪 TESTING CONFIGURABLE QC THRESHOLD")
    print("=" * 60)
    
    try:
        # Import required modules
        from fluorescence_tool.algorithms.curve_fitting import CurveFitter
        from fluorescence_tool.algorithms.threshold_analysis import ThresholdAnalyzer
        from fluorescence_tool.parsers.biorad_parser import BioRadParser
        from fluorescence_tool.parsers.layout_parser import LayoutParser
        
        print("✅ Successfully imported modules")
        
        # Load test data
        biorad_parser = BioRadParser()
        fluorescence_data = biorad_parser.parse_file("test_data/TEST01.BIORAD.FORMAT.1.txt", cycle_time_minutes=0.25)
        
        layout_parser = LayoutParser()
        layout_data = layout_parser.parse_file("test_data/tinyTEST01.BIORAD_layout.csv")
        
        print(f"✅ Loaded data: {fluorescence_data.measurements.shape[0]} wells, {fluorescence_data.measurements.shape[1]} time points")
        
        # Test wells C7, C8, C9 with different QC thresholds
        test_wells = ['C7', 'C8', 'C9']
        qc_thresholds = [10.0, 7.0, 5.0]  # Test 10%, 7%, and 5%
        
        print(f"\n🔍 TESTING WELLS: {', '.join(test_wells)}")
        print("=" * 40)
        
        for qc_threshold in qc_thresholds:
            print(f"\n--- Testing QC Threshold: {qc_threshold}% ---")
            
            # Initialize components with the test threshold
            curve_fitter = CurveFitter(timeout_seconds=5)
            threshold_analyzer = ThresholdAnalyzer(baseline_percentage=qc_threshold/100.0)
            
            results = {}
            
            for well_id in test_wells:
                if well_id in fluorescence_data.wells:
                    well_idx = fluorescence_data.wells.index(well_id)
                    time_points = np.array(fluorescence_data.time_points)
                    fluo_values = fluorescence_data.measurements[well_idx, :]
                    
                    # Fit curve
                    curve_result = curve_fitter.fit_curve(time_points, fluo_values)
                    
                    if curve_result.success:
                        # Test threshold analysis with the configured QC threshold
                        threshold_result = threshold_analyzer.analyze_threshold_crossing_with_fitted_curve(
                            time_points, fluo_values, curve_result.parameters, method="qc_second_derivative")
                        
                        results[well_id] = {
                            'success': threshold_result.success,
                            'cp_time': threshold_result.crossing_time,
                            'error': threshold_result.error_message
                        }
                        
                        status = "✅ PASS" if threshold_result.success else "❌ FAIL"
                        cp_text = f"CP: {threshold_result.crossing_time:.2f}" if threshold_result.success else f"Error: {threshold_result.error_message}"
                        print(f"  {well_id}: {status} - {cp_text}")
                    else:
                        results[well_id] = {'success': False, 'cp_time': None, 'error': 'Curve fitting failed'}
                        print(f"  {well_id}: ❌ FAIL - Curve fitting failed")
            
            # Summary for this threshold
            successful_wells = [w for w, r in results.items() if r['success']]
            print(f"  Summary: {len(successful_wells)}/{len(test_wells)} wells got CP values")
        
        print(f"\n🎉 CONFIGURABLE QC THRESHOLD TEST COMPLETED!")
        print("Expected behavior:")
        print("  - 10% threshold: C7-C9 should FAIL (original issue)")
        print("  - 7% threshold: C7 should PASS, C8-C9 might FAIL")
        print("  - 5% threshold: C7-C8 should PASS, C9 might FAIL")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_configurable_qc_threshold()