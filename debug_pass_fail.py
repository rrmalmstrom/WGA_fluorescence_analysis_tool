#!/usr/bin/env python3
"""
Debug script to test pass/fail analysis logic.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fluorescence_tool.core.models import PassFailThresholds
from fluorescence_tool.algorithms.pass_fail_analysis import PassFailAnalyzer

def debug_pass_fail_analysis():
    """Debug the pass/fail analysis with sample data."""
    
    # Create sample analysis results structure (mimicking what comes from main window)
    sample_analysis_results = {
        'fluorescence_data': None,  # Not needed for pass/fail
        'layout_data': [],  # Not needed for pass/fail
        'curve_fits': {
            'A1': {
                'curve_result': type('obj', (object,), {
                    'success': True,
                    'delta_fluorescence': 1200.0  # Should pass (> 500)
                })(),
                'threshold_result': None,
                'fitted_curve': None,
                'crossing_point': 25.0,  # Should pass (< 400)
                'threshold_value': 100.0
            },
            'A2': {
                'curve_result': type('obj', (object,), {
                    'success': True,
                    'delta_fluorescence': 300.0  # Should fail (<= 500)
                })(),
                'threshold_result': None,
                'fitted_curve': None,
                'crossing_point': 450.0,  # Should fail (>= 400)
                'threshold_value': 100.0
            },
            'A3': {
                'curve_result': type('obj', (object,), {
                    'success': True,
                    'delta_fluorescence': 800.0  # Should pass (> 500)
                })(),
                'threshold_result': None,
                'fitted_curve': None,
                'crossing_point': 350.0,  # Should pass (< 400)
                'threshold_value': 100.0
            }
        }
    }
    
    # Create pass/fail analyzer with default thresholds
    thresholds = PassFailThresholds(cp_threshold=400.0, fluorescence_change_threshold=500.0, enabled=True)
    analyzer = PassFailAnalyzer(thresholds)
    
    print("=== Pass/Fail Analysis Debug ===")
    print(f"CP Threshold: {thresholds.cp_threshold} minutes (below = PASS)")
    print(f"Fluorescence Change Threshold: {thresholds.fluorescence_change_threshold} (above = PASS)")
    print()
    
    # Analyze each well
    for well_id in sample_analysis_results['curve_fits'].keys():
        print(f"--- Analyzing Well {well_id} ---")
        
        # Get raw data
        well_data = sample_analysis_results['curve_fits'][well_id]
        cp_value = well_data.get('crossing_point')
        curve_result = well_data.get('curve_result')
        fluor_change = curve_result.delta_fluorescence if curve_result else None
        
        print(f"Raw CP Value: {cp_value}")
        print(f"Raw Fluorescence Change: {fluor_change}")
        
        # Analyze with our logic
        result = analyzer.analyze_well(well_id, sample_analysis_results)
        
        print(f"CP Passed: {result.cp_passed} (CP {result.cp_value} < {thresholds.cp_threshold})")
        print(f"Fluorescence Passed: {result.fluorescence_change_passed} (Change {result.fluorescence_change_value} > {thresholds.fluorescence_change_threshold})")
        print(f"Overall Passed: {result.passed}")
        print(f"Failure Reason: {result.failure_reason}")
        print()
    
    # Test summary statistics
    all_results = analyzer.analyze_all_wells(sample_analysis_results)
    summary = analyzer.get_summary_statistics(all_results)
    
    print("=== Summary Statistics ===")
    print(f"Total Wells: {summary['total_wells']}")
    print(f"Analyzed Wells: {summary['analyzed_wells']}")
    print(f"Passed Wells: {summary['passed_wells']}")
    print(f"Failed Wells: {summary['failed_wells']}")
    print(f"Pass Rate: {summary['pass_rate']:.1f}%")

if __name__ == "__main__":
    debug_pass_fail_analysis()