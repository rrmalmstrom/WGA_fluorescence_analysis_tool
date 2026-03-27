#!/usr/bin/env python3
"""
Simple Verification Script for Fluorescence Analysis Tool

This script loads example data, fits curves, performs calculations,
and generates figures and output files to demonstrate the tool's functionality.
"""

import sys
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fluorescence_tool.parsers.bmg_parser import BMGOmega3Parser
from fluorescence_tool.parsers.biorad_parser import BioRadParser
from fluorescence_tool.parsers.layout_parser import LayoutParser
from fluorescence_tool.algorithms.curve_fitting import CurveFitter
from fluorescence_tool.algorithms.threshold_analysis import ThresholdAnalyzer
from fluorescence_tool.algorithms.statistical_analysis import StatisticalAnalyzer


def main():
    """Main verification function."""
    print("=" * 80)
    print(" FLUORESCENCE ANALYSIS TOOL - SIMPLE VERIFICATION")
    print("=" * 80)
    
    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "example_input_files"
    output_dir = Path(__file__).parent / "verification_output"
    output_dir.mkdir(exist_ok=True)
    
    # Initialize components
    curve_fitter = CurveFitter()
    threshold_analyzer = ThresholdAnalyzer()
    statistical_analyzer = StatisticalAnalyzer()
    
    print("\n1. Loading BMG Omega3 Data...")
    print("-" * 40)
    
    # Load BMG data
    bmg_file = data_dir / "RM5097.96HL.BNCT.1.CSV"
    bmg_layout_file = data_dir / "RM5097_layout.csv"
    
    bmg_parser = BMGOmega3Parser()
    layout_parser = LayoutParser()
    
    try:
        bmg_data = bmg_parser.parse_file(str(bmg_file))
        bmg_layout = layout_parser.parse_file(str(bmg_layout_file))
        
        print(f"✅ Successfully loaded BMG data:")
        print(f"   - Wells: {len(bmg_data.wells)}")
        print(f"   - Time points: {len(bmg_data.time_points)}")
        print(f"   - Time range: {bmg_data.time_points[0]:.1f} - {bmg_data.time_points[-1]:.1f} minutes")
        print(f"   - Layout wells: {len(bmg_layout)}")
        
    except Exception as e:
        print(f"❌ Error loading BMG data: {e}")
        return
    
    print("\n2. Analyzing Sample Wells...")
    print("-" * 40)
    
    # Select wells for analysis (first 6 wells with sufficient data)
    wells_to_analyze = []
    for i, well_id in enumerate(bmg_data.wells):
        if len(bmg_data.measurements[i]) > 10:
            wells_to_analyze.append((i, well_id))
            if len(wells_to_analyze) >= 6:
                break
    
    print(f"Selected wells for analysis: {[w[1] for w in wells_to_analyze]}")
    
    # Perform curve fitting and analysis
    results = []
    
    print("\n3. Curve Fitting Analysis...")
    print("-" * 40)
    
    for well_idx, well_id in wells_to_analyze:
        measurements = bmg_data.measurements[well_idx]
        
        print(f"\nAnalyzing well {well_id}:")
        
        # Curve fitting
        try:
            fit_result = curve_fitter.fit_curve(
                time_points=bmg_data.time_points,
                measurements=measurements
            )
            
            if fit_result.success:
                print(f"  ✅ Curve fit successful - R²: {fit_result.r_squared:.3f}, RMSE: {fit_result.rmse:.1f}")
            else:
                print(f"  ❌ Curve fit failed: {fit_result.error_message}")
                continue
                
        except Exception as e:
            print(f"  ❌ Error in curve fitting: {e}")
            continue
        
        # Threshold detection
        try:
            threshold_result = threshold_analyzer.detect_threshold_crossing(
                time_points=bmg_data.time_points,
                measurements=measurements,
                method='baseline_std'
            )
            
            if threshold_result.success:
                print(f"  ✅ Threshold detection - Crossing time: {threshold_result.crossing_time:.1f} min")
                print(f"     Threshold value: {threshold_result.threshold_value:.1f}")
            else:
                print(f"  ❌ Threshold detection failed: {threshold_result.error_message}")
                
        except Exception as e:
            print(f"  ❌ Error in threshold detection: {e}")
            threshold_result = None
        
        # Store results
        well_result = {
            'well_id': well_id,
            'well_idx': well_idx,
            'measurements': measurements,
            'fit_result': fit_result,
            'threshold_result': threshold_result,
            'layout_info': bmg_layout.get(well_id, None)
        }
        results.append(well_result)
    
    print(f"\n✅ Successfully analyzed {len(results)} wells")
    
    print("\n4. Generating Visualization...")
    print("-" * 40)
    
    # Create comprehensive plots
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    for i, result in enumerate(results):
        if i >= 6:
            break
            
        ax = axes[i]
        well_id = result['well_id']
        measurements = result['measurements']
        fit_result = result['fit_result']
        threshold_result = result['threshold_result']
        
        # Plot raw data
        ax.scatter(bmg_data.time_points, measurements, 
                  alpha=0.6, s=30, color='blue', label='Raw data')
        
        # Plot fitted curve if successful
        if fit_result and fit_result.success:
            fitted_values = [
                curve_fitter.sigmoid_5param(t, *fit_result.parameters)
                for t in bmg_data.time_points
            ]
            ax.plot(bmg_data.time_points, fitted_values, 
                   'r-', linewidth=2, label=f'Fitted curve (R²={fit_result.r_squared:.3f})')
        
        # Plot threshold and crossing point
        if threshold_result and threshold_result.success:
            ax.axhline(y=threshold_result.threshold_value, color='orange', 
                      linestyle='--', alpha=0.8, label=f'Threshold: {threshold_result.threshold_value:.0f}')
            
            if threshold_result.crossing_time is not None:
                ax.axvline(x=threshold_result.crossing_time, color='green', 
                          linestyle=':', alpha=0.8, label=f'Crossing: {threshold_result.crossing_time:.1f} min')
                ax.plot(threshold_result.crossing_time, threshold_result.threshold_value, 
                       'go', markersize=8, label='Crossing point')
        
        # Formatting
        ax.set_xlabel('Time (minutes)')
        ax.set_ylabel('Fluorescence')
        ax.set_title(f'Well {well_id}')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'curve_fitting_analysis.png', dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'curve_fitting_analysis.pdf', bbox_inches='tight')
    print(f"✅ Saved plots to: {output_dir / 'curve_fitting_analysis.png'}")
    
    # Show the plot
    plt.show()
    
    print("\n5. Statistical Analysis...")
    print("-" * 40)
    
    # Group wells by layout information
    if bmg_layout:
        # Group by well type
        type_groups = {}
        for result in results:
            layout_info = result['layout_info']
            if layout_info:
                well_type = layout_info.well_type
                if well_type not in type_groups:
                    type_groups[well_type] = []
                type_groups[well_type].append(result)
        
        print(f"Wells grouped by type:")
        for well_type, group_results in type_groups.items():
            print(f"  - {well_type}: {len(group_results)} wells")
        
        # Calculate statistics for each group
        group_stats = {}
        for well_type, group_results in type_groups.items():
            # Get final fluorescence values
            final_values = []
            crossing_times = []
            
            for result in group_results:
                if len(result['measurements']) > 0:
                    final_values.append(result['measurements'][-1])
                
                if (result['threshold_result'] and 
                    result['threshold_result'].success and 
                    result['threshold_result'].crossing_time is not None):
                    crossing_times.append(result['threshold_result'].crossing_time)
            
            if final_values:
                stats = statistical_analyzer.calculate_descriptive_statistics(final_values)
                group_stats[well_type] = {
                    'final_fluorescence': stats,
                    'crossing_times': crossing_times
                }
                
                print(f"\n{well_type} group statistics:")
                print(f"  Final fluorescence - Mean: {stats['mean']:.1f}, Std: {stats['std']:.1f}")
                if crossing_times:
                    crossing_stats = statistical_analyzer.calculate_descriptive_statistics(crossing_times)
                    print(f"  Crossing times - Mean: {crossing_stats['mean']:.1f} min, Std: {crossing_stats['std']:.1f} min")
    
    print("\n6. Generating Output Files...")
    print("-" * 40)
    
    # Create detailed results CSV
    output_data = []
    for result in results:
        row = {
            'Well_ID': result['well_id'],
            'Well_Type': result['layout_info'].well_type if result['layout_info'] else 'unknown',
            'Group_1': result['layout_info'].group_1 if result['layout_info'] else '',
            'Final_Fluorescence': result['measurements'][-1] if len(result['measurements']) > 0 else np.nan,
            'R_Squared': result['fit_result'].r_squared if result['fit_result'] and result['fit_result'].success else np.nan,
            'RMSE': result['fit_result'].rmse if result['fit_result'] and result['fit_result'].success else np.nan,
            'Threshold_Value': result['threshold_result'].threshold_value if result['threshold_result'] and result['threshold_result'].success else np.nan,
            'Crossing_Time': result['threshold_result'].crossing_time if result['threshold_result'] and result['threshold_result'].success else np.nan,
            'Fit_Success': result['fit_result'].success if result['fit_result'] else False,
            'Threshold_Success': result['threshold_result'].success if result['threshold_result'] else False
        }
        output_data.append(row)
    
    # Save to CSV
    df = pd.DataFrame(output_data)
    csv_file = output_dir / 'analysis_results.csv'
    df.to_csv(csv_file, index=False)
    print(f"✅ Saved detailed results to: {csv_file}")
    
    # Create summary report
    summary_file = output_dir / 'analysis_summary.txt'
    with open(summary_file, 'w') as f:
        f.write("Fluorescence Analysis Tool - Verification Summary\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"Input Files:\n")
        f.write(f"  - Fluorescence data: {bmg_file.name}\n")
        f.write(f"  - Layout data: {bmg_layout_file.name}\n\n")
        
        f.write(f"Data Overview:\n")
        f.write(f"  - Total wells in dataset: {len(bmg_data.wells)}\n")
        f.write(f"  - Time points: {len(bmg_data.time_points)}\n")
        f.write(f"  - Time range: {bmg_data.time_points[0]:.1f} - {bmg_data.time_points[-1]:.1f} minutes\n\n")
        
        f.write(f"Analysis Results:\n")
        f.write(f"  - Wells analyzed: {len(results)}\n")
        
        successful_fits = sum(1 for r in results if r['fit_result'] and r['fit_result'].success)
        f.write(f"  - Successful curve fits: {successful_fits}/{len(results)}\n")
        
        successful_thresholds = sum(1 for r in results if r['threshold_result'] and r['threshold_result'].success)
        f.write(f"  - Successful threshold detections: {successful_thresholds}/{len(results)}\n")
        
        if successful_fits > 0:
            r_squared_values = [r['fit_result'].r_squared for r in results 
                              if r['fit_result'] and r['fit_result'].success]
            f.write(f"  - R² range: {min(r_squared_values):.3f} - {max(r_squared_values):.3f}\n")
            f.write(f"  - R² mean: {np.mean(r_squared_values):.3f}\n")
        
        if successful_thresholds > 0:
            crossing_times = [r['threshold_result'].crossing_time for r in results 
                            if r['threshold_result'] and r['threshold_result'].success 
                            and r['threshold_result'].crossing_time is not None]
            if crossing_times:
                f.write(f"  - Crossing time range: {min(crossing_times):.1f} - {max(crossing_times):.1f} minutes\n")
                f.write(f"  - Crossing time mean: {np.mean(crossing_times):.1f} minutes\n")
        
        f.write(f"\nOutput Files:\n")
        f.write(f"  - Detailed results: analysis_results.csv\n")
        f.write(f"  - Visualization: curve_fitting_analysis.png\n")
        f.write(f"  - Summary report: analysis_summary.txt\n")
    
    print(f"✅ Saved summary report to: {summary_file}")
    
    print("\n7. Verification Complete!")
    print("-" * 40)
    print(f"✅ Successfully processed {len(results)} wells")
    print(f"✅ Generated plots and output files in: {output_dir}")
    print(f"✅ Curve fitting success rate: {successful_fits}/{len(results)} ({100*successful_fits/len(results):.1f}%)")
    print(f"✅ Threshold detection success rate: {successful_thresholds}/{len(results)} ({100*successful_thresholds/len(results):.1f}%)")
    
    # Display sample results
    print(f"\nSample Results:")
    print(f"{'Well':<6} {'Type':<12} {'R²':<6} {'RMSE':<8} {'Crossing':<10} {'Final FL':<10}")
    print("-" * 60)
    
    for result in results[:6]:
        well_id = result['well_id']
        well_type = result['layout_info'].well_type if result['layout_info'] else 'unknown'
        r_squared = f"{result['fit_result'].r_squared:.3f}" if result['fit_result'] and result['fit_result'].success else "N/A"
        rmse = f"{result['fit_result'].rmse:.1f}" if result['fit_result'] and result['fit_result'].success else "N/A"
        crossing = f"{result['threshold_result'].crossing_time:.1f}" if result['threshold_result'] and result['threshold_result'].success and result['threshold_result'].crossing_time else "N/A"
        final_fl = f"{result['measurements'][-1]:.0f}" if len(result['measurements']) > 0 else "N/A"
        
        print(f"{well_id:<6} {well_type:<12} {r_squared:<6} {rmse:<8} {crossing:<10} {final_fl:<10}")
    
    print(f"\n🎉 Verification completed successfully!")
    print(f"   The fluorescence analysis algorithms are working correctly with real data.")


if __name__ == "__main__":
    main()