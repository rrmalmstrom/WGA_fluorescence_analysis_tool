"""
Unit tests for Layout file parser.

Tests use real data from test_data/RM5097_layout.csv
Following TDD methodology - these tests should initially fail.
"""

import pytest
from pathlib import Path
from fluorescence_tool.parsers.layout_parser import LayoutParser
from fluorescence_tool.core.models import WellInfo


class TestLayoutParser:
    """Test Layout file parser with real data."""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return LayoutParser()
    
    @pytest.fixture
    def test_file_path(self):
        """Path to real layout test data file."""
        return Path("test_data/RM5097_layout.csv")
    
    def test_parser_creation(self, parser):
        """Test parser can be created."""
        assert isinstance(parser, LayoutParser)
    
    def test_parse_real_layout_file(self, parser, test_file_path):
        """Test parsing real layout file."""
        result = parser.parse_file(str(test_file_path))
        
        # Should return dictionary of well info
        assert isinstance(result, dict)
        assert len(result) > 0
        
        # All values should be WellInfo objects
        for well_id, well_info in result.items():
            assert isinstance(well_info, WellInfo)
            assert well_info.well_id == well_id
    
    def test_required_columns_validation(self, parser, test_file_path):
        """Test that required columns are present."""
        result = parser.parse_file(str(test_file_path))
        
        # Should have wells with required fields
        for well_info in result.values():
            assert well_info.plate_id  # Should not be empty
            assert well_info.well_type  # Should not be empty
            assert well_info.well_id  # Should not be empty
    
    def test_well_types_parsing(self, parser, test_file_path):
        """Test parsing of different well types."""
        result = parser.parse_file(str(test_file_path))
        
        # Should have different well types
        well_types = {info.well_type for info in result.values()}
        expected_types = {'unused', 'sample', 'neg_cntrl'}
        
        # Should contain expected well types
        assert len(well_types.intersection(expected_types)) > 0
    
    def test_plate_id_consistency(self, parser, test_file_path):
        """Test that plate ID is consistent."""
        result = parser.parse_file(str(test_file_path))
        
        # All wells should have the same plate ID
        plate_ids = {info.plate_id for info in result.values()}
        assert len(plate_ids) == 1
        
        # Should match expected plate ID from test data
        expected_plate_id = "RM5097.96HL.BNCT.1"
        assert expected_plate_id in plate_ids
    
    def test_optional_fields_handling(self, parser, test_file_path):
        """Test handling of optional fields."""
        result = parser.parse_file(str(test_file_path))
        
        # Some wells should have optional fields, others should not
        has_cell_count = any(info.cell_count is not None for info in result.values())
        has_groups = any(info.group_1 is not None for info in result.values())
        
        # At least some wells should have these optional fields
        assert has_cell_count or has_groups
    
    def test_cell_count_parsing(self, parser, test_file_path):
        """Test cell count parsing and validation."""
        result = parser.parse_file(str(test_file_path))
        
        # Find wells with cell counts
        wells_with_counts = [info for info in result.values() 
                           if info.cell_count is not None]
        
        if wells_with_counts:
            for info in wells_with_counts:
                assert isinstance(info.cell_count, int)
                assert info.cell_count >= 0
    
    def test_group_parsing(self, parser, test_file_path):
        """Test group field parsing."""
        result = parser.parse_file(str(test_file_path))
        
        # Find wells with groups
        wells_with_groups = [info for info in result.values() 
                           if info.group_1 is not None]
        
        if wells_with_groups:
            for info in wells_with_groups:
                assert isinstance(info.group_1, str)
                assert len(info.group_1.strip()) > 0
    
    def test_well_id_format_validation(self, parser, test_file_path):
        """Test well ID format validation."""
        result = parser.parse_file(str(test_file_path))
        
        # All well IDs should be in correct format (letter + number)
        for well_id in result.keys():
            assert len(well_id) >= 2
            assert well_id[0].isalpha()  # First character is letter
            assert well_id[1:].isdigit()  # Rest are digits
    
    def test_safe_string_conversion(self, parser):
        """Test safe string conversion utility."""
        # Test various input types
        assert parser._safe_str("test") == "test"
        assert parser._safe_str("  test  ") == "test"
        assert parser._safe_str("") is None
        assert parser._safe_str("   ") is None
        assert parser._safe_str(None) is None
        
        # Test pandas NaN handling
        import pandas as pd
        assert parser._safe_str(pd.NA) is None
        assert parser._safe_str(float('nan')) is None
    
    def test_safe_int_conversion(self, parser):
        """Test safe integer conversion utility."""
        # Test various input types
        assert parser._safe_int(100) == 100
        assert parser._safe_int("100") == 100
        assert parser._safe_int(100.0) == 100
        assert parser._safe_int(100.7) == 100  # Should truncate
        assert parser._safe_int("") is None
        assert parser._safe_int("invalid") is None
        assert parser._safe_int(None) is None
        
        # Test pandas NaN handling
        import pandas as pd
        assert parser._safe_int(pd.NA) is None
        assert parser._safe_int(float('nan')) is None
    
    def test_file_validation_layout(self, parser):
        """Test file validation for non-existent files."""
        with pytest.raises(FileNotFoundError):
            parser.parse_file("nonexistent_layout.csv")
    
    def test_invalid_layout_format(self, parser, tmp_path):
        """Test handling of invalid layout file format."""
        # Create a file missing required columns
        invalid_file = tmp_path / "invalid_layout.csv"
        invalid_file.write_text("Invalid,Header\n1,2\n")
        
        with pytest.raises(ValueError, match="Missing required columns"):
            parser.parse_file(str(invalid_file))
    
    def test_empty_layout_file(self, parser, tmp_path):
        """Test handling of empty layout file."""
        # Create valid headers but no data
        empty_file = tmp_path / "empty_layout.csv"
        empty_file.write_text("Plate_ID,Well_Row,Well_Col,Well,Type\n")
        
        with pytest.raises(ValueError, match="No valid well information found"):
            parser.parse_file(str(empty_file))
    
    def test_bom_handling(self, parser, tmp_path):
        """Test handling of BOM (Byte Order Mark) in CSV files."""
        # Create file with BOM
        bom_file = tmp_path / "bom_layout.csv"
        content = "Plate_ID,Well_Row,Well_Col,Well,Type\nTEST,A,1,A1,sample\n"
        bom_file.write_bytes(b'\xef\xbb\xbf' + content.encode('utf-8'))
        
        result = parser.parse_file(str(bom_file))
        assert "A1" in result
        assert result["A1"].plate_id == "TEST"