"""
Unit tests for BioRad format parser.

Tests use real data from test_data/TEST01.BIORAD.FORMAT.1.txt
Following TDD methodology - these tests should initially fail.
"""

import pytest
import numpy as np
from pathlib import Path
from fluorescence_tool.parsers.biorad_parser import BioRadParser
from fluorescence_tool.core.models import FluorescenceData, FileFormat


class TestBioRadParser:
    """Test BioRad format parser with real data."""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return BioRadParser()
    
    @pytest.fixture
    def test_file_path(self):
        """Path to real BioRad test data file."""
        return Path("test_data/TEST01.BIORAD.FORMAT.1.txt")
    
    def test_parser_creation(self, parser):
        """Test parser can be created."""
        assert isinstance(parser, BioRadParser)
    
    def test_parse_real_biorad_file(self, parser, test_file_path):
        """Test parsing real BioRad file with cycle time."""
        cycle_time_minutes = 15.0  # 15 minutes per cycle
        result = parser.parse_file(str(test_file_path), cycle_time_minutes)
        
        # Verify result type
        assert isinstance(result, FluorescenceData)
        assert result.format_type == FileFormat.BIORAD
        
        # Verify basic structure
        assert len(result.wells) > 0
        assert len(result.time_points) > 0
        assert result.measurements.shape[0] == len(result.wells)
        assert result.measurements.shape[1] == len(result.time_points)
    
    def test_cycle_time_conversion(self, parser, test_file_path):
        """Test cycle time to hours conversion."""
        cycle_time_minutes = 15.0
        result = parser.parse_file(str(test_file_path), cycle_time_minutes)
        
        # First few time points should be: 0, 0.25, 0.5, 0.75 hours
        expected_times = [0.0, 0.25, 0.5, 0.75, 1.0]
        
        assert len(result.time_points) >= 5
        for i, expected in enumerate(expected_times):
            assert abs(result.time_points[i] - expected) < 0.01
    
    def test_well_identification_384_format(self, parser, test_file_path):
        """Test well identification for 384-well format."""
        result = parser.parse_file(str(test_file_path), 15.0)
        
        # Should detect 384-well format (A1-P24)
        assert "A1" in result.wells
        assert "A24" in result.wells
        assert "P1" in result.wells
        assert "P24" in result.wells
        
        # Should have correct plate format in metadata
        assert result.metadata["plate_format"] == "384-well"
    
    def test_fluorescence_values_biorad(self, parser, test_file_path):
        """Test fluorescence value extraction from BioRad format."""
        result = parser.parse_file(str(test_file_path), 15.0)
        
        # All measurements should be positive numbers
        assert np.all(result.measurements >= 0)
        
        # Should have reasonable fluorescence values
        assert np.all(result.measurements < 10000)
        assert np.all(result.measurements > 100)
        
        # No NaN or infinite values
        assert np.all(np.isfinite(result.measurements))
    
    def test_metadata_extraction_biorad(self, parser, test_file_path):
        """Test metadata extraction for BioRad format."""
        cycle_time = 15.0
        result = parser.parse_file(str(test_file_path), cycle_time)
        
        # Should store cycle time in metadata
        assert result.metadata["cycle_time_minutes"] == cycle_time
        
        # Should detect number of cycles
        assert "num_cycles" in result.metadata
        assert result.metadata["num_cycles"] > 0
        
        # Should detect plate format
        assert "plate_format" in result.metadata
    
    def test_different_cycle_times(self, parser, test_file_path):
        """Test parsing with different cycle times."""
        cycle_times = [10.0, 15.0, 20.0, 30.0]
        
        for cycle_time in cycle_times:
            result = parser.parse_file(str(test_file_path), cycle_time)
            
            # Time points should scale with cycle time
            expected_second_time = cycle_time / 60.0  # Convert to hours
            assert abs(result.time_points[1] - expected_second_time) < 0.01
    
    def test_invalid_cycle_time(self, parser, test_file_path):
        """Test handling of invalid cycle times."""
        with pytest.raises(ValueError):
            parser.parse_file(str(test_file_path), 0.0)  # Zero cycle time
        
        with pytest.raises(ValueError):
            parser.parse_file(str(test_file_path), -5.0)  # Negative cycle time
    
    def test_file_validation_biorad(self, parser):
        """Test file validation for non-existent files."""
        with pytest.raises(FileNotFoundError):
            parser.parse_file("nonexistent_biorad.txt", 15.0)
    
    def test_invalid_biorad_format(self, parser, tmp_path):
        """Test handling of invalid BioRad file format."""
        # Create a file without 'Cycle' column
        invalid_file = tmp_path / "invalid_biorad.txt"
        invalid_file.write_text("A1\tA2\tA3\n1\t2\t3\n")
        
        with pytest.raises(ValueError, match="missing 'Cycle' column"):
            parser.parse_file(str(invalid_file), 15.0)
    
    def test_plate_format_detection(self, parser):
        """Test automatic plate format detection."""
        # Test 96-well detection
        wells_96 = ["A1", "A12", "H1", "H12"]
        format_96 = parser._detect_plate_format(wells_96)
        assert format_96 == "96-well"
        
        # Test 384-well detection
        wells_384 = ["A1", "A24", "P1", "P24"]
        format_384 = parser._detect_plate_format(wells_384)
        assert format_384 == "384-well"
        
        # Test unknown format
        wells_unknown = ["A1", "Z50"]
        format_unknown = parser._detect_plate_format(wells_unknown)
        assert format_unknown == "unknown"
    
    def test_data_consistency_biorad(self, parser, test_file_path):
        """Test that parsed BioRad data maintains consistency."""
        result = parser.parse_file(str(test_file_path), 15.0)
        
        # Each well should have measurements for all time points
        for i, well in enumerate(result.wells):
            well_measurements = result.measurements[i]
            assert len(well_measurements) == len(result.time_points)
            
            # All measurements should be finite
            assert np.all(np.isfinite(well_measurements))
            
            # Should have some variation (not all identical values)
            if len(well_measurements) > 1:
                assert np.std(well_measurements) > 0