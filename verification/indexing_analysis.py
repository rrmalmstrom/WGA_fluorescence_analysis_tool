#!/usr/bin/env python3
"""
Indexing Analysis
Investigates the zero-based vs one-based indexing issue
"""

import numpy as np

def analyze_indexing_offset():
    """Analyze the indexing offset between time and column indices"""
    print("="*60)
    print(" INDEXING OFFSET ANALYSIS")
    print("="*60)
    
    # CSV structure
    print("CSV Column Structure:")
    print("Column 0: Plate_ID")
    print("Column 1: Well_Row") 
    print("Column 2: Well_Col")
    print("Column 3: Well")
    print("Column 4: Type")
    print("Column 5: number_of_cells/capsules")
    print("Column 6: Group_1")
    print("Column 7: Group_2")
    print("Column 8: Group_3")
    print("Column 9: 0 hours (first time point)")
    print("Column 10: 0.25 hours")
    print("Column 11: 0.5 hours")
    print("...")
    print("Column 40: 7.75 hours (last time point)")
    
    # Original script indexing
    print(f"\nOriginal Script Logic:")
    print(f"time_points = np.arange(8, len(row))")
    print(f"This gives: [8, 9, 10, 11, ..., 39]")
    print(f"But these are COLUMN INDICES, not time values!")
    
    # The key insight
    print(f"\n" + "="*60)
    print(" THE KEY INSIGHT")
    print("="*60)
    
    print("Time measurements start at 0:")
    actual_times = [0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
    print(f"Actual times: {actual_times}")
    print(f"Array indices: {list(range(len(actual_times)))}")
    
    print(f"\nColumn indices start at 9 (for first time point):")
    column_indices = list(range(9, 18))  # First 9 time columns
    print(f"Column indices: {column_indices}")
    
    print(f"\nOriginal script uses column indices AS IF they were time:")
    original_time_points = list(range(8, 17))  # What original script uses
    print(f"Original 'time_points': {original_time_points}")
    
    # The offset calculation
    print(f"\n" + "="*60)
    print(" OFFSET CALCULATION")
    print("="*60)
    
    # Example: crossing at "time point" 32.9 in original script
    original_cp = 32.9
    print(f"Original crossing point: {original_cp}")
    
    # Method 1: Direct conversion (what I initially did)
    # Column 32 = measurement index 32-8 = 24
    measurement_idx_direct = int(original_cp) - 8
    print(f"Direct conversion: column {int(original_cp)} → measurement index {measurement_idx_direct}")
    
    # Method 2: Accounting for the fact that column 9 = measurement 0
    # Column 32 = measurement index 32-9 = 23  
    measurement_idx_corrected = int(original_cp) - 9
    print(f"Corrected conversion: column {int(original_cp)} → measurement index {measurement_idx_corrected}")
    
    # Convert to actual time
    actual_time_minutes = [0, 15.0, 30.0, 45.0, 60, 75.0, 90.0, 105.0, 120, 135.0, 150.0, 165.0, 180, 195.0, 210.0, 225.0, 240, 255.0, 270.0, 285.0, 300, 315.0, 330.0, 345.0, 360, 375.0, 390.0, 405.0, 420, 435.0, 450.0, 465.0]
    
    if measurement_idx_corrected < len(actual_time_minutes) and measurement_idx_corrected + 1 < len(actual_time_minutes):
        time_at_idx = actual_time_minutes[measurement_idx_corrected]
        time_at_next = actual_time_minutes[measurement_idx_corrected + 1]
        fraction = original_cp - int(original_cp)
        interpolated_time = time_at_idx + fraction * (time_at_next - time_at_idx)
        
        print(f"\nCorrected interpolation:")
        print(f"Measurement index {measurement_idx_corrected}: {time_at_idx} minutes")
        print(f"Measurement index {measurement_idx_corrected + 1}: {time_at_next} minutes")
        print(f"Fraction: {fraction}")
        print(f"Interpolated time: {interpolated_time:.2f} minutes")
        
        # Compare with NEW tool result
        new_cp = 358.28
        difference = abs(new_cp - interpolated_time)
        print(f"\nNEW tool result: {new_cp} minutes")
        print(f"Difference: {difference:.2f} minutes")
        
        if difference < 1.0:
            print("✅ EXCELLENT AGREEMENT!")
        elif difference < 5.0:
            print("✅ Good agreement")
        else:
            print("❌ Still significant difference")

if __name__ == "__main__":
    analyze_indexing_offset()