"""
Tests for statistical analysis algorithms.

These tests validate the group-based statistical analysis functionality
that works with layout metadata and analysis results.
"""

import pytest
import numpy as np
from pathlib import Path

from fluorescence_tool.algorithms.statistical_analysis import (
    StatisticalAnalyzer, StatisticalResult, GroupStatistics
)
from fluorescence_tool.algorithms.curve_fitting import CurveFitResult
from fluorescence_tool.algorithms.threshold_analysis import ThresholdResult
from fluorescence_tool.core.models import WellInfo


class TestStatisticalAnalyzer:
    """Test the statistical analysis functionality."""
    
    def test_calculate_descriptive_statistics(self):
        """Test descriptive statistics calculation."""
        analyzer = StatisticalAnalyzer()
        
        # Test with normal data
        values = [10.0, 12.0, 11.0, 13.0, 9.0, 14.0, 10.5, 11.5]
        mean, std, cv, sem = analyzer.calculate_descriptive_statistics(values)
        
        expected_mean = np.mean(values)
        expected_std = np.std(values, ddof=1)
        expected_cv = (expected_std / expected_mean) * 100
        expected_sem = expected_std / np.sqrt(len(values))
        
        assert abs(mean - expected_mean) < 0.01
        assert abs(std - expected_std) < 0.01
        assert abs(cv - expected_cv) < 0.01
        assert abs(sem - expected_sem) < 0.01
    
    def test_calculate_descriptive_statistics_empty(self):
        """Test descriptive statistics with empty data."""
        analyzer = StatisticalAnalyzer()
        
        mean, std, cv, sem = analyzer.calculate_descriptive_statistics([])
        
        assert np.isnan(mean)
        assert np.isnan(std)
        assert np.isnan(cv)
        assert np.isnan(sem)
    
    def test_calculate_descriptive_statistics_with_nan(self):
        """Test descriptive statistics with NaN values."""
        analyzer = StatisticalAnalyzer()
        
        values = [10.0, np.nan, 12.0, 11.0, np.nan, 13.0]
        mean, std, cv, sem = analyzer.calculate_descriptive_statistics(values)
        
        # Should calculate stats on valid values only: [10.0, 12.0, 11.0, 13.0]
        valid_values = [10.0, 12.0, 11.0, 13.0]
        expected_mean = np.mean(valid_values)
        
        assert abs(mean - expected_mean) < 0.01
        assert not np.isnan(std)
    
    def test_group_wells_by_layout(self):
        """Test grouping wells by layout metadata."""
        analyzer = StatisticalAnalyzer()
        
        # Create test well info data
        wells = [
            WellInfo(well_id="A1", plate_id="plate1", sample="sample1", well_type="Control", cell_count=None, group_1=None, group_2=None, group_3=None),
            WellInfo(well_id="A2", plate_id="plate1", sample="sample2", well_type="Control", cell_count=None, group_1=None, group_2=None, group_3=None),
            WellInfo(well_id="B1", plate_id="plate1", sample="sample3", well_type="Treatment", cell_count=None, group_1=None, group_2=None, group_3=None),
            WellInfo(well_id="B2", plate_id="plate1", sample="sample4", well_type="Treatment", cell_count=None, group_1=None, group_2=None, group_3=None),
            WellInfo(well_id="C1", plate_id="plate1", sample="sample5", well_type="Control", cell_count=None, group_1=None, group_2=None, group_3=None),
            WellInfo(well_id="D1", plate_id="plate1", sample="sample6", well_type=None, cell_count=None, group_1=None, group_2=None, group_3=None)  # Unknown group
        ]
        
        groups = analyzer.group_wells_by_layout(wells)
        
        assert "Control" in groups
        assert "Treatment" in groups
        assert "Unknown" in groups
        
        assert len(groups["Control"]) == 3
        assert len(groups["Treatment"]) == 2
        assert len(groups["Unknown"]) == 1
        
        # Check well IDs are correct
        control_ids = [w.well_id for w in groups["Control"]]
        assert "A1" in control_ids
        assert "A2" in control_ids
        assert "C1" in control_ids
    
    def test_analyze_group_statistics(self):
        """Test statistical analysis for a group of wells."""
        analyzer = StatisticalAnalyzer()
        
        # Create test wells
        wells = [
            WellInfo(well_id="A1", plate_id="plate1", sample="sample1", well_type="Control", cell_count=None, group_1=None, group_2=None, group_3=None),
            WellInfo(well_id="A2", plate_id="plate1", sample="sample2", well_type="Control", cell_count=None, group_1=None, group_2=None, group_3=None),
            WellInfo(well_id="A3", plate_id="plate1", sample="sample3", well_type="Control", cell_count=None, group_1=None, group_2=None, group_3=None)
        ]
        
        # Create mock curve fitting results
        curve_results = {
            "A1": CurveFitResult(
                success=True,
                parameters=[100, 0.5, 10, 20, 0.1],
                r_squared=0.95,
                fluorescence_change=200.0,
                baseline_fluorescence=50.0,
                final_fluorescence=250.0
            ),
            "A2": CurveFitResult(
                success=True,
                parameters=[110, 0.6, 12, 25, 0.2],
                r_squared=0.92,
                fluorescence_change=180.0,
                baseline_fluorescence=60.0,
                final_fluorescence=240.0
            ),
            "A3": CurveFitResult(
                success=False,
                error_message="Fit failed"
            )
        }
        
        # Create mock threshold results
        threshold_results = {
            "A1": ThresholdResult(
                success=True,
                crossing_time=15.5,
                threshold_value=55.0
            ),
            "A2": ThresholdResult(
                success=True,
                crossing_time=17.2,
                threshold_value=66.0
            ),
            "A3": ThresholdResult(
                success=False,
                error_message="No crossing found"
            )
        }
        
        stats = analyzer.analyze_group_statistics(
            "Control", wells, curve_results, threshold_results)
        
        assert isinstance(stats, GroupStatistics)
        assert stats.group_name == "Control"
        assert stats.sample_count == 3
        assert stats.successful_fits == 2
        assert stats.success_rate == (2/3) * 100
        
        # Check crossing time statistics
        assert len(stats.crossing_times) == 2
        assert 15.5 in stats.crossing_times
        assert 17.2 in stats.crossing_times
        assert stats.crossing_time_mean is not None
        assert abs(stats.crossing_time_mean - np.mean([15.5, 17.2])) < 0.01
        
        # Check fluorescence change statistics
        assert len(stats.fluorescence_changes) == 2
        assert 200.0 in stats.fluorescence_changes
        assert 180.0 in stats.fluorescence_changes
        
        # Check curve parameter statistics
        assert len(stats.curve_parameters) == 2
        assert stats.parameter_means is not None
        assert len(stats.parameter_means) == 5  # 5-parameter sigmoid
        
        # Check R-squared statistics
        assert len(stats.r_squared_values) == 2
        assert stats.r_squared_mean is not None
    
    def test_analyze_group_statistics_no_successful_results(self):
        """Test group statistics when no wells have successful results."""
        analyzer = StatisticalAnalyzer()
        
        wells = [
            WellInfo(well_id="A1", plate_id="plate1", sample="sample1", well_type="Failed", cell_count=None, group_1=None, group_2=None, group_3=None)
        ]
        
        curve_results = {
            "A1": CurveFitResult(success=False, error_message="Fit failed")
        }
        
        threshold_results = {
            "A1": ThresholdResult(success=False, error_message="No crossing")
        }
        
        stats = analyzer.analyze_group_statistics(
            "Failed", wells, curve_results, threshold_results)
        
        assert stats.sample_count == 1
        assert stats.successful_fits == 0
        assert stats.success_rate == 0.0
        assert len(stats.crossing_times) == 0
        assert stats.crossing_time_mean is None
    
    def test_compare_groups_crossing_times(self):
        """Test statistical comparison between groups for crossing times."""
        analyzer = StatisticalAnalyzer()
        
        # Create group statistics with different crossing times
        group1_stats = GroupStatistics(
            group_name="Control",
            sample_count=5,
            crossing_times=[10.0, 11.0, 10.5, 11.5, 10.2]
        )
        
        group2_stats = GroupStatistics(
            group_name="Treatment", 
            sample_count=5,
            crossing_times=[15.0, 16.0, 15.5, 16.5, 15.2]
        )
        
        group_stats = {
            "Control": group1_stats,
            "Treatment": group2_stats
        }
        
        comparisons = analyzer.compare_groups(group_stats)
        
        assert "crossing_time_comparisons" in comparisons
        assert "Control_vs_Treatment" in comparisons["crossing_time_comparisons"]
        
        comparison = comparisons["crossing_time_comparisons"]["Control_vs_Treatment"]
        assert "p_value" in comparison
        assert "mean_difference" in comparison
        assert "significant" in comparison
        
        # Should show significant difference (Treatment > Control)
        assert comparison["mean_difference"] < 0  # Control - Treatment should be negative
        assert comparison["p_value"] < 0.05  # Should be significant
    
    def test_compare_groups_insufficient_data(self):
        """Test group comparison with insufficient groups."""
        analyzer = StatisticalAnalyzer()
        
        # Only one group
        group_stats = {
            "Control": GroupStatistics(
                group_name="Control",
                sample_count=3,
                crossing_times=[10.0, 11.0, 10.5]
            )
        }
        
        comparisons = analyzer.compare_groups(group_stats)
        
        # Should return empty comparisons
        assert len(comparisons) == 0
    
    def test_calculate_overall_statistics(self):
        """Test calculation of overall statistics across groups."""
        analyzer = StatisticalAnalyzer()
        
        group1_stats = GroupStatistics(
            group_name="Control",
            sample_count=3,
            crossing_times=[10.0, 11.0, 10.5],
            fluorescence_changes=[100.0, 110.0, 105.0],
            r_squared_values=[0.95, 0.92, 0.94],
            successful_fits=3
        )
        
        group2_stats = GroupStatistics(
            group_name="Treatment",
            sample_count=2,
            crossing_times=[15.0, 16.0],
            fluorescence_changes=[200.0, 210.0],
            r_squared_values=[0.90, 0.88],
            successful_fits=2
        )
        
        group_stats = {
            "Control": group1_stats,
            "Treatment": group2_stats
        }
        
        overall = analyzer.calculate_overall_statistics(group_stats)
        
        assert overall.group_name == "Overall"
        assert overall.sample_count == 5
        assert overall.successful_fits == 5
        assert overall.success_rate == 100.0
        
        # Check combined crossing times
        expected_crossing_times = [10.0, 11.0, 10.5, 15.0, 16.0]
        assert len(overall.crossing_times) == 5
        assert overall.crossing_time_mean == np.mean(expected_crossing_times)
        
        # Check combined fluorescence changes
        expected_fluor_changes = [100.0, 110.0, 105.0, 200.0, 210.0]
        assert len(overall.fluorescence_changes) == 5
        assert overall.fluor_change_mean == np.mean(expected_fluor_changes)
    
    def test_analyze_complete_dataset(self):
        """Test complete statistical analysis workflow."""
        analyzer = StatisticalAnalyzer()
        
        # Create test well info data
        wells = [
            WellInfo(well_id="A1", plate_id="plate1", sample="sample1", well_type="Control", cell_count=None, group_1=None, group_2=None, group_3=None),
            WellInfo(well_id="A2", plate_id="plate1", sample="sample2", well_type="Control", cell_count=None, group_1=None, group_2=None, group_3=None),
            WellInfo(well_id="B1", plate_id="plate1", sample="sample3", well_type="Treatment", cell_count=None, group_1=None, group_2=None, group_3=None),
            WellInfo(well_id="B2", plate_id="plate1", sample="sample4", well_type="Treatment", cell_count=None, group_1=None, group_2=None, group_3=None)
        ]
        
        # Create mock results
        curve_results = {
            "A1": CurveFitResult(
                success=True,
                parameters=[100, 0.5, 10, 20, 0.1],
                r_squared=0.95,
                fluorescence_change=200.0
            ),
            "A2": CurveFitResult(
                success=True,
                parameters=[110, 0.6, 12, 25, 0.2],
                r_squared=0.92,
                fluorescence_change=180.0
            ),
            "B1": CurveFitResult(
                success=True,
                parameters=[120, 0.4, 8, 15, 0.05],
                r_squared=0.88,
                fluorescence_change=300.0
            ),
            "B2": CurveFitResult(
                success=True,
                parameters=[115, 0.45, 9, 18, 0.08],
                r_squared=0.90,
                fluorescence_change=280.0
            )
        }
        
        threshold_results = {
            "A1": ThresholdResult(success=True, crossing_time=15.5),
            "A2": ThresholdResult(success=True, crossing_time=17.2),
            "B1": ThresholdResult(success=True, crossing_time=12.1),
            "B2": ThresholdResult(success=True, crossing_time=13.8)
        }
        
        result = analyzer.analyze_complete_dataset(
            wells, curve_results, threshold_results)
        
        assert isinstance(result, StatisticalResult)
        assert result.success is True
        
        # Check group statistics
        assert "Control" in result.group_statistics
        assert "Treatment" in result.group_statistics
        
        control_stats = result.group_statistics["Control"]
        treatment_stats = result.group_statistics["Treatment"]
        
        assert control_stats.sample_count == 2
        assert treatment_stats.sample_count == 2
        assert control_stats.successful_fits == 2
        assert treatment_stats.successful_fits == 2
        
        # Check overall statistics
        assert result.overall_statistics is not None
        assert result.overall_statistics.sample_count == 4
        assert result.overall_statistics.successful_fits == 4
        
        # Check group comparisons
        assert len(result.group_comparisons) > 0
    
    def test_generate_summary_report(self):
        """Test generation of summary report."""
        analyzer = StatisticalAnalyzer()
        
        # Create a simple result
        group_stats = {
            "Control": GroupStatistics(
                group_name="Control",
                sample_count=3,
                crossing_times=[10.0, 11.0, 10.5],
                successful_fits=3,
                success_rate=100.0
            )
        }
        
        overall_stats = GroupStatistics(
            group_name="Overall",
            sample_count=3,
            crossing_times=[10.0, 11.0, 10.5],
            successful_fits=3,
            success_rate=100.0
        )
        overall_stats.crossing_time_mean = 10.5
        overall_stats.crossing_time_std = 0.5
        overall_stats.crossing_time_cv = 4.8
        
        result = StatisticalResult(
            success=True,
            group_statistics=group_stats,
            overall_statistics=overall_stats
        )
        
        report = analyzer.generate_summary_report(result)
        
        assert isinstance(report, str)
        assert "FLUORESCENCE DATA STATISTICAL ANALYSIS REPORT" in report
        assert "OVERALL STATISTICS" in report
        assert "GROUP STATISTICS" in report
        assert "Total wells analyzed: 3" in report
        assert "Success rate: 100.0%" in report
        assert "Control" in report
    
    def test_generate_summary_report_failed(self):
        """Test summary report generation for failed analysis."""
        analyzer = StatisticalAnalyzer()
        
        result = StatisticalResult(
            success=False,
            error_message="Analysis failed due to invalid data"
        )
        
        report = analyzer.generate_summary_report(result)
        
        assert "Statistical analysis failed" in report
        assert "Analysis failed due to invalid data" in report
    
    def test_edge_case_single_well_group(self):
        """Test statistical analysis with single-well groups."""
        analyzer = StatisticalAnalyzer()
        
        wells = [WellInfo(well_id="A1", plate_id="plate1", sample="sample1", well_type="Single", cell_count=None, group_1=None, group_2=None, group_3=None)]
        
        curve_results = {
            "A1": CurveFitResult(
                success=True,
                parameters=[100, 0.5, 10, 20, 0.1],
                r_squared=0.95,
                fluorescence_change=200.0
            )
        }
        
        threshold_results = {
            "A1": ThresholdResult(success=True, crossing_time=15.5)
        }
        
        stats = analyzer.analyze_group_statistics(
            "Single", wells, curve_results, threshold_results)
        
        assert stats.sample_count == 1
        assert stats.successful_fits == 1
        assert stats.success_rate == 100.0
        assert len(stats.crossing_times) == 1
        assert stats.crossing_time_mean == 15.5
        assert stats.crossing_time_std == 0.0  # Single value has zero std
    
    def test_coefficient_of_variation_calculation(self):
        """Test coefficient of variation calculation."""
        analyzer = StatisticalAnalyzer()
        
        # Test with known CV
        values = [10.0, 12.0, 8.0]  # Mean = 10, Std ≈ 2, CV = 20%
        mean, std, cv, sem = analyzer.calculate_descriptive_statistics(values)
        
        expected_cv = (std / mean) * 100
        assert abs(cv - expected_cv) < 0.01
        
        # Test with zero mean (should return NaN)
        values_zero_mean = [-1.0, 0.0, 1.0]  # Mean = 0
        mean, std, cv, sem = analyzer.calculate_descriptive_statistics(values_zero_mean)
        assert np.isnan(cv)
    
    def test_integration_with_layout_metadata(self):
        """Test integration with layout metadata parsing."""
        analyzer = StatisticalAnalyzer()
        
        # Create wells with various metadata
        wells = [
            WellInfo(well_id="A1", plate_id="plate1", sample="sample1", well_type="Positive Control", cell_count=None, group_1=None, group_2=None, group_3=None),
            WellInfo(well_id="A2", plate_id="plate1", sample="sample2", well_type="Positive Control", cell_count=None, group_1=None, group_2=None, group_3=None),
            WellInfo(well_id="B1", plate_id="plate1", sample="sample3", well_type="Negative Control", cell_count=None, group_1=None, group_2=None, group_3=None),
            WellInfo(well_id="B2", plate_id="plate1", sample="sample4", well_type="Negative Control", cell_count=None, group_1=None, group_2=None, group_3=None),
            WellInfo(well_id="C1", plate_id="plate1", sample="sample5", well_type="Sample_1", cell_count=None, group_1=None, group_2=None, group_3=None),
            WellInfo(well_id="C2", plate_id="plate1", sample="sample6", well_type="Sample_1", cell_count=None, group_1=None, group_2=None, group_3=None),
            WellInfo(well_id="D1", plate_id="plate1", sample="sample7", well_type="Sample_2", cell_count=None, group_1=None, group_2=None, group_3=None)
        ]
        
        groups = analyzer.group_wells_by_layout(wells)
        
        assert "Positive Control" in groups
        assert "Negative Control" in groups
        assert "Sample_1" in groups
        assert "Sample_2" in groups
        
        assert len(groups["Positive Control"]) == 2
        assert len(groups["Negative Control"]) == 2
        assert len(groups["Sample_1"]) == 2
        assert len(groups["Sample_2"]) == 1