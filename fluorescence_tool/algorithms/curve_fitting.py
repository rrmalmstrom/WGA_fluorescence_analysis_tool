"""
Curve fitting algorithms based on analyze_fluorescence_data.py.

This module implements the proven 5-parameter sigmoid curve fitting
functionality that has been validated with real fluorescence data.
"""

import numpy as np
import signal
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass
from scipy.optimize import curve_fit
import warnings


@dataclass
class CurveFitResult:
    """Result of curve fitting operation."""
    success: bool
    parameters: Optional[List[float]] = None
    r_squared: Optional[float] = None
    strategy_used: Optional[str] = None
    error_message: Optional[str] = None
    covariance_matrix: Optional[np.ndarray] = None
    fit_error: Optional[float] = None
    fit_type: str = "sigmoid"  # "sigmoid" or "polynomial"
    # Additional fluorescence metrics
    baseline_fluorescence: Optional[float] = None
    final_fluorescence: Optional[float] = None
    fluorescence_change: Optional[float] = None
    percent_change: Optional[float] = None


class TimeoutException(Exception):
    """Exception raised when curve fitting times out."""
    pass


class CurveFitter:
    """
    Curve fitting implementation based on analyze_fluorescence_data.py.
    
    Implements 5-parameter sigmoid curve fitting with multiple strategies
    and robust error handling.
    """
    
    def __init__(self, timeout_seconds: int = 2):
        """
        Initialize curve fitter.
        
        Args:
            timeout_seconds: Maximum time allowed for each fitting attempt
        """
        self.timeout_seconds = timeout_seconds
    
    def sigmoid_5param(self, x: np.ndarray, a: float, b: float, c: float, d: float, e: float) -> np.ndarray:
        """
        5-parameter logistic function with overflow protection.
        
        Based on the proven implementation in analyze_fluorescence_data.py.
        
        Args:
            x: Independent variable (time points)
            a: Amplitude (difference between upper and lower asymptotes)
            b: Slope factor (steepness of the curve)
            c: Inflection point (x-coordinate where curve changes most rapidly)
            d: Lower asymptote (minimum y value)
            e: Linear term coefficient (accounts for linear drift)
            
        Returns:
            Calculated y values
        """
        try:
            # Limit b to prevent overflow in exp (from analyze_fluorescence_data.py)
            b = max(min(b, 10), -10)
            # Calculate exponent with overflow protection
            exp_val = np.exp(-b * (x - c))
            # Handle division by zero or very small numbers
            denom = 1 + exp_val
            result = a / denom + d + e * x
            # Check for NaN or inf values
            if not np.all(np.isfinite(result)):
                raise ValueError("Overflow detected in sigmoid calculation")
            return result
        except Exception as e:
            # print(f"Error in sigmoid calculation: {e}")
            return np.full_like(x, np.nan)
    
    def calculate_fit_error(self, time_points: np.ndarray, fluo_values: np.ndarray, params: List[float]) -> float:
        """
        Calculate fit error (sum of squared residuals).
        
        Based on analyze_fluorescence_data.py implementation.
        """
        fitted_values = self.sigmoid_5param(time_points, *params)
        residuals = fluo_values - fitted_values
        return np.sum(residuals**2)
    
    def calculate_threshold(self, fluo_values: np.ndarray) -> float:
        """
        Calculate threshold as 10% greater than average of time points 2-4.
        
        Based on the proven method in analyze_fluorescence_data.py.
        """
        avg = np.mean(fluo_values[1:4])
        return avg * 1.10
    
    def calculate_r_squared(self, observed: np.ndarray, predicted: np.ndarray) -> float:
        """Calculate R-squared value for fit quality assessment."""
        ss_res = np.sum((observed - predicted) ** 2)
        ss_tot = np.sum((observed - np.mean(observed)) ** 2)
        return 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    def calculate_fluorescence_change(self, fluo_values: np.ndarray) -> Tuple[float, float, float, float]:
        """
        Calculate fluorescence change metrics from baseline to final.
        
        Args:
            fluo_values: Array of fluorescence values
            
        Returns:
            Tuple of (baseline_fluorescence, final_fluorescence, fluorescence_change, percent_change)
        """
        # Calculate baseline as average of first 3 time points
        baseline_fluorescence = np.mean(fluo_values[:3])
        
        # Calculate final as average of last 3 time points
        final_fluorescence = np.mean(fluo_values[-3:])
        
        # Calculate absolute change
        fluorescence_change = final_fluorescence - baseline_fluorescence
        
        # Calculate percent change
        percent_change = (fluorescence_change / baseline_fluorescence * 100) if baseline_fluorescence != 0 else 0.0
        
        return baseline_fluorescence, final_fluorescence, fluorescence_change, percent_change
    
    def polynomial_3param(self, x: np.ndarray, a: float, b: float, c: float, d: float) -> np.ndarray:
        """
        3rd degree polynomial function for QC-failing wells.
        
        Args:
            x: Independent variable (time points)
            a, b, c, d: Polynomial coefficients (d + c*x + b*x^2 + a*x^3)
            
        Returns:
            Calculated y values
        """
        return d + c*x + b*x**2 + a*x**3
    
    def fit_polynomial(self, time_points: np.ndarray, fluo_values: np.ndarray) -> CurveFitResult:
        """
        Fit cubic polynomial to QC-failing wells (fast, no iteration).
        
        Args:
            time_points: Array of time values
            fluo_values: Array of fluorescence values
            
        Returns:
            CurveFitResult with polynomial fit
        """
        try:
            # Fit cubic polynomial using numpy (closed-form solution, no iteration)
            poly_coeffs = np.polyfit(time_points, fluo_values, deg=3)
            
            # Calculate fitted values and R-squared
            fitted_values = np.polyval(poly_coeffs, time_points)
            r_squared = self.calculate_r_squared(fluo_values, fitted_values)
            
            # Calculate fluorescence change metrics
            baseline_fluor, final_fluor, fluor_change, percent_change = self.calculate_fluorescence_change(fluo_values)
            
            return CurveFitResult(
                success=True,
                parameters=poly_coeffs.tolist(),  # [a, b, c, d] for a*x^3 + b*x^2 + c*x + d
                r_squared=r_squared,
                strategy_used="Polynomial fit",
                fit_type="polynomial",
                baseline_fluorescence=baseline_fluor,
                final_fluorescence=final_fluor,
                fluorescence_change=fluor_change,
                percent_change=percent_change
            )
            
        except Exception as e:
            return CurveFitResult(
                success=False,
                error_message=f"Polynomial fit failed: {e}",
                fit_type="polynomial"
            )

    def _timeout_handler(self, signum, frame):
        """Signal handler for timeout."""
        raise TimeoutException("Curve fitting timed out")
    
    def _estimate_inflection_point(self, time_points: np.ndarray, fluo_values: np.ndarray) -> float:
        """
        Estimate the inflection point (time of maximum rate of change).
        
        Uses the index of maximum first difference to find where the curve
        rises or falls fastest. This gives a much better initial guess for
        the sigmoid parameter c than using argmax(fluo_values).
        
        Args:
            time_points: Array of time values
            fluo_values: Array of fluorescence values
            
        Returns:
            Estimated time of inflection point
        """
        diffs = np.abs(np.diff(fluo_values))
        if len(diffs) == 0:
            return time_points[len(time_points) // 2]
        inflection_idx = np.argmax(diffs)
        # Return the midpoint between the two time points straddling the max diff
        return (time_points[inflection_idx] + time_points[inflection_idx + 1]) / 2.0

    def fit_curve(self, time_points: np.ndarray, fluo_values: np.ndarray,
                  qc_threshold_percent: float = 10.0) -> CurveFitResult:
        """
        Two-path curve fitting based on QC pre-check.
        
        Path A (QC-failing wells, |percent_change| < qc_threshold_percent):
            Fits a fast cubic polynomial — no iteration, always succeeds,
            suitable for display of flat/declining/barely-changing wells.
            Returns success=True with fit_type="polynomial".
        
        Path B (QC-passing wells, |percent_change| >= qc_threshold_percent):
            Fits a 5-parameter sigmoid using a smart initial guess derived
            from the inflection point of the data. Uses maxfev=200 with one
            fallback attempt. Returns success=True with fit_type="sigmoid"
            when a CP can be calculated.
        
        Args:
            time_points: Array of time values
            fluo_values: Array of fluorescence values
            qc_threshold_percent: Minimum percent change to attempt sigmoid fit
            
        Returns:
            CurveFitResult with fitting results
        """
        try:
            # Check if there's enough variation in the data to fit any curve
            if np.max(fluo_values) - np.min(fluo_values) < 0.1:
                return CurveFitResult(
                    success=False,
                    error_message="Insufficient variation in data for curve fitting"
                )
            
            # Calculate fluorescence change metrics (used for QC pre-check)
            baseline_fluor, final_fluor, fluor_change, percent_change = self.calculate_fluorescence_change(fluo_values)
            
            # --- PATH A: QC-failing wells — fast polynomial fit ---
            if abs(percent_change) < qc_threshold_percent:
                return self.fit_polynomial(time_points, fluo_values)
            
            # --- PATH B: QC-passing wells — smart sigmoid fit ---
            amplitude = np.max(fluo_values) - np.min(fluo_values)
            baseline = np.min(fluo_values)
            
            # Smart inflection point estimate: time of maximum rate of change
            c_inflection = self._estimate_inflection_point(time_points, fluo_values)
            
            # Slope direction: positive if curve rises overall, negative if it falls
            b_init = 1.0 if fluor_change >= 0 else -1.0
            
            # Shared bounds: allow both rising and falling slopes
            bounds = (
                [0, -10, min(time_points), min(fluo_values), -np.inf],
                [np.inf, 10, max(time_points), max(fluo_values), np.inf]
            )
            
            # Strategy 1: inflection-point-based initial guess
            strategies = [
                {
                    "name": "Inflection point fit",
                    "p0": [amplitude, b_init, c_inflection, baseline, 0.0],
                },
                # Fallback: midpoint of time range as c estimate
                {
                    "name": "Midpoint fallback fit",
                    "p0": [amplitude, b_init, time_points[len(time_points) // 2], baseline, 0.0],
                },
            ]
            
            best_fit = None
            best_error = float('inf')
            best_strategy = None
            
            for attempt in strategies:
                try:
                    popt, pcov = curve_fit(
                        self.sigmoid_5param, time_points, fluo_values,
                        p0=attempt["p0"], maxfev=200,
                        bounds=bounds
                    )
                    
                    # Validate covariance and parameters
                    if pcov is None or not np.all(np.isfinite(pcov)):
                        continue
                    if not np.all(np.isfinite(popt)) or any(p == 0 for p in popt[:4]):
                        continue
                    
                    error = self.calculate_fit_error(time_points, fluo_values, popt)
                    if error < best_error:
                        best_error = error
                        best_fit = (popt, pcov, error)
                        best_strategy = attempt["name"]
                    
                    # Accept first good fit immediately (no need to try fallback)
                    break
                    
                except Exception:
                    continue
            
            # If sigmoid fit failed, fall back to polynomial for display
            if best_fit is None:
                poly_result = self.fit_polynomial(time_points, fluo_values)
                # Override success=False so CP is not calculated, but curve is displayed
                poly_result.success = False
                poly_result.error_message = "Sigmoid fit failed after all strategies; polynomial shown for display"
                return poly_result
            
            popt, pcov, fit_error = best_fit
            fitted_values = self.sigmoid_5param(time_points, *popt)
            
            if not np.all(np.isfinite(fitted_values)):
                return CurveFitResult(
                    success=False,
                    error_message="Fitted values contain NaN or inf"
                )
            
            r_squared = self.calculate_r_squared(fluo_values, fitted_values)
            
            return CurveFitResult(
                success=True,
                parameters=popt.tolist(),
                r_squared=r_squared,
                strategy_used=best_strategy,
                covariance_matrix=pcov,
                fit_error=fit_error,
                fit_type="sigmoid",
                baseline_fluorescence=baseline_fluor,
                final_fluorescence=final_fluor,
                fluorescence_change=fluor_change,
                percent_change=percent_change
            )
        
        except Exception as e:
            return CurveFitResult(
                success=False,
                error_message=f"Error fitting curve: {e}"
            )
    
    def find_crossing_time(self, time_points: np.ndarray, fitted_values: np.ndarray, threshold: float) -> Optional[float]:
        """
        Find where the fitted curve crosses the threshold using linear interpolation.
        
        Based on the proven method in analyze_fluorescence_data.py.
        
        Args:
            time_points: Array of time values
            fitted_values: Array of fitted fluorescence values
            threshold: Threshold value to find crossing for
            
        Returns:
            Crossing time or None if no crossing found
        """
        try:
            # Interpolate to find exact crossing time
            for i in range(1, len(fitted_values)):
                if fitted_values[i] > threshold and fitted_values[i-1] <= threshold:
                    t1, y1 = time_points[i-1], fitted_values[i-1]
                    t2, y2 = time_points[i], fitted_values[i]
                    crossing_time = t1 + (threshold - y1) * (t2 - t1) / (y2 - y1)
                    return crossing_time
            
            return None
        
        except Exception as e:
            # print(f"Error finding crossing time: {e}")
            return None
    
    def fit_curve_and_find_crossing(self, time_points: np.ndarray, fluo_values: np.ndarray, threshold: Optional[float] = None) -> Tuple[Optional[float], Optional[List[float]]]:
        """
        Combined curve fitting and crossing time detection.
        
        Replicates the main function from analyze_fluorescence_data.py.
        
        Args:
            time_points: Array of time values
            fluo_values: Array of fluorescence values
            threshold: Threshold value (calculated if None)
            
        Returns:
            Tuple of (crossing_time, fitted_parameters)
        """
        # Calculate threshold if not provided
        if threshold is None:
            threshold = self.calculate_threshold(fluo_values)
        
        # Fit curve
        fit_result = self.fit_curve(time_points, fluo_values)
        
        if not fit_result.success:
            return None, None
        
        # Find crossing time
        fitted_values = self.sigmoid_5param(time_points, *fit_result.parameters)
        crossing_time = self.find_crossing_time(time_points, fitted_values, threshold)
        
        return crossing_time, fit_result.parameters