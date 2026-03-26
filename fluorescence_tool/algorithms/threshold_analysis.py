"""
Threshold analysis algorithms based on analyze_fluorescence_data.py.

This module implements threshold detection and crossing point analysis
functionality that has been validated with real fluorescence data.
"""

import numpy as np
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass
from scipy import interpolate
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
    
    def analyze_threshold_crossing(self, time_points: np.ndarray, fluo_values: np.ndarray, 
                                 threshold: Optional[float] = None,
                                 method: str = "linear") -> ThresholdResult:
        """
        Complete threshold crossing analysis.
        
        Args:
            time_points: Array of time values
            fluo_values: Array of fluorescence values
            threshold: Threshold value (calculated if None)
            method: Interpolation method ("linear" or "spline")
            
        Returns:
            ThresholdResult with analysis results
        """
        try:
            # Calculate threshold if not provided
            if threshold is None:
                threshold_value, baseline_value = self.calculate_baseline_threshold(fluo_values)
                baseline_points = [1, 2, 3]
            else:
                threshold_value = threshold
                baseline_value = None
                baseline_points = None
            
            # Find crossing point using specified method
            if method == "linear":
                crossing_time = self.find_crossing_point_linear_interpolation(
                    time_points, fluo_values, threshold_value)
            elif method == "spline":
                crossing_time = self.find_crossing_point_spline_interpolation(
                    time_points, fluo_values, threshold_value)
            else:
                return ThresholdResult(
                    success=False,
                    error_message=f"Unknown interpolation method: {method}"
                )
            
            # Calculate confidence interval if crossing found
            confidence_interval = None
            if crossing_time is not None:
                confidence_interval = self.calculate_confidence_interval(
                    time_points, fluo_values, crossing_time, threshold_value)
            
            success = crossing_time is not None
            
            return ThresholdResult(
                success=success,
                threshold_value=threshold_value,
                crossing_time=crossing_time,
                crossing_method=method,
                confidence_interval=confidence_interval,
                baseline_points=baseline_points,
                baseline_value=baseline_value,
                error_message=None if success else "No threshold crossing found"
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