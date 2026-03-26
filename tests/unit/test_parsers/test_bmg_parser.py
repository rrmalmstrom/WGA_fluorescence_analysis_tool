"""
Unit tests for BMG Omega3 format parser.

Tests use real data from test_data/RM5097.96HL.BNCT.1.CSV
Following TDD methodology - these tests should initially fail.
"""

import pytest
import numpy as np
from pathlib import Path
from fluorescence_tool.parsers.bmg_parser import BMGOmega3Parser
from fluorescence_tool.core.models import FluorescenceData, FileFormat


class TestBMGOmega3Parser:
    """Test BMG Omega3 format parser with real data."""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return BMGOmega3Parser()
    
    @pytest.fixture
    def test_file_path(self):
        """Path to real BMG test data file."""
        return Path("test_data/RM5097.96HL.BNCT.1.CSV")
    
    def test_parser_creation(self, parser):
        """Test parser can be created."""
        assert isinstance(parser, BMGOmega3Parser)
    
    def test_parse_real_bmg_file(self, parser, test_file_path):
        """Test parsing real BMG Omega3 file."""
        result = parser.parse_file(str(test_file_path))
        
        # Verify result type
        assert isinstance(result, FluorescenceData)
        assert result.format_type == FileFormat.BMG_OMEGA3
        
        # Verify basic structure
        assert len(result.wells) > 0
        assert len(result.time_points) > 0
        assert result.measurements.shape[0] == len(result.wells)
        assert result.measurements.shape[1] == len(result.time_points)
    
    def test_parse_time_headers(self, parser, test_file_path):
        """Test time header parsing from real data."""
        result = parser.parse_file(str(test_file_path))
        
        # Based on real file: "0 h", "0 h 15 min", "0 h 30 min", etc.
        expected_first_times = [0.0, 0.25, 0.5, 0.75, 1.0]
        
        assert len(result.time_points) >= 5
        for i, expected in enumerate(expected_first_times):
            assert abs(result.time_points[i] - expected) < 0.01
    
    def test_parse_well_identifiers(self, parser, test_file_path):
        """Test well identifier extraction."""
        result = parser.parse_file(str(test_file_path))
        
        # Should have wells like A1, A2, A3, etc.
        assert "A1" in result.wells
        assert "A2" in result.wells
        assert "B1" in result.wells
        
        # Wells should be in expected format
        for well in result.wells[:10]:  # Check first 10
            assert len(well) >= 2
            assert well[0].isalpha()  # Row letter
            assert well[1:].isdigit()  # Column number
    
    def test_parse_metadata_extraction(self, parser, test_file_path):
        """Test metadata extraction from headers."""
        result = parser.parse_file(str(test_file_path))
        
        # Should extract metadata from header rows
        assert "plate_id" in result.metadata
        assert result.metadata["plate_id"] == "RM5097.96HL.BNCT.1"
        
        # Should have test name
        assert "test_name" in result.metadata
        assert result.metadata["test_name"] == "WGAXProduction"
    
    def test_parse_fluorescence_values(self, parser, test_file_path):
        """Test fluorescence value extraction and validation."""
        result = parser.parse_file(str(test_file_path))
        
        # All measurements should be positive numbers
        assert np.all(result.measurements >= 0)
        
        # Should have reasonable fluorescence values (typically 1000-5000 range for this data)
        assert np.all(result.measurements < 10000)
        assert np.all(result.measurements > 100)
        
        # No NaN or infinite values
        assert np.all(np.isfinite(result.measurements))
    
    def test_time_string_parsing(self, parser):
        """Test individual time string parsing methods."""
        # Test various time formats from BMG files
        assert parser._parse_time_string("0 h") == 0.0
        assert parser._parse_time_string("1 h") == 1.0
        assert parser._parse_time_string("0 h 15 min") == 0.25
        assert parser._parse_time_string("0 h 30 min") == 0.5
        assert parser._parse_time_string("1 h 45 min") == 1.75
        assert parser._parse_time_string("2 h 30 min") == 2.5
        
        # Test minutes-only format
        assert parser._parse_time_string("15 min") == 0.25
        assert parser._parse_time_string("30 min") == 0.5
        assert parser._parse_time_string("90 min") == 1.5
    
    def test_time_string_parsing_edge_cases(self, parser):
        """Test edge cases in time string parsing."""
        # Invalid formats should raise ValueError
        with pytest.raises(ValueError):
            parser._parse_time_string("invalid")
        
        with pytest.raises(ValueError):
            parser._parse_time_string("1 h 60 min")  # Invalid minutes
        
        with pytest.raises(ValueError):
            parser._parse_time_string("")
    
    def test_file_validation(self, parser):
        """Test file validation for non-existent files."""
        with pytest.raises(FileNotFoundError):
            parser.parse_file("nonexistent_file.csv")
    
    def test_invalid_file_format(self, parser, tmp_path):
        """Test handling of invalid file format."""
        # Create a file with wrong format
        invalid_file = tmp_path / "invalid.csv"
        invalid_file.write_text("This is not a BMG file\nInvalid format")
        
        with pytest.raises(Exception):  # Should raise some parsing error
            parser.parse_file(str(invalid_file))
    
    def test_data_consistency_validation(self, parser, test_file_path):
        """Test that parsed data maintains consistency."""
        result = parser.parse_file(str(test_file_path))
        
        # Each well should have measurements for all time points
        for i, well in enumerate(result.wells):
            well_measurements = result.measurements[i]
            assert len(well_measurements) == len(result.time_points)
            
            # Measurements should be reasonable (no extreme outliers)
            mean_val = np.mean(well_measurements)
            std_val = np.std(well_measurements)
            
            # No values should be more than 10 standard deviations from mean
            # (this catches obvious parsing errors)
            assert np.all(np.abs(well_measurements - mean_val) < 10 * std_val)