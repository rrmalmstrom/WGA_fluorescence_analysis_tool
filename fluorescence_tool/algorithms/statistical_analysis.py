"""
Statistical analysis algorithms for fluorescence data.

This module provides statistical analysis functionality for group-based
calculations using layout metadata, descriptive statistics, and quality metrics.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from scipy import stats
import warnings

from fluorescence_tool.core.models import WellInfo, FluorescenceData
from fluorescence_tool.algorithms.curve_fitting import CurveFitResult
from fluorescence_tool.algorithms.threshold_analysis import ThresholdResult


@dataclass
class GroupStatistics:
    """Statistical results for a group of wells."""
    group_name: str
    sample_count: int
    
    # Crossing time statistics
    crossing_times: List[float] = field(default_factory=list)
    crossing_time_mean: Optional[float] = None
    crossing_time_std: Optional[float] = None
    crossing_time_cv: Optional[float] = None
    crossing_time_sem: Optional[float] = None
    
    # Curve parameter statistics (5-parameter sigmoid: a, b, c, d, e)
    curve_parameters: List[List[float]] = field(default_factory=list)
    parameter_means: Optional[List[float]] = None
    parameter_stds: Optional[List[float]] = None
    parameter_cvs: Optional[List[float]] = None
    
    # Fluorescence change statistics
    fluorescence_changes: List[float] = field(default_factory=list)
    fluor_change_mean: Optional[float] = None
    fluor_change_std: Optional[float] = None
    fluor_change_cv: Optional[float] = None
    
    # Quality metrics
    r_squared_values: List[float] = field(default_factory=list)
    r_squared_mean: Optional[float] = None
    successful_fits: int = 0
    success_rate: Optional[float] = None


@dataclass
class StatisticalResult:
    """Result of statistical analysis operation."""
    success: bool
    group_statistics: Dict[str, GroupStatistics] = field(default_factory=dict)
    overall_statistics: Optional[GroupStatistics] = None
    error_message: Optional[str] = None
    
    # Comparative statistics between groups
    group_comparisons: Dict[str, Any] = field(default_factory=dict)


class StatisticalAnalyzer:
    """
    Statistical analysis for fluorescence data with group-based calculations.
    
    Provides descriptive statistics, quality metrics, and group comparisons
    using layout metadata to organize wells into experimental groups.
    """
    
    def __init__(self):
        """Initialize statistical analyzer."""
        pass
    
    def calculate_descriptive_statistics(self, values: List[float]) -> Tuple[float, float, float, float]:
        """
        Calculate descriptive statistics for a list of values.
        
        Args:
            values: List of numerical values
            
        Returns:
            Tuple of (mean, std, cv, sem)
        """
        if not values or len(values) == 0:
            return np.nan, np.nan, np.nan, np.nan
        
        values_array = np.array(values)
        # Remove NaN values
        valid_values = values_array[~np.isnan(values_array)]
        
        if len(valid_values) == 0:
            return np.nan, np.nan, np.nan, np.nan
        
        mean_val = np.mean(valid_values)
        std_val = np.std(valid_values, ddof=1) if len(valid_values) > 1 else 0.0
        cv_val = (std_val / mean_val * 100) if mean_val != 0 else np.nan
        sem_val = std_val / np.sqrt(len(valid_values)) if len(valid_values) > 0 else np.nan
        
        return mean_val, std_val, cv_val, sem_val
    
    def group_wells_by_layout(self, well_infos: List[WellInfo]) -> Dict[str, List[WellInfo]]:
        """
        Group wells by their sample type from layout metadata.
        
        Args:
            well_infos: List of well information objects
            
        Returns:
            Dictionary mapping group names to lists of wells
        """
        groups = {}
        
        for well in well_infos:
            group_name = well.well_type if well.well_type else "Unknown"
            
            if group_name not in groups:
                groups[group_name] = []
            
            groups[group_name].append(well)
        
        return groups
    
    def analyze_group_statistics(self, group_name: str, wells: List[WellInfo],
                                curve_results: Dict[str, CurveFitResult],
                                threshold_results: Dict[str, ThresholdResult]) -> GroupStatistics:
        """
        Calculate statistics for a group of wells.
        
        Args:
            group_name: Name of the experimental group
            wells: List of wells in the group
            curve_results: Dictionary mapping well IDs to curve fit results
            threshold_results: Dictionary mapping well IDs to threshold results
            
        Returns:
            GroupStatistics object with calculated statistics
        """
        stats_obj = GroupStatistics(group_name=group_name, sample_count=len(wells))
        
        # Collect data from successful analyses
        crossing_times = []
        curve_parameters = []
        fluorescence_changes = []
        r_squared_values = []
        successful_fits = 0
        
        for well in wells:
            well_id = well.well_id
            
            # Get curve fitting results
            if well_id in curve_results:
                curve_result = curve_results[well_id]
                if curve_result.success:
                    successful_fits += 1
                    
                    if curve_result.parameters:
                        curve_parameters.append(curve_result.parameters)
                    
                    if curve_result.r_squared is not None:
                        r_squared_values.append(curve_result.r_squared)
                    
                    if curve_result.fluorescence_change is not None:
                        fluorescence_changes.append(curve_result.fluorescence_change)
            
            # Get threshold results
            if well_id in threshold_results:
                threshold_result = threshold_results[well_id]
                if threshold_result.success and threshold_result.crossing_time is not None:
                    crossing_times.append(threshold_result.crossing_time)
        
        # Calculate crossing time statistics
        if crossing_times:
            stats_obj.crossing_times = crossing_times
            mean_ct, std_ct, cv_ct, sem_ct = self.calculate_descriptive_statistics(crossing_times)
            stats_obj.crossing_time_mean = mean_ct
            stats_obj.crossing_time_std = std_ct
            stats_obj.crossing_time_cv = cv_ct
            stats_obj.crossing_time_sem = sem_ct
        
        # Calculate curve parameter statistics
        if curve_parameters:
            stats_obj.curve_parameters = curve_parameters
            param_array = np.array(curve_parameters)
            
            # Calculate statistics for each parameter (a, b, c, d, e)
            param_means = []
            param_stds = []
            param_cvs = []
            
            for i in range(param_array.shape[1]):  # For each parameter
                param_values = param_array[:, i].tolist()
                mean_p, std_p, cv_p, _ = self.calculate_descriptive_statistics(param_values)
                param_means.append(mean_p)
                param_stds.append(std_p)
                param_cvs.append(cv_p)
            
            stats_obj.parameter_means = param_means
            stats_obj.parameter_stds = param_stds
            stats_obj.parameter_cvs = param_cvs
        
        # Calculate fluorescence change statistics
        if fluorescence_changes:
            stats_obj.fluorescence_changes = fluorescence_changes
            mean_fc, std_fc, cv_fc, _ = self.calculate_descriptive_statistics(fluorescence_changes)
            stats_obj.fluor_change_mean = mean_fc
            stats_obj.fluor_change_std = std_fc
            stats_obj.fluor_change_cv = cv_fc
        
        # Calculate quality metrics
        if r_squared_values:
            stats_obj.r_squared_values = r_squared_values
            stats_obj.r_squared_mean = np.mean(r_squared_values)
        
        stats_obj.successful_fits = successful_fits
        stats_obj.success_rate = (successful_fits / len(wells) * 100) if len(wells) > 0 else 0.0
        
        return stats_obj
    
    def compare_groups(self, group_stats: Dict[str, GroupStatistics]) -> Dict[str, Any]:
        """
        Perform statistical comparisons between groups.
        
        Args:
            group_stats: Dictionary of group statistics
            
        Returns:
            Dictionary with comparison results
        """
        comparisons = {}
        
        group_names = list(group_stats.keys())
        
        # Skip comparisons if less than 2 groups
        if len(group_names) < 2:
            return comparisons
        
        # Compare crossing times between groups
        crossing_time_data = {}
        for group_name, stats in group_stats.items():
            if stats.crossing_times:
                crossing_time_data[group_name] = stats.crossing_times
        
        if len(crossing_time_data) >= 2:
            comparisons['crossing_time_comparisons'] = self._compare_crossing_times(crossing_time_data)
        
        # Compare fluorescence changes between groups
        fluor_change_data = {}
        for group_name, stats in group_stats.items():
            if stats.fluorescence_changes:
                fluor_change_data[group_name] = stats.fluorescence_changes
        
        if len(fluor_change_data) >= 2:
            comparisons['fluorescence_change_comparisons'] = self._compare_fluorescence_changes(fluor_change_data)
        
        # Compare success rates
        success_rates = {}
        for group_name, stats in group_stats.items():
            if stats.success_rate is not None:
                success_rates[group_name] = stats.success_rate
        
        if len(success_rates) >= 2:
            comparisons['success_rate_comparison'] = success_rates
        
        return comparisons
    
    def _compare_crossing_times(self, crossing_time_data: Dict[str, List[float]]) -> Dict[str, Any]:
        """Compare crossing times between groups using statistical tests."""
        comparison_results = {}
        
        group_names = list(crossing_time_data.keys())
        
        # Perform pairwise comparisons
        for i in range(len(group_names)):
            for j in range(i + 1, len(group_names)):
                group1, group2 = group_names[i], group_names[j]
                data1, data2 = crossing_time_data[group1], crossing_time_data[group2]
                
                comparison_key = f"{group1}_vs_{group2}"
                
                try:
                    # Perform t-test
                    t_stat, p_value = stats.ttest_ind(data1, data2)
                    
                    # Calculate effect size (Cohen's d)
                    pooled_std = np.sqrt(((len(data1) - 1) * np.var(data1, ddof=1) + 
                                        (len(data2) - 1) * np.var(data2, ddof=1)) / 
                                       (len(data1) + len(data2) - 2))
                    cohens_d = (np.mean(data1) - np.mean(data2)) / pooled_std if pooled_std > 0 else 0
                    
                    comparison_results[comparison_key] = {
                        'group1_mean': np.mean(data1),
                        'group2_mean': np.mean(data2),
                        'mean_difference': np.mean(data1) - np.mean(data2),
                        't_statistic': t_stat,
                        'p_value': p_value,
                        'cohens_d': cohens_d,
                        'significant': p_value < 0.05
                    }
                
                except Exception as e:
                    comparison_results[comparison_key] = {
                        'error': f"Statistical comparison failed: {e}"
                    }
        
        return comparison_results
    
    def _compare_fluorescence_changes(self, fluor_change_data: Dict[str, List[float]]) -> Dict[str, Any]:
        """Compare fluorescence changes between groups using statistical tests."""
        comparison_results = {}
        
        group_names = list(fluor_change_data.keys())
        
        # Perform pairwise comparisons
        for i in range(len(group_names)):
            for j in range(i + 1, len(group_names)):
                group1, group2 = group_names[i], group_names[j]
                data1, data2 = fluor_change_data[group1], fluor_change_data[group2]
                
                comparison_key = f"{group1}_vs_{group2}"
                
                try:
                    # Perform t-test
                    t_stat, p_value = stats.ttest_ind(data1, data2)
                    
                    comparison_results[comparison_key] = {
                        'group1_mean': np.mean(data1),
                        'group2_mean': np.mean(data2),
                        'mean_difference': np.mean(data1) - np.mean(data2),
                        't_statistic': t_stat,
                        'p_value': p_value,
                        'significant': p_value < 0.05
                    }
                
                except Exception as e:
                    comparison_results[comparison_key] = {
                        'error': f"Statistical comparison failed: {e}"
                    }
        
        return comparison_results
    
    def calculate_overall_statistics(self, group_stats: Dict[str, GroupStatistics]) -> GroupStatistics:
        """
        Calculate overall statistics across all groups.
        
        Args:
            group_stats: Dictionary of group statistics
            
        Returns:
            GroupStatistics object with overall statistics
        """
        # Combine data from all groups
        all_crossing_times = []
        all_curve_parameters = []
        all_fluorescence_changes = []
        all_r_squared = []
        total_wells = 0
        total_successful = 0
        
        for stats in group_stats.values():
            all_crossing_times.extend(stats.crossing_times)
            all_curve_parameters.extend(stats.curve_parameters)
            all_fluorescence_changes.extend(stats.fluorescence_changes)
            all_r_squared.extend(stats.r_squared_values)
            total_wells += stats.sample_count
            total_successful += stats.successful_fits
        
        # Create overall statistics object
        overall_stats = GroupStatistics(group_name="Overall", sample_count=total_wells)
        
        # Calculate overall crossing time statistics
        if all_crossing_times:
            overall_stats.crossing_times = all_crossing_times
            mean_ct, std_ct, cv_ct, sem_ct = self.calculate_descriptive_statistics(all_crossing_times)
            overall_stats.crossing_time_mean = mean_ct
            overall_stats.crossing_time_std = std_ct
            overall_stats.crossing_time_cv = cv_ct
            overall_stats.crossing_time_sem = sem_ct
        
        # Calculate overall fluorescence change statistics
        if all_fluorescence_changes:
            overall_stats.fluorescence_changes = all_fluorescence_changes
            mean_fc, std_fc, cv_fc, _ = self.calculate_descriptive_statistics(all_fluorescence_changes)
            overall_stats.fluor_change_mean = mean_fc
            overall_stats.fluor_change_std = std_fc
            overall_stats.fluor_change_cv = cv_fc
        
        # Calculate overall quality metrics
        if all_r_squared:
            overall_stats.r_squared_values = all_r_squared
            overall_stats.r_squared_mean = np.mean(all_r_squared)
        
        overall_stats.successful_fits = total_successful
        overall_stats.success_rate = (total_successful / total_wells * 100) if total_wells > 0 else 0.0
        
        return overall_stats
    
    def analyze_complete_dataset(self, well_infos: List[WellInfo],
                                curve_results: Dict[str, CurveFitResult],
                                threshold_results: Dict[str, ThresholdResult]) -> StatisticalResult:
        """
        Perform complete statistical analysis on the dataset.
        
        Args:
            well_infos: List of well information objects
            curve_results: Dictionary mapping well IDs to curve fit results
            threshold_results: Dictionary mapping well IDs to threshold results
            
        Returns:
            StatisticalResult with comprehensive analysis
        """
        try:
            # Group wells by layout metadata
            well_groups = self.group_wells_by_layout(well_infos)
            
            # Calculate statistics for each group
            group_statistics = {}
            for group_name, wells in well_groups.items():
                group_stats = self.analyze_group_statistics(
                    group_name, wells, curve_results, threshold_results)
                group_statistics[group_name] = group_stats
            
            # Calculate overall statistics
            overall_stats = self.calculate_overall_statistics(group_statistics)
            
            # Perform group comparisons
            comparisons = self.compare_groups(group_statistics)
            
            return StatisticalResult(
                success=True,
                group_statistics=group_statistics,
                overall_statistics=overall_stats,
                group_comparisons=comparisons
            )
        
        except Exception as e:
            return StatisticalResult(
                success=False,
                error_message=f"Error in statistical analysis: {e}"
            )
    
    def generate_summary_report(self, result: StatisticalResult) -> str:
        """
        Generate a text summary report of the statistical analysis.
        
        Args:
            result: StatisticalResult object
            
        Returns:
            Formatted text report
        """
        if not result.success:
            return f"Statistical analysis failed: {result.error_message}"
        
        report_lines = []
        report_lines.append("FLUORESCENCE DATA STATISTICAL ANALYSIS REPORT")
        report_lines.append("=" * 50)
        report_lines.append("")
        
        # Overall statistics
        if result.overall_statistics:
            overall = result.overall_statistics
            report_lines.append("OVERALL STATISTICS")
            report_lines.append("-" * 20)
            report_lines.append(f"Total wells analyzed: {overall.sample_count}")
            report_lines.append(f"Successful curve fits: {overall.successful_fits}")
            report_lines.append(f"Success rate: {overall.success_rate:.1f}%")
            
            if overall.crossing_time_mean is not None:
                report_lines.append(f"Mean crossing time: {overall.crossing_time_mean:.2f} ± {overall.crossing_time_std:.2f}")
                report_lines.append(f"Crossing time CV: {overall.crossing_time_cv:.1f}%")
            
            if overall.fluor_change_mean is not None:
                report_lines.append(f"Mean fluorescence change: {overall.fluor_change_mean:.1f} ± {overall.fluor_change_std:.1f}")
                report_lines.append(f"Fluorescence change CV: {overall.fluor_change_cv:.1f}%")
            
            if overall.r_squared_mean is not None:
                report_lines.append(f"Mean R-squared: {overall.r_squared_mean:.3f}")
            
            report_lines.append("")
        
        # Group statistics
        report_lines.append("GROUP STATISTICS")
        report_lines.append("-" * 20)
        
        for group_name, stats in result.group_statistics.items():
            report_lines.append(f"\nGroup: {group_name}")
            report_lines.append(f"  Sample count: {stats.sample_count}")
            report_lines.append(f"  Success rate: {stats.success_rate:.1f}%")
            
            if stats.crossing_time_mean is not None:
                report_lines.append(f"  Crossing time: {stats.crossing_time_mean:.2f} ± {stats.crossing_time_std:.2f} (CV: {stats.crossing_time_cv:.1f}%)")
            
            if stats.fluor_change_mean is not None:
                report_lines.append(f"  Fluorescence change: {stats.fluor_change_mean:.1f} ± {stats.fluor_change_std:.1f} (CV: {stats.fluor_change_cv:.1f}%)")
            
            if stats.r_squared_mean is not None:
                report_lines.append(f"  Mean R-squared: {stats.r_squared_mean:.3f}")
        
        # Group comparisons
        if result.group_comparisons:
            report_lines.append("\n\nGROUP COMPARISONS")
            report_lines.append("-" * 20)
            
            if 'crossing_time_comparisons' in result.group_comparisons:
                report_lines.append("\nCrossing Time Comparisons:")
                for comparison, data in result.group_comparisons['crossing_time_comparisons'].items():
                    if 'error' not in data:
                        significance = "***" if data['p_value'] < 0.001 else "**" if data['p_value'] < 0.01 else "*" if data['p_value'] < 0.05 else "ns"
                        report_lines.append(f"  {comparison}: p = {data['p_value']:.4f} {significance}")
                        report_lines.append(f"    Mean difference: {data['mean_difference']:.2f}")
        
        return "\n".join(report_lines)