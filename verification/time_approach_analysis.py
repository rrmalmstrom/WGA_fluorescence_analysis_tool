#!/usr/bin/env python3
"""
Time Approach Analysis
Compares the advantages/disadvantages of using column indices vs actual time values
"""

import numpy as np
from scipy.optimize import curve_fit

def sigmoid_5param(x, a, b, c, d, e):
    """5-parameter sigmoid function"""
    try:
        b = max(min(b, 10), -10)
        exp_val = np.exp(-b * (x - c))
        denom = 1 + exp_val
        result = a / denom + d + e * x
        return result
    except:
        return np.full_like(x, np.nan)

def analyze_time_approaches():
    """Analyze advantages/disadvantages of different time approaches"""
    print("="*80)
    print(" TIME APPROACH ANALYSIS: Column Indices vs Actual Time")
    print("="*80)
    
    # Sample fluorescence data (realistic values)
    fluo_values = np.array([3150, 3145, 3140, 3135, 3130, 3125, 3120, 3115, 3110, 3105, 
                           3100, 3095, 3090, 3085, 3080, 3075, 3070, 3065, 3060, 3055,
                           3050, 3100, 3200, 3400, 3700, 4100, 4500, 4800, 5000, 5100,
                           5150, 5180])
    
    # Approach 1: Column indices (original method)
    column_indices = np.arange(8, 8 + len(fluo_values))  # [8, 9, 10, ..., 39]
    
    # Approach 2: Actual time in minutes (NEW method)
    actual_time_minutes = np.array([0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 
                                   180, 195, 210, 225, 240, 255, 270, 285, 300, 315, 330, 
                                   345, 360, 375, 390, 405, 420, 435, 450, 465])
    
    print("APPROACH 1: Column Indices")
    print(f"Time points: {column_indices}")
    print(f"Range: {column_indices[0]} to {column_indices[-1]}")
    print(f"Spacing: uniform (1 unit)")
    
    print(f"\nAPPROACH 2: Actual Time (minutes)")
    print(f"Time points: {actual_time_minutes}")
    print(f"Range: {actual_time_minutes[0]} to {actual_time_minutes[-1]} minutes")
    print(f"Spacing: uniform (15 minutes)")
    
    # Fit curves with both approaches
    print(f"\n" + "="*80)
    print(" CURVE FITTING COMPARISON")
    print("="*80)
    
    # Fit with column indices
    try:
        initial_guess = [np.max(fluo_values) - np.min(fluo_values), 1.0, 
                        column_indices[np.argmax(fluo_values)], np.min(fluo_values), 0.0]
        popt1, _ = curve_fit(sigmoid_5param, column_indices, fluo_values, 
                            p0=initial_guess, maxfev=5000)
        fitted1 = sigmoid_5param(column_indices, *popt1)
        r2_1 = 1 - np.sum((fluo_values - fitted1)**2) / np.sum((fluo_values - np.mean(fluo_values))**2)
        print(f"Column Index Approach:")
        print(f"  Parameters: {popt1}")
        print(f"  R²: {r2_1:.6f}")
        print(f"  Midpoint parameter (c): {popt1[2]:.2f} (column index)")
    except Exception as e:
        print(f"Column Index Approach failed: {e}")
        popt1, r2_1 = None, 0
    
    # Fit with actual time
    try:
        initial_guess = [np.max(fluo_values) - np.min(fluo_values), 0.01, 
                        actual_time_minutes[np.argmax(fluo_values)], np.min(fluo_values), 0.0]
        popt2, _ = curve_fit(sigmoid_5param, actual_time_minutes, fluo_values, 
                            p0=initial_guess, maxfev=5000)
        fitted2 = sigmoid_5param(actual_time_minutes, *popt2)
        r2_2 = 1 - np.sum((fluo_values - fitted2)**2) / np.sum((fluo_values - np.mean(fluo_values))**2)
        print(f"\nActual Time Approach:")
        print(f"  Parameters: {popt2}")
        print(f"  R²: {r2_2:.6f}")
        print(f"  Midpoint parameter (c): {popt2[2]:.2f} minutes")
    except Exception as e:
        print(f"Actual Time Approach failed: {e}")
        popt2, r2_2 = None, 0
    
    # Analysis of advantages/disadvantages
    print(f"\n" + "="*80)
    print(" ADVANTAGES/DISADVANTAGES ANALYSIS")
    print("="*80)
    
    print("COLUMN INDEX APPROACH (Original):")
    print("✅ ADVANTAGES:")
    print("  • Simpler implementation (no time conversion needed)")
    print("  • Uniform spacing (1 unit between measurements)")
    print("  • Avoids potential time parsing errors")
    print("  • Computationally slightly faster")
    print("  • Works regardless of actual time intervals")
    
    print("\n❌ DISADVANTAGES:")
    print("  • Results are meaningless in real-world units")
    print("  • Cannot compare across different experiments with different time intervals")
    print("  • Crossing points are in arbitrary units (column numbers)")
    print("  • Parameters have no physical interpretation")
    print("  • Cannot extrapolate or interpolate to real time points")
    print("  • Confusing for users (what does 'crossing at 32.9' mean?)")
    
    print(f"\nACTUAL TIME APPROACH (NEW):")
    print("✅ ADVANTAGES:")
    print("  • Results have real-world meaning (minutes/hours)")
    print("  • Can compare across different experiments")
    print("  • Crossing points are interpretable (e.g., '358 minutes')")
    print("  • Parameters have physical meaning")
    print("  • Can extrapolate/interpolate to any time point")
    print("  • Scientifically accurate and publishable")
    print("  • Enables proper kinetic analysis")
    
    print("\n❌ DISADVANTAGES:")
    print("  • Requires proper time parsing and conversion")
    print("  • Slightly more complex implementation")
    print("  • Potential for time unit errors if not handled carefully")
    
    # Practical implications
    print(f"\n" + "="*80)
    print(" PRACTICAL IMPLICATIONS")
    print("="*80)
    
    if popt1 is not None and popt2 is not None:
        print("Curve Fitting Quality:")
        print(f"  Column Index R²: {r2_1:.6f}")
        print(f"  Actual Time R²:  {r2_2:.6f}")
        if abs(r2_1 - r2_2) < 0.001:
            print("  → Both approaches give essentially identical fit quality")
        
        print(f"\nParameter Interpretation:")
        print(f"  Column Index midpoint: {popt1[2]:.2f} (column number - meaningless)")
        print(f"  Actual Time midpoint:  {popt2[2]:.2f} minutes ({popt2[2]/60:.2f} hours)")
        print("  → Actual time provides interpretable results")
    
    print(f"\nRecommendation:")
    print("🎯 USE ACTUAL TIME APPROACH because:")
    print("   • Scientific accuracy and interpretability outweigh minor complexity")
    print("   • Results are meaningful and comparable across experiments")
    print("   • Modern computational power makes the overhead negligible")
    print("   • Essential for publication and regulatory compliance")
    print("   • Enables proper kinetic modeling and analysis")

if __name__ == "__main__":
    analyze_time_approaches()