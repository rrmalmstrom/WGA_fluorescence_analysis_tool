"""
Threshold analysis algorithms based on analyze_fluorescence_data.py.

This module implements threshold detection and crossing point analysis
functionality that has been validated with real fluorescence data.
"""

import numpy as np
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass
from scipy import interpolate, signal
from scipy.interpolate import CubicSpline
import warnings


@dataclass
class ThresholdResult:
    """Result of threshold analysis operation."""
    success: bool
    threshold_value: Optional[float] = None
    crossing_time: Optional[float] = None
    crossing_method: Optional[str] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    error_message: Optional[str] = None
    baseline_points: Optional[List[int]] = None
    baseline_value: Optional[float] = None


class ThresholdAnalyzer:
    """
    Threshold analysis implementation based on analyze_fluorescence_data.py.
    
    Implements baseline percentage method for threshold detection and
    linear interpolation for precise crossing point calculation.
    """
    
    def __init__(self, baseline_percentage: float = 0.10):
        """
        Initialize threshold analyzer.
        
        Args:
            baseline_percentage: Percentage above baseline for threshold (default 10%)
        """
        self.baseline_percentage = baseline_percentage
    
    def calculate_baseline_threshold(self, fluo_values: np.ndarray, baseline_points: Optional[List[int]] = None) -> Tuple[float, float]:
        """
        Calculate threshold using baseline percentage method.
        
        Based on the proven implementation in analyze_fluorescence_data.py.
        
        Args:
            fluo_values: Array of fluorescence values
            baseline_points: Indices to use for baseline calculation (default: points 1-3)
            
        Returns:
            Tuple of (threshold_value, baseline_value)
        """
        if baseline_points is None:
            # Use points 1-3 (indices 1:4) as in analyze_fluorescence_data.py
            baseline_points = [1, 2, 3]
        
        # Ensure baseline points are within array bounds
        valid_points = [i for i in baseline_points if 0 <= i < len(fluo_values)]
        
        if len(valid_points) == 0:
            raise ValueError("No valid baseline points within array bounds")
        
        # Calculate baseline as average of specified points
        baseline_value = np.mean(fluo_values[valid_points])
        
        # Calculate threshold as percentage above baseline
        threshold_value = baseline_value * (1.0 + self.baseline_percentage)
        
        return threshold_value, baseline_value
    
    def find_crossing_point_linear_interpolation(self, time_points: np.ndarray, fluo_values: np.ndarray, threshold: float) -> Optional[float]:
        """
        Find crossing point using linear interpolation.
        
        Based on the proven method in analyze_fluorescence_data.py.
        
        Args:
            time_points: Array of time values
            fluo_values: Array of fluorescence values
            threshold: Threshold value to find crossing for
            
        Returns:
            Crossing time or None if no crossing found
        """
        try:
            # Find where fluorescence crosses threshold (going upward)
            for i in range(1, len(fluo_values)):
                if fluo_values[i] > threshold and fluo_values[i-1] <= threshold:
                    # Linear interpolation between the two points
                    t1, y1 = time_points[i-1], fluo_values[i-1]
                    t2, y2 = time_points[i], fluo_values[i]
                    
                    # Avoid division by zero
                    if y2 == y1:
                        crossing_time = t1
                    else:
                        crossing_time = t1 + (threshold - y1) * (t2 - t1) / (y2 - y1)
                    
                    return crossing_time
            
            return None
        
        except Exception as e:
            print(f"Error finding crossing point: {e}")
            return None
    
    def find_crossing_point_spline_interpolation(self, time_points: np.ndarray, fluo_values: np.ndarray, threshold: float) -> Optional[float]:
        """
        Find crossing point using spline interpolation for higher precision.
        
        Args:
            time_points: Array of time values
            fluo_values: Array of fluorescence values
            threshold: Threshold value to find crossing for
            
        Returns:
            Crossing time or None if no crossing found
        """
        try:
            # Check if data crosses threshold
            if np.max(fluo_values) <= threshold:
                return None
            
            # Create spline interpolation
            spline = interpolate.UnivariateSpline(time_points, fluo_values - threshold, s=0)
            
            # Find roots (where spline crosses zero, i.e., where original data crosses threshold)
            roots = spline.roots()
            
            if len(roots) == 0:
                return None
            
            # Return first positive crossing
            valid_roots = roots[(roots >= time_points[0]) & (roots <= time_points[-1])]
            
            if len(valid_roots) > 0:
                return float(valid_roots[0])
            
            return None
        
        except Exception as e:
            print(f"Error in spline interpolation: {e}")
            return None
    
    def calculate_second_derivative_crossing_point(self, time_points: np.ndarray, fluo_values: np.ndarray) -> Optional[float]:
        """
        Calculate crossing point using second derivative of FITTED SIGMOIDAL CURVE.
        
        This is the industry-standard method: fit a sigmoidal curve first, then find
        the maximum of the second derivative of that fitted curve.
        
        Args:
            time_points: Array of time values
            fluo_values: Array of fluorescence values
            
        Returns:
            Crossing point time or None if calculation fails
        """
        try:
            # Import curve fitter
            from .curve_fitting import CurveFitter
            
            # Ensure we have enough data points
            if len(time_points) < 5 or len(fluo_values) < 5:
                return None
            
            # Check for sufficient variation in data
            if np.max(fluo_values) - np.min(fluo_values) < 0.1:
                return None
            
            # Step 1: Fit sigmoidal curve to the data
            curve_fitter = CurveFitter(timeout_seconds=2)
            fit_result = curve_fitter.fit_curve(time_points, fluo_values)
            
            if not fit_result.success or fit_result.parameters is None:
                return None
            
            # Step 2: Create fine-resolution time points for smooth derivative calculation
            fine_time = np.linspace(time_points[0], time_points[-1], len(time_points) * 20)
            
            # Step 3: Generate fitted curve values at fine resolution
            fitted_values = curve_fitter.sigmoid_5param(fine_time, *fit_result.parameters)
            
            # Step 4: Calculate second derivative of the fitted curve
            spline = CubicSpline(fine_time, fitted_values)
            second_derivative = spline(fine_time, nu=2)  # nu=2 for second derivative
            
            # Step 5: Find the maximum of the second derivative (steepest acceleration)
            max_second_deriv_idx = np.argmax(second_derivative)
            crossing_point = fine_time[max_second_deriv_idx]
            
            # Validate the crossing point is within reasonable bounds
            if crossing_point < time_points[0] or crossing_point > time_points[-1]:
                return None
            
            return float(crossing_point)
            
        except Exception as e:
            print(f"Error calculating second derivative crossing point: {e}")
            return None
    
    def check_signal_quality(self, fluo_values: np.ndarray, baseline_points: Optional[List[int]] = None) -> bool:
        """
        Quality control check: Does the signal increase by more than 10% above baseline?
        
        This is used as a filter before calculating crossing points. Only wells that pass
        this QC check will get a crossing point calculated using the second derivative method.
        
        Args:
            fluo_values: Array of fluorescence values
            baseline_points: Indices to use for baseline calculation (default: points 1-3)
            
        Returns:
            True if signal increases >10% above baseline, False otherwise
        """
        try:
            # Calculate baseline threshold (this includes the 10% increase)
            threshold_value, baseline_value = self.calculate_baseline_threshold(fluo_values, baseline_points)
            
            # Check if maximum signal exceeds the threshold
            max_signal = np.max(fluo_values)
            
            # Signal passes QC if max signal is above the 10% threshold
            return max_signal >= threshold_value
            
        except Exception:
            # If calculation fails, assume signal doesn't pass QC
            return False
    
    def calculate_confidence_interval(self, time_points: np.ndarray, fluo_values: np.ndarray,
                                    crossing_time: float, threshold: float,
                                    confidence_level: float = 0.95) -> Optional[Tuple[float, float]]:
        """
        Calculate confidence interval for crossing time estimate.
        
        Args:
            time_points: Array of time values
            fluo_values: Array of fluorescence values
            crossing_time: Estimated crossing time
            threshold: Threshold value
            confidence_level: Confidence level (default 95%)
            
        Returns:
            Tuple of (lower_bound, upper_bound) or None if calculation fails
        """
        try:
            # Find the two points around the crossing
            crossing_idx = np.searchsorted(time_points, crossing_time)
            
            if crossing_idx == 0 or crossing_idx >= len(time_points):
                return None
            
            # Use local noise estimate around crossing point
            window_size = min(3, crossing_idx, len(time_points) - crossing_idx)
            start_idx = max(0, crossing_idx - window_size)
            end_idx = min(len(time_points), crossing_idx + window_size)
            
            local_values = fluo_values[start_idx:end_idx]
            noise_std = np.std(local_values)
            
            # Estimate uncertainty in crossing time based on noise and slope
            t1, y1 = time_points[crossing_idx-1], fluo_values[crossing_idx-1]
            t2, y2 = time_points[crossing_idx], fluo_values[crossing_idx]
            
            slope = (y2 - y1) / (t2 - t1) if t2 != t1 else 1.0
            
            if abs(slope) < 1e-10:  # Avoid division by very small numbers
                return None
            
            # Time uncertainty based on noise and slope
            time_uncertainty = noise_std / abs(slope)
            
            # Apply confidence level (approximate)
            z_score = 1.96 if confidence_level == 0.95 else 2.58  # 95% or 99%
            margin = z_score * time_uncertainty
            
            return (crossing_time - margin, crossing_time + margin)
        
        except Exception as e:
            print(f"Error calculating confidence interval: {e}")
            return None
    
    def analyze_threshold_crossing_with_fitted_curve(self, time_points: np.ndarray, fluo_values: np.ndarray,
                                                   fitted_parameters: List[float],
                                                   threshold: Optional[float] = None,
                                                   method: str = "qc_second_derivative") -> ThresholdResult:
        """
        Complete threshold crossing analysis using pre-fitted curve parameters.
        
        This ensures the CP is calculated using the SAME fitted curve that is used for plotting,
        eliminating offset issues caused by different curve fitting results.
        
        Args:
            time_points: Array of time values
            fluo_values: Array of fluorescence values
            fitted_parameters: Pre-fitted sigmoid parameters [a, b, c, d, e]
            threshold: Threshold value (calculated if None, only used for legacy methods)
            method: Analysis method ("qc_second_derivative", "linear", or "spline")
            
        Returns:
            ThresholdResult with analysis results
        """
        print(f"\n=== DEBUG: analyze_threshold_crossing_with_fitted_curve called ===")
        print(f"Time points range: {time_points[0]:.2f} to {time_points[-1]:.2f}")
        print(f"Fluorescence range: {fluo_values.min():.2f} to {fluo_values.max():.2f}")
        print(f"Fitted parameters: {fitted_parameters}")
        print(f"Method: {method}")
        
        try:
            # Handle different analysis methods
            if method == "qc_second_derivative":
                # NEW APPROACH: QC filter + second derivative using pre-fitted curve
                
                # Step 1: Quality control check using fixed threshold
                passes_qc = self.check_signal_quality(fluo_values)
                
                if not passes_qc:
                    # Signal doesn't meet QC criteria - no CP calculated
                    threshold_value, baseline_value = self.calculate_baseline_threshold(fluo_values)
                    return ThresholdResult(
                        success=False,
                        threshold_value=threshold_value,
                        crossing_time=None,
                        crossing_method=method,
                        confidence_interval=None,
                        baseline_points=[1, 2, 3],
                        baseline_value=baseline_value,
                        error_message="Signal does not increase >10% above baseline (QC filter failed)"
                    )
                
                # Step 2: Signal passes QC - calculate CP using second derivative with pre-fitted curve
                crossing_time = self.calculate_second_derivative_crossing_point_with_fitted_curve(
                    time_points, fitted_parameters)
                
                # Calculate baseline and threshold for reference
                threshold_value, baseline_value = self.calculate_baseline_threshold(fluo_values)
                baseline_points = [1, 2, 3]
                confidence_interval = None
                
                success = crossing_time is not None
                error_message = None if success else "Second derivative calculation failed"
                
            else:
                # For legacy methods, fall back to original implementation
                return self.analyze_threshold_crossing(time_points, fluo_values, threshold, method)
            
            return ThresholdResult(
                success=success,
                threshold_value=threshold_value,
                crossing_time=crossing_time,
                crossing_method=method,
                confidence_interval=confidence_interval,
                baseline_points=baseline_points,
                baseline_value=baseline_value,
                error_message=error_message
            )
        
        except Exception as e:
            return ThresholdResult(
                success=False,
                error_message=f"Error in threshold analysis with fitted curve: {e}"
            )

    def calculate_second_derivative_crossing_point_with_fitted_curve(self, time_points: np.ndarray,
                                                                   fitted_parameters: List[float]) -> Optional[float]:
        """
        Calculate crossing point using second derivative of pre-fitted sigmoidal curve.
        
        This uses the SAME fitted curve parameters that are used for plotting,
        ensuring perfect alignment between CP and curve.
        
        Args:
            time_points: Array of time values
            fitted_parameters: Pre-fitted sigmoid parameters [a, b, c, d, e]
            
        Returns:
            Crossing point time or None if calculation fails
        """
        print(f"\n--- DEBUG: calculate_second_derivative_crossing_point_with_fitted_curve ---")
        print(f"Input parameters: {fitted_parameters}")
        
        try:
            # Import curve fitter to access sigmoid function
            from .curve_fitting import CurveFitter
            curve_fitter = CurveFitter()
            
            # Ensure we have valid parameters
            if len(fitted_parameters) != 5:
                print(f"ERROR: Invalid parameter count: {len(fitted_parameters)}, expected 5")
                return None
            
            # Step 1: Create fine-resolution time points for smooth derivative calculation
            fine_time = np.linspace(time_points[0], time_points[-1], len(time_points) * 20)
            print(f"Fine time range: {fine_time[0]:.2f} to {fine_time[-1]:.2f}, {len(fine_time)} points")
            
            # Step 2: Generate fitted curve values at fine resolution using PRE-FITTED parameters
            fitted_values = curve_fitter.sigmoid_5param(fine_time, *fitted_parameters)
            print(f"Fitted values range: {fitted_values.min():.2f} to {fitted_values.max():.2f}")
            
            # Step 3: Calculate second derivative of the fitted curve
            spline = CubicSpline(fine_time, fitted_values)
            second_derivative = spline(fine_time, nu=2)  # nu=2 for second derivative
            print(f"Second derivative range: {second_derivative.min():.6f} to {second_derivative.max():.6f}")
            
            # Step 4: Find the maximum of the second derivative (steepest acceleration)
            max_second_deriv_idx = np.argmax(second_derivative)
            crossing_point = fine_time[max_second_deriv_idx]
            print(f"Max second derivative at index {max_second_deriv_idx}, time = {crossing_point:.2f}")
            
            # Calculate fluorescence at CP for debugging
            cp_fluorescence = curve_fitter.sigmoid_5param(np.array([crossing_point]), *fitted_parameters)[0]
            print(f"CP fluorescence at {crossing_point:.2f}: {cp_fluorescence:.2f}")
            
            # Validate the crossing point is within reasonable bounds
            if crossing_point < time_points[0] or crossing_point > time_points[-1]:
                print(f"ERROR: CP {crossing_point:.2f} outside time bounds [{time_points[0]:.2f}, {time_points[-1]:.2f}]")
                return None
            
            print(f"SUCCESS: CP calculated at {crossing_point:.2f}")
            return float(crossing_point)
            
        except Exception as e:
            print(f"Error calculating second derivative crossing point with fitted curve: {e}")
            return None

    def analyze_threshold_crossing(self, time_points: np.ndarray, fluo_values: np.ndarray,
                                 threshold: Optional[float] = None,
                                 method: str = "qc_second_derivative") -> ThresholdResult:
        """
        Complete threshold crossing analysis with QC filtering.
        
        NEW APPROACH: Uses fixed threshold as QC filter, then second derivative for CP calculation.
        Only wells that increase >10% above baseline get a crossing point calculated.
        
        Args:
            time_points: Array of time values
            fluo_values: Array of fluorescence values
            threshold: Threshold value (calculated if None, only used for legacy methods)
            method: Analysis method ("qc_second_derivative", "linear", or "spline")
                   - "qc_second_derivative": QC filter + second derivative (recommended)
                   - "linear": Fixed baseline percentage method (legacy)
                   - "spline": Spline interpolation method (legacy)
            
        Returns:
            ThresholdResult with analysis results
        """
        try:
            # Handle different analysis methods
            if method == "qc_second_derivative":
                # NEW APPROACH: QC filter + second derivative
                
                # Step 1: Quality control check using fixed threshold
                passes_qc = self.check_signal_quality(fluo_values)
                
                if not passes_qc:
                    # Signal doesn't meet QC criteria - no CP calculated
                    threshold_value, baseline_value = self.calculate_baseline_threshold(fluo_values)
                    return ThresholdResult(
                        success=False,
                        threshold_value=threshold_value,
                        crossing_time=None,
                        crossing_method=method,
                        confidence_interval=None,
                        baseline_points=[1, 2, 3],
                        baseline_value=baseline_value,
                        error_message="Signal does not increase >10% above baseline (QC filter failed)"
                    )
                
                # Step 2: Signal passes QC - calculate CP using second derivative
                crossing_time = self.calculate_second_derivative_crossing_point(time_points, fluo_values)
                
                # Calculate baseline and threshold for reference
                threshold_value, baseline_value = self.calculate_baseline_threshold(fluo_values)
                baseline_points = [1, 2, 3]
                confidence_interval = None
                
                success = crossing_time is not None
                error_message = None if success else "Second derivative calculation failed"
                
            else:
                # LEGACY METHODS: Baseline percentage threshold crossing
                # Calculate threshold if not provided
                if threshold is None:
                    threshold_value, baseline_value = self.calculate_baseline_threshold(fluo_values)
                    baseline_points = [1, 2, 3]
                else:
                    threshold_value = threshold
                    baseline_value = None
                    baseline_points = None
                
                # Find crossing point using specified legacy method
                if method == "linear":
                    crossing_time = self.find_crossing_point_linear_interpolation(
                        time_points, fluo_values, threshold_value)
                elif method == "spline":
                    crossing_time = self.find_crossing_point_spline_interpolation(
                        time_points, fluo_values, threshold_value)
                else:
                    return ThresholdResult(
                        success=False,
                        error_message=f"Unknown analysis method: {method}"
                    )
                
                # Calculate confidence interval if crossing found
                confidence_interval = None
                if crossing_time is not None:
                    confidence_interval = self.calculate_confidence_interval(
                        time_points, fluo_values, crossing_time, threshold_value)
                
                success = crossing_time is not None
                error_message = None if success else f"No crossing point found using {method} method"
            
            return ThresholdResult(
                success=success,
                threshold_value=threshold_value,
                crossing_time=crossing_time,
                crossing_method=method,
                confidence_interval=confidence_interval,
                baseline_points=baseline_points,
                baseline_value=baseline_value,
                error_message=error_message
            )
        
        except Exception as e:
            return ThresholdResult(
                success=False,
                error_message=f"Error in threshold analysis: {e}"
            )
    
    def detect_multiple_crossings(self, time_points: np.ndarray, fluo_values: np.ndarray, 
                                threshold: float) -> List[float]:
        """
        Detect multiple threshold crossings in the data.
        
        Args:
            time_points: Array of time values
            fluo_values: Array of fluorescence values
            threshold: Threshold value
            
        Returns:
            List of crossing times
        """
        crossings = []
        
        try:
            for i in range(1, len(fluo_values)):
                # Check for upward crossing
                if fluo_values[i] > threshold and fluo_values[i-1] <= threshold:
                    t1, y1 = time_points[i-1], fluo_values[i-1]
                    t2, y2 = time_points[i], fluo_values[i]
                    
                    if y2 != y1:
                        crossing_time = t1 + (threshold - y1) * (t2 - t1) / (y2 - y1)
                        crossings.append(crossing_time)
                    else:
                        crossings.append(t1)
        
        except Exception as e:
            print(f"Error detecting multiple crossings: {e}")
        
        return crossings
    
    def validate_crossing_quality(self, time_points: np.ndarray, fluo_values: np.ndarray, 
                                crossing_time: float, threshold: float) -> Dict[str, Any]:
        """
        Validate the quality of a detected crossing point.
        
        Args:
            time_points: Array of time values
            fluo_values: Array of fluorescence values
            crossing_time: Detected crossing time
            threshold: Threshold value
            
        Returns:
            Dictionary with quality metrics
        """
        try:
            # Find crossing index
            crossing_idx = np.searchsorted(time_points, crossing_time)
            
            if crossing_idx == 0 or crossing_idx >= len(time_points):
                return {"valid": False, "reason": "Crossing outside time range"}
            
            # Check signal-to-noise ratio around crossing
            window_size = min(5, crossing_idx, len(time_points) - crossing_idx)
            start_idx = max(0, crossing_idx - window_size)
            end_idx = min(len(time_points), crossing_idx + window_size)
            
            local_values = fluo_values[start_idx:end_idx]
            signal_range = np.max(local_values) - np.min(local_values)
            noise_std = np.std(local_values)
            
            snr = signal_range / noise_std if noise_std > 0 else float('inf')
            
            # Check slope at crossing
            t1, y1 = time_points[crossing_idx-1], fluo_values[crossing_idx-1]
            t2, y2 = time_points[crossing_idx], fluo_values[crossing_idx]
            slope = (y2 - y1) / (t2 - t1) if t2 != t1 else 0
            
            return {
                "valid": True,
                "signal_to_noise_ratio": snr,
                "slope_at_crossing": slope,
                "crossing_index": crossing_idx,
                "local_noise_std": noise_std
            }
        
        except Exception as e:
            return {"valid": False, "reason": f"Error in validation: {e}"}