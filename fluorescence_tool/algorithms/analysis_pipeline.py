"""
Integrated analysis pipeline for fluorescence data.

This module provides a complete analysis workflow that combines:
- Data parsing (BMG Omega3, BioRad, Layout files)
- Curve fitting with 5-parameter sigmoid functions
- Threshold detection and crossing point analysis
- Statistical analysis with group-based calculations
- Results export and reporting
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json
import csv

from fluorescence_tool.core.models import FluorescenceData, WellInfo, FileFormat
from fluorescence_tool.parsers.bmg_parser import BMGOmega3Parser
from fluorescence_tool.parsers.biorad_parser import BioRadParser
from fluorescence_tool.parsers.layout_parser import LayoutParser
from fluorescence_tool.algorithms.curve_fitting import CurveFitter, CurveFitResult
from fluorescence_tool.algorithms.threshold_analysis import ThresholdAnalyzer, ThresholdResult
from fluorescence_tool.algorithms.statistical_analysis import StatisticalAnalyzer, StatisticalResult


@dataclass
class AnalysisConfiguration:
    """Configuration for analysis pipeline."""
    
    # Curve fitting parameters
    curve_fitting_timeout: int = 2
    
    # Crossing point analysis parameters
    baseline_percentage: float = 0.10  # Only used for legacy methods
    threshold_method: str = "qc_second_derivative"  # "qc_second_derivative", "linear", or "spline"
    
    # Output configuration
    export_individual_results: bool = True
    export_summary_report: bool = True
    export_statistical_analysis: bool = True
    
    # File paths
    output_directory: Optional[str] = None


@dataclass
class PipelineResult:
    """Complete analysis pipeline results."""
    success: bool
    
    # Input data
    fluorescence_data: Optional[FluorescenceData] = None
    layout_data: Optional[List[WellInfo]] = None
    
    # Analysis results
    curve_results: Dict[str, CurveFitResult] = field(default_factory=dict)
    threshold_results: Dict[str, ThresholdResult] = field(default_factory=dict)
    statistical_results: Optional[StatisticalResult] = None
    
    # Summary metrics
    total_wells_processed: int = 0
    successful_curve_fits: int = 0
    successful_threshold_detections: int = 0
    overall_success_rate: float = 0.0
    
    # Export paths
    exported_files: List[str] = field(default_factory=list)
    
    # Error information
    error_message: Optional[str] = None
    processing_warnings: List[str] = field(default_factory=list)


class FluorescenceAnalysisPipeline:
    """
    Complete fluorescence data analysis pipeline.
    
    Integrates all analysis components into a single, easy-to-use workflow
    that processes fluorescence data from raw files to final statistical results.
    """
    
    def __init__(self, config: Optional[AnalysisConfiguration] = None):
        """
        Initialize analysis pipeline.
        
        Args:
            config: Analysis configuration (uses defaults if None)
        """
        self.config = config or AnalysisConfiguration()
        
        # Initialize analysis components
        self.curve_fitter = CurveFitter(timeout_seconds=self.config.curve_fitting_timeout)
        self.threshold_analyzer = ThresholdAnalyzer(baseline_percentage=self.config.baseline_percentage)
        self.statistical_analyzer = StatisticalAnalyzer()
        
        # Initialize parsers
        self.bmg_parser = BMGOmega3Parser()
        self.biorad_parser = BioRadParser()
        self.layout_parser = LayoutParser()
    
    def detect_file_format(self, file_path: str) -> FileFormat:
        """
        Detect the format of a fluorescence data file.
        
        Args:
            file_path: Path to the data file
            
        Returns:
            Detected file format
        """
        file_path = Path(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                first_lines = [f.readline().strip() for _ in range(5)]
            
            # Check for BMG Omega3 format
            if any('Time [s]' in line or 'Cycle Nr.' in line for line in first_lines):
                return FileFormat.BMG_OMEGA3
            
            # Check for BioRad format (tab-separated with specific headers)
            if any('\t' in line and ('Well' in line or 'Cycle' in line) for line in first_lines):
                return FileFormat.BIORAD
            
            return FileFormat.UNKNOWN
        
        except Exception:
            return FileFormat.UNKNOWN
    
    def parse_fluorescence_data(self, file_path: str, cycle_time_minutes: Optional[float] = None) -> FluorescenceData:
        """
        Parse fluorescence data file based on detected format.
        
        Args:
            file_path: Path to the fluorescence data file
            cycle_time_minutes: Cycle time for BioRad files (required for BioRad format)
            
        Returns:
            Parsed fluorescence data
            
        Raises:
            ValueError: If file format is unsupported or parsing fails
        """
        file_format = self.detect_file_format(file_path)
        
        if file_format == FileFormat.BMG_OMEGA3:
            return self.bmg_parser.parse_file(file_path)
        elif file_format == FileFormat.BIORAD:
            if cycle_time_minutes is None:
                raise ValueError("cycle_time_minutes is required for BioRad format files")
            return self.biorad_parser.parse_file(file_path, cycle_time_minutes)
        else:
            raise ValueError(f"Unsupported file format detected for {file_path}")
    
    def parse_layout_data(self, layout_file_path: str) -> List[WellInfo]:
        """
        Parse layout file to get well information.
        
        Args:
            layout_file_path: Path to the layout CSV file
            
        Returns:
            List of well information objects
        """
        layout_data = self.layout_parser.parse_file(layout_file_path)
        return layout_data.wells
    
    def process_well_data(self, fluorescence_data: FluorescenceData, well_index: int) -> Tuple[Optional[CurveFitResult], Optional[ThresholdResult]]:
        """
        Process a single well's fluorescence data.
        
        Args:
            fluorescence_data: Parsed fluorescence data
            well_index: Index of the well to process
            
        Returns:
            Tuple of (curve_fit_result, threshold_result)
        """
        try:
            # Extract time points and fluorescence values for this well
            time_points = np.array(fluorescence_data.time_points)
            fluo_values = fluorescence_data.measurements[well_index, :]
            
            # Perform curve fitting
            curve_result = self.curve_fitter.fit_curve(time_points, fluo_values)
            
            # Perform crossing point analysis
            threshold_result = self.threshold_analyzer.analyze_threshold_crossing(
                time_points, fluo_values, method=self.config.threshold_method)
            
            return curve_result, threshold_result
        
        except Exception as e:
            # Return failed results with error information
            curve_result = CurveFitResult(success=False, error_message=f"Curve fitting failed: {e}")
            threshold_result = ThresholdResult(success=False, error_message=f"Threshold analysis failed: {e}")
            return curve_result, threshold_result
    
    def analyze_complete_dataset(self, fluorescence_file: str, layout_file: Optional[str] = None, 
                                cycle_time_minutes: Optional[float] = None) -> PipelineResult:
        """
        Perform complete analysis on a fluorescence dataset.
        
        Args:
            fluorescence_file: Path to fluorescence data file
            layout_file: Path to layout file (optional)
            cycle_time_minutes: Cycle time for BioRad files
            
        Returns:
            Complete pipeline results
        """
        result = PipelineResult(success=False)
        
        try:
            # Parse fluorescence data
            result.fluorescence_data = self.parse_fluorescence_data(fluorescence_file, cycle_time_minutes)
            
            # Parse layout data if provided
            if layout_file:
                result.layout_data = self.parse_layout_data(layout_file)
            
            # Process each well
            result.total_wells_processed = len(result.fluorescence_data.wells)
            
            for i, well_id in enumerate(result.fluorescence_data.wells):
                curve_result, threshold_result = self.process_well_data(result.fluorescence_data, i)
                
                result.curve_results[well_id] = curve_result
                result.threshold_results[well_id] = threshold_result
                
                if curve_result.success:
                    result.successful_curve_fits += 1
                
                if threshold_result.success:
                    result.successful_threshold_detections += 1
            
            # Calculate overall success rate
            result.overall_success_rate = (result.successful_curve_fits / result.total_wells_processed * 100) if result.total_wells_processed > 0 else 0.0
            
            # Perform statistical analysis if layout data is available
            if result.layout_data:
                result.statistical_results = self.statistical_analyzer.analyze_complete_dataset(
                    result.layout_data, result.curve_results, result.threshold_results)
            
            result.success = True
            
        except Exception as e:
            result.error_message = f"Pipeline analysis failed: {e}"
            result.success = False
        
        return result
    
    def export_results(self, result: PipelineResult, output_directory: Optional[str] = None) -> List[str]:
        """
        Export analysis results to files.
        
        Args:
            result: Pipeline results to export
            output_directory: Directory to save files (uses config if None)
            
        Returns:
            List of exported file paths
        """
        if not result.success:
            return []
        
        output_dir = Path(output_directory or self.config.output_directory or "output")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        exported_files = []
        
        try:
            # Export individual well results
            if self.config.export_individual_results:
                individual_file = output_dir / "individual_well_results.csv"
                self._export_individual_results(result, individual_file)
                exported_files.append(str(individual_file))
            
            # Export summary report
            if self.config.export_summary_report:
                summary_file = output_dir / "analysis_summary.txt"
                self._export_summary_report(result, summary_file)
                exported_files.append(str(summary_file))
            
            # Export statistical analysis
            if self.config.export_statistical_analysis and result.statistical_results:
                stats_file = output_dir / "statistical_analysis.txt"
                self._export_statistical_analysis(result, stats_file)
                exported_files.append(str(stats_file))
                
                # Export group statistics as JSON
                json_file = output_dir / "group_statistics.json"
                self._export_group_statistics_json(result, json_file)
                exported_files.append(str(json_file))
        
        except Exception as e:
            result.processing_warnings.append(f"Export failed: {e}")
        
        return exported_files
    
    def _export_individual_results(self, result: PipelineResult, file_path: Path):
        """Export individual well results to CSV."""
        rows = []
        
        for well_id in result.fluorescence_data.wells:
            curve_result = result.curve_results.get(well_id)
            threshold_result = result.threshold_results.get(well_id)
            
            row = {
                'Well_ID': well_id,
                'Curve_Fit_Success': curve_result.success if curve_result else False,
                'R_Squared': curve_result.r_squared if curve_result and curve_result.success else None,
                'Baseline_Fluorescence': curve_result.baseline_fluorescence if curve_result and curve_result.success else None,
                'Final_Fluorescence': curve_result.final_fluorescence if curve_result and curve_result.success else None,
                'Fluorescence_Change': curve_result.fluorescence_change if curve_result and curve_result.success else None,
                'Percent_Change': curve_result.percent_change if curve_result and curve_result.success else None,
                'Threshold_Success': threshold_result.success if threshold_result else False,
                'Crossing_Time': threshold_result.crossing_time if threshold_result and threshold_result.success else None,
                'Threshold_Value': threshold_result.threshold_value if threshold_result and threshold_result.success else None,
                'Baseline_Value': threshold_result.baseline_value if threshold_result and threshold_result.success else None
            }
            
            # Add curve parameters if available
            if curve_result and curve_result.success and curve_result.parameters:
                for i, param in enumerate(curve_result.parameters):
                    row[f'Curve_Param_{chr(97+i)}'] = param  # a, b, c, d, e
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        df.to_csv(file_path, index=False)
    
    def _export_summary_report(self, result: PipelineResult, file_path: Path):
        """Export summary report to text file."""
        lines = []
        lines.append("FLUORESCENCE ANALYSIS PIPELINE SUMMARY")
        lines.append("=" * 50)
        lines.append("")
        lines.append(f"Total wells processed: {result.total_wells_processed}")
        lines.append(f"Successful curve fits: {result.successful_curve_fits}")
        lines.append(f"Successful threshold detections: {result.successful_threshold_detections}")
        lines.append(f"Overall success rate: {result.overall_success_rate:.1f}%")
        lines.append("")
        
        if result.processing_warnings:
            lines.append("WARNINGS:")
            for warning in result.processing_warnings:
                lines.append(f"- {warning}")
            lines.append("")
        
        # Add file information
        if result.fluorescence_data:
            lines.append("DATA FILE INFORMATION:")
            lines.append(f"File format: {result.fluorescence_data.format_type.value}")
            lines.append(f"Number of wells: {len(result.fluorescence_data.wells)}")
            lines.append(f"Number of time points: {len(result.fluorescence_data.time_points)}")
            lines.append(f"Time range: {min(result.fluorescence_data.time_points):.1f} - {max(result.fluorescence_data.time_points):.1f} hours")
        
        with open(file_path, 'w') as f:
            f.write('\n'.join(lines))
    
    def _export_statistical_analysis(self, result: PipelineResult, file_path: Path):
        """Export statistical analysis report."""
        if result.statistical_results:
            report = self.statistical_analyzer.generate_summary_report(result.statistical_results)
            with open(file_path, 'w') as f:
                f.write(report)
    
    def _export_group_statistics_json(self, result: PipelineResult, file_path: Path):
        """Export group statistics as JSON for programmatic access."""
        if not result.statistical_results:
            return
        
        # Convert group statistics to JSON-serializable format
        json_data = {
            'overall_statistics': {
                'sample_count': result.statistical_results.overall_statistics.sample_count,
                'successful_fits': result.statistical_results.overall_statistics.successful_fits,
                'success_rate': result.statistical_results.overall_statistics.success_rate,
                'crossing_time_mean': result.statistical_results.overall_statistics.crossing_time_mean,
                'crossing_time_std': result.statistical_results.overall_statistics.crossing_time_std,
                'crossing_time_cv': result.statistical_results.overall_statistics.crossing_time_cv,
                'fluorescence_change_mean': result.statistical_results.overall_statistics.fluor_change_mean,
                'fluorescence_change_std': result.statistical_results.overall_statistics.fluor_change_std,
                'r_squared_mean': result.statistical_results.overall_statistics.r_squared_mean
            },
            'group_statistics': {},
            'group_comparisons': result.statistical_results.group_comparisons
        }
        
        for group_name, stats in result.statistical_results.group_statistics.items():
            json_data['group_statistics'][group_name] = {
                'sample_count': stats.sample_count,
                'successful_fits': stats.successful_fits,
                'success_rate': stats.success_rate,
                'crossing_time_mean': stats.crossing_time_mean,
                'crossing_time_std': stats.crossing_time_std,
                'crossing_time_cv': stats.crossing_time_cv,
                'fluorescence_change_mean': stats.fluor_change_mean,
                'fluorescence_change_std': stats.fluor_change_std,
                'r_squared_mean': stats.r_squared_mean
            }
        
        with open(file_path, 'w') as f:
            json.dump(json_data, f, indent=2, default=str)
    
    def run_complete_analysis(self, fluorescence_file: str, layout_file: Optional[str] = None,
                            cycle_time_minutes: Optional[float] = None,
                            output_directory: Optional[str] = None) -> PipelineResult:
        """
        Run complete analysis pipeline from files to exported results.
        
        Args:
            fluorescence_file: Path to fluorescence data file
            layout_file: Path to layout file (optional)
            cycle_time_minutes: Cycle time for BioRad files
            output_directory: Directory to save results
            
        Returns:
            Complete pipeline results with exported files
        """
        # Perform analysis
        result = self.analyze_complete_dataset(fluorescence_file, layout_file, cycle_time_minutes)
        
        # Export results if analysis was successful
        if result.success:
            exported_files = self.export_results(result, output_directory)
            result.exported_files = exported_files
        
        return result