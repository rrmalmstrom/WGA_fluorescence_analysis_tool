#!/usr/bin/env python3
"""
Test CP offset issue with synthetic data to isolate the problem.
"""

import numpy as np
import matplotlib.pyplot as plt
from fluorescence_tool.algorithms.curve_fitting import CurveFitter
from fluorescence_tool.algorithms.threshold_analysis import ThresholdAnalyzer

def create_synthetic_sigmoid_data():
    """Create synthetic sigmoid data with known parameters."""
    # Known sigmoid parameters: [a, b, c, d, e]
    # a = baseline, b = slope, c = inflection point, d = max, e = asymmetry
    true_params = [1000.0, 0.5, 15.0, 5000.0, 1.0]
    
    # Time points (similar to real data)
    time_points = np.linspace(0, 30, 31)  # 0 to 30 in steps of 1
    
    # Generate perfect sigmoid curve
    curve_fitter = CurveFitter()
    true_curve = curve_fitter.sigmoid_5param(time_points, *true_params)
    
    # Add small amount of noise
    np.random.seed(42)  # For reproducible results
    noise = np.random.normal(0, 50, len(true_curve))  # Small noise
    noisy_data = true_curve + noise
    
    return time_points, noisy_data, true_params, true_curve

def test_cp_offset_with_synthetic_data():
    """Test CP calculation and plotting with synthetic data."""
    
    print("=== CP Offset Test with Synthetic Data ===")
    
    # Create synthetic data
    time_points, fluo_values, true_params, true_curve = create_synthetic_sigmoid_data()
    
    print(f"Time points: {time_points[0]:.1f} to {time_points[-1]:.1f}")
    print(f"Fluorescence range: {fluo_values.min():.1f} to {fluo_values.max():.1f}")
    print(f"True parameters: {true_params}")
    
    # Step 1: Fit curve to synthetic data
    curve_fitter = CurveFitter(timeout_seconds=5)
    curve_result = curve_fitter.fit_curve(time_points, fluo_values)
    
    print(f"\nCurve fitting success: {curve_result.success}")
    if curve_result.success:
        print(f"Fitted parameters: {curve_result.parameters}")
        print(f"Parameter differences from true:")
        for i, (true, fitted) in enumerate(zip(true_params, curve_result.parameters)):
            diff = abs(fitted - true)
            print(f"  Param {i}: true={true:.2f}, fitted={fitted:.2f}, diff={diff:.2f}")
        
        # Generate fitted curve for plotting
        fitted_curve = curve_fitter.sigmoid_5param(time_points, *curve_result.parameters)
        
        # Step 2: Calculate CP using new method with fitted parameters
        threshold_analyzer = ThresholdAnalyzer(baseline_percentage=0.10)
        threshold_result = threshold_analyzer.analyze_threshold_crossing_with_fitted_curve(
            time_points, fluo_values, curve_result.parameters, method="qc_second_derivative")
        
        print(f"\nThreshold analysis success: {threshold_result.success}")
        if threshold_result.success:
            cp_time = threshold_result.crossing_time
            print(f"Calculated CP time: {cp_time:.2f}")
            
            # Calculate CP fluorescence using SAME sigmoid as plotting (this is the key test)
            cp_fluorescence_sigmoid = curve_fitter.sigmoid_5param(np.array([cp_time]), *curve_result.parameters)[0]
            print(f"CP fluorescence (sigmoid): {cp_fluorescence_sigmoid:.2f}")
            
            # Calculate CP fluorescence using interpolation from fitted curve array
            cp_fluorescence_interp = np.interp(cp_time, time_points, fitted_curve)
            print(f"CP fluorescence (interp): {cp_fluorescence_interp:.2f}")
            
            # This is the critical test - these should be identical or very close
            difference = abs(cp_fluorescence_sigmoid - cp_fluorescence_interp)
            print(f"Difference between sigmoid and interpolation: {difference:.6f}")
            
            if difference > 0.01:  # More than 0.01 difference indicates a problem
                print("WARNING: Significant difference detected - this could cause offset!")
            else:
                print("GOOD: Sigmoid and interpolation match closely")
            
            # Step 3: Test with true parameters (should be perfect)
            print(f"\n--- Testing with TRUE parameters ---")
            threshold_result_true = threshold_analyzer.analyze_threshold_crossing_with_fitted_curve(
                time_points, fluo_values, true_params, method="qc_second_derivative")
            
            if threshold_result_true.success:
                cp_time_true = threshold_result_true.crossing_time
                cp_fluorescence_true = curve_fitter.sigmoid_5param(np.array([cp_time_true]), *true_params)[0]
                print(f"CP with true params: time={cp_time_true:.2f}, fluor={cp_fluorescence_true:.2f}")
                
                # Compare fitted vs true CP
                cp_time_diff = abs(cp_time - cp_time_true)
                cp_fluor_diff = abs(cp_fluorescence_sigmoid - cp_fluorescence_true)
                print(f"CP differences (fitted vs true): time={cp_time_diff:.2f}, fluor={cp_fluor_diff:.2f}")
            
            # Create comprehensive debug plot
            plt.figure(figsize=(15, 10))
            
            # Main plot
            plt.subplot(2, 2, 1)
            plt.plot(time_points, fluo_values, 'o', alpha=0.7, label='Synthetic data (with noise)')
            plt.plot(time_points, true_curve, '--', linewidth=2, label='True curve', color='green')
            plt.plot(time_points, fitted_curve, '-', linewidth=2, label='Fitted curve', color='blue')
            plt.plot(cp_time, cp_fluorescence_sigmoid, 'ro', markersize=10, label=f'CP (sigmoid): ({cp_time:.2f}, {cp_fluorescence_sigmoid:.1f})')
            plt.plot(cp_time, cp_fluorescence_interp, 'bs', markersize=8, label=f'CP (interp): ({cp_time:.2f}, {cp_fluorescence_interp:.1f})')
            plt.xlabel('Time')
            plt.ylabel('Fluorescence')
            plt.title('CP Offset Debug - Synthetic Data')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Zoomed view around CP
            plt.subplot(2, 2, 2)
            zoom_range = 3  # +/- 3 time units around CP
            zoom_mask = (time_points >= cp_time - zoom_range) & (time_points <= cp_time + zoom_range)
            plt.plot(time_points[zoom_mask], fluo_values[zoom_mask], 'o', alpha=0.7, label='Data')
            plt.plot(time_points[zoom_mask], fitted_curve[zoom_mask], '-', linewidth=2, label='Fitted curve')
            plt.plot(cp_time, cp_fluorescence_sigmoid, 'ro', markersize=10, label='CP (sigmoid)')
            plt.plot(cp_time, cp_fluorescence_interp, 'bs', markersize=8, label='CP (interp)')
            plt.xlabel('Time')
            plt.ylabel('Fluorescence')
            plt.title(f'Zoomed View Around CP (±{zoom_range} time units)')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Second derivative plot
            plt.subplot(2, 2, 3)
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
            
            # Parameter comparison
            plt.subplot(2, 2, 4)
            param_names = ['a (baseline)', 'b (slope)', 'c (inflection)', 'd (max)', 'e (asymmetry)']
            x_pos = np.arange(len(param_names))
            plt.bar(x_pos - 0.2, true_params, 0.4, label='True', alpha=0.7)
            plt.bar(x_pos + 0.2, curve_result.parameters, 0.4, label='Fitted', alpha=0.7)
            plt.xlabel('Parameters')
            plt.ylabel('Value')
            plt.title('Parameter Comparison')
            plt.xticks(x_pos, param_names, rotation=45)
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig('cp_offset_synthetic_debug.png', dpi=150, bbox_inches='tight')
            print(f"\nDebug plot saved as 'cp_offset_synthetic_debug.png'")
            
            return difference < 0.01  # Return True if no significant offset detected
        else:
            print(f"Threshold analysis failed: {threshold_result.error_message}")
            return False
    else:
        print(f"Curve fitting failed: {curve_result.error_message}")
        return False

if __name__ == "__main__":
    success = test_cp_offset_with_synthetic_data()
    if success:
        print("\n✓ SUCCESS: No significant CP offset detected with synthetic data")
    else:
        print("\n✗ FAILURE: CP offset issue detected or analysis failed")