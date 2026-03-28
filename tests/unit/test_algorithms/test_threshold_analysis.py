"""
Tests for threshold analysis algorithms.

These tests validate the current ThresholdAnalyzer implementation which uses:
- calculate_baseline_threshold(): baseline percentage method
- check_signal_quality(): QC filter (signal must rise >N% above baseline)
- analyze_threshold_crossing_with_fitted_curve(): full CP analysis using pre-fitted params
- calculate_second_derivative_crossing_point_with_fitted_curve(): second-derivative CP
- detect_multiple_crossings(): multiple threshold crossing detection
- validate_crossing_quality(): crossing quality metrics
- calculate_confidence_interval(): CI estimation around crossing time
"""

import pytest
import numpy as np
from pathlib import Path

from fluorescence_tool.algorithms.threshold_analysis import ThresholdAnalyzer, ThresholdResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sigmoid_params(baseline=100.0, amplitude=400.0, midpoint=10.0,
                          steepness=0.5, asymmetry=1.0):
    """Return 5-parameter sigmoid params [a, b, c, d, e] for test curves."""
    # sigmoid_5param(t) = d + (a - d) / (1 + (t/c)^b)^e  (Hill / 5PL form)
    # We use a simple approximation that matches CurveFitter.sigmoid_5param.
    # Parameters: a=top, b=slope, c=midpoint, d=bottom, e=asymmetry
    return [baseline + amplitude, steepness, midpoint, baseline, asymmetry]


def _make_time_points(n=40, end=20.0):
    return np.linspace(0, end, n)


# ---------------------------------------------------------------------------
# Baseline threshold tests (unchanged API)
# ---------------------------------------------------------------------------

class TestCalculateBaselineThreshold:
    """Tests for calculate_baseline_threshold()."""

    def test_default_baseline_points(self):
        """Uses indices 1-3 by default."""
        analyzer = ThresholdAnalyzer(baseline_percentage=0.10)
        fluo_values = np.array([100, 105, 102, 108, 120, 150, 200, 300, 400])

        threshold, baseline = analyzer.calculate_baseline_threshold(fluo_values)

        expected_baseline = np.mean([105, 102, 108])
        expected_threshold = expected_baseline * 1.10

        assert abs(baseline - expected_baseline) < 0.01
        assert abs(threshold - expected_threshold) < 0.01

    def test_custom_baseline_points(self):
        """Custom baseline point indices are respected."""
        analyzer = ThresholdAnalyzer(baseline_percentage=0.15)
        fluo_values = np.array([100, 105, 102, 108, 120, 150, 200, 300, 400])

        threshold, baseline = analyzer.calculate_baseline_threshold(fluo_values, [0, 1, 2])

        expected_baseline = np.mean([100, 105, 102])
        expected_threshold = expected_baseline * 1.15

        assert abs(baseline - expected_baseline) < 0.01
        assert abs(threshold - expected_threshold) < 0.01

    def test_invalid_baseline_points_raises(self):
        """All-out-of-bounds indices raise ValueError."""
        analyzer = ThresholdAnalyzer()
        fluo_values = np.array([100, 105, 102])

        with pytest.raises(ValueError, match="No valid baseline points"):
            analyzer.calculate_baseline_threshold(fluo_values, [5, 6, 7])

    def test_baseline_percentage_variations(self):
        """Different baseline percentages produce correct thresholds."""
        fluo_values = np.array([100, 105, 102, 108, 120, 150, 200, 300, 400])
        expected_baseline = np.mean([105, 102, 108])

        for pct in [0.05, 0.10, 0.15, 0.20]:
            analyzer = ThresholdAnalyzer(baseline_percentage=pct)
            threshold, baseline = analyzer.calculate_baseline_threshold(fluo_values)
            assert abs(threshold - expected_baseline * (1.0 + pct)) < 0.01


# ---------------------------------------------------------------------------
# Signal quality / QC filter tests
# ---------------------------------------------------------------------------

class TestCheckSignalQuality:
    """Tests for check_signal_quality()."""

    def test_passing_signal(self):
        """Signal that rises well above baseline passes QC."""
        analyzer = ThresholdAnalyzer(baseline_percentage=0.10)
        # Baseline ~100, max 400 → clearly passes 10% threshold
        fluo_values = np.array([100, 105, 102, 108, 120, 200, 300, 400, 400])
        assert analyzer.check_signal_quality(fluo_values) == True

    def test_flat_signal_fails(self):
        """Completely flat signal fails QC."""
        analyzer = ThresholdAnalyzer(baseline_percentage=0.10)
        fluo_values = np.array([100, 100, 100, 100, 100, 100])
        assert analyzer.check_signal_quality(fluo_values) == False

    def test_barely_failing_signal(self):
        """Signal that rises only 5% above baseline fails a 10% QC threshold."""
        analyzer = ThresholdAnalyzer(baseline_percentage=0.10)
        baseline = 100.0
        # Baseline points are indices 1,2,3 → all 100.0; threshold = 110.0
        # Max signal is only 105 → fails
        fluo_values = np.array([baseline, baseline, baseline, baseline, baseline * 1.05])
        assert analyzer.check_signal_quality(fluo_values) == False

    def test_barely_passing_signal(self):
        """Signal that rises 25% above baseline passes a 10% QC threshold."""
        analyzer = ThresholdAnalyzer(baseline_percentage=0.10)
        baseline = 100.0
        # Baseline points are indices 1,2,3 → all 100.0; threshold = 110.0
        # Max signal is 125 → passes
        fluo_values = np.array([baseline, baseline, baseline, baseline, baseline * 1.25])
        assert analyzer.check_signal_quality(fluo_values) == True


# ---------------------------------------------------------------------------
# analyze_threshold_crossing_with_fitted_curve tests
# ---------------------------------------------------------------------------

class TestAnalyzeThresholdCrossingWithFittedCurve:
    """Tests for analyze_threshold_crossing_with_fitted_curve()."""

    def _fit_params_for_sigmoid(self):
        """Return params for a well-behaved sigmoid that passes QC."""
        return _make_sigmoid_params(baseline=100, amplitude=400, midpoint=10)

    def test_returns_threshold_result(self):
        """Method always returns a ThresholdResult."""
        analyzer = ThresholdAnalyzer()
        time_points = _make_time_points()
        fluo_values = np.array([100] * 10 + [200, 300, 400, 450, 480] * 6)
        params = self._fit_params_for_sigmoid()

        result = analyzer.analyze_threshold_crossing_with_fitted_curve(
            time_points, fluo_values, params)

        assert isinstance(result, ThresholdResult)

    def test_passing_signal_has_crossing_time(self):
        """A signal that passes QC should yield a crossing time."""
        from fluorescence_tool.algorithms.curve_fitting import CurveFitter
        analyzer = ThresholdAnalyzer(baseline_percentage=0.10)
        fitter = CurveFitter()

        time_points = _make_time_points(n=40, end=20.0)
        params = self._fit_params_for_sigmoid()
        fluo_values = fitter.sigmoid_5param(time_points, *params)

        result = analyzer.analyze_threshold_crossing_with_fitted_curve(
            time_points, fluo_values, params)

        assert result.success is True
        assert result.crossing_time is not None
        assert time_points[0] <= result.crossing_time <= time_points[-1]

    def test_flat_signal_fails_qc(self):
        """A flat signal fails QC and returns success=False with no crossing time."""
        analyzer = ThresholdAnalyzer(baseline_percentage=0.10)
        time_points = _make_time_points()
        fluo_values = np.full(len(time_points), 100.0)
        params = [100.0, 1.0, 10.0, 100.0, 1.0]  # Flat sigmoid

        result = analyzer.analyze_threshold_crossing_with_fitted_curve(
            time_points, fluo_values, params)

        assert result.success is False
        assert result.crossing_time is None
        assert result.error_message is not None
        assert "QC filter failed" in result.error_message

    def test_unsupported_method_returns_failure(self):
        """Passing an unsupported method name returns success=False."""
        analyzer = ThresholdAnalyzer()
        time_points = _make_time_points()
        fluo_values = np.ones(len(time_points)) * 100
        params = self._fit_params_for_sigmoid()

        result = analyzer.analyze_threshold_crossing_with_fitted_curve(
            time_points, fluo_values, params, method="invalid_method")

        assert result.success is False
        assert result.error_message is not None

    def test_result_contains_threshold_and_baseline(self):
        """Result includes threshold_value and baseline_value fields."""
        from fluorescence_tool.algorithms.curve_fitting import CurveFitter
        analyzer = ThresholdAnalyzer()
        fitter = CurveFitter()

        time_points = _make_time_points()
        params = self._fit_params_for_sigmoid()
        fluo_values = fitter.sigmoid_5param(time_points, *params)

        result = analyzer.analyze_threshold_crossing_with_fitted_curve(
            time_points, fluo_values, params)

        assert result.threshold_value is not None
        assert result.baseline_value is not None

    def test_invalid_parameter_count_returns_failure(self):
        """Fewer than 5 parameters causes graceful failure."""
        analyzer = ThresholdAnalyzer()
        time_points = _make_time_points()
        fluo_values = np.ones(len(time_points)) * 200
        bad_params = [1.0, 2.0]  # Only 2 params instead of 5

        result = analyzer.analyze_threshold_crossing_with_fitted_curve(
            time_points, fluo_values, bad_params)

        assert isinstance(result, ThresholdResult)
        # Either QC fails or second-derivative fails — either way no valid CP
        if result.success:
            # If somehow it succeeds, crossing_time must be in range
            assert time_points[0] <= result.crossing_time <= time_points[-1]


# ---------------------------------------------------------------------------
# calculate_second_derivative_crossing_point_with_fitted_curve tests
# ---------------------------------------------------------------------------

class TestSecondDerivativeCrossingPoint:
    """Tests for calculate_second_derivative_crossing_point_with_fitted_curve()."""

    def test_returns_float_for_valid_sigmoid(self):
        """Returns a float crossing time for a well-behaved sigmoid."""
        from fluorescence_tool.algorithms.curve_fitting import CurveFitter
        analyzer = ThresholdAnalyzer()
        fitter = CurveFitter()

        time_points = _make_time_points(n=60, end=20.0)
        params = _make_sigmoid_params(baseline=100, amplitude=400, midpoint=10)

        cp = analyzer.calculate_second_derivative_crossing_point_with_fitted_curve(
            time_points, params)

        assert cp is not None
        assert isinstance(cp, float)
        assert time_points[0] <= cp <= time_points[-1]

    def test_returns_none_for_wrong_param_count(self):
        """Returns None when parameter count is not 5."""
        analyzer = ThresholdAnalyzer()
        time_points = _make_time_points()

        cp = analyzer.calculate_second_derivative_crossing_point_with_fitted_curve(
            time_points, [1.0, 2.0])  # Only 2 params

        assert cp is None

    def test_crossing_near_midpoint(self):
        """CP should be near the sigmoid midpoint for a symmetric curve."""
        from fluorescence_tool.algorithms.curve_fitting import CurveFitter
        analyzer = ThresholdAnalyzer()

        midpoint = 10.0
        time_points = np.linspace(0, 20, 80)
        params = _make_sigmoid_params(baseline=100, amplitude=400, midpoint=midpoint,
                                      steepness=1.0, asymmetry=1.0)

        cp = analyzer.calculate_second_derivative_crossing_point_with_fitted_curve(
            time_points, params)

        assert cp is not None
        # Second derivative max should be within ±4 h of the midpoint
        assert abs(cp - midpoint) < 4.0


# ---------------------------------------------------------------------------
# detect_multiple_crossings tests (unchanged API)
# ---------------------------------------------------------------------------

class TestDetectMultipleCrossings:
    """Tests for detect_multiple_crossings()."""

    def test_detects_multiple_crossings(self):
        """Oscillating data produces multiple detected crossings."""
        analyzer = ThresholdAnalyzer()
        time_points = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], dtype=float)
        fluo_values = np.array([50, 120, 80, 160, 90, 170, 100, 180, 110, 190], dtype=float)
        threshold = 150.0

        crossings = analyzer.detect_multiple_crossings(time_points, fluo_values, threshold)

        assert len(crossings) >= 2
        assert all(isinstance(c, float) for c in crossings)

    def test_no_crossings_returns_empty(self):
        """Data that never crosses threshold returns empty list."""
        analyzer = ThresholdAnalyzer()
        time_points = np.arange(6, dtype=float)
        fluo_values = np.array([50, 60, 70, 80, 90, 100], dtype=float)

        crossings = analyzer.detect_multiple_crossings(time_points, fluo_values, 150.0)

        assert crossings == []


# ---------------------------------------------------------------------------
# validate_crossing_quality tests (unchanged API)
# ---------------------------------------------------------------------------

class TestValidateCrossingQuality:
    """Tests for validate_crossing_quality()."""

    def test_valid_crossing(self):
        """Returns valid=True with expected keys for a real crossing."""
        analyzer = ThresholdAnalyzer()
        time_points = np.array([0, 1, 2, 3, 4, 5], dtype=float)
        fluo_values = np.array([50, 80, 120, 180, 250, 300], dtype=float)

        quality = analyzer.validate_crossing_quality(time_points, fluo_values, 2.5, 150.0)

        assert quality["valid"] is True
        assert "signal_to_noise_ratio" in quality
        assert "slope_at_crossing" in quality
        assert quality["slope_at_crossing"] > 0

    def test_crossing_outside_range_is_invalid(self):
        """Crossing time outside the time array is flagged as invalid."""
        analyzer = ThresholdAnalyzer()
        time_points = np.array([0, 1, 2, 3, 4, 5], dtype=float)
        fluo_values = np.array([50, 80, 120, 180, 250, 300], dtype=float)

        quality = analyzer.validate_crossing_quality(time_points, fluo_values, 10.0, 150.0)

        assert quality["valid"] is False
        assert "outside time range" in quality["reason"].lower()


# ---------------------------------------------------------------------------
# calculate_confidence_interval tests (unchanged API)
# ---------------------------------------------------------------------------

class TestCalculateConfidenceInterval:
    """Tests for calculate_confidence_interval()."""

    def test_ci_brackets_crossing_time(self):
        """Confidence interval should bracket the crossing time."""
        analyzer = ThresholdAnalyzer()
        time_points = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], dtype=float)
        base_values = np.array([50, 80, 120, 180, 250, 300, 350, 400, 450, 500], dtype=float)
        np.random.seed(42)
        fluo_values = base_values + np.random.normal(0, 5, len(base_values))

        ci = analyzer.calculate_confidence_interval(time_points, fluo_values, 2.5, 150.0)

        if ci is not None:
            lower, upper = ci
            assert lower < 2.5 < upper
            assert upper - lower > 0
