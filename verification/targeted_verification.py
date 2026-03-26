#!/usr/bin/env python3
"""
Targeted Verification Script
Tests NEW fluorescence tool on wells that have crossing points in the original data
"""

import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def get_wells_with_crossing_points():
    """Get list of wells that have crossing points in original data"""
    project_root = Path(__file__).parent.parent.parent
    original_csv = project_root / "example_input_files" / "analyzed_fluorescence_data.csv"
    
    if not original_csv.exists():
        print(f"❌ Original results not found: {original_csv}")
        return []
    
    try:
        df = pd.read_csv(original_csv)
        # Find wells with crossing points (not empty)
        wells_with_cp = df[df['Crossing_Time'].notna() & (df['Crossing_Time'] != '')]['Well'].tolist()
        return wells_with_cp
    except Exception as e:
        print(f"❌ Failed to read original results: {e}")
        return []

def run_targeted_analysis():
    """Run NEW tool analysis on wells that should have crossing points"""
    print("="*60)
    print(" TARGETED NEW TOOL VERIFICATION")
    print("="*60)
    
    # Get wells with crossing points from original data
    target_wells = get_wells_with_crossing_points()
    if not target_wells:
        return False
    
    print(f"Found {len(target_wells)} wells with crossing points in original data")
    print(f"Testing first 20: {target_wells[:20]}")
    
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
    original_csv = project_root / "example_input_files" / "analyzed_fluorescence_data.csv"
    
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
        
        # Load original results for comparison
        original_df = pd.read_csv(original_csv)
        
        print(f"✅ Parsed data: {len(fluorescence_data.wells)} wells, {len(fluorescence_data.time_points)} time points")
    except Exception as e:
        print(f"❌ Parsing failed: {e}")
        return False
    
    # Step 2: Initialize analysis components
    curve_fitter = CurveFitter()
    threshold_analyzer = ThresholdAnalyzer()
    
    # Step 3: Process target wells (first 20 with crossing points)
    print("\n2. Processing target wells...")
    results = []
    successful_fits = 0
    wells_to_process = target_wells[:20]  # Process first 20 wells with crossing points
    
    for i, well_id in enumerate(wells_to_process):
        print(f"   Processing well {i+1}/{len(wells_to_process)}: {well_id}")
        
        # Get original crossing point for comparison
        orig_row = original_df[original_df['Well'] == well_id]
        if len(orig_row) > 0:
            orig_cp = orig_row['Crossing_Time'].iloc[0]
            print(f"      Original CP: {orig_cp}")
        else:
            orig_cp = None
        
        # Get well data
        if well_id not in fluorescence_data.wells:
            print(f"      ❌ Well {well_id} not found in fluorescence data")
            continue
            
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
            print(f"      Threshold: {threshold:.1f}, Baseline: {baseline:.1f}")
            
            # Fit curve
            fit_result = curve_fitter.fit_curve(time_points, fluo_values)
            
            if fit_result.success:
                # Calculate fitted curve for crossing point detection
                fitted_values = curve_fitter.sigmoid_5param(time_points, *fit_result.parameters)
                
                # Find crossing point
                crossing_time = curve_fitter.find_crossing_time(time_points, fitted_values, threshold)
                
                if crossing_time is not None:
                    successful_fits += 1
                    diff = abs(float(orig_cp) - crossing_time) if orig_cp else None
                    print(f"      ✅ NEW CP: {crossing_time:.2f} min, R²={fit_result.r_squared:.3f}")
                    if diff is not None:
                        print(f"      📊 Difference: {diff:.2f} min")
                    
                    # Create plot for successful fits
                    create_well_plot(well_id, time_points, fluo_values, fitted_values, 
                                   threshold, crossing_time, fit_result, plot_dir, orig_cp)
                else:
                    print(f"      ⚠️ Fit successful (R²={fit_result.r_squared:.3f}) but no crossing point found")
                    # Still create a plot to see what's happening
                    create_well_plot(well_id, time_points, fluo_values, fitted_values, 
                                   threshold, None, fit_result, plot_dir, orig_cp)
            else:
                print(f"      ❌ Curve fitting failed: {fit_result.error_message}")
        
        except Exception as e:
            print(f"      ❌ Processing failed: {e}")
            import traceback
            traceback.print_exc()
        
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
            'Crossing_Time': crossing_time if crossing_time is not None else "",
            'Original_CP': orig_cp if orig_cp else ""
        }
        
        # Add fluorescence values (convert time from minutes to hours for column names)
        for j, time_min in enumerate(time_points):
            time_hours = time_min / 60.0
            result_row[str(time_hours)] = fluo_values[j]
        
        results.append(result_row)
    
    print(f"\n✅ Processed {len(wells_to_process)} target wells, {successful_fits} successful curve fits with crossing points")
    
    # Step 4: Save results to CSV
    print("\n3. Saving results...")
    try:
        results_df = pd.DataFrame(results)
        output_csv = output_dir / "new_tool_targeted_results.csv"
        results_df.to_csv(output_csv, index=False)
        print(f"✅ Saved results to: {output_csv}")
        print(f"   Rows: {len(results_df)}, Columns: {len(results_df.columns)}")
    except Exception as e:
        print(f"❌ Failed to save results: {e}")
        return False
    
    # Step 5: Summary comparison
    print("\n4. Summary comparison...")
    try:
        new_cp_count = len(results_df[results_df['Crossing_Time'].notna() & (results_df['Crossing_Time'] != '')])
        orig_cp_count = len(wells_to_process)  # All target wells should have crossing points
        
        print(f"Expected crossing points: {orig_cp_count}")
        print(f"Found crossing points: {new_cp_count}")
        print(f"Success rate: {new_cp_count/orig_cp_count*100:.1f}%")
        
        # Calculate differences for successful matches
        successful_matches = results_df[
            (results_df['Crossing_Time'].notna()) & 
            (results_df['Crossing_Time'] != '') & 
            (results_df['Original_CP'].notna()) & 
            (results_df['Original_CP'] != '')
        ]
        
        if len(successful_matches) > 0:
            differences = []
            for _, row in successful_matches.iterrows():
                diff = abs(float(row['Crossing_Time']) - float(row['Original_CP']))
                differences.append(diff)
            
            avg_diff = np.mean(differences)
            max_diff = max(differences)
            print(f"Average difference: {avg_diff:.2f} minutes")
            print(f"Maximum difference: {max_diff:.2f} minutes")
            
            if avg_diff < 5.0:
                print("✅ Crossing points are reasonably close to original")
            else:
                print("⚠️ Crossing points show significant differences")
        
    except Exception as e:
        print(f"⚠️ Summary comparison failed: {e}")
    
    print("\n" + "="*60)
    print(" TARGETED VERIFICATION COMPLETE")
    print("="*60)
    print(f"Output directory: {output_dir}")
    print("Files generated:")
    print("  - new_tool_targeted_results.csv (wells with expected crossing points)")
    print("  - well_plots/ (individual well plots)")
    
    return True

def create_well_plot(well_id, time_points, fluo_values, fitted_values, threshold, 
                    crossing_time, fit_result, plot_dir, orig_cp):
    """Create a plot for a single well"""
    try:
        plt.figure(figsize=(12, 8))
        
        # Plot data points
        plt.scatter(time_points, fluo_values, alpha=0.7, color='blue', s=30, label='Data')
        
        # Plot fitted curve
        if fitted_values is not None:
            plt.plot(time_points, fitted_values, 'r-', linewidth=2, 
                    label=f'Fitted Curve (R²={fit_result.r_squared:.3f})')
        
        # Plot threshold line
        plt.axhline(y=threshold, color='green', linestyle='--', linewidth=1, 
                   label=f'Threshold ({threshold:.1f})')
        
        # Plot crossing points
        if crossing_time is not None:
            plt.axvline(x=crossing_time, color='orange', linestyle='--', linewidth=2,
                       label=f'NEW CP ({crossing_time:.2f} min)')
        
        if orig_cp and orig_cp != '':
            plt.axvline(x=float(orig_cp), color='purple', linestyle=':', linewidth=2,
                       label=f'Original CP ({float(orig_cp):.2f} min)')
        
        plt.xlabel('Time (minutes)')
        plt.ylabel('Fluorescence')
        plt.title(f'Well {well_id} - NEW vs Original Analysis')
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
    success = run_targeted_analysis()
    sys.exit(0 if success else 1)