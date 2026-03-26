"""
Integration tests for the complete analysis pipeline.

These tests validate the end-to-end workflow from raw data files
to final analysis results and exported outputs.
"""

import pytest
import numpy as np
import tempfile
import shutil
from pathlib import Path

from fluorescence_tool.algorithms.analysis_pipeline import (
    FluorescenceAnalysisPipeline, AnalysisConfiguration, PipelineResult
)
from fluorescence_tool.core.models import FileFormat


class TestAnalysisPipeline:
    """Test the complete analysis pipeline integration."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_data_dir = Path(__file__).parent.parent.parent.parent / "test_data"
        
        # Create pipeline with test configuration
        config = AnalysisConfiguration(
            curve_fitting_timeout=5,
            baseline_percentage=0.10,
            threshold_method="linear",
            export_individual_results=True,
            export_summary_report=True,
            export_statistical_analysis=True,
            output_directory=str(self.temp_dir)
        )
        self.pipeline = FluorescenceAnalysisPipeline(config)
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_file_format_detection(self):
        """Test automatic file format detection."""
        # Test BMG format detection
        bmg_file = self.test_data_dir / "RM5097.96HL.BNCT.1.CSV"
        if bmg_file.exists():
            format_detected = self.pipeline.detect_file_format(str(bmg_file))
            assert format_detected == FileFormat.BMG_OMEGA3
        
        # Test BioRad format detection
        biorad_file = self.test_data_dir / "TEST01.BIORAD.FORMAT.1.txt"
        if biorad_file.exists():
            format_detected = self.pipeline.detect_file_format(str(biorad_file))
            assert format_detected == FileFormat.BIORAD
    
    @pytest.mark.integration
    def test_bmg_complete_analysis_without_layout(self):
        """Test complete analysis pipeline with BMG data (no layout file)."""
        bmg_file = self.test_data_dir / "RM5097.96HL.BNCT.1.CSV"
        
        if not bmg_file.exists():
            pytest.skip("BMG test data not available")
        
        result = self.pipeline.analyze_complete_dataset(str(bmg_file))
        
        assert isinstance(result, PipelineResult)
        assert result.success is True
        assert result.fluorescence_data is not None
        assert result.total_wells_processed > 0
        assert result.successful_curve_fits >= 0
        assert result.successful_threshold_detections >= 0
        assert 0 <= result.overall_success_rate <= 100
        
        # Check that some wells were processed successfully
        assert len(result.curve_results) == result.total_wells_processed
        assert len(result.threshold_results) == result.total_wells_processed
        
        # Statistical analysis should be None without layout data
        assert result.statistical_results is None
    
    @pytest.mark.integration
    def test_bmg_complete_analysis_with_layout(self):
        """Test complete analysis pipeline with BMG data and layout file."""
        bmg_file = self.test_data_dir / "RM5097.96HL.BNCT.1.CSV"
        layout_file = self.test_data_dir / "RM5097_layout.csv"
        
        if not (bmg_file.exists() and layout_file.exists()):
            pytest.skip("BMG test data or layout file not available")
        
        result = self.pipeline.analyze_complete_dataset(str(bmg_file), str(layout_file))
        
        assert result.success is True
        assert result.layout_data is not None
        assert len(result.layout_data) > 0
        
        # Statistical analysis should be available with layout data
        assert result.statistical_results is not None
        assert result.statistical_results.success is True
        assert len(result.statistical_results.group_statistics) > 0
    
    @pytest.mark.integration
    def test_biorad_complete_analysis(self):
        """Test complete analysis pipeline with BioRad data."""
        biorad_file = self.test_data_dir / "TEST01.BIORAD.FORMAT.1.txt"
        layout_file = self.test_data_dir / "TEST01.BIORAD_layout.csv"
        
        if not biorad_file.exists():
            pytest.skip("BioRad test data not available")
        
        # Test with cycle time
        cycle_time = 1.0  # 1 minute cycles
        result = self.pipeline.analyze_complete_dataset(
            str(biorad_file), 
            str(layout_file) if layout_file.exists() else None,
            cycle_time_minutes=cycle_time
        )
        
        assert result.success is True
        assert result.fluorescence_data is not None
        assert result.fluorescence_data.format_type == FileFormat.BIORAD
        assert result.total_wells_processed > 0
    
    def test_export_functionality(self):
        """Test result export functionality."""
        # Create a mock successful result
        result = PipelineResult(success=True)
        result.total_wells_processed = 10
        result.successful_curve_fits = 8
        result.successful_threshold_detections = 7
        result.overall_success_rate = 80.0
        
        # Create mock fluorescence data
        from fluorescence_tool.core.models import FluorescenceData
        result.fluorescence_data = FluorescenceData(
            time_points=[0, 1, 2, 3, 4],
            wells=['A1', 'A2', 'B1'],
            measurements=np.random.rand(3, 5),
            metadata={},
            format_type=FileFormat.BMG_OMEGA3
        )
        
        # Create mock analysis results
        from fluorescence_tool.algorithms.curve_fitting import CurveFitResult
        from fluorescence_tool.algorithms.threshold_analysis import ThresholdResult
        
        for well_id in result.fluorescence_data.wells:
            result.curve_results[well_id] = CurveFitResult(
                success=True,
                parameters=[100, 0.5, 2, 10, 0.1],
                r_squared=0.95,
                baseline_fluorescence=50.0,
                final_fluorescence=200.0,
                fluorescence_change=150.0,
                percent_change=300.0
            )
            
            result.threshold_results[well_id] = ThresholdResult(
                success=True,
                threshold_value=55.0,
                crossing_time=2.5,
                baseline_value=50.0
            )
        
        # Export results
        exported_files = self.pipeline.export_results(result, str(self.temp_dir))
        
        assert len(exported_files) > 0
        
        # Check that files were created
        for file_path in exported_files:
            assert Path(file_path).exists()
            assert Path(file_path).stat().st_size > 0
    
    def test_run_complete_analysis_with_export(self):
        """Test the complete run_complete_analysis workflow."""
        bmg_file = self.test_data_dir / "RM5097.96HL.BNCT.1.CSV"
        
        if not bmg_file.exists():
            pytest.skip("BMG test data not available")
        
        result = self.pipeline.run_complete_analysis(
            str(bmg_file),
            output_directory=str(self.temp_dir)
        )
        
        assert result.success is True
        assert len(result.exported_files) > 0
        
        # Verify exported files exist
        for file_path in result.exported_files:
            assert Path(file_path).exists()
    
    def test_error_handling_invalid_file(self):
        """Test error handling with invalid input files."""
        # Test with non-existent file
        result = self.pipeline.analyze_complete_dataset("nonexistent_file.csv")
        
        assert result.success is False
        assert result.error_message is not None
        assert "failed" in result.error_message.lower()
    
    def test_error_handling_unsupported_format(self):
        """Test error handling with unsupported file format."""
        # Create a temporary file with unsupported content
        temp_file = self.temp_dir / "unsupported.txt"
        with open(temp_file, 'w') as f:
            f.write("This is not a supported fluorescence data format\n")
            f.write("Random content that doesn't match any parser\n")
        
        result = self.pipeline.analyze_complete_dataset(str(temp_file))
        
        assert result.success is False
        assert result.error_message is not None
    
    def test_biorad_missing_cycle_time(self):
        """Test error handling when cycle time is missing for BioRad files."""
        biorad_file = self.test_data_dir / "TEST01.BIORAD.FORMAT.1.txt"
        
        if not biorad_file.exists():
            pytest.skip("BioRad test data not available")
        
        # Try to analyze without providing cycle_time_minutes
        result = self.pipeline.analyze_complete_dataset(str(biorad_file))
        
        assert result.success is False
        assert "cycle_time_minutes" in result.error_message
    
    def test_configuration_customization(self):
        """Test pipeline with custom configuration."""
        custom_config = AnalysisConfiguration(
            curve_fitting_timeout=10,
            baseline_percentage=0.15,
            threshold_method="spline",
            export_individual_results=False,
            export_summary_report=True,
            export_statistical_analysis=False
        )
        
        custom_pipeline = FluorescenceAnalysisPipeline(custom_config)
        
        assert custom_pipeline.config.curve_fitting_timeout == 10
        assert custom_pipeline.config.baseline_percentage == 0.15
        assert custom_pipeline.config.threshold_method == "spline"
        assert custom_pipeline.threshold_analyzer.baseline_percentage == 0.15
    
    def test_statistical_analysis_integration(self):
        """Test integration of statistical analysis with group data."""
        bmg_file = self.test_data_dir / "RM5097.96HL.BNCT.1.CSV"
        layout_file = self.test_data_dir / "RM5097_layout.csv"
        
        if not (bmg_file.exists() and layout_file.exists()):
            pytest.skip("Test data not available")
        
        result = self.pipeline.analyze_complete_dataset(str(bmg_file), str(layout_file))
        
        if result.success and result.statistical_results:
            stats = result.statistical_results
            
            # Check that statistical analysis was performed
            assert stats.success is True
            assert len(stats.group_statistics) > 0
            assert stats.overall_statistics is not None
            
            # Check that group statistics contain expected data
            for group_name, group_stats in stats.group_statistics.items():
                assert group_stats.sample_count > 0
                assert 0 <= group_stats.success_rate <= 100
    
    def test_data_quality_metrics(self):
        """Test that quality metrics are properly calculated."""
        bmg_file = self.test_data_dir / "RM5097.96HL.BNCT.1.CSV"
        
        if not bmg_file.exists():
            pytest.skip("BMG test data not available")
        
        result = self.pipeline.analyze_complete_dataset(str(bmg_file))
        
        if result.success:
            # Check that quality metrics are reasonable
            assert 0 <= result.overall_success_rate <= 100
            assert result.successful_curve_fits <= result.total_wells_processed
            assert result.successful_threshold_detections <= result.total_wells_processed
            
            # Check individual well results have quality metrics
            for well_id, curve_result in result.curve_results.items():
                if curve_result.success:
                    assert curve_result.r_squared is not None
                    assert 0 <= curve_result.r_squared <= 1
                    
                    # Check fluorescence change metrics
                    assert curve_result.baseline_fluorescence is not None
                    assert curve_result.final_fluorescence is not None
                    assert curve_result.fluorescence_change is not None
                    assert curve_result.percent_change is not None
    
    def test_output_file_formats(self):
        """Test that output files are in correct formats."""
        bmg_file = self.test_data_dir / "RM5097.96HL.BNCT.1.CSV"
        
        if not bmg_file.exists():
            pytest.skip("BMG test data not available")
        
        result = self.pipeline.run_complete_analysis(
            str(bmg_file),
            output_directory=str(self.temp_dir)
        )
        
        if result.success and result.exported_files:
            for file_path in result.exported_files:
                file_path = Path(file_path)
                
                if file_path.suffix == '.csv':
                    # Check CSV format
                    import pandas as pd
                    df = pd.read_csv(file_path)
                    assert len(df) > 0
                    assert 'Well_ID' in df.columns
                
                elif file_path.suffix == '.json':
                    # Check JSON format
                    import json
                    with open(file_path) as f:
                        data = json.load(f)
                    assert isinstance(data, dict)
                
                elif file_path.suffix == '.txt':
                    # Check text format
                    with open(file_path) as f:
                        content = f.read()
                    assert len(content) > 0
                    assert "FLUORESCENCE" in content.upper()
    
    @pytest.mark.performance
    def test_pipeline_performance(self):
        """Test pipeline performance with timing."""
        import time
        
        bmg_file = self.test_data_dir / "RM5097.96HL.BNCT.1.CSV"
        
        if not bmg_file.exists():
            pytest.skip("BMG test data not available")
        
        start_time = time.time()
        result = self.pipeline.analyze_complete_dataset(str(bmg_file))
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        if result.success:
            # Performance should be reasonable (adjust threshold as needed)
            wells_per_second = result.total_wells_processed / processing_time
            assert wells_per_second > 0.1  # At least 0.1 wells per second
            
            print(f"Processed {result.total_wells_processed} wells in {processing_time:.2f} seconds")
            print(f"Rate: {wells_per_second:.2f} wells/second")