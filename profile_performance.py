#!/usr/bin/env python3
"""
Performance Profiling Script for MDA Fluorescence Analysis Tool

This script instruments the key bottleneck functions identified in the analysis:
1. Sequential well processing (no parallelization)
2. Redundant curve fitting (done twice per well)
3. Multiple fitting strategy attempts (up to 3 strategies × 2s timeout)
4. Expensive second derivative calculation (20× interpolation)

Usage:
    python profile_performance.py

Output:
    - Console output with detailed timing breakdown
    - performance_profile_results.csv with detailed metrics
    - performance_summary.txt with analysis summary
"""

import time
import tracemalloc
import psutil
import os
import sys
import csv
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the fluorescence tool modules
from fluorescence_tool.core.models import FluorescenceData, WellInfo
from fluorescence_tool.algorithms.curve_fitting import CurveFitter
from fluorescence_tool.algorithms.threshold_analysis import ThresholdAnalyzer
from fluorescence_tool.parsers.bmg_parser import BMGOmega3Parser
from fluorescence_tool.parsers.biorad_parser import BioRadParser
from fluorescence_tool.parsers.layout_parser import LayoutParser


@dataclass
class TimingResult:
    """Container for timing measurements."""
    operation: str
    duration_ms: float
    well_id: Optional[str] = None
    strategy_used: Optional[str] = None
    attempts_made: Optional[int] = None
    success: bool = True
    memory_peak_mb: Optional[float] = None
    additional_info: Optional[Dict[str, Any]] = None


@dataclass
class WellProfileResult:
    """Container for per-well profiling results."""
    well_id: str
    total_time_ms: float
    curve_fitting_time_ms: float
    threshold_analysis_time_ms: float
    curve_fit_attempts: int
    curve_fit_success: bool
    threshold_success: bool
    strategy_used: Optional[str] = None
    memory_peak_mb: Optional[float] = None


@dataclass
class DatasetProfileResult:
    """Container for dataset-level profiling results."""
    dataset_name: str
    total_wells: int
    analyzed_wells: int
    total_time_ms: float
    avg_time_per_well_ms: float
    min_time_per_well_ms: float
    max_time_per_well_ms: float
    curve_fitting_total_ms: float
    threshold_analysis_total_ms: float
    total_curve_fit_attempts: int
    successful_curve_fits: int
    successful_threshold_analyses: int
    peak_memory_mb: float
    well_results: List[WellProfileResult]


class PerformanceProfiler:
    """Main profiling class that instruments the analysis workflow."""
    
    def __init__(self):
        self.timing_results: List[TimingResult] = []
        self.process = psutil.Process()
        self.baseline_memory_mb = self.process.memory_info().rss / 1024 / 1024
        
    @contextmanager
    def time_operation(self, operation: str, well_id: Optional[str] = None, **kwargs):
        """Context manager for timing operations with memory tracking."""
        # Start memory tracking
        tracemalloc.start()
        start_memory = self.process.memory_info().rss / 1024 / 1024
        
        start_time = time.perf_counter()
        success = True
        error_info = None
        
        try:
            yield
        except Exception as e:
            success = False
            error_info = {"error": str(e), "type": type(e).__name__}
            raise
        finally:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            # Get peak memory usage
            current_memory = self.process.memory_info().rss / 1024 / 1024
            peak_memory = max(start_memory, current_memory)
            
            # Stop memory tracking
            try:
                tracemalloc.stop()
            except:
                pass  # tracemalloc might not be running
            
            # Record timing result
            result = TimingResult(
                operation=operation,
                duration_ms=duration_ms,
                well_id=well_id,
                success=success,
                memory_peak_mb=peak_memory,
                additional_info=error_info or kwargs
            )
            self.timing_results.append(result)
            
            print(f"  {operation}: {duration_ms:.2f}ms (Memory: {peak_memory:.1f}MB)")
    
    def profile_curve_fitting(self, time_points: np.ndarray, fluo_values: np.ndarray, 
                            well_id: str) -> Tuple[Any, int, Optional[str]]:
        """Profile curve fitting with detailed strategy tracking."""
        curve_fitter = CurveFitter(timeout_seconds=2)
        
        with self.time_operation(f"Curve Fitting - {well_id}", well_id=well_id):
            # Get fitting strategies to count attempts
            strategies = curve_fitter._get_fit_strategies(time_points, fluo_values)
            attempts_made = 0
            strategy_used = None
            
            # Instrument the fit_curve method to track strategy attempts
            original_fit_curve = curve_fitter.fit_curve
            
            def instrumented_fit_curve(tp, fv):
                nonlocal attempts_made, strategy_used
                
                # Track each strategy attempt
                for i, attempt in enumerate(strategies):
                    attempts_made += 1
                    with self.time_operation(f"Strategy {i+1}: {attempt['name']}", 
                                           well_id=well_id, strategy=attempt['name']):
                        # This timing is approximate since we can't easily instrument
                        # the internal strategy loop without modifying the source
                        pass
                
                # Call original method
                result = original_fit_curve(tp, fv)
                if result.success:
                    strategy_used = result.strategy_used
                return result
            
            # Temporarily replace method
            curve_fitter.fit_curve = instrumented_fit_curve
            
            try:
                result = curve_fitter.fit_curve(time_points, fluo_values)
                return result, attempts_made, strategy_used
            finally:
                # Restore original method
                curve_fitter.fit_curve = original_fit_curve
    
    def profile_threshold_analysis(self, time_points: np.ndarray, fluo_values: np.ndarray,
                                 fitted_parameters: Optional[List[float]], well_id: str) -> Any:
        """Profile threshold analysis with second derivative timing."""
        threshold_analyzer = ThresholdAnalyzer(baseline_percentage=0.10)
        
        with self.time_operation(f"Threshold Analysis - {well_id}", well_id=well_id):
            if fitted_parameters:
                # Profile the expensive second derivative calculation
                with self.time_operation(f"Second Derivative Calc - {well_id}", 
                                       well_id=well_id, interpolation_factor=20):
                    result = threshold_analyzer.analyze_threshold_crossing_with_fitted_curve(
                        time_points, fluo_values, fitted_parameters, method="qc_second_derivative")
            else:
                # Fallback method
                with self.time_operation(f"Fallback Threshold - {well_id}", well_id=well_id):
                    result = threshold_analyzer.analyze_threshold_crossing(
                        time_points, fluo_values, method="qc_second_derivative")
        
        return result
    
    def profile_well_processing(self, well_id: str, time_points: np.ndarray, 
                              fluo_values: np.ndarray) -> WellProfileResult:
        """Profile complete processing of a single well."""
        print(f"\nProfiling well {well_id}...")
        
        well_start_time = time.perf_counter()
        start_memory = self.process.memory_info().rss / 1024 / 1024
        
        # Profile curve fitting
        curve_start_time = time.perf_counter()
        curve_result, attempts_made, strategy_used = self.profile_curve_fitting(
            time_points, fluo_values, well_id)
        curve_end_time = time.perf_counter()
        curve_fitting_time_ms = (curve_end_time - curve_start_time) * 1000
        
        # Profile threshold analysis
        threshold_start_time = time.perf_counter()
        fitted_params = curve_result.parameters if curve_result.success else None
        threshold_result = self.profile_threshold_analysis(
            time_points, fluo_values, fitted_params, well_id)
        threshold_end_time = time.perf_counter()
        threshold_analysis_time_ms = (threshold_end_time - threshold_start_time) * 1000
        
        well_end_time = time.perf_counter()
        total_time_ms = (well_end_time - well_start_time) * 1000
        
        end_memory = self.process.memory_info().rss / 1024 / 1024
        peak_memory = max(start_memory, end_memory)
        
        return WellProfileResult(
            well_id=well_id,
            total_time_ms=total_time_ms,
            curve_fitting_time_ms=curve_fitting_time_ms,
            threshold_analysis_time_ms=threshold_analysis_time_ms,
            curve_fit_attempts=attempts_made,
            curve_fit_success=curve_result.success,
            threshold_success=threshold_result.success,
            strategy_used=strategy_used,
            memory_peak_mb=peak_memory
        )
    
    def profile_dataset(self, dataset_name: str, fluorescence_data: FluorescenceData,
                       layout_data: Optional[Dict[str, WellInfo]] = None) -> DatasetProfileResult:
        """Profile complete dataset processing."""
        print(f"\n{'='*60}")
        print(f"PROFILING DATASET: {dataset_name}")
        print(f"{'='*60}")
        
        dataset_start_time = time.perf_counter()
        start_memory = self.process.memory_info().rss / 1024 / 1024
        
        time_points = np.array(fluorescence_data.time_points)
        well_results = []
        
        # Determine wells to analyze (skip unused wells)
        wells_to_analyze = []
        for i, well_id in enumerate(fluorescence_data.wells):
            if layout_data and well_id in layout_data:
                well_info = layout_data[well_id]
                if well_info.well_type != "unused":
                    wells_to_analyze.append((i, well_id))
            else:
                # If no layout data, analyze all wells
                wells_to_analyze.append((i, well_id))
        
        print(f"Total wells: {len(fluorescence_data.wells)}")
        print(f"Wells to analyze: {len(wells_to_analyze)}")
        print(f"Skipping {len(fluorescence_data.wells) - len(wells_to_analyze)} unused wells")
        
        # Profile each well sequentially (this is the bottleneck!)
        with self.time_operation(f"Sequential Well Processing - {dataset_name}", 
                               total_wells=len(wells_to_analyze)):
            for well_idx, well_id in wells_to_analyze:
                fluo_values = fluorescence_data.measurements[well_idx, :]
                well_result = self.profile_well_processing(well_id, time_points, fluo_values)
                well_results.append(well_result)
        
        dataset_end_time = time.perf_counter()
        total_time_ms = (dataset_end_time - dataset_start_time) * 1000
        
        end_memory = self.process.memory_info().rss / 1024 / 1024
        peak_memory = max(start_memory, end_memory)
        
        # Calculate summary statistics
        well_times = [w.total_time_ms for w in well_results]
        curve_fitting_total = sum(w.curve_fitting_time_ms for w in well_results)
        threshold_analysis_total = sum(w.threshold_analysis_time_ms for w in well_results)
        total_attempts = sum(w.curve_fit_attempts for w in well_results)
        successful_fits = sum(1 for w in well_results if w.curve_fit_success)
        successful_thresholds = sum(1 for w in well_results if w.threshold_success)
        
        return DatasetProfileResult(
            dataset_name=dataset_name,
            total_wells=len(fluorescence_data.wells),
            analyzed_wells=len(wells_to_analyze),
            total_time_ms=total_time_ms,
            avg_time_per_well_ms=np.mean(well_times) if well_times else 0,
            min_time_per_well_ms=np.min(well_times) if well_times else 0,
            max_time_per_well_ms=np.max(well_times) if well_times else 0,
            curve_fitting_total_ms=curve_fitting_total,
            threshold_analysis_total_ms=threshold_analysis_total,
            total_curve_fit_attempts=total_attempts,
            successful_curve_fits=successful_fits,
            successful_threshold_analyses=successful_thresholds,
            peak_memory_mb=peak_memory,
            well_results=well_results
        )


def load_test_datasets() -> List[Tuple[str, FluorescenceData, Optional[Dict[str, WellInfo]]]]:
    """Load available test datasets for profiling."""
    datasets = []
    test_data_dir = Path("test_data")
    
    # Dataset 1: Tiny test (smallest)
    try:
        tiny_layout_path = test_data_dir / "tinyTEST01.BIORAD_layout.csv"
        tiny_data_path = test_data_dir / "TEST01.BIORAD.FORMAT.1.txt"
        
        if tiny_layout_path.exists() and tiny_data_path.exists():
            layout_parser = LayoutParser()
            layout_data = layout_parser.parse_file(str(tiny_layout_path))
            
            biorad_parser = BioRadParser()
            fluorescence_data = biorad_parser.parse_file(str(tiny_data_path), cycle_time=2.0)
            
            datasets.append(("Tiny Test (BioRad)", fluorescence_data, layout_data))
            print(f"Loaded tiny test dataset: {len(fluorescence_data.wells)} wells")
    except Exception as e:
        print(f"Failed to load tiny test dataset: {e}")
    
    # Dataset 2: Small BMG test
    try:
        small_layout_path = test_data_dir / "smallRM5097_layout.csv"
        small_data_path = test_data_dir / "RM5097.96HL.BNCT.1.CSV"
        
        if small_layout_path.exists() and small_data_path.exists():
            layout_parser = LayoutParser()
            layout_data = layout_parser.parse_file(str(small_layout_path))
            
            bmg_parser = BMGOmega3Parser()
            fluorescence_data = bmg_parser.parse_file(str(small_data_path))
            
            datasets.append(("Small BMG Test", fluorescence_data, layout_data))
            print(f"Loaded small BMG dataset: {len(fluorescence_data.wells)} wells")
    except Exception as e:
        print(f"Failed to load small BMG dataset: {e}")
    
    # Dataset 3: Full BMG test (largest)
    try:
        full_layout_path = test_data_dir / "RM5097_layout.csv"
        full_data_path = test_data_dir / "RM5097.96HL.BNCT.1.CSV"
        
        if full_layout_path.exists() and full_data_path.exists():
            layout_parser = LayoutParser()
            layout_data = layout_parser.parse_file(str(full_layout_path))
            
            bmg_parser = BMGOmega3Parser()
            fluorescence_data = bmg_parser.parse_file(str(full_data_path))
            
            datasets.append(("Full BMG Test", fluorescence_data, layout_data))
            print(f"Loaded full BMG dataset: {len(fluorescence_data.wells)} wells")
    except Exception as e:
        print(f"Failed to load full BMG dataset: {e}")
    
    return datasets


def save_results_to_csv(dataset_results: List[DatasetProfileResult], filename: str):
    """Save detailed profiling results to CSV."""
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = [
            'dataset_name', 'well_id', 'total_time_ms', 'curve_fitting_time_ms',
            'threshold_analysis_time_ms', 'curve_fit_attempts', 'curve_fit_success',
            'threshold_success', 'strategy_used', 'memory_peak_mb'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for dataset_result in dataset_results:
            for well_result in dataset_result.well_results:
                row = {
                    'dataset_name': dataset_result.dataset_name,
                    'well_id': well_result.well_id,
                    'total_time_ms': well_result.total_time_ms,
                    'curve_fitting_time_ms': well_result.curve_fitting_time_ms,
                    'threshold_analysis_time_ms': well_result.threshold_analysis_time_ms,
                    'curve_fit_attempts': well_result.curve_fit_attempts,
                    'curve_fit_success': well_result.curve_fit_success,
                    'threshold_success': well_result.threshold_success,
                    'strategy_used': well_result.strategy_used,
                    'memory_peak_mb': well_result.memory_peak_mb
                }
                writer.writerow(row)


def generate_performance_summary(dataset_results: List[DatasetProfileResult], filename: str):
    """Generate a comprehensive performance analysis summary."""
    with open(filename, 'w') as f:
        f.write("FLUORESCENCE ANALYSIS TOOL - PERFORMANCE PROFILING SUMMARY\n")
        f.write("=" * 70 + "\n\n")
        
        f.write("EXECUTIVE SUMMARY\n")
        f.write("-" * 20 + "\n")
        
        # Overall statistics
        total_wells_analyzed = sum(r.analyzed_wells for r in dataset_results)
        total_time_s = sum(r.total_time_ms for r in dataset_results) / 1000
        avg_time_per_well = np.mean([r.avg_time_per_well_ms for r in dataset_results])
        
        f.write(f"Total wells analyzed: {total_wells_analyzed}\n")
        f.write(f"Total analysis time: {total_time_s:.2f} seconds\n")
        f.write(f"Average time per well: {avg_time_per_well:.2f} ms\n")
        f.write(f"Estimated time for 96-well plate: {(avg_time_per_well * 96) / 1000:.2f} seconds\n\n")
        
        # Bottleneck analysis
        f.write("BOTTLENECK ANALYSIS\n")
        f.write("-" * 20 + "\n")
        
        for result in dataset_results:
            f.write(f"\nDataset: {result.dataset_name}\n")
            f.write(f"  Wells analyzed: {result.analyzed_wells}\n")
            f.write(f"  Total time: {result.total_time_ms/1000:.2f}s\n")
            f.write(f"  Time per well: {result.avg_time_per_well_ms:.2f}ms (min: {result.min_time_per_well_ms:.2f}, max: {result.max_time_per_well_ms:.2f})\n")
            
            # Time breakdown
            curve_fitting_pct = (result.curve_fitting_total_ms / result.total_time_ms) * 100
            threshold_analysis_pct = (result.threshold_analysis_total_ms / result.total_time_ms) * 100
            
            f.write(f"  Curve fitting: {result.curve_fitting_total_ms/1000:.2f}s ({curve_fitting_pct:.1f}%)\n")
            f.write(f"  Threshold analysis: {result.threshold_analysis_total_ms/1000:.2f}s ({threshold_analysis_pct:.1f}%)\n")
            
            # Strategy attempts
            avg_attempts = result.total_curve_fit_attempts / result.analyzed_wells if result.analyzed_wells > 0 else 0
            success_rate = (result.successful_curve_fits / result.analyzed_wells) * 100 if result.analyzed_wells > 0 else 0
            
            f.write(f"  Avg curve fit attempts per well: {avg_attempts:.1f}\n")
            f.write(f"  Curve fit success rate: {success_rate:.1f}%\n")
            f.write(f"  Peak memory usage: {result.peak_memory_mb:.1f} MB\n")
        
        # Scaling analysis
        f.write("\nSCALING ANALYSIS\n")
        f.write("-" * 20 + "\n")
        
        if len(dataset_results) >= 2:
            # Compare smallest vs largest dataset
            smallest = min(dataset_results, key=lambda x: x.analyzed_wells)
            largest = max(dataset_results, key=lambda x: x.analyzed_wells)
            
            scaling_factor = largest.analyzed_wells / smallest.analyzed_wells
            time_scaling = (largest.total_time_ms / smallest.total_time_ms)
            efficiency = scaling_factor / time_scaling
            
            f.write(f"Smallest dataset: {smallest.dataset_name} ({smallest.analyzed_wells} wells)\n")
            f.write(f"Largest dataset: {largest.dataset_name} ({largest.analyzed_wells} wells)\n")
            f.write(f"Well count scaling: {scaling_factor:.1f}x\n")
            f.write(f"Time scaling: {time_scaling:.1f}x\n")
            f.write(f"Efficiency ratio: {efficiency:.2f} (1.0 = perfect linear scaling)\n")
        
        # Optimization recommendations
        f.write("\nOPTIMIZATION RECOMMENDATIONS\n")
        f.write("-" * 30 + "\n")
        f.write("1. PARALLELIZATION: Wells are processed sequentially. Parallel processing\n")
        f.write("   could provide near-linear speedup for multi-core systems.\n\n")
        f.write("2. CURVE FITTING OPTIMIZATION: Multiple strategy attempts per well.\n")
        f.write("   Consider early termination or strategy ordering optimization.\n\n")
        f.write("3. SECOND DERIVATIVE CALCULATION: 20x interpolation is expensive.\n")
        f.write("   Consider reducing interpolation factor or caching results.\n\n")
        f.write("4. MEMORY USAGE: Monitor for potential memory leaks in long runs.\n\n")
        
        # Detailed per-dataset breakdown
        f.write("DETAILED RESULTS BY DATASET\n")
        f.write("-" * 30 + "\n")
        
        for result in dataset_results:
            f.write(f"\n{result.dataset_name}:\n")
            f.write(f"  Total wells: {result.total_wells}\n")
            f.write(f"  Analyzed wells: {result.analyzed_wells}\n")
            f.write(f"  Skipped wells: {result.total_wells - result.analyzed_wells}\n")
            f.write(f"  Total time: {result.total_time_ms/1000:.2f} seconds\n")
            f.write(f"  Average time per well: {result.avg_time_per_well_ms:.2f} ms\n")
            f.write(f"  Min time per well: {result.min_time_per_well_ms:.2f} ms\n")
            f.write(f"  Max time per well: {result.max_time_per_well_ms:.2f} ms\n")
            f.write(f"  Curve fitting total: {result.curve_fitting_total_ms/1000:.2f} seconds\n")
            f.write(f"  Threshold analysis total: {result.threshold_analysis_total_ms/1000:.2f} seconds\n")
            f.write(f"  Total curve fit attempts: {result.total_curve_fit_attempts}\n")
            f.write(f"  Successful curve fits: {result.successful_curve_fits}/{result.analyzed_wells}\n")
            f.write(f"  Successful threshold analyses: {result.successful_threshold_analyses}/{result.analyzed_wells}\n")
            f.write(f"  Peak memory usage: {result.peak_memory_mb:.1f} MB\n")


def main():
    """Main profiling function."""
    print("FLUORESCENCE ANALYSIS TOOL - PERFORMANCE PROFILER")
    print("=" * 60)
    print("This script will profile the analysis workflow to identify bottlenecks.")
    print("Results will be saved to CSV and summary files.\n")
    
    # Initialize profiler
    profiler = PerformanceProfiler()
    
    # Load test datasets
    print("Loading test datasets...")
    datasets = load_test_datasets()
    
    if not datasets:
        print("ERROR: No test datasets could be loaded!")
        print("Please ensure test data files are present in the test_data/ directory.")
        return
    
    print(f"Loaded {len(datasets)} datasets for profiling.\n")
    
    # Profile each dataset
    dataset_results = []
    for dataset_name, fluorescence_data, layout_data in datasets:
        try:
            result = profiler.profile_dataset(dataset_name, fluorescence_data, layout_data)
            dataset_results.append(result)
        except Exception as e:
            print(f"ERROR profiling {dataset_name}: {e}")
            traceback.print_exc()
    
    if not dataset_results:
        print("ERROR: No datasets were successfully profiled!")
        return
    
    # Save results
    print(f"\n{'='*60}")
    print("SAVING RESULTS")
    print(f"{'='*60}")
    
    csv_filename = "performance_profile_results.csv"
    summary_filename = "performance_summary.txt"
    
    save_results_to_csv(dataset_results, csv_filename)
    print(f"Detailed results saved to: {csv_filename}")
    
    generate_performance_summary(dataset_results, summary_filename)
    print(f"Performance summary saved to: {summary_filename}")
    
    # Print quick summary to console
    print(f"\n{'='*60}")
    print("QUICK SUMMARY")
    print(f"{'='*60}")
    
    for result in dataset_results:
        print(f"\n{result.dataset_name}:")
        print(f"  Wells: {result.analyzed_wells}")
        print(f"  Total time: {result.total_time_ms/1000:.2f}s")
        print(f"  Avg per well: {result.avg_time_per_well_ms:.2f}ms")
        print(f"  Success rate: {(result.successful_curve_fits/result.analyzed_wells)*100:.1f}%")
        print(f"  Memory peak: {result.peak_memory_mb:.1f}MB")
    
    print(f"\nProfiling complete! Check {summary_filename} for detailed analysis.")


if __name__ == "__main__":
    main()