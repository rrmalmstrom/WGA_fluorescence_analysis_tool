"""
Analysis algorithms for fluorescence data processing.

This module provides core analysis functionality including:
- Curve fitting with 5-parameter sigmoid functions
- Threshold detection and crossing point analysis
- Statistical analysis and quality metrics
"""

from .curve_fitting import CurveFitter, CurveFitResult
from .threshold_analysis import ThresholdAnalyzer, ThresholdResult
from .statistical_analysis import StatisticalAnalyzer, StatisticalResult, GroupStatistics
from .analysis_pipeline import FluorescenceAnalysisPipeline, AnalysisConfiguration, PipelineResult

__all__ = [
    'CurveFitter',
    'CurveFitResult',
    'ThresholdAnalyzer',
    'ThresholdResult',
    'StatisticalAnalyzer',
    'StatisticalResult',
    'GroupStatistics',
    'FluorescenceAnalysisPipeline',
    'AnalysisConfiguration',
    'PipelineResult'
]