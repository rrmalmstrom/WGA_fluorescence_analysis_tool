#!/usr/bin/env python3
"""
Layout Parser Verification Script
Compares NEW layout parser with original script parsing logic
"""

import sys
import os
import pandas as pd
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def parse_layout_original_method(file_path):
    """Parse layout file using the original script method from process_fluorescence_data.py"""
    print("Parsing with ORIGINAL method...")
    
    # Read the metadata CSV file (from original script)
    df = pd.read_csv(file_path)
    
    # Rename columns to match fluorescence DataFrame
    df.rename(columns={
        'Well Row': 'Well_Row',
        'Well Col': 'Well_Col',
        'Well': 'Well'
    }, inplace=True)
    
    # Convert to dictionary format for comparison
    layout_dict = {}
    for _, row in df.iterrows():
        well_id = row['Well']
        layout_dict[well_id] = {
            'plate_id': row.get('Plate_ID', ''),
            'well_row': row.get('Well_Row', ''),
            'well_col': row.get('Well_Col', ''),
            'well_type': row.get('Type', ''),
            'number_of_cells': row.get('number_of_cells/capsules', ''),
            'group_1': row.get('Group_1', ''),
            'group_2': row.get('Group_2', ''),
            'group_3': row.get('Group_3', '')
        }
    
    return {
        'layout_dict': layout_dict,
        'raw_dataframe': df,
        'well_count': len(layout_dict)
    }

def parse_layout_new_method(file_path):
    """Parse layout file using the NEW fluorescence tool parser"""
    print("Parsing with NEW method...")
    
    try:
        from fluorescence_tool.parsers.layout_parser import LayoutParser
        
        parser = LayoutParser()
        layout = parser.parse_file(str(file_path))
        
        # Convert to comparable format
        layout_dict = {}
        for well_id, well_info in layout.items():
            layout_dict[well_id] = {
                'plate_id': well_info.plate_id,
                'well_row': '',  # Not stored separately in WellInfo
                'well_col': '',  # Not stored separately in WellInfo
                'well_type': well_info.well_type,
                'number_of_cells': well_info.cell_count,
                'group_1': well_info.group_1,
                'group_2': well_info.group_2,
                'group_3': well_info.group_3
            }
        
        return {
            'layout_dict': layout_dict,
            'raw_layout': layout,
            'well_count': len(layout_dict)
        }
        
    except Exception as e:
        print(f"❌ NEW parser error: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_layout_results(original, new):
    """Compare the results from both parsing methods"""
    print("\n" + "="*60)
    print(" COMPARISON RESULTS")
    print("="*60)
    
    if new is None:
        print("❌ NEW parser failed - cannot compare")
        return False
    
    # Compare basic structure
    print(f"Well count - Original: {original['well_count']}, New: {new['well_count']}")
    
    # Check if wells match
    orig_wells = set(original['layout_dict'].keys())
    new_wells = set(new['layout_dict'].keys())
    wells_match = orig_wells == new_wells
    print(f"Wells match: {'✅' if wells_match else '❌'}")
    
    if not wells_match:
        missing_in_new = orig_wells - new_wells
        missing_in_original = new_wells - orig_wells
        if missing_in_new:
            print(f"  Missing in NEW: {list(missing_in_new)[:5]}")
        if missing_in_original:
            print(f"  Extra in NEW: {list(missing_in_original)[:5]}")
    
    # Check well data for common wells
    common_wells = orig_wells & new_wells
    data_matches = True
    mismatches = []
    
    for well_id in list(common_wells)[:10]:  # Check first 10 wells
        orig_data = original['layout_dict'][well_id]
        new_data = new['layout_dict'][well_id]
        
        for field in ['plate_id', 'well_type', 'group_1', 'group_2', 'group_3']:
            orig_val = str(orig_data.get(field, '')).strip()
            new_val = str(new_data.get(field, '')).strip()
            
            # Handle empty/NaN values
            if orig_val in ['', 'nan', 'None']:
                orig_val = ''
            if new_val in ['', 'nan', 'None']:
                new_val = ''
            
            if orig_val != new_val:
                data_matches = False
                mismatches.append(f"Well {well_id}, field {field}: '{orig_val}' vs '{new_val}'")
    
    if data_matches:
        print("✅ Well data matches for tested wells")
    else:
        print("❌ Well data mismatches found:")
        for mismatch in mismatches[:5]:  # Show first 5 mismatches
            print(f"  {mismatch}")
    
    # Check specific well examples
    print("\nSample well data comparison:")
    sample_wells = list(common_wells)[:3]
    for well_id in sample_wells:
        orig_data = original['layout_dict'][well_id]
        new_data = new['layout_dict'][well_id]
        print(f"  {well_id}:")
        print(f"    Original: Type={orig_data.get('well_type', '')}, Group_1={orig_data.get('group_1', '')}")
        print(f"    New:      Type={new_data.get('well_type', '')}, Group_1={new_data.get('group_1', '')}")
    
    # Overall assessment
    overall_success = wells_match and data_matches
    print(f"\nOverall comparison: {'✅ PASS' if overall_success else '❌ FAIL'}")
    
    return overall_success

def main():
    """Main verification function"""
    print("="*60)
    print(" LAYOUT PARSER VERIFICATION")
    print("="*60)
    
    # File paths
    project_root = Path(__file__).parent.parent.parent
    layout_file = project_root / "example_input_files" / "RM5097_layout.csv"
    
    if not layout_file.exists():
        print(f"❌ Layout file not found: {layout_file}")
        return False
    
    print(f"Testing file: {layout_file.name}")
    
    # Parse with both methods
    try:
        original_result = parse_layout_original_method(layout_file)
        print(f"✅ Original parsing successful")
        print(f"   Wells: {original_result['well_count']}")
        print(f"   Columns: {list(original_result['raw_dataframe'].columns)}")
    except Exception as e:
        print(f"❌ Original parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    new_result = parse_layout_new_method(layout_file)
    if new_result:
        print(f"✅ New parsing successful")
        print(f"   Wells: {new_result['well_count']}")
    
    # Compare results
    success = compare_layout_results(original_result, new_result)
    
    print("\n" + "="*60)
    print(f" LAYOUT PARSER VERIFICATION {'COMPLETE' if success else 'FAILED'}")
    print("="*60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)