#!/usr/bin/env python3
"""
REAL Performance Profiling Script for MDA Fluorescence Analysis Tool

This script profiles the ACTUAL GUI workflow to get realistic timing data.
It simulates the real user workflow by loading data and running the analysis
exactly as it would happen in the GUI.

Usage:
    python profile_real_performance.py

Output:
    - Console output with realistic timing breakdown
    - real_performance_results.csv with detailed metrics
    - real_performance_summary.txt with analysis
"""

import time
import cProfile
import pstats
import io
import sys
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import csv

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the actual GUI components and workflow
from fluorescence_tool.core.models import FluorescenceData, WellInfo
from fluorescence_tool.algorithms.curve_fitting import CurveFitter
from fluorescence_tool.algorithms.threshold_analysis import ThresholdAnalyzer
from fluorescence_tool.parsers.bmg_parser import BMGOmega3Parser
from fluorescence_tool.parsers.biorad_parser import BioRadParser
from fluorescence_tool.parsers.layout_parser import LayoutParser


class RealPerformanceProfiler:
    """Profiles the actual analysis workflow as it runs in the GUI."""
    
    def __init__(self):
        self.results = []
        
    def simulate_gui_analysis_workflow(self, fluorescence_data: FluorescenceData, 
                                     layout_data: Optional[Dict[str, WellInfo]] = None,
                                     qc_threshold_percent: float = 10.0) -> Dict:
        """
        Simulate the exact analysis workflow from main_window.py _run_analysis method.
        This replicates the real bottlenecks exactly as they occur in the GUI.
        """
        print(f"\n=== SIMULATING REAL GUI WORKFLOW ===")
        print(f"Dataset: {len(fluorescence_data.wells)} total wells")
        
        # Start timing the complete workflow
        workflow_start = time.perf_counter()
        
        # Initialize analysis components exactly as in GUI
        curve_fitter = CurveFitter(timeout_seconds=2)  # Real 2-second timeout per strategy
        threshold_analyzer = ThresholdAnalyzer(baseline_percentage=qc_threshold_percent/100.0)
        
        # Prepare results structure (as in GUI)
        analysis_results = {
            'fluorescence_data': fluorescence_data,
            'layout_data': list(layout_data.values()) if layout_data else [],
            'curve_fits': {}
        }
        
        # Process each well exactly as in GUI (this is the main bottleneck!)
        total_wells = len(fluorescence_data.wells)
        time_points = np.array(fluorescence_data.time_points)
        
        # Count wells to analyze (excluding unused) - exactly as in GUI
        wells_to_analyze = []
        for well_id in fluorescence_data.wells:
            if layout_data and well_id in layout_data:
                well_info = layout_data[well_id]
                if well_info.well_type != "unused":
                    wells_to_analyze.append(well_id)
            else:
                # If no layout data, analyze all wells
                wells_to_analyze.append(well_id)
        
        print(f"Wells to analyze: {len(wells_to_analyze)}")
        print(f"Skipping {total_wells - len(wells_to_analyze)} unused wells")
        
        # Time the sequential well processing (THE MAIN BOTTLENECK)
        sequential_start = time.perf_counter()
        
        well_timings = []
        curve_fit_timings = []
        threshold_timings = []
        
        for i, well_id in enumerate(fluorescence_data.wells):
            well_start = time.perf_counter()
            
            # Skip unused wells (as in GUI)
            if well_id not in wells_to_analyze:
                analysis_results['curve_fits'][well_id] = {
                    'curve_result': None,
                    'threshold_result': None,
                    'fitted_curve': None,
                    'crossing_point': None,
                    'threshold_value': None
                }
                continue
            
            print(f"Processing well {well_id} ({wells_to_analyze.index(well_id)+1}/{len(wells_to_analyze)})...")
            
            # Extract fluorescence values for this well
            fluo_values = fluorescence_data.measurements[i, :]
            
            # CURVE FITTING - This is where the real time is spent
            curve_start = time.perf_counter()
            curve_result = curve_fitter.fit_curve(time_points, fluo_values)
            curve_end = time.perf_counter()
            curve_time = (curve_end - curve_start) * 1000
            curve_fit_timings.append(curve_time)
            
            # Generate fitted curve from parameters if successful
            fitted_curve = None
            if curve_result.success and curve_result.parameters:
                try:
                    fitted_curve = curve_fitter.sigmoid_5param(
                        time_points, *curve_result.parameters)
                except Exception as e:
                    print(f"Warning: Could not generate fitted curve for {well_id}: {e}")
            
            # THRESHOLD ANALYSIS - Second derivative calculation
            threshold_start = time.perf_counter()
            if curve_result.success and curve_result.parameters:
                # Use the fitted curve method (as in GUI)
                threshold_result = threshold_analyzer.analyze_threshold_crossing_with_fitted_curve(
                    time_points, fluo_values, curve_result.parameters, method="qc_second_derivative")
            else:
                # Fallback method (as in GUI)
                threshold_result = threshold_analyzer.analyze_threshold_crossing(
                    time_points, fluo_values, method="qc_second_derivative")
            threshold_end = time.perf_counter()
            threshold_time = (threshold_end - threshold_start) * 1000
            threshold_timings.append(threshold_time)
            
            # Store results (as in GUI)
            analysis_results['curve_fits'][well_id] = {
                'curve_result': curve_result,
                'threshold_result': threshold_result,
                'fitted_curve': fitted_curve,
                'crossing_point': threshold_result.crossing_time if threshold_result.success else None,
                'threshold_value': threshold_result.threshold_value if threshold_result.success else None
            }
            
            well_end = time.perf_counter()
            well_time = (well_end - well_start) * 1000
            well_timings.append(well_time)
            
            print(f"  Well {well_id}: {well_time:.1f}ms (Curve: {curve_time:.1f}ms, Threshold: {threshold_time:.1f}ms)")
        
        sequential_end = time.perf_counter()
        sequential_time = (sequential_end - sequential_start) * 1000
        
        workflow_end = time.perf_counter()
        total_workflow_time = (workflow_end - workflow_start) * 1000
        
        # Calculate statistics
        successful_fits = sum(1 for result in analysis_results['curve_fits'].values()
                            if result['curve_result'] is not None and result['curve_result'].success)
        successful_thresholds = sum(1 for result in analysis_results['curve_fits'].values()
                                  if result['threshold_result'] is not None and result['threshold_result'].success)
        
        return {
            'dataset_name': f"Real Workflow Test ({len(wells_to_analyze)} wells)",
            'total_wells': total_wells,
            'analyzed_wells': len(wells_to_analyze),
            'total_workflow_time_ms': total_workflow_time,
            'sequential_processing_time_ms': sequential_time,
            'well_timings_ms': well_timings,
            'curve_fit_timings_ms': curve_fit_timings,
            'threshold_timings_ms': threshold_timings,
            'avg_time_per_well_ms': np.mean(well_timings) if well_timings else 0,
            'min_time_per_well_ms': np.min(well_timings) if well_timings else 0,
            'max_time_per_well_ms': np.max(well_timings) if well_timings else 0,
            'avg_curve_fit_time_ms': np.mean(curve_fit_timings) if curve_fit_timings else 0,
            'avg_threshold_time_ms': np.mean(threshold_timings) if threshold_timings else 0,
            'successful_curve_fits': successful_fits,
            'successful_threshold_analyses': successful_thresholds,
            'analysis_results': analysis_results
        }
    
    def profile_with_cprofile(self, fluorescence_data: FluorescenceData, 
                            layout_data: Optional[Dict[str, WellInfo]] = None) -> Tuple[Dict, str]:
        """Profile using cProfile to get detailed function-level timing."""
        print(f"\n=== DETAILED FUNCTION PROFILING ===")
        
        # Create a profiler
        profiler = cProfile.Profile()
        
        # Profile the workflow
        profiler.enable()
        results = self.simulate_gui_analysis_workflow(fluorescence_data, layout_data)
        profiler.disable()
        
        # Get profiling results
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s)
        ps.sort_stats('cumulative')
        ps.print_stats(50)  # Top 50 functions
        profile_output = s.getvalue()
        
        return results, profile_output
    
    def load_test_dataset(self) -> Tuple[FluorescenceData, Optional[Dict[str, WellInfo]]]:
        """Load a realistic test dataset for profiling."""
        test_data_dir = Path("test_data")
        
        # Try to load the full BMG dataset (most realistic)
        try:
            layout_path = test_data_dir / "RM5097_layout.csv"
            data_path = test_data_dir / "RM5097.96HL.BNCT.1.CSV"
            
            if layout_path.exists() and data_path.exists():
                layout_parser = LayoutParser()
                layout_data = layout_parser.parse_file(str(layout_path))
                
                bmg_parser = BMGOmega3Parser()
                fluorescence_data = bmg_parser.parse_file(str(data_path))
                
                print(f"Loaded full BMG dataset: {len(fluorescence_data.wells)} wells")
                return fluorescence_data, layout_data
        except Exception as e:
            print(f"Failed to load full BMG dataset: {e}")
        
        # Fallback to small dataset
        try:
            layout_path = test_data_dir / "smallRM5097_layout.csv"
            data_path = test_data_dir / "RM5097.96HL.BNCT.1.CSV"
            
            if layout_path.exists() and data_path.exists():
                layout_parser = LayoutParser()
                layout_data = layout_parser.parse_file(str(layout_path))
                
                bmg_parser = BMGOmega3Parser()
                fluorescence_data = bmg_parser.parse_file(str(data_path))
                
                print(f"Loaded small BMG dataset: {len(fluorescence_data.wells)} wells")
                return fluorescence_data, layout_data
        except Exception as e:
            print(f"Failed to load small BMG dataset: {e}")
        
        raise RuntimeError("No test datasets could be loaded!")


def save_real_results(results: Dict, profile_output: str):
    """Save the real performance results."""
    
    # Save CSV with per-well data
    csv_filename = "real_performance_results.csv"
    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['well_index', 'well_time_ms', 'curve_fit_time_ms', 'threshold_time_ms']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for i, (well_time, curve_time, threshold_time) in enumerate(zip(
            results['well_timings_ms'], 
            results['curve_fit_timings_ms'], 
            results['threshold_timings_ms']
        )):
            writer.writerow({
                'well_index': i,
                'well_time_ms': well_time,
                'curve_fit_time_ms': curve_time,
                'threshold_time_ms': threshold_time
            })
    
    # Save detailed summary
    summary_filename = "real_performance_summary.txt"
    with open(summary_filename, 'w') as f:
        f.write("REAL FLUORESCENCE ANALYSIS TOOL - PERFORMANCE PROFILING\n")
        f.write("=" * 70 + "\n\n")
        
        f.write("REALISTIC PERFORMANCE MEASUREMENTS\n")
        f.write("-" * 40 + "\n")
        f.write(f"Dataset: {results['dataset_name']}\n")
        f.write(f"Total wells: {results['total_wells']}\n")
        f.write(f"Analyzed wells: {results['analyzed_wells']}\n")
        f.write(f"Skipped wells: {results['total_wells'] - results['analyzed_wells']}\n\n")
        
        f.write("TIMING BREAKDOWN\n")
        f.write("-" * 20 + "\n")
        f.write(f"Total workflow time: {results['total_workflow_time_ms']/1000:.2f} seconds\n")
        f.write(f"Sequential processing time: {results['sequential_processing_time_ms']/1000:.2f} seconds\n")
        f.write(f"Average time per well: {results['avg_time_per_well_ms']:.1f} ms\n")
        f.write(f"Min time per well: {results['min_time_per_well_ms']:.1f} ms\n")
        f.write(f"Max time per well: {results['max_time_per_well_ms']:.1f} ms\n")
        f.write(f"Average curve fitting time: {results['avg_curve_fit_time_ms']:.1f} ms\n")
        f.write(f"Average threshold analysis time: {results['avg_threshold_time_ms']:.1f} ms\n\n")
        
        # Calculate percentages
        curve_pct = (results['avg_curve_fit_time_ms'] / results['avg_time_per_well_ms']) * 100 if results['avg_time_per_well_ms'] > 0 else 0
        threshold_pct = (results['avg_threshold_time_ms'] / results['avg_time_per_well_ms']) * 100 if results['avg_time_per_well_ms'] > 0 else 0
        
        f.write("TIME DISTRIBUTION\n")
        f.write("-" * 20 + "\n")
        f.write(f"Curve fitting: {curve_pct:.1f}% of per-well time\n")
        f.write(f"Threshold analysis: {threshold_pct:.1f}% of per-well time\n\n")
        
        f.write("SUCCESS RATES\n")
        f.write("-" * 15 + "\n")
        f.write(f"Successful curve fits: {results['successful_curve_fits']}/{results['analyzed_wells']} ({(results['successful_curve_fits']/results['analyzed_wells']*100):.1f}%)\n")
        f.write(f"Successful threshold analyses: {results['successful_threshold_analyses']}/{results['analyzed_wells']} ({(results['successful_threshold_analyses']/results['analyzed_wells']*100):.1f}%)\n\n")
        
        # Extrapolation
        f.write("PERFORMANCE EXTRAPOLATION\n")
        f.write("-" * 30 + "\n")
        f.write(f"Estimated time for 96-well plate: {(results['avg_time_per_well_ms'] * 96)/1000:.1f} seconds\n")
        f.write(f"Estimated time for 384-well plate: {(results['avg_time_per_well_ms'] * 384)/1000:.1f} seconds\n\n")
        
        f.write("DETAILED FUNCTION PROFILING\n")
        f.write("-" * 35 + "\n")
        f.write(profile_output)
    
    print(f"\nResults saved to:")
    print(f"  {csv_filename}")
    print(f"  {summary_filename}")


def main():
    """Main profiling function."""
    print("REAL FLUORESCENCE ANALYSIS TOOL - PERFORMANCE PROFILER")
    print("=" * 70)
    print("This script profiles the ACTUAL GUI workflow to get realistic timing data.")
    print("It simulates the real bottlenecks exactly as they occur in production.\n")
    
    # Initialize profiler
    profiler = RealPerformanceProfiler()
    
    # Load test dataset
    try:
        fluorescence_data, layout_data = profiler.load_test_dataset()
    except Exception as e:
        print(f"ERROR: Could not load test dataset: {e}")
        return
    
    # Run realistic profiling
    print(f"\n{'='*70}")
    print("RUNNING REALISTIC PERFORMANCE PROFILING")
    print(f"{'='*70}")
    
    try:
        results, profile_output = profiler.profile_with_cprofile(fluorescence_data, layout_data)
        
        # Save results
        save_real_results(results, profile_output)
        
        # Print summary
        print(f"\n{'='*70}")
        print("REAL PERFORMANCE SUMMARY")
        print(f"{'='*70}")
        print(f"Dataset: {results['dataset_name']}")
        print(f"Total workflow time: {results['total_workflow_time_ms']/1000:.2f} seconds")
        print(f"Average time per well: {results['avg_time_per_well_ms']:.1f} ms")
        print(f"Curve fitting average: {results['avg_curve_fit_time_ms']:.1f} ms")
        print(f"Threshold analysis average: {results['avg_threshold_time_ms']:.1f} ms")
        print(f"Success rate: {(results['successful_curve_fits']/results['analyzed_wells']*100):.1f}%")
        print(f"\nEstimated 96-well plate time: {(results['avg_time_per_well_ms'] * 96)/1000:.1f} seconds")
        
        print(f"\nReal profiling complete! Check real_performance_summary.txt for detailed analysis.")
        
    except Exception as e:
        print(f"ERROR during profiling: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()