#!/usr/bin/env python3
"""
End-to-End Verification Script
Runs the NEW fluorescence tool on real data and generates complete outputs for comparison
"""

import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import shutil

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def create_verification_copy():
    """Create a copy of input files for verification testing"""
    project_root = Path(__file__).parent.parent.parent
    original_dir = project_root / "example_input_files"
    verification_dir = Path(__file__).parent / "verification_input_files"
    
    # Create verification directory
    verification_dir.mkdir(exist_ok=True)
    
    # Copy input files
    files_to_copy = [
        "RM5097.96HL.BNCT.1.CSV",
        "RM5097_layout.csv"
    ]
    
    for file_name in files_to_copy:
        src = original_dir / file_name
        dst = verification_dir / file_name
        if src.exists():
            shutil.copy2(src, dst)
            print(f"✅ Copied {file_name}")
        else:
            print(f"❌ Source file not found: {src}")
            return False
    
    return verification_dir

def run_new_fluorescence_analysis(input_dir, output_dir):
    """Run the NEW fluorescence tool end-to-end analysis"""
    print("\n" + "="*60)
    print(" RUNNING NEW FLUORESCENCE TOOL ANALYSIS")
    print("="*60)
    
    # Import NEW tool components
    try:
        from fluorescence_tool.parsers.bmg_parser import BMGOmega3Parser
        from fluorescence_tool.parsers.layout_parser import LayoutParser
        from fluorescence_tool.algorithms.curve_fitting import CurveFitter
        from fluorescence_tool.algorithms.threshold_analysis import ThresholdAnalyzer
        print("✅ Successfully imported NEW tool components")
    except Exception as e:
        print(f"❌ Failed to import NEW tool components: {e}")
        return False
    
    # File paths
    bmg_file = input_dir / "RM5097.96HL.BNCT.1.CSV"
    layout_file = input_dir / "RM5097_layout.csv"
    
    # Step 1: Parse BMG data
    print("\n1. Parsing BMG data...")
    try:
        bmg_parser = BMGOmega3Parser()
        fluorescence_data = bmg_parser.parse_file(str(bmg_file))
        print(f"✅ Parsed BMG data: {len(fluorescence_data.wells)} wells, {len(fluorescence_data.time_points)} time points")
    except Exception as e:
        print(f"❌ BMG parsing failed: {e}")
        return False
    
    # Step 2: Parse layout data
    print("\n2. Parsing layout data...")
    try:
        layout_parser = LayoutParser()
        layout_data = layout_parser.parse_file(str(layout_file))
        print(f"✅ Parsed layout data: {len(layout_data)} wells")
    except Exception as e:
        print(f"❌ Layout parsing failed: {e}")
        return False
    
    # Step 3: Initialize analysis components
    print("\n3. Initializing analysis components...")
    curve_fitter = CurveFitter()
    threshold_analyzer = ThresholdAnalyzer()
    
    # Step 4: Process each well
    print("\n4. Processing wells...")
    results = []
    plot_dir = output_dir / "well_plots"
    plot_dir.mkdir(exist_ok=True)
    
    successful_fits = 0
    total_wells = len(fluorescence_data.wells)
    
    for i, well_id in enumerate(fluorescence_data.wells):
        if i % 50 == 0:
            print(f"   Processing well {i+1}/{total_wells}: {well_id}")
        
        # Get well data
        time_points = np.array(fluorescence_data.time_points)
        fluo_values = np.array(fluorescence_data.measurements[i])
        
        # Get layout info
        well_info = layout_data.get(well_id)
        if well_info:
            plate_id = well_info.plate_id
            well_type = well_info.well_type
            group_1 = well_info.group_1 or ""
            group_2 = well_info.group_2 or ""
            group_3 = well_info.group_3 or ""
            cell_count = well_info.cell_count or ""
        else:
            plate_id = ""
            well_type = "unknown"
            group_1 = group_2 = group_3 = ""
            cell_count = ""
        
        # Fit curve and calculate threshold
        try:
            # Calculate threshold using baseline method
            threshold, baseline = threshold_analyzer.calculate_baseline_threshold(fluo_values)
            
            # Fit curve
            fit_result = curve_fitter.fit_curve(time_points, fluo_values)
            
            if fit_result.success:
                # Calculate fitted curve for crossing point detection
                fitted_values = curve_fitter.sigmoid_5param(time_points, *fit_result.parameters)
                
                # Find crossing point
                crossing_time = curve_fitter.find_crossing_time(time_points, fitted_values, threshold)
                
                successful_fits += 1
                
                # Create plot for wells with good fits (sample some)
                if (crossing_time is not None and 
                    fit_result.r_squared > 0.5 and 
                    successful_fits <= 50):  # Limit to first 50 good fits
                    create_well_plot(well_id, time_points, fluo_values, fitted_values, 
                                   threshold, crossing_time, fit_result, plot_dir)
            else:
                fitted_values = None
                crossing_time = None
        
        except Exception as e:
            print(f"   Warning: Failed to process well {well_id}: {e}")
            crossing_time = None
            fit_result = None
        
        # Create result row (matching original format)
        result_row = {
            'Plate_ID': plate_id,
            'Well_Row': well_id[0] if well_id else "",
            'Well_Col': well_id[1:] if len(well_id) > 1 else "",
            'Well': well_id,
            'Type': well_type,
            'number_of_cells/capsules': cell_count,
            'Group_1': group_1,
            'Group_2': group_2,
            'Group_3': group_3,
            'Crossing_Time': crossing_time if crossing_time is not None else ""
        }
        
        # Add fluorescence values (convert time from minutes to hours for column names)
        for j, time_min in enumerate(time_points):
            time_hours = time_min / 60.0
            result_row[str(time_hours)] = fluo_values[j]
        
        results.append(result_row)
    
    print(f"✅ Processed {total_wells} wells, {successful_fits} successful curve fits")
    
    # Step 5: Save results to CSV
    print("\n5. Saving results...")
    try:
        results_df = pd.DataFrame(results)
        output_csv = output_dir / "new_tool_analyzed_fluorescence_data.csv"
        results_df.to_csv(output_csv, index=False)
        print(f"✅ Saved results to: {output_csv}")
        print(f"   Rows: {len(results_df)}, Columns: {len(results_df.columns)}")
    except Exception as e:
        print(f"❌ Failed to save results: {e}")
        return False
    
    return True

def create_well_plot(well_id, time_points, fluo_values, fitted_values, threshold, 
                    crossing_time, fit_result, plot_dir):
    """Create a plot for a single well"""
    try:
        plt.figure(figsize=(10, 6))
        
        # Plot data points
        plt.scatter(time_points, fluo_values, alpha=0.7, color='blue', s=30, label='Data')
        
        # Plot fitted curve if available
        if fitted_values is not None:
            plt.plot(time_points, fitted_values, 'r-', linewidth=2, 
                    label=f'Fitted Curve (R²={fit_result.r_squared:.3f})')
        
        # Plot threshold line
        plt.axhline(y=threshold, color='green', linestyle='--', linewidth=1, 
                   label=f'Threshold ({threshold:.1f})')
        
        # Plot crossing point if found
        if crossing_time is not None:
            plt.axvline(x=crossing_time, color='orange', linestyle='--', linewidth=1,
                       label=f'Crossing Point ({crossing_time:.2f} min)')
        
        plt.xlabel('Time (minutes)')
        plt.ylabel('Fluorescence')
        plt.title(f'Well {well_id} - Fluorescence Analysis')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Save plot
        plot_path = plot_dir / f'well_{well_id}.png'
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()
        
    except Exception as e:
        print(f"   Warning: Failed to create plot for well {well_id}: {e}")
        plt.close()

def compare_with_original():
    """Compare NEW tool output with original reference output"""
    print("\n" + "="*60)
    print(" COMPARING WITH ORIGINAL RESULTS")
    print("="*60)
    
    # Load original results
    project_root = Path(__file__).parent.parent.parent
    original_csv = project_root / "example_input_files" / "analyzed_fluorescence_data.csv"
    
    # Load new results
    verification_dir = Path(__file__).parent / "verification_output"
    new_csv = verification_dir / "new_tool_analyzed_fluorescence_data.csv"
    
    if not original_csv.exists():
        print(f"❌ Original results not found: {original_csv}")
        return False
    
    if not new_csv.exists():
        print(f"❌ New results not found: {new_csv}")
        return False
    
    try:
        original_df = pd.read_csv(original_csv)
        new_df = pd.read_csv(new_csv)
        
        print(f"Original results: {len(original_df)} rows, {len(original_df.columns)} columns")
        print(f"New results: {len(new_df)} rows, {len(new_df.columns)} columns")
        
        # Compare crossing points for wells that have them in both
        original_cp = original_df[original_df['Crossing_Time'].notna() & (original_df['Crossing_Time'] != '')]
        new_cp = new_df[new_df['Crossing_Time'].notna() & (new_df['Crossing_Time'] != '')]
        
        print(f"Wells with crossing points - Original: {len(original_cp)}, New: {len(new_cp)}")
        
        # Find common wells with crossing points
        common_wells = set(original_cp['Well']) & set(new_cp['Well'])
        print(f"Common wells with crossing points: {len(common_wells)}")
        
        if len(common_wells) > 0:
            # Compare crossing point values
            differences = []
            for well in list(common_wells)[:10]:  # Check first 10
                orig_cp = float(original_cp[original_cp['Well'] == well]['Crossing_Time'].iloc[0])
                new_cp_val = new_cp[new_cp['Well'] == well]['Crossing_Time'].iloc[0]
                if pd.notna(new_cp_val) and new_cp_val != '':
                    new_cp_val = float(new_cp_val)
                    diff = abs(orig_cp - new_cp_val)
                    differences.append(diff)
                    print(f"  {well}: Original={orig_cp:.2f}, New={new_cp_val:.2f}, Diff={diff:.2f}")
            
            if differences:
                avg_diff = np.mean(differences)
                print(f"\nAverage crossing point difference: {avg_diff:.2f} minutes")
                print(f"Max difference: {max(differences):.2f} minutes")
                
                if avg_diff < 5.0:  # Within 5 minutes average
                    print("✅ Crossing points are reasonably similar")
                else:
                    print("⚠️ Crossing points show significant differences")
        
        return True
        
    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        return False

def main():
    """Main verification function"""
    print("="*60)
    print(" END-TO-END FLUORESCENCE TOOL VERIFICATION")
    print("="*60)
    
    # Create verification directories
    verification_dir = Path(__file__).parent / "verification_output"
    verification_dir.mkdir(exist_ok=True)
    
    # Step 1: Copy input files
    print("\n1. Setting up verification environment...")
    input_dir = create_verification_copy()
    if not input_dir:
        return False
    
    # Step 2: Run NEW tool analysis
    success = run_new_fluorescence_analysis(input_dir, verification_dir)
    if not success:
        return False
    
    # Step 3: Compare with original results
    compare_with_original()
    
    print("\n" + "="*60)
    print(" VERIFICATION COMPLETE")
    print("="*60)
    print(f"Output directory: {verification_dir}")
    print("Files generated:")
    print("  - new_tool_analyzed_fluorescence_data.csv")
    print("  - well_plots/ (directory with individual well plots)")
    print("\nYou can now compare these outputs with the original results.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)