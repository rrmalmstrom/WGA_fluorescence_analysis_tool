#!/usr/bin/env python3
"""
BMG Parser Verification Script
Compares NEW BMG parser with original script parsing logic
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def parse_bmg_original_method(file_path):
    """Parse BMG file using the original script method from process_fluorescence_data.py"""
    print("Parsing with ORIGINAL method...")
    
    # Read the file with custom header rows (from original script)
    df = pd.read_csv(file_path, header=7)  # Use row 7 for headers, data starts at row 8

    # Rename the first three columns
    df.columns.values[0:3] = ["Well_Row", "Well_Col", "Well"]

    # Convert time-based column headers (from column 4 onwards) to decimal hours
    new_columns = list(df.columns)
    for i in range(3, len(new_columns)):
        col_name = new_columns[i]
        if isinstance(col_name, str) and 'h' in col_name:
            # Handle format with hours only (e.g., "7 h")
            if 'min' not in col_name:
                hours = int(col_name.split()[0])
                new_columns[i] = str(hours)
            # Handle format with hours and minutes (e.g., "7 h 30 min")
            elif 'min' in col_name:
                parts = col_name.split()
                if len(parts) >= 3:
                    hours = int(parts[0])
                    minutes = int(parts[2])
                    # Convert to decimal hours
                    decimal_hours = hours + minutes / 60
                    new_columns[i] = str(decimal_hours)

    df.columns = new_columns
    
    # Extract time points and convert to minutes (original uses hours)
    time_columns = [col for col in df.columns[3:] if col.replace('.', '').replace('-', '').isdigit()]
    time_points = [float(col) * 60 for col in time_columns]  # Convert hours to minutes
    
    # Extract well data
    wells = []
    measurements = []
    
    for _, row in df.iterrows():
        well_id = f"{row['Well_Row']}{row['Well_Col']}"
        wells.append(well_id)
        
        # Extract fluorescence values for this well
        well_measurements = []
        for col in time_columns:
            well_measurements.append(float(row[col]))
        measurements.append(well_measurements)
    
    return {
        'wells': wells,
        'time_points': time_points,
        'measurements': np.array(measurements),
        'raw_dataframe': df
    }

def parse_bmg_new_method(file_path):
    """Parse BMG file using the NEW fluorescence tool parser"""
    print("Parsing with NEW method...")
    
    try:
        from fluorescence_tool.parsers.bmg_parser import BMGOmega3Parser
        
        parser = BMGOmega3Parser()
        data = parser.parse_file(str(file_path))
        
        return {
            'wells': data.wells,
            'time_points': data.time_points,
            'measurements': data.measurements,
            'metadata': data.metadata
        }
        
    except Exception as e:
        print(f"❌ NEW parser error: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_parsing_results(original, new):
    """Compare the results from both parsing methods"""
    print("\n" + "="*60)
    print(" COMPARISON RESULTS")
    print("="*60)
    
    if new is None:
        print("❌ NEW parser failed - cannot compare")
        return False
    
    # Compare basic structure
    print(f"Wells count - Original: {len(original['wells'])}, New: {len(new['wells'])}")
    print(f"Time points count - Original: {len(original['time_points'])}, New: {len(new['time_points'])}")
    print(f"Measurements shape - Original: {original['measurements'].shape}, New: {new['measurements'].shape}")
    
    # Check if wells match
    wells_match = set(original['wells']) == set(new['wells'])
    print(f"Wells match: {'✅' if wells_match else '❌'}")
    
    if not wells_match:
        print(f"  Original wells (first 10): {original['wells'][:10]}")
        print(f"  New wells (first 10): {new['wells'][:10]}")
        missing_in_new = set(original['wells']) - set(new['wells'])
        missing_in_original = set(new['wells']) - set(original['wells'])
        if missing_in_new:
            print(f"  Missing in NEW: {list(missing_in_new)[:5]}")
        if missing_in_original:
            print(f"  Extra in NEW: {list(missing_in_original)[:5]}")
    
    # Check time points (with tolerance for floating point differences)
    time_points_close = np.allclose(original['time_points'], new['time_points'], rtol=1e-5)
    print(f"Time points match: {'✅' if time_points_close else '❌'}")
    
    if not time_points_close:
        print(f"  Original time range: {original['time_points'][0]:.3f} - {original['time_points'][-1]:.3f}")
        print(f"  New time range: {new['time_points'][0]:.3f} - {new['time_points'][-1]:.3f}")
        print(f"  Original first 5: {original['time_points'][:5]}")
        print(f"  New first 5: {new['time_points'][:5]}")
    
    # Check measurements for a few wells
    measurements_match = True
    if original['measurements'].shape == new['measurements'].shape:
        # Compare first few wells
        for i in range(min(5, len(original['wells']))):
            well_id = original['wells'][i]
            if well_id in new['wells']:
                new_idx = new['wells'].index(well_id)
                orig_values = original['measurements'][i]
                new_values = new['measurements'][new_idx]
                
                if not np.allclose(orig_values, new_values, rtol=1e-5):
                    measurements_match = False
                    print(f"❌ Measurements differ for well {well_id}")
                    print(f"  Original first 5: {orig_values[:5]}")
                    print(f"  New first 5: {new_values[:5]}")
                    break
    else:
        measurements_match = False
        print("❌ Measurement array shapes don't match")
    
    if measurements_match:
        print("✅ Measurements match for tested wells")
    
    # Overall assessment
    overall_success = wells_match and time_points_close and measurements_match
    print(f"\nOverall comparison: {'✅ PASS' if overall_success else '❌ FAIL'}")
    
    return overall_success

def main():
    """Main verification function"""
    print("="*60)
    print(" BMG PARSER VERIFICATION")
    print("="*60)
    
    # File paths
    project_root = Path(__file__).parent.parent.parent
    bmg_file = project_root / "example_input_files" / "RM5097.96HL.BNCT.1.CSV"
    
    if not bmg_file.exists():
        print(f"❌ BMG file not found: {bmg_file}")
        return False
    
    print(f"Testing file: {bmg_file.name}")
    
    # Parse with both methods
    try:
        original_result = parse_bmg_original_method(bmg_file)
        print(f"✅ Original parsing successful")
        print(f"   Wells: {len(original_result['wells'])}")
        print(f"   Time points: {len(original_result['time_points'])}")
        print(f"   Measurements shape: {original_result['measurements'].shape}")
    except Exception as e:
        print(f"❌ Original parsing failed: {e}")
        return False
    
    new_result = parse_bmg_new_method(bmg_file)
    if new_result:
        print(f"✅ New parsing successful")
        print(f"   Wells: {len(new_result['wells'])}")
        print(f"   Time points: {len(new_result['time_points'])}")
        print(f"   Measurements shape: {new_result['measurements'].shape}")
    
    # Compare results
    success = compare_parsing_results(original_result, new_result)
    
    print("\n" + "="*60)
    print(f" BMG PARSER VERIFICATION {'COMPLETE' if success else 'FAILED'}")
    print("="*60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)