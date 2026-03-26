#!/usr/bin/env python3
"""
Time Unit Analysis
Investigates the time unit discrepancy between original and new methods
"""

import numpy as np

def analyze_time_units():
    """Analyze the time unit differences"""
    print("="*60)
    print(" TIME UNIT ANALYSIS")
    print("="*60)
    
    # Original script uses column indices
    original_time_points = np.arange(8, 40)  # Columns 9-40 (indices 8-39)
    print(f"Original 'time_points' (column indices): {original_time_points}")
    print(f"Range: {original_time_points[0]} to {original_time_points[-1]}")
    
    # Actual time values from CSV headers (in hours)
    actual_time_hours = [0, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 2.75, 
                        3, 3.25, 3.5, 3.75, 4, 4.25, 4.5, 4.75, 5, 5.25, 5.5, 5.75, 
                        6, 6.25, 6.5, 6.75, 7, 7.25, 7.5, 7.75]
    
    # Convert to minutes (what my NEW tool uses)
    actual_time_minutes = [h * 60 for h in actual_time_hours]
    
    print(f"\nActual time values (hours): {actual_time_hours}")
    print(f"Range: {actual_time_hours[0]} to {actual_time_hours[-1]} hours")
    
    print(f"\nActual time values (minutes): {actual_time_minutes}")
    print(f"Range: {actual_time_minutes[0]} to {actual_time_minutes[-1]} minutes")
    
    # Example crossing point analysis
    print("\n" + "="*60)
    print(" CROSSING POINT ANALYSIS")
    print("="*60)
    
    # Example: Original found crossing at "time point" 32.9
    original_cp = 32.9
    print(f"Original crossing point: {original_cp}")
    
    print(f"\nDEBUGGING INDEX CONVERSION:")
    print(f"Original uses column indices starting from 8")
    print(f"Column indices: {original_time_points}")
    print(f"Corresponding measurement indices (0-based): {original_time_points - 8}")
    
    # The original crossing point 32.9 means column index 32.9
    # Column index 32 = measurement index 32-8 = 24 (0-based)
    # Column index 33 = measurement index 33-8 = 25 (0-based)
    
    # BUT WAIT - let me check if there's an off-by-one error
    # Maybe the original script uses 1-based indexing or different offset
    
    print(f"\nTesting different interpretations:")
    
    # Interpretation 1: Direct conversion (what I did above)
    measurement_index_24 = actual_time_minutes[24]  # 6.0 hours = 360 minutes
    measurement_index_25 = actual_time_minutes[25]  # 6.25 hours = 375 minutes
    fraction = original_cp - 32  # 0.9
    interpolated_time_1 = measurement_index_24 + fraction * (measurement_index_25 - measurement_index_24)
    print(f"Interpretation 1 (direct): {interpolated_time_1:.2f} minutes")
    
    # Interpretation 2: Maybe off-by-one in my conversion
    measurement_index_23 = actual_time_minutes[23]  # 5.75 hours = 345 minutes
    measurement_index_24_alt = actual_time_minutes[24]  # 6.0 hours = 360 minutes
    interpolated_time_2 = measurement_index_23 + fraction * (measurement_index_24_alt - measurement_index_23)
    print(f"Interpretation 2 (off-by-one): {interpolated_time_2:.2f} minutes")
    
    # Interpretation 3: Maybe the original uses different base
    # Let's see what happens if we treat 32.9 as direct array index into actual times
    if int(original_cp) < len(actual_time_minutes) and int(original_cp) + 1 < len(actual_time_minutes):
        base_idx = int(original_cp)
        next_idx = base_idx + 1
        fraction_alt = original_cp - base_idx
        interpolated_time_3 = actual_time_minutes[base_idx] + fraction_alt * (actual_time_minutes[next_idx] - actual_time_minutes[base_idx])
        print(f"Interpretation 3 (direct array index): {interpolated_time_3:.2f} minutes")
    
    print(f"Measurement index 24 (column 32): {measurement_index_24} minutes")
    print(f"Measurement index 25 (column 33): {measurement_index_25} minutes")
    print(f"Interpolated actual time: {interpolated_time:.2f} minutes")
    
    # Compare with NEW tool result
    new_cp = 358.28  # From our verification
    difference = abs(new_cp - interpolated_time)
    print(f"NEW tool crossing point: {new_cp} minutes")
    print(f"Difference: {difference:.2f} minutes")
    
    if difference < 5:
        print("✅ Results are actually very close when properly converted!")
    else:
        print("❌ Still significant difference after conversion")

if __name__ == "__main__":
    analyze_time_units()