"""
Tests for threshold analysis algorithms based on analyze_fluorescence_data.py.

These tests validate the threshold detection and crossing point analysis
functionality that has been proven to work with real fluorescence data.
"""

import pytest
import numpy as np
from pathlib import Path

from fluorescence_tool.algorithms.threshold_analysis import ThresholdAnalyzer, ThresholdResult


class TestThresholdAnalyzer:
    """Test the threshold analysis algorithm based on proven implementation."""
    
    def test_calculate_baseline_threshold_default(self):
        """Test baseline threshold calculation with default parameters."""
        analyzer = ThresholdAnalyzer(baseline_percentage=0.10)
        
        # Test data similar to real fluorescence data
        fluo_values = np.array([100, 105, 102, 108, 120, 150, 200, 300, 400])
        
        threshold, baseline = analyzer.calculate_baseline_threshold(fluo_values)
        
        # Should use points 1-3 (indices 1:4) as baseline: [105, 102, 108]
        expected_baseline = np.mean([105, 102, 108])
        expected_threshold = expected_baseline * 1.10
        
        assert abs(baseline - expected_baseline) < 0.01
        assert abs(threshold - expected_threshold) < 0.01
    
    def test_calculate_baseline_threshold_custom_points(self):
        """Test baseline threshold calculation with custom baseline points."""
        analyzer = ThresholdAnalyzer(baseline_percentage=0.15)
        
        fluo_values = np.array([100, 105, 102, 108, 120, 150, 200, 300, 400])
        custom_points = [0, 1, 2]  # First three points
        
        threshold, baseline = analyzer.calculate_baseline_threshold(fluo_values, custom_points)
        
        expected_baseline = np.mean([100, 105, 102])
        expected_threshold = expected_baseline * 1.15
        
        assert abs(baseline - expected_baseline) < 0.01
        assert abs(threshold - expected_threshold) < 0.01
    
    def test_calculate_baseline_threshold_invalid_points(self):
        """Test baseline threshold calculation with invalid baseline points."""
        analyzer = ThresholdAnalyzer()
        
        fluo_values = np.array([100, 105, 102])
        invalid_points = [5, 6, 7]  # Points outside array bounds
        
        with pytest.raises(ValueError, match="No valid baseline points"):
            analyzer.calculate_baseline_threshold(fluo_values, invalid_points)
    
    def test_find_crossing_point_linear_interpolation(self):
        """Test crossing point detection with linear interpolation."""
        analyzer = ThresholdAnalyzer()
        
        # Create data with known crossing point
        time_points = np.array([0, 1, 2, 3, 4, 5])
        fluo_values = np.array([50, 80, 120, 180, 250, 300])
        threshold = 150
        
        crossing_time = analyzer.find_crossing_point_linear_interpolation(
            time_points, fluo_values, threshold)
        
        # Should interpolate between points 2 and 3 (120 and 180)
        # Linear interpolation: t = 2 + (150-120)/(180-120) * (3-2) = 2.5
        expected_crossing = 2.5
        
        assert crossing_time is not None
        assert abs(crossing_time - expected_crossing) < 0.01
    
    def test_find_crossing_point_no_crossing(self):
        """Test crossing point detection when no crossing occurs."""
        analyzer = ThresholdAnalyzer()
        
        time_points = np.array([0, 1, 2, 3, 4, 5])
        fluo_values = np.array([50, 60, 70, 80, 90, 100])  # Never crosses threshold
        threshold = 150
        
        crossing_time = analyzer.find_crossing_point_linear_interpolation(
            time_points, fluo_values, threshold)
        
        assert crossing_time is None
    
    def test_find_crossing_point_exact_crossing(self):
        """Test crossing point detection when data exactly hits threshold."""
        analyzer = ThresholdAnalyzer()
        
        time_points = np.array([0, 1, 2, 3, 4, 5])
        fluo_values = np.array([50, 80, 150, 180, 250, 300])  # Exactly hits threshold at t=2
        threshold = 150
        
        crossing_time = analyzer.find_crossing_point_linear_interpolation(
            time_points, fluo_values, threshold)
        
        # Should find crossing between points 1 and 2
        assert crossing_time is not None
        assert 1 < crossing_time <= 2
    
    def test_find_crossing_point_spline_interpolation(self):
        """Test crossing point detection with spline interpolation."""
        analyzer = ThresholdAnalyzer()
        
        # Create smooth sigmoid-like data
        time_points = np.linspace(0, 10, 21)
        fluo_values = 100 + 200 / (1 + np.exp(-0.5 * (time_points - 5)))
        threshold = 200
        
        crossing_time = analyzer.find_crossing_point_spline_interpolation(
            time_points, fluo_values, threshold)
        
        assert crossing_time is not None
        assert 4 < crossing_time < 6  # Should be around the inflection point
    
    def test_detect_multiple_crossings(self):
        """Test detection of multiple threshold crossings."""
        analyzer = ThresholdAnalyzer()
        
        # Create data with multiple crossings (oscillating around threshold)
        time_points = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        fluo_values = np.array([50, 120, 80, 160, 90, 170, 100, 180, 110, 190])
        threshold = 150
        
        crossings = analyzer.detect_multiple_crossings(time_points, fluo_values, threshold)
        
        # Should detect crossings around t=3, t=5, t=7
        assert len(crossings) >= 2
        assert all(isinstance(c, float) for c in crossings)
    
    def test_analyze_threshold_crossing_complete(self):
        """Test complete threshold crossing analysis."""
        analyzer = ThresholdAnalyzer(baseline_percentage=0.10)
        
        # Create realistic fluorescence time series
        time_points = np.arange(0, 20, 1)
        # Sigmoid curve: low baseline, then rapid increase
        fluo_values = 100 + 300 / (1 + np.exp(-0.3 * (time_points - 10)))
        
        result = analyzer.analyze_threshold_crossing(time_points, fluo_values, method="linear")
        
        assert isinstance(result, ThresholdResult)
        assert result.success is True
        assert result.threshold_value is not None
        assert result.crossing_time is not None
        assert result.crossing_method == "linear"
        assert result.baseline_value is not None
        assert result.baseline_points == [1, 2, 3]
    
    def test_analyze_threshold_crossing_with_custom_threshold(self):
        """Test threshold crossing analysis with custom threshold."""
        analyzer = ThresholdAnalyzer()
        
        time_points = np.array([0, 1, 2, 3, 4, 5])
        fluo_values = np.array([50, 80, 120, 180, 250, 300])
        custom_threshold = 150
        
        result = analyzer.analyze_threshold_crossing(
            time_points, fluo_values, threshold=custom_threshold, method="linear")
        
        assert result.success is True
        assert result.threshold_value == custom_threshold
        assert result.crossing_time is not None
        assert result.baseline_value is None  # Not calculated when threshold provided
    
    def test_analyze_threshold_crossing_spline_method(self):
        """Test threshold crossing analysis with spline interpolation."""
        analyzer = ThresholdAnalyzer()
        
        time_points = np.linspace(0, 10, 21)
        fluo_values = 100 + 200 / (1 + np.exp(-0.5 * (time_points - 5)))
        
        result = analyzer.analyze_threshold_crossing(time_points, fluo_values, method="spline")
        
        assert result.success is True
        assert result.crossing_method == "spline"
        assert result.crossing_time is not None
    
    def test_analyze_threshold_crossing_no_crossing(self):
        """Test threshold crossing analysis when no crossing occurs."""
        analyzer = ThresholdAnalyzer()
        
        time_points = np.array([0, 1, 2, 3, 4, 5])
        fluo_values = np.array([50, 50, 50, 50, 50, 50])  # Completely flat signal
        
        result = analyzer.analyze_threshold_crossing(time_points, fluo_values)
        
        assert result.success is False
        assert result.crossing_time is None
        assert "No threshold crossing found" in result.error_message
    
    def test_analyze_threshold_crossing_invalid_method(self):
        """Test threshold crossing analysis with invalid method."""
        analyzer = ThresholdAnalyzer()
        
        time_points = np.array([0, 1, 2, 3, 4, 5])
        fluo_values = np.array([50, 80, 120, 180, 250, 300])
        
        result = analyzer.analyze_threshold_crossing(
            time_points, fluo_values, method="invalid_method")
        
        assert result.success is False
        assert "Unknown interpolation method" in result.error_message
    
    def test_calculate_confidence_interval(self):
        """Test confidence interval calculation for crossing time."""
        analyzer = ThresholdAnalyzer()
        
        # Create data with some noise
        time_points = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        base_values = np.array([50, 80, 120, 180, 250, 300, 350, 400, 450, 500])
        noise = np.random.normal(0, 5, len(base_values))
        fluo_values = base_values + noise
        
        crossing_time = 2.5
        threshold = 150
        
        ci = analyzer.calculate_confidence_interval(
            time_points, fluo_values, crossing_time, threshold)
        
        if ci is not None:
            lower, upper = ci
            assert lower < crossing_time < upper
            assert upper - lower > 0  # Should have some width
    
    def test_validate_crossing_quality(self):
        """Test crossing quality validation."""
        analyzer = ThresholdAnalyzer()
        
        time_points = np.array([0, 1, 2, 3, 4, 5])
        fluo_values = np.array([50, 80, 120, 180, 250, 300])
        crossing_time = 2.5
        threshold = 150
        
        quality = analyzer.validate_crossing_quality(
            time_points, fluo_values, crossing_time, threshold)
        
        assert quality["valid"] is True
        assert "signal_to_noise_ratio" in quality
        assert "slope_at_crossing" in quality
        assert quality["slope_at_crossing"] > 0  # Should be positive slope
    
    def test_validate_crossing_quality_invalid(self):
        """Test crossing quality validation for invalid crossing."""
        analyzer = ThresholdAnalyzer()
        
        time_points = np.array([0, 1, 2, 3, 4, 5])
        fluo_values = np.array([50, 80, 120, 180, 250, 300])
        crossing_time = 10  # Outside time range
        threshold = 150
        
        quality = analyzer.validate_crossing_quality(
            time_points, fluo_values, crossing_time, threshold)
        
        assert quality["valid"] is False
        assert "outside time range" in quality["reason"].lower()
    
    def test_edge_case_single_point(self):
        """Test edge case with single data point."""
        analyzer = ThresholdAnalyzer()
        
        time_points = np.array([0])
        fluo_values = np.array([100])
        
        result = analyzer.analyze_threshold_crossing(time_points, fluo_values)
        
        # Should handle gracefully
        assert isinstance(result, ThresholdResult)
    
    def test_edge_case_identical_values(self):
        """Test edge case with identical fluorescence values."""
        analyzer = ThresholdAnalyzer()
        
        time_points = np.array([0, 1, 2, 3, 4, 5])
        fluo_values = np.array([100, 100, 100, 100, 100, 100])  # All identical
        threshold = 150
        
        crossing_time = analyzer.find_crossing_point_linear_interpolation(
            time_points, fluo_values, threshold)
        
        assert crossing_time is None  # No crossing possible
    
    def test_baseline_percentage_variations(self):
        """Test different baseline percentage values."""
        fluo_values = np.array([100, 105, 102, 108, 120, 150, 200, 300, 400])
        
        # Test different percentages
        for percentage in [0.05, 0.10, 0.15, 0.20]:
            analyzer = ThresholdAnalyzer(baseline_percentage=percentage)
            threshold, baseline = analyzer.calculate_baseline_threshold(fluo_values)
            
            expected_baseline = np.mean([105, 102, 108])
            expected_threshold = expected_baseline * (1.0 + percentage)
            
            assert abs(threshold - expected_threshold) < 0.01
    
    def test_integration_with_curve_fitting_data(self):
        """Test threshold analysis with data structure from curve fitting."""
        analyzer = ThresholdAnalyzer()
        
        # Simulate data that would come from curve fitting
        time_points = np.arange(0, 30, 1)
        # Sigmoid curve similar to what curve fitting would produce
        fluo_values = 50 + 200 / (1 + np.exp(-0.2 * (time_points - 15)))
        
        result = analyzer.analyze_threshold_crossing(time_points, fluo_values)
        
        assert result.success is True
        assert result.crossing_time is not None
        assert 10 < result.crossing_time < 20  # Should be around inflection point
        
        # Test that confidence interval is reasonable
        if result.confidence_interval:
            lower, upper = result.confidence_interval
            assert lower < result.crossing_time < upper