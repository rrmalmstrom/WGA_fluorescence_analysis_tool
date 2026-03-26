"""
Pass/fail analysis module for fluorescence data.

This module provides functionality to evaluate analysis results against
user-defined thresholds to determine pass/fail status for each well.
"""

from typing import Dict, List, Optional, Any
from ..core.models import PassFailThresholds, PassFailResult


class PassFailAnalyzer:
    """
    Analyzer for determining pass/fail status based on threshold criteria.
    
    Evaluates crossing point (CP) and fluorescence change values against
    user-defined thresholds to determine whether wells pass or fail.
    """
    
    def __init__(self, thresholds: Optional[PassFailThresholds] = None):
        """
        Initialize the pass/fail analyzer.
        
        Args:
            thresholds: Pass/fail threshold criteria (uses defaults if None)
        """
        self.thresholds = thresholds or PassFailThresholds()
    
    def update_thresholds(self, thresholds: PassFailThresholds):
        """Update the threshold criteria."""
        self.thresholds = thresholds
    
    def analyze_well(self, well_id: str, analysis_results: Dict[str, Any]) -> PassFailResult:
        """
        Analyze a single well for pass/fail status.
        
        Args:
            well_id: Well identifier
            analysis_results: Analysis results containing curve_fits data
            
        Returns:
            PassFailResult with pass/fail determination
        """
        if not self.thresholds.enabled:
            # If pass/fail analysis is disabled, return neutral result
            return PassFailResult(
                well_id=well_id,
                passed=False,
                cp_value=None,
                fluorescence_change_value=None,
                cp_passed=False,
                fluorescence_change_passed=False,
                analysis_available=False,
                failure_reason="Pass/fail analysis disabled"
            )
        
        # Check if analysis results are available for this well
        if 'curve_fits' not in analysis_results or well_id not in analysis_results['curve_fits']:
            return PassFailResult(
                well_id=well_id,
                passed=False,
                cp_value=None,
                fluorescence_change_value=None,
                cp_passed=False,
                fluorescence_change_passed=False,
                analysis_available=False,
                failure_reason="No analysis results available"
            )
        
        well_results = analysis_results['curve_fits'][well_id]
        
        # Extract CP value from threshold analysis
        cp_value = None
        if well_results.get('crossing_point') is not None:
            cp_value = well_results['crossing_point']
        
        # Extract fluorescence change from curve fitting
        fluorescence_change_value = None
        curve_result = well_results.get('curve_result')
        if curve_result and hasattr(curve_result, 'fluorescence_change'):
            fluorescence_change_value = curve_result.fluorescence_change
        
        # Check if we have the required values
        if cp_value is None and fluorescence_change_value is None:
            return PassFailResult(
                well_id=well_id,
                passed=False,
                cp_value=cp_value,
                fluorescence_change_value=fluorescence_change_value,
                cp_passed=False,
                fluorescence_change_passed=False,
                analysis_available=False,
                failure_reason="No CP or fluorescence change values available"
            )
        
        # Evaluate pass/fail criteria
        cp_passed = False
        fluorescence_change_passed = False
        failure_reasons = []
        
        # CP criterion: CP < threshold = PASS
        if cp_value is not None:
            cp_passed = cp_value < self.thresholds.cp_threshold
            if not cp_passed:
                failure_reasons.append(f"CP {cp_value:.1f} >= {self.thresholds.cp_threshold}")
        else:
            failure_reasons.append("No CP value available")
        
        # Fluorescence change criterion: change > threshold = PASS
        if fluorescence_change_value is not None:
            fluorescence_change_passed = fluorescence_change_value > self.thresholds.fluorescence_change_threshold
            if not fluorescence_change_passed:
                failure_reasons.append(f"Fluorescence change {fluorescence_change_value:.1f} <= {self.thresholds.fluorescence_change_threshold}")
        else:
            failure_reasons.append("No fluorescence change value available")
        
        # Overall pass: BOTH criteria must be met
        overall_passed = cp_passed and fluorescence_change_passed
        
        # Determine failure reason
        failure_reason = None
        if not overall_passed:
            if failure_reasons:
                failure_reason = "; ".join(failure_reasons)
            else:
                failure_reason = "Unknown failure"
        
        return PassFailResult(
            well_id=well_id,
            passed=overall_passed,
            cp_value=cp_value,
            fluorescence_change_value=fluorescence_change_value,
            cp_passed=cp_passed,
            fluorescence_change_passed=fluorescence_change_passed,
            analysis_available=True,
            failure_reason=failure_reason
        )
    
    def analyze_all_wells(self, analysis_results: Dict[str, Any]) -> Dict[str, PassFailResult]:
        """
        Analyze all wells for pass/fail status.
        
        Args:
            analysis_results: Complete analysis results
            
        Returns:
            Dictionary mapping well IDs to PassFailResult objects
        """
        pass_fail_results = {}
        
        if 'curve_fits' not in analysis_results:
            return pass_fail_results
        
        for well_id in analysis_results['curve_fits'].keys():
            pass_fail_results[well_id] = self.analyze_well(well_id, analysis_results)
        
        return pass_fail_results
    
    def get_summary_statistics(self, pass_fail_results: Dict[str, PassFailResult]) -> Dict[str, Any]:
        """
        Generate summary statistics for pass/fail results.
        
        Args:
            pass_fail_results: Dictionary of pass/fail results
            
        Returns:
            Dictionary with summary statistics
        """
        total_wells = len(pass_fail_results)
        analyzed_wells = sum(1 for result in pass_fail_results.values() if result.analysis_available)
        passed_wells = sum(1 for result in pass_fail_results.values() if result.passed)
        failed_wells = analyzed_wells - passed_wells
        
        pass_rate = (passed_wells / analyzed_wells * 100) if analyzed_wells > 0 else 0.0
        
        return {
            'total_wells': total_wells,
            'analyzed_wells': analyzed_wells,
            'passed_wells': passed_wells,
            'failed_wells': failed_wells,
            'pass_rate': pass_rate,
            'cp_threshold': self.thresholds.cp_threshold,
            'fluorescence_change_threshold': self.thresholds.fluorescence_change_threshold
        }