"""
Tests for curve fitting algorithms based on analyze_fluorescence_data.py.

These tests validate the 5-parameter sigmoid curve fitting functionality
that has been proven to work with real fluorescence data.
"""

import pytest
import numpy as np
from pathlib import Path

from fluorescence_tool.algorithms.curve_fitting import CurveFitter, CurveFitResult
from fluorescence_tool.parsers.bmg_parser import BMGOmega3Parser
from fluorescence_tool.parsers.biorad_parser import BioRadParser


class TestCurveFitter:
    """Test the curve fitting algorithm based on proven implementation."""
    
    def test_sigmoid_5param_function(self):
        """Test the 5-parameter sigmoid function matches analyze_fluorescence_data.py."""
        fitter = CurveFitter()
        
        # Test with known parameters
        x = np.array([0, 1, 2, 3, 4, 5])
        a, b, c, d, e = 100, 1.0, 2.5, 10, 0.1
        
        # Calculate expected values using the proven formula
        expected = a / (1 + np.exp(-b * (x - c))) + d + e * x
        
        result = fitter.sigmoid_5param(x, a, b, c, d, e)
        
        np.testing.assert_array_almost_equal(result, expected, decimal=10)
    
    def test_sigmoid_overflow_protection(self):
        """Test overflow protection in sigmoid function."""
        fitter = CurveFitter()
        
        # Test with extreme parameters that could cause overflow
        x = np.array([0, 1, 2, 3, 4, 5])
        a, b, c, d, e = 100, 50.0, 2.5, 10, 0.1  # Very large b value
        
        result = fitter.sigmoid_5param(x, a, b, c, d, e)
        
        # Should not contain NaN or inf values
        assert np.all(np.isfinite(result))
    
    def test_calculate_threshold_baseline_method(self):
        """Test threshold calculation using baseline percentage method."""
        fitter = CurveFitter()
        
        # Test data similar to real fluorescence data
        fluo_values = np.array([100, 105, 102, 108, 120, 150, 200, 300, 400])
        
        # Should calculate threshold as 10% above average of time points 2-4 (indices 1-3)
        expected_avg = np.mean(fluo_values[1:4])  # [105, 102, 108]
        expected_threshold = expected_avg * 1.10
        
        threshold = fitter.calculate_threshold(fluo_values)
        
        assert abs(threshold - expected_threshold) < 0.01
    
    def test_fit_curve_with_real_data_structure(self):
        """Test curve fitting with data structure similar to real fluorescence data."""
        fitter = CurveFitter()
        
        # Simulate realistic fluorescence time series
        time_points = np.arange(0, 40, 1)  # 40 time points
        
        # Create synthetic sigmoid curve with noise
        true_params = [300, 0.3, 20, 50, 0.5]  # a, b, c, d, e
        true_curve = fitter.sigmoid_5param(time_points, *true_params)
        noise = np.random.normal(0, 5, len(time_points))
        fluo_values = true_curve + noise
        
        result = fitter.fit_curve(time_points, fluo_values)
        
        assert isinstance(result, CurveFitResult)
        assert result.success is True
        assert result.parameters is not None
        assert len(result.parameters) == 5
        assert result.r_squared > 0.9  # Should be a good fit
        
        # Test fluorescence change metrics are calculated
        assert result.baseline_fluorescence is not None
        assert result.final_fluorescence is not None
        assert result.fluorescence_change is not None
        assert result.percent_change is not None
    
    def test_fluorescence_change_calculation(self):
        """Test fluorescence change calculation from baseline to final."""
        fitter = CurveFitter()
        
        # Test with known values
        fluo_values = np.array([100, 105, 102, 120, 150, 200, 300, 400, 450, 480, 490, 500])
        
        baseline, final, change, percent = fitter.calculate_fluorescence_change(fluo_values)
        
        # Baseline should be average of first 3 values: (100 + 105 + 102) / 3 = 102.33
        expected_baseline = np.mean([100, 105, 102])
        assert abs(baseline - expected_baseline) < 0.01
        
        # Final should be average of last 3 values: (480 + 490 + 500) / 3 = 490
        expected_final = np.mean([480, 490, 500])
        assert abs(final - expected_final) < 0.01
        
        # Change should be final - baseline
        expected_change = expected_final - expected_baseline
        assert abs(change - expected_change) < 0.01
        
        # Percent change should be (change / baseline) * 100
        expected_percent = (expected_change / expected_baseline) * 100
        assert abs(percent - expected_percent) < 0.01
    
    def test_fit_curve_multiple_strategies(self):
        """Test that multiple fitting strategies are attempted as in analyze_fluorescence_data.py."""
        fitter = CurveFitter()
        
        # Create challenging data that might need multiple strategies
        time_points = np.arange(0, 30, 1)
        # Steep curve that might be difficult to fit
        true_params = [500, -2.0, 15, 20, 0.1]
        fluo_values = fitter.sigmoid_5param(time_points, *true_params)
        
        result = fitter.fit_curve(time_points, fluo_values)
        
        assert isinstance(result, CurveFitResult)
        # Should succeed with one of the strategies
        assert result.success is True
        assert result.strategy_used is not None
    
    def test_fit_curve_insufficient_variation(self):
        """Test handling of data with insufficient variation."""
        fitter = CurveFitter()
        
        time_points = np.arange(0, 20, 1)
        fluo_values = np.full(20, 100.0)  # Flat line, no variation
        
        result = fitter.fit_curve(time_points, fluo_values)
        
        assert isinstance(result, CurveFitResult)
        assert result.success is False
        assert "insufficient variation" in result.error_message.lower()
    
    def test_find_crossing_time_interpolation(self):
        """Test crossing time calculation with linear interpolation."""
        fitter = CurveFitter()
        
        time_points = np.array([0, 1, 2, 3, 4, 5])
        fitted_values = np.array([50, 80, 120, 180, 250, 300])
        threshold = 150
        
        crossing_time = fitter.find_crossing_time(time_points, fitted_values, threshold)
        
        # Should interpolate between points where crossing occurs
        assert crossing_time is not None
        assert 2 < crossing_time < 3  # Between time points 2 and 3
    
    def test_find_crossing_time_no_crossing(self):
        """Test handling when no crossing is found."""
        fitter = CurveFitter()
        
        time_points = np.array([0, 1, 2, 3, 4, 5])
        fitted_values = np.array([50, 60, 70, 80, 90, 100])  # Never crosses threshold
        threshold = 150
        
        crossing_time = fitter.find_crossing_time(time_points, fitted_values, threshold)
        
        assert crossing_time is None
    
    @pytest.mark.integration
    def test_with_real_bmg_data(self):
        """Test curve fitting with real BMG data file."""
        test_data_dir = Path(__file__).parent.parent.parent.parent / "test_data"
        bmg_file = test_data_dir / "RM5097.96HL.BNCT.1.CSV"
        
        if not bmg_file.exists():
            pytest.skip("Real BMG test data not available")
        
        parser = BMGOmega3Parser()
        data = parser.parse_file(str(bmg_file))
        
        fitter = CurveFitter()
        
        # data.wells is a list of well ID strings; data.measurements is a 2D numpy array
        assert len(data.wells) > 0, "No wells found in BMG data"
        assert len(data.time_points) > 10, "Insufficient time points in BMG data"
        
        time_points = np.array(data.time_points)
        
        # Test fitting on the first well
        fluo_values = data.measurements[0, :]
        result = fitter.fit_curve(time_points, fluo_values)
        
        # Should be able to process real data and return a CurveFitResult
        assert isinstance(result, CurveFitResult)
    
    @pytest.mark.integration
    def test_with_real_biorad_data(self):
        """Test curve fitting with real BioRad data file."""
        test_data_dir = Path(__file__).parent.parent.parent.parent / "test_data"
        biorad_file = test_data_dir / "TEST01.BIORAD.FORMAT.1.txt"
        
        if not biorad_file.exists():
            pytest.skip("Real BioRad test data not available")
        
        parser = BioRadParser()
        data = parser.parse_file(str(biorad_file), cycle_time_minutes=1.0)
        
        fitter = CurveFitter()
        
        # data.wells is a list of well ID strings; data.measurements is a 2D numpy array
        assert len(data.wells) > 0, "No wells found in BioRad data"
        assert len(data.time_points) > 10, "Insufficient time points in BioRad data"
        
        time_points = np.array(data.time_points)
        
        # Test fitting on the first well
        fluo_values = data.measurements[0, :]
        result = fitter.fit_curve(time_points, fluo_values)
        
        # Should be able to process real data and return a CurveFitResult
        assert isinstance(result, CurveFitResult)
    
    def test_timeout_protection(self):
        """Test that curve fitting has timeout protection."""
        fitter = CurveFitter()
        
        # Create data that might cause fitting to hang
        time_points = np.arange(0, 100, 1)
        fluo_values = np.random.random(100) * 1000  # Random noisy data
        
        result = fitter.fit_curve(time_points, fluo_values)
        
        # Should complete within reasonable time and not hang
        assert isinstance(result, CurveFitResult)
    
    def test_r_squared_calculation(self):
        """Test R-squared calculation for fit quality assessment."""
        fitter = CurveFitter()
        
        # Perfect fit case
        time_points = np.arange(0, 20, 1)
        true_params = [200, 0.5, 10, 30, 0.1]
        fluo_values = fitter.sigmoid_5param(time_points, *true_params)
        
        result = fitter.fit_curve(time_points, fluo_values)
        
        assert result.success is True
        assert result.r_squared > 0.99  # Should be near perfect fit
        
        # Poor fit case with noise
        noisy_values = fluo_values + np.random.normal(0, 50, len(fluo_values))
        result_noisy = fitter.fit_curve(time_points, noisy_values)
        
        if result_noisy.success:
            assert result_noisy.r_squared < result.r_squared  # Should be lower quality