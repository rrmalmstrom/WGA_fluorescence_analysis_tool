#!/usr/bin/env python3
"""
Debug script to test CP calculation and identify offset issues.
"""

import numpy as np
import matplotlib.pyplot as plt
from fluorescence_tool.algorithms.curve_fitting import CurveFitter
from fluorescence_tool.algorithms.threshold_analysis import ThresholdAnalyzer
from fluorescence_tool.parsers.bmg_parser import BMGOmega3Parser
from fluorescence_tool.parsers.layout_parser import LayoutParser

def test_cp_calculation():
    """Test CP calculation with real data to debug offset issues."""
    
    print("=== CP Calculation Debug Test ===")
    
    # Load test data
    try:
        # Load fluorescence data
        bmg_parser = BMGOmega3Parser()
        fluorescence_data = bmg_parser.parse_file("test_data/RM5097.96HL.BNCT.1.CSV")
        
        # Load layout data
        layout_parser = LayoutParser()
        layout_data = layout_parser.parse_file("test_data/smallRM5097_layout.csv")
        
        print(f"Loaded data: {fluorescence_data.measurements.shape[0]} wells, {fluorescence_data.measurements.shape[1]} time points")
        print(f"Time points: {fluorescence_data.time_points[:5]}... to {fluorescence_data.time_points[-5:]}")
        
        # Find a well that is not "unused" and has good signal
        test_well_idx = None
        test_well_id = None
        
        for i, well_id in enumerate(fluorescence_data.wells):
            if well_id in layout_data:
                well_info = layout_data[well_id]
                well_type = well_info.well_type
                if well_type.lower() != "unused":
                    fluo_values = fluorescence_data.measurements[i, :]
                    # Check if well has significant signal change
                    if fluo_values.max() - fluo_values.min() > 100:  # Arbitrary threshold for signal
                        test_well_idx = i
                        test_well_id = well_id
                        print(f"Found test well: {well_id} (type: {well_type})")
                        break
        
        if test_well_idx is None:
            print("No suitable test wells found!")
            return False
            
        time_points = fluorescence_data.time_points
        fluo_values = fluorescence_data.measurements[test_well_idx, :]
        
        print(f"\n=== Testing well {test_well_id} ===")
        print(f"Fluorescence range: {fluo_values.min():.2f} to {fluo_values.max():.2f}")
        
        # Step 1: Fit curve
        curve_fitter = CurveFitter(timeout_seconds=5)
        curve_result = curve_fitter.fit_curve(time_points, fluo_values)
        
        print(f"Curve fitting success: {curve_result.success}")
        if curve_result.success:
            print(f"Fitted parameters: {curve_result.parameters}")
            
            # Generate fitted curve for plotting
            fitted_curve = curve_fitter.sigmoid_5param(time_points, *curve_result.parameters)
            
            # Step 2: Calculate CP using new method
            threshold_analyzer = ThresholdAnalyzer(baseline_percentage=0.10)
            threshold_result = threshold_analyzer.analyze_threshold_crossing_with_fitted_curve(
                time_points, fluo_values, curve_result.parameters, method="qc_second_derivative")
            
            print(f"\nThreshold analysis success: {threshold_result.success}")
            if threshold_result.success:
                cp_time = threshold_result.crossing_time
                print(f"Calculated CP time: {cp_time:.2f}")
                
                # Calculate CP fluorescence using same sigmoid as plotting
                cp_fluorescence = curve_fitter.sigmoid_5param(np.array([cp_time]), *curve_result.parameters)[0]
                print(f"CP fluorescence (sigmoid): {cp_fluorescence:.2f}")
                
                # Compare with interpolation from fitted curve
                cp_fluorescence_interp = np.interp(cp_time, time_points, fitted_curve)
                print(f"CP fluorescence (interp): {cp_fluorescence_interp:.2f}")
                print(f"Difference: {abs(cp_fluorescence - cp_fluorescence_interp):.6f}")
                
                # Create debug plot
                plt.figure(figsize=(12, 8))
                
                # Plot raw data
                plt.subplot(2, 1, 1)
                plt.plot(time_points, fluo_values, 'o-', alpha=0.7, label='Raw data')
                plt.plot(time_points, fitted_curve, '-', linewidth=2, label='Fitted curve')
                plt.plot(cp_time, cp_fluorescence, 'ro', markersize=10, label=f'CP (sigmoid): ({cp_time:.2f}, {cp_fluorescence:.2f})')
                plt.plot(cp_time, cp_fluorescence_interp, 'bs', markersize=8, label=f'CP (interp): ({cp_time:.2f}, {cp_fluorescence_interp:.2f})')
                plt.xlabel('Time')
                plt.ylabel('Fluorescence')
                plt.title(f'CP Debug Plot - Well {test_well_id}')
                plt.legend()
                plt.grid(True, alpha=0.3)
                
                # Plot second derivative
                plt.subplot(2, 1, 2)
                fine_time = np.linspace(time_points[0], time_points[-1], len(time_points) * 20)
                fine_fitted = curve_fitter.sigmoid_5param(fine_time, *curve_result.parameters)
                
                from scipy.interpolate import CubicSpline
                spline = CubicSpline(fine_time, fine_fitted)
                second_derivative = spline(fine_time, nu=2)
                
                plt.plot(fine_time, second_derivative, '-', label='Second derivative')
                plt.axvline(cp_time, color='red', linestyle='--', label=f'CP at {cp_time:.2f}')
                plt.xlabel('Time')
                plt.ylabel('Second Derivative')
                plt.title('Second Derivative Analysis')
                plt.legend()
                plt.grid(True, alpha=0.3)
                
                plt.tight_layout()
                plt.savefig('cp_debug_analysis.png', dpi=150, bbox_inches='tight')
                print(f"\nDebug plot saved as 'cp_debug_analysis.png'")
                
                return True
            else:
                print(f"Threshold analysis failed: {threshold_result.error_message}")
                return False
        else:
            print(f"Curve fitting failed: {curve_result.error_message}")
            return False
            
    except Exception as e:
        print(f"Error in test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_cp_calculation()