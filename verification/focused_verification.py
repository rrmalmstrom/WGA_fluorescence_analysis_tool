#!/usr/bin/env python3
"""
Focused Verification Script
Runs the NEW fluorescence tool on a subset of wells to generate outputs for comparison
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

def run_focused_analysis():
    """Run NEW tool analysis on a focused set of wells"""
    print("="*60)
    print(" FOCUSED NEW TOOL VERIFICATION")
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
    project_root = Path(__file__).parent.parent.parent
    bmg_file = project_root / "example_input_files" / "RM5097.96HL.BNCT.1.CSV"
    layout_file = project_root / "example_input_files" / "RM5097_layout.csv"
    
    # Output directory
    output_dir = Path(__file__).parent / "verification_output"
    output_dir.mkdir(exist_ok=True)
    plot_dir = output_dir / "well_plots"
    plot_dir.mkdir(exist_ok=True)
    
    # Step 1: Parse data
    print("\n1. Parsing data...")
    try:
        bmg_parser = BMGOmega3Parser()
        fluorescence_data = bmg_parser.parse_file(str(bmg_file))
        
        layout_parser = LayoutParser()
        layout_data = layout_parser.parse_file(str(layout_file))
        
        print(f"✅ Parsed data: {len(fluorescence_data.wells)} wells, {len(fluorescence_data.time_points)} time points")
    except Exception as e:
        print(f"❌ Parsing failed: {e}")
        return False
    
    # Step 2: Initialize analysis components
    curve_fitter = CurveFitter()
    threshold_analyzer = ThresholdAnalyzer()
    
    # Step 3: Process a focused set of wells (first 50 wells)
    print("\n2. Processing wells...")
    results = []
    successful_fits = 0
    wells_to_process = fluorescence_data.wells[:50]  # Process first 50 wells
    
    for i, well_id in enumerate(wells_to_process):
        print(f"   Processing well {i+1}/{len(wells_to_process)}: {well_id}")
        
        # Get well data
        well_index = fluorescence_data.wells.index(well_id)
        time_points = np.array(fluorescence_data.time_points)
        fluo_values = np.array(fluorescence_data.measurements[well_index])
        
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
        
        # Process well
        crossing_time = None
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
                
                if crossing_time is not None:
                    successful_fits += 1
                    print(f"      ✅ Fit successful: R²={fit_result.r_squared:.3f}, CP={crossing_time:.2f} min")
                    
                    # Create plot for successful fits
                    create_well_plot(well_id, time_points, fluo_values, fitted_values, 
                                   threshold, crossing_time, fit_result, plot_dir)
                else:
                    print(f"      ⚠️ Fit successful but no crossing point found")
            else:
                print(f"      ❌ Curve fitting failed: {fit_result.error_message}")
        
        except Exception as e:
            print(f"      ❌ Processing failed: {e}")
        
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
    
    print(f"\n✅ Processed {len(wells_to_process)} wells, {successful_fits} successful curve fits with crossing points")
    
    # Step 4: Save results to CSV
    print("\n3. Saving results...")
    try:
        results_df = pd.DataFrame(results)
        output_csv = output_dir / "new_tool_sample_results.csv"
        results_df.to_csv(output_csv, index=False)
        print(f"✅ Saved results to: {output_csv}")
        print(f"   Rows: {len(results_df)}, Columns: {len(results_df.columns)}")
    except Exception as e:
        print(f"❌ Failed to save results: {e}")
        return False
    
    # Step 5: Compare with original results for same wells
    print("\n4. Comparing with original results...")
    try:
        original_csv = project_root / "example_input_files" / "analyzed_fluorescence_data.csv"
        if original_csv.exists():
            original_df = pd.read_csv(original_csv)
            
            # Filter original results to same wells
            original_subset = original_df[original_df['Well'].isin(wells_to_process)]
            
            # Count crossing points
            new_cp_count = len(results_df[results_df['Crossing_Time'].notna() & (results_df['Crossing_Time'] != '')])
            orig_cp_count = len(original_subset[original_subset['Crossing_Time'].notna() & (original_subset['Crossing_Time'] != '')])
            
            print(f"Crossing points found - Original: {orig_cp_count}, New: {new_cp_count}")
            
            # Compare specific wells that have crossing points in both
            if new_cp_count > 0 and orig_cp_count > 0:
                new_cp_wells = set(results_df[results_df['Crossing_Time'].notna() & (results_df['Crossing_Time'] != '')]['Well'])
                orig_cp_wells = set(original_subset[original_subset['Crossing_Time'].notna() & (original_subset['Crossing_Time'] != '')]['Well'])
                common_wells = new_cp_wells & orig_cp_wells
                
                print(f"Wells with crossing points in both: {len(common_wells)}")
                if len(common_wells) > 0:
                    print("Sample comparisons:")
                    for well in list(common_wells)[:5]:
                        orig_cp = float(original_subset[original_subset['Well'] == well]['Crossing_Time'].iloc[0])
                        new_cp = float(results_df[results_df['Well'] == well]['Crossing_Time'].iloc[0])
                        diff = abs(orig_cp - new_cp)
                        print(f"  {well}: Original={orig_cp:.2f}, New={new_cp:.2f}, Diff={diff:.2f} min")
        
    except Exception as e:
        print(f"⚠️ Comparison failed: {e}")
    
    print("\n" + "="*60)
    print(" VERIFICATION COMPLETE")
    print("="*60)
    print(f"Output directory: {output_dir}")
    print("Files generated:")
    print("  - new_tool_sample_results.csv (first 50 wells)")
    print("  - well_plots/ (individual well plots for successful fits)")
    
    return True

def create_well_plot(well_id, time_points, fluo_values, fitted_values, threshold, 
                    crossing_time, fit_result, plot_dir):
    """Create a plot for a single well"""
    try:
        plt.figure(figsize=(10, 6))
        
        # Plot data points
        plt.scatter(time_points, fluo_values, alpha=0.7, color='blue', s=30, label='Data')
        
        # Plot fitted curve
        plt.plot(time_points, fitted_values, 'r-', linewidth=2, 
                label=f'Fitted Curve (R²={fit_result.r_squared:.3f})')
        
        # Plot threshold line
        plt.axhline(y=threshold, color='green', linestyle='--', linewidth=1, 
                   label=f'Threshold ({threshold:.1f})')
        
        # Plot crossing point
        plt.axvline(x=crossing_time, color='orange', linestyle='--', linewidth=1,
                   label=f'Crossing Point ({crossing_time:.2f} min)')
        
        plt.xlabel('Time (minutes)')
        plt.ylabel('Fluorescence')
        plt.title(f'Well {well_id} - NEW Tool Analysis')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Save plot
        plot_path = plot_dir / f'well_{well_id}.png'
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()
        
    except Exception as e:
        print(f"   Warning: Failed to create plot for well {well_id}: {e}")
        plt.close()

if __name__ == "__main__":
    success = run_focused_analysis()
    sys.exit(0 if success else 1)