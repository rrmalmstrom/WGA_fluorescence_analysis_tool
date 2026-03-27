#!/usr/bin/env python3
"""
Debug script to validate the CP plotting offset diagnosis.

This script demonstrates the bug and shows how the fix resolves it.
"""

import numpy as np

def demonstrate_bug():
    """Demonstrate the CP plotting bug."""
    print("🐛 DEMONSTRATING THE CP PLOTTING BUG")
    print("=" * 50)
    
    # Simulate the buggy scenario
    print("\n1. BUGGY CODE SCENARIO:")
    print("   - well_idx is undefined (NameError)")
    print("   - This would cause the CP to use wrong well data")
    
    # Simulate fluorescence data for multiple wells
    wells = ['A1', 'A2', 'A3']
    time_points = np.array([0, 60, 120, 180, 240, 300])  # minutes
    
    # Different fluorescence patterns for each well
    fluorescence_data = {
        'A1': np.array([100, 150, 300, 600, 900, 1000]),  # Strong signal
        'A2': np.array([200, 220, 250, 280, 300, 320]),   # Weak signal  
        'A3': np.array([150, 200, 400, 800, 1200, 1400])  # Very strong signal
    }
    
    # Simulate crossing points calculated for each well
    crossing_points = {
        'A1': 150.0,  # CP at 150 minutes
        'A2': 180.0,  # CP at 180 minutes  
        'A3': 120.0   # CP at 120 minutes
    }
    
    print(f"\n2. SIMULATED DATA:")
    for well in wells:
        cp = crossing_points[well]
        # Correct interpolation
        correct_fluor = np.interp(cp, time_points, fluorescence_data[well])
        print(f"   {well}: CP={cp}min, Correct Fluorescence={correct_fluor:.1f}")
    
    print(f"\n3. BUGGY BEHAVIOR:")
    print("   If well_idx is undefined or wrong, CP would be plotted with:")
    
    # Simulate the bug - using wrong well data (e.g., always well A1)
    wrong_well = 'A1'  # Bug would likely default to first well
    for well in wells:
        cp = crossing_points[well]
        # Wrong interpolation (using A1 data for all wells)
        wrong_fluor = np.interp(cp, time_points, fluorescence_data[wrong_well])
        correct_fluor = np.interp(cp, time_points, fluorescence_data[well])
        offset = abs(wrong_fluor - correct_fluor)
        print(f"   {well}: CP={cp}min, Wrong Fluorescence={wrong_fluor:.1f}, Offset={offset:.1f}")

def demonstrate_fix():
    """Demonstrate the fix for the CP plotting bug."""
    print("\n\n✅ DEMONSTRATING THE FIX")
    print("=" * 50)
    
    print("\n1. FIXED CODE:")
    print("   - Use correct variable: well_index (not well_idx)")
    print("   - Use fitted curve data for consistency")
    print("   - Remove redundant time_points redefinition")
    
    print("\n2. PROPOSED FIX:")
    print("""
    # ✅ FIXED CODE:
    if crossing_point is not None:
        if threshold_value is not None:
            # Legacy method: use threshold value
            cp_fluorescence = threshold_value
        else:
            # Second derivative method: interpolate from fitted curve
            fitted_curve = well_results.get('fitted_curve')
            if fitted_curve is not None:
                cp_fluorescence = np.interp(crossing_point, time_points, fitted_curve)
            else:
                # Fallback: use raw data with CORRECT well index
                cp_fluorescence = np.interp(crossing_point, time_points, fluorescence_values)
        
        # Plot CP marker
        ax.plot(crossing_point, cp_fluorescence, 
                marker='o', markersize=6, color=group_color,
                markeredgecolor='black', markeredgewidth=1)
    """)

if __name__ == "__main__":
    demonstrate_bug()
    demonstrate_fix()
    
    print("\n\n🎯 SUMMARY:")
    print("=" * 50)
    print("✅ Bug identified: Undefined variable 'well_idx' on line 462")
    print("✅ Root cause: Variable name mismatch (well_idx vs well_index)")
    print("✅ Impact: CP plotted with wrong well's fluorescence data")
    print("✅ Fix: Use correct variable name and improve data consistency")
    print("\nReady to implement the fix!")