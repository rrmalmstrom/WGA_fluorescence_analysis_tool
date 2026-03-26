#!/usr/bin/env python3
"""
Test pass/fail analysis with the actual data structure from main_window.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fluorescence_tool.core.models import PassFailThresholds
from fluorescence_tool.algorithms.pass_fail_analysis import PassFailAnalyzer
from fluorescence_tool.algorithms.curve_fitting import CurveFitResult
from fluorescence_tool.algorithms.threshold_analysis import ThresholdResult
import numpy as np

def test_with_real_data_structure():
    """Test pass/fail with the actual data structure from main_window.py"""
    
    # Create realistic CurveFitResult objects (like what comes from curve fitting)
    good_curve_result = CurveFitResult(
        well_id="A1",
        fitted_params=np.array([1000, 0.1, 30, 2000, 1]),
        fitted_curve=np.array([1000, 1100, 1200, 1500, 2000]),
        r_squared=0.95,
        crossing_point=25.0,  # This will be overridden by threshold_result
        threshold_value=1500.0,
        delta_fluorescence=1000.0,  # 2000 - 1000 = 1000 (should pass > 500)
        fit_quality="excellent",
        convergence_info={"success": True}
    )
    
    bad_curve_result = CurveFitResult(
        well_id="A2", 
        fitted_params=np.array([1000, 0.1, 450, 1200, 1]),
        fitted_curve=np.array([1000, 1050, 1100, 1150, 1200]),
        r_squared=0.85,
        crossing_point=450.0,  # This will be overridden by threshold_result
        threshold_value=1100.0,
        delta_fluorescence=200.0,  # 1200 - 1000 = 200 (should fail <= 500)
        fit_quality="good",
        convergence_info={"success": True}
    )
    
    # Create realistic ThresholdResult objects
    good_threshold_result = ThresholdResult(
        success=True,
        crossing_time=25.0,  # Should pass (< 400)
        threshold_value=1500.0,
        baseline_value=1000.0,
        method="linear"
    )
    
    bad_threshold_result = ThresholdResult(
        success=True,
        crossing_time=450.0,  # Should fail (>= 400)
        threshold_value=1100.0,
        baseline_value=1000.0,
        method="linear"
    )
    
    # Create analysis results in the exact format from main_window.py
    analysis_results = {
        'fluorescence_data': None,
        'layout_data': [],
        'curve_fits': {
            'A1': {
                'curve_result': good_curve_result,
                'threshold_result': good_threshold_result,
                'fitted_curve': np.array([1000, 1100, 1200, 1500, 2000]),
                'crossing_point': good_threshold_result.crossing_time,  # 25.0
                'threshold_value': good_threshold_result.threshold_value  # 1500.0
            },
            'A2': {
                'curve_result': bad_curve_result,
                'threshold_result': bad_threshold_result,
                'fitted_curve': np.array([1000, 1050, 1100, 1150, 1200]),
                'crossing_point': bad_threshold_result.crossing_time,  # 450.0
                'threshold_value': bad_threshold_result.threshold_value  # 1100.0
            }
        }
    }
    
    # Test pass/fail analysis
    thresholds = PassFailThresholds(cp_threshold=400.0, fluorescence_change_threshold=500.0, enabled=True)
    analyzer = PassFailAnalyzer(thresholds)
    
    print("=== Testing Pass/Fail with Real Data Structure ===")
    print(f"CP Threshold: {thresholds.cp_threshold} minutes (below = PASS)")
    print(f"Fluorescence Change Threshold: {thresholds.fluorescence_change_threshold} (above = PASS)")
    print()
    
    for well_id in ['A1', 'A2']:
        print(f"--- Testing Well {well_id} ---")
        
        # Get the data as stored by main_window.py
        well_data = analysis_results['curve_fits'][well_id]
        cp_from_threshold = well_data['crossing_point']
        curve_result = well_data['curve_result']
        delta_fluor = curve_result.delta_fluorescence if curve_result else None
        
        print(f"CP from threshold analysis: {cp_from_threshold}")
        print(f"Delta fluorescence from curve result: {delta_fluor}")
        
        # Test our pass/fail logic
        result = analyzer.analyze_well(well_id, analysis_results)
        
        print(f"CP Passed: {result.cp_passed} ({result.cp_value} < {thresholds.cp_threshold})")
        print(f"Fluorescence Passed: {result.fluorescence_change_passed} ({result.fluorescence_change_value} > {thresholds.fluorescence_change_threshold})")
        print(f"Overall Passed: {result.passed}")
        print(f"Failure Reason: {result.failure_reason}")
        print()
    
    # Test summary
    all_results = analyzer.analyze_all_wells(analysis_results)
    summary = analyzer.get_summary_statistics(all_results)
    
    print("=== Expected Results ===")
    print("A1: CP=25 < 400 ✓, Delta=1000 > 500 ✓ → PASS")
    print("A2: CP=450 >= 400 ✗, Delta=200 <= 500 ✗ → FAIL")
    print()
    print("=== Actual Results ===")
    print(f"Total Wells: {summary['total_wells']}")
    print(f"Analyzed Wells: {summary['analyzed_wells']}")
    print(f"Passed Wells: {summary['passed_wells']}")
    print(f"Failed Wells: {summary['failed_wells']}")
    print(f"Pass Rate: {summary['pass_rate']:.1f}%")

if __name__ == "__main__":
    test_with_real_data_structure()