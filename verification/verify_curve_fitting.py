#!/usr/bin/env python3
"""
Curve Fitting Verification Script
Compares NEW curve fitting algorithm with original script logic
"""

import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Original sigmoid function from analyze_fluorescence_data.py
def sigmoid_5param_original(x, a, b, c, d, e):
    """Original 5-parameter sigmoid function"""
    try:
        # Limit b to prevent overflow in exp
        b = max(min(b, 10), -10)
        # Calculate exponent with overflow protection
        exp_val = np.exp(-b * (x - c))
        # Handle division by zero or very small numbers
        denom = 1 + exp_val
        result = a / denom + d + e * x
        # Check for NaN or inf values
        if not np.all(np.isfinite(result)):
            raise ValueError("Overflow detected in sigmoid calculation")
        return result
    except Exception as e:
        print(f"Error in sigmoid calculation: {e}")
        return np.full_like(x, np.nan)

def fit_curve_original_method(time_points, fluo_values):
    """Fit curve using the original script method"""
    print("Fitting with ORIGINAL method...")
    
    try:
        # Check if there's enough variation in the data to fit a curve
        if np.max(fluo_values) - np.min(fluo_values) < 0.1:
            return None
        
        # Use the first fit attempt from original script
        initial_guess = [
            np.max(fluo_values) - np.min(fluo_values),  # a: range of values
            1.0,  # b: growth rate
            time_points[np.argmax(fluo_values)],  # c: midpoint
            np.min(fluo_values),  # d: baseline
            0.0  # e: linear component
        ]
        
        bounds = ([0, 0, min(time_points), min(fluo_values), -np.inf],
                 [np.inf, np.inf, max(time_points), max(fluo_values), np.inf])
        
        # Fit the curve
        popt, pcov = curve_fit(
            sigmoid_5param_original,
            np.array(time_points),
            np.array(fluo_values),
            p0=initial_guess,
            bounds=bounds,
            maxfev=5000
        )
        
        # Calculate R-squared
        fitted_values = sigmoid_5param_original(np.array(time_points), *popt)
        ss_res = np.sum((np.array(fluo_values) - fitted_values) ** 2)
        ss_tot = np.sum((np.array(fluo_values) - np.mean(fluo_values)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Calculate fit error
        fit_error = np.sum((np.array(fluo_values) - fitted_values)**2)
        
        return {
            'success': True,
            'parameters': popt,
            'fitted_curve': fitted_values,
            'r_squared': r_squared,
            'fit_error': fit_error,
            'strategy_used': 'original_standard'
        }
        
    except Exception as e:
        print(f"Original fitting failed: {e}")
        return {
            'success': False,
            'error_message': str(e),
            'parameters': None,
            'fitted_curve': None,
            'r_squared': 0,
            'fit_error': np.inf,
            'strategy_used': 'failed'
        }

def fit_curve_new_method(time_points, fluo_values):
    """Fit curve using the NEW fluorescence tool algorithm"""
    print("Fitting with NEW method...")
    
    try:
        from fluorescence_tool.algorithms.curve_fitting import CurveFitter
        
        fitter = CurveFitter()
        result = fitter.fit_curve(
            time_points=np.array(time_points),
            fluo_values=np.array(fluo_values)
        )
        
        # Calculate fitted curve if successful
        fitted_curve = None
        if result.success and result.parameters:
            try:
                from fluorescence_tool.algorithms.curve_fitting import CurveFitter
                fitter = CurveFitter()
                fitted_curve = fitter.sigmoid_5param(np.array(time_points), *result.parameters)
            except Exception as e:
                print(f"Failed to calculate fitted curve: {e}")
        
        return {
            'success': result.success,
            'parameters': result.parameters if result.success else None,
            'fitted_curve': fitted_curve,
            'r_squared': result.r_squared if result.success else 0,
            'fit_error': result.fit_error if result.success else np.inf,
            'strategy_used': result.strategy_used if result.success else 'failed',
            'error_message': result.error_message if not result.success else None
        }
        
    except Exception as e:
        print(f"❌ NEW fitting error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error_message': str(e),
            'parameters': None,
            'fitted_curve': None,
            'r_squared': 0,
            'fit_error': np.inf,
            'strategy_used': 'failed'
        }

def compare_fitting_results(original, new, time_points, fluo_values, well_id):
    """Compare the results from both fitting methods"""
    print(f"\n" + "="*60)
    print(f" COMPARISON RESULTS - Well {well_id}")
    print("="*60)
    
    if new is None:
        print("❌ NEW fitting failed - cannot compare")
        return False
    
    # Compare success status
    print(f"Success - Original: {original['success']}, New: {new['success']}")
    
    if not original['success'] and not new['success']:
        print("✅ Both methods failed consistently")
        return True
    
    if original['success'] != new['success']:
        print(f"❌ Success status mismatch")
        if original['success']:
            print(f"  Original succeeded, New failed: {new.get('error_message', 'Unknown error')}")
        else:
            print(f"  New succeeded, Original failed: {original.get('error_message', 'Unknown error')}")
        return False
    
    if not original['success']:  # Both failed
        return True
    
    # Compare R-squared values
    r2_diff = abs(original['r_squared'] - new['r_squared'])
    r2_match = r2_diff < 0.1  # Allow 10% difference
    print(f"R-squared - Original: {original['r_squared']:.3f}, New: {new['r_squared']:.3f}, Diff: {r2_diff:.3f}")
    print(f"R-squared match: {'✅' if r2_match else '❌'}")
    
    # Compare parameters (allow some tolerance)
    params_match = True
    if original['parameters'] is not None and new['parameters'] is not None:
        param_names = ['a', 'b', 'c', 'd', 'e']
        for i, name in enumerate(param_names):
            orig_val = original['parameters'][i]
            new_val = new['parameters'][i]
            rel_diff = abs(orig_val - new_val) / (abs(orig_val) + 1e-10)
            
            if rel_diff > 0.5:  # Allow 50% relative difference
                params_match = False
                print(f"❌ Parameter {name} differs significantly: {orig_val:.3f} vs {new_val:.3f}")
    
    if params_match:
        print("✅ Parameters are reasonably similar")
    
    # Compare fit quality
    fit_error_ratio = new['fit_error'] / (original['fit_error'] + 1e-10)
    fit_quality_match = 0.5 < fit_error_ratio < 2.0  # Within 2x
    print(f"Fit error - Original: {original['fit_error']:.2e}, New: {new['fit_error']:.2e}")
    print(f"Fit quality match: {'✅' if fit_quality_match else '❌'}")
    
    # Overall assessment
    overall_success = r2_match and params_match and fit_quality_match
    print(f"Overall comparison: {'✅ PASS' if overall_success else '❌ FAIL'}")
    
    return overall_success

def create_comparison_plot(original, new, time_points, fluo_values, well_id, output_dir):
    """Create a comparison plot of the fitting results"""
    try:
        plt.figure(figsize=(12, 8))
        
        # Plot original data
        plt.scatter(time_points, fluo_values, alpha=0.7, color='blue', label='Data', s=30)
        
        # Plot fitted curves if available
        if original['success'] and original['fitted_curve'] is not None:
            plt.plot(time_points, original['fitted_curve'], 'r-', linewidth=2, 
                    label=f'Original Fit (R²={original["r_squared"]:.3f})')
        
        if new['success'] and new['fitted_curve'] is not None:
            plt.plot(time_points, new['fitted_curve'], 'g--', linewidth=2, 
                    label=f'New Fit (R²={new["r_squared"]:.3f})')
        
        plt.xlabel('Time (minutes)')
        plt.ylabel('Fluorescence')
        plt.title(f'Curve Fitting Comparison - Well {well_id}')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Save plot
        plot_path = output_dir / f'curve_fit_comparison_{well_id}.png'
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"Comparison plot saved: {plot_path}")
        
    except Exception as e:
        print(f"Failed to create comparison plot: {e}")

def main():
    """Main verification function"""
    print("="*60)
    print(" CURVE FITTING VERIFICATION")
    print("="*60)
    
    # Parse BMG data first
    try:
        from fluorescence_tool.parsers.bmg_parser import BMGOmega3Parser
        
        project_root = Path(__file__).parent.parent.parent
        bmg_file = project_root / "example_input_files" / "RM5097.96HL.BNCT.1.CSV"
        
        if not bmg_file.exists():
            print(f"❌ BMG file not found: {bmg_file}")
            return False
        
        parser = BMGOmega3Parser()
        data = parser.parse_file(str(bmg_file))
        
        print(f"✅ Loaded BMG data: {len(data.wells)} wells, {len(data.time_points)} time points")
        
    except Exception as e:
        print(f"❌ Failed to load BMG data: {e}")
        return False
    
    # Create output directory
    output_dir = Path(__file__).parent / "verification_output"
    output_dir.mkdir(exist_ok=True)
    
    # Test curve fitting on a few wells with good data
    test_wells = []
    for i, well_id in enumerate(data.wells[:20]):  # Check first 20 wells
        measurements = data.measurements[i]
        if np.max(measurements) - np.min(measurements) > 10:  # Good signal variation
            test_wells.append((i, well_id))
        if len(test_wells) >= 5:  # Test 5 wells
            break
    
    if not test_wells:
        print("❌ No wells with sufficient signal variation found")
        return False
    
    print(f"Testing curve fitting on {len(test_wells)} wells with good signal")
    
    # Compare fitting results
    successes = 0
    total_tests = len(test_wells)
    
    for well_idx, well_id in test_wells:
        print(f"\nTesting well {well_id}...")
        
        time_points = data.time_points
        fluo_values = data.measurements[well_idx]
        
        # Fit with both methods
        original_result = fit_curve_original_method(time_points, fluo_values)
        new_result = fit_curve_new_method(time_points, fluo_values)
        
        # Compare results
        success = compare_fitting_results(original_result, new_result, time_points, fluo_values, well_id)
        
        if success:
            successes += 1
        
        # Create comparison plot
        create_comparison_plot(original_result, new_result, time_points, fluo_values, well_id, output_dir)
    
    # Overall assessment
    success_rate = successes / total_tests
    overall_success = success_rate >= 0.8  # 80% success rate
    
    print("\n" + "="*60)
    print(f" CURVE FITTING VERIFICATION SUMMARY")
    print("="*60)
    print(f"Tests passed: {successes}/{total_tests} ({success_rate:.1%})")
    print(f"Overall result: {'✅ PASS' if overall_success else '❌ FAIL'}")
    print("="*60)
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)