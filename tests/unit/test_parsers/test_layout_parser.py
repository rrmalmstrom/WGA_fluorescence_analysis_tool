"""
Unit tests for Layout file parser.

Tests use real data from test_data/TEST01.BIORAD_layout.csv (384-well, with Sample
column, plate_id='TEST01.BIORAD.FORMAT.1').  The old format without a Sample column
is no longer accepted and should raise a ValueError.
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
        """Path to current required-format layout test data file (with Sample column)."""
        return Path("test_data/TEST01.BIORAD_layout.csv")
    
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
        
        # Should match expected plate ID from TEST01.BIORAD_layout.csv
        expected_plate_id = "TEST01.BIORAD.FORMAT.1"
        assert expected_plate_id in plate_ids
    
    def test_optional_fields_handling(self, parser, test_file_path):
        """Test handling of optional fields."""
        result = parser.parse_file(str(test_file_path))
        
        # Some wells should have optional group fields
        has_groups = any(info.group_1 is not None for info in result.values())
        
        # At least some wells should have group_1 populated
        assert has_groups
    
    def test_cell_count_parsing(self, parser, test_file_path):
        """Test cell count parsing and validation."""
        result = parser.parse_file(str(test_file_path))
        
        # Find wells with cell counts (may be none in this file — that's OK)
        wells_with_counts = [info for info in result.values() 
                           if info.cell_count is not None]
        
        for info in wells_with_counts:
            assert isinstance(info.cell_count, int)
            assert info.cell_count >= 0
    
    def test_group_parsing(self, parser, test_file_path):
        """Test group field parsing."""
        result = parser.parse_file(str(test_file_path))
        
        # Find wells with groups
        wells_with_groups = [info for info in result.values() 
                           if info.group_1 is not None]
        
        assert len(wells_with_groups) > 0
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
        """Test handling of empty layout file (valid headers including Sample, but no data rows)."""
        empty_file = tmp_path / "empty_layout.csv"
        empty_file.write_text("Plate_ID,Well_Row,Well_Col,Well,Sample,Type\n")

        with pytest.raises(ValueError, match="Plate_ID"):
            parser.parse_file(str(empty_file))
    
    def test_bom_handling(self, parser, tmp_path):
        """Test handling of BOM (Byte Order Mark) in CSV files (new format with Sample)."""
        bom_file = tmp_path / "bom_layout.csv"
        content = "Plate_ID,Well_Row,Well_Col,Well,Sample,Type\nTEST,A,1,A1,SAMPLE_X,sample\n"
        bom_file.write_bytes(b'\xef\xbb\xbf' + content.encode('utf-8'))

        result = parser.parse_file(str(bom_file))
        assert "A1" in result
        assert result["A1"].plate_id == "TEST"
        assert result["A1"].sample == "SAMPLE_X"


class TestLayoutParserNewFormat:
    """
    Test Layout file parser with new format data (TEST01.BIORAD_layout.csv).

    The format includes a 'Sample' column between 'Well' and 'Type':
      Plate_ID, Well_Row, Well_Col, Well, Sample, Type, number_of_cells/capsules,
      Group_1, Group_2, Group_3
    """

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return LayoutParser()

    @pytest.fixture
    def new_format_file_path(self):
        """Path to new format layout test data file."""
        return Path("test_data/TEST01.BIORAD_layout.csv")

    def test_parse_new_format_file(self, parser, new_format_file_path):
        """Test that the new format file (with Sample column) parses successfully."""
        result = parser.parse_file(str(new_format_file_path))

        assert isinstance(result, dict)
        assert len(result) > 0

        for well_id, well_info in result.items():
            assert isinstance(well_info, WellInfo)
            assert well_info.well_id == well_id

    def test_new_format_plate_id(self, parser, new_format_file_path):
        """Test that plate ID is parsed correctly from new format file."""
        result = parser.parse_file(str(new_format_file_path))

        plate_ids = {info.plate_id for info in result.values()}
        assert len(plate_ids) == 1
        assert "TEST01.BIORAD.FORMAT.1" in plate_ids

    def test_new_format_sample_column_populated(self, parser, new_format_file_path):
        """Test that the Sample column is read and stored on WellInfo objects."""
        result = parser.parse_file(str(new_format_file_path))

        sample_wells = [info for info in result.values() if info.well_type == "sample"]
        assert len(sample_wells) > 0

        # The majority of sample wells should have a non-empty sample value.
        # (One well in the real test file has an empty sample field — that's a data
        # quirk we accept rather than reject at parse time.)
        wells_with_sample = [info for info in sample_wells if info.sample]
        assert len(wells_with_sample) > 0, "No sample wells have a sample name"
        assert len(wells_with_sample) >= len(sample_wells) - 1, (
            "More than one sample-type well is missing a sample name"
        )

    def test_new_format_sample_value_correct(self, parser, new_format_file_path):
        """Test that the Sample column value matches expected data (biorad_sample)."""
        result = parser.parse_file(str(new_format_file_path))

        # All non-unused wells in TEST01.BIORAD_layout.csv carry sample 'biorad_sample'
        active_wells = [
            info for info in result.values() if info.well_type != "unused"
        ]
        assert len(active_wells) > 0

        for info in active_wells:
            if info.sample:  # neg_cntrl wells may have empty sample
                assert info.sample == "biorad_sample", (
                    f"Well {info.well_id} expected sample='biorad_sample', got {info.sample!r}"
                )

    def test_new_format_unused_wells_have_empty_sample(self, parser, new_format_file_path):
        """Test that unused wells have an empty (falsy) sample value."""
        result = parser.parse_file(str(new_format_file_path))

        unused_wells = [info for info in result.values() if info.well_type == "unused"]
        assert len(unused_wells) > 0

        for info in unused_wells:
            # sample should be empty string or None for unused wells
            assert not info.sample, (
                f"Unused well {info.well_id} unexpectedly has sample={info.sample!r}"
            )

    def test_new_format_well_types_present(self, parser, new_format_file_path):
        """Test that expected well types are present in new format file."""
        result = parser.parse_file(str(new_format_file_path))

        well_types = {info.well_type for info in result.values()}
        # TEST01.BIORAD_layout.csv has: unused, sample, neg_cntrl
        expected_types = {"unused", "sample", "neg_cntrl"}

        assert len(well_types.intersection(expected_types)) >= 2

    def test_new_format_group_columns_parsed(self, parser, new_format_file_path):
        """Test that Group_1/2/3 columns are still parsed correctly in new format."""
        result = parser.parse_file(str(new_format_file_path))

        sample_wells = [info for info in result.values() if info.well_type == "sample"]
        assert len(sample_wells) > 0

        # Sample wells should have group_1 populated (e.g. 15min, 20min, 30min, 40min)
        wells_with_group1 = [info for info in sample_wells if info.group_1 is not None]
        assert len(wells_with_group1) > 0

    def test_new_format_cell_count_parsed(self, parser, tmp_path):
        """Test that number_of_cells/capsules is parsed correctly in new format."""
        # TEST01.BIORAD_layout.csv has no cell counts; use a synthetic file to test parsing
        cell_count_file = tmp_path / "cell_count_layout.csv"
        content = (
            "Plate_ID,Well_Row,Well_Col,Well,Sample,Type,number_of_cells/capsules,"
            "Group_1,Group_2,Group_3\n"
            "PLATE1,A,1,A1,SAMPLE_X,sample,500,Rep1,BONCAT,Big\n"
            "PLATE1,B,1,B1,,unused,,,,\n"
        )
        cell_count_file.write_bytes(b'\xef\xbb\xbf' + content.encode('utf-8'))

        result = parser.parse_file(str(cell_count_file))

        wells_with_count = [
            info for info in result.values() if info.cell_count is not None
        ]
        assert len(wells_with_count) > 0

        for info in wells_with_count:
            assert isinstance(info.cell_count, int)
            assert info.cell_count >= 0

    def test_new_format_bom_handling(self, parser, tmp_path):
        """Test new format file with BOM and Sample column parses correctly."""
        bom_file = tmp_path / "new_format_bom.csv"
        content = (
            "Plate_ID,Well_Row,Well_Col,Well,Sample,Type,number_of_cells/capsules,"
            "Group_1,Group_2,Group_3\n"
            "PLATE1,A,1,A1,SAMPLE_X,sample,100,Rep1,BONCAT,Big\n"
            "PLATE1,B,1,B1,,unused,,,,\n"
        )
        bom_file.write_bytes(b'\xef\xbb\xbf' + content.encode('utf-8'))

        result = parser.parse_file(str(bom_file))

        assert "A1" in result
        assert result["A1"].sample == "SAMPLE_X"
        assert result["A1"].well_type == "sample"
        assert result["A1"].cell_count == 100
        assert result["A1"].group_1 == "Rep1"

        assert "B1" in result
        assert not result["B1"].sample
        assert result["B1"].well_type == "unused"

    def test_old_format_without_sample_column_is_rejected(self, parser, tmp_path):
        """
        A file missing the required 'Sample' column must be rejected with a ValueError.
        """
        old_format_file = tmp_path / "old_format_no_sample.csv"
        content = (
            "Plate_ID,Well_Row,Well_Col,Well,Type,number_of_cells/capsules,"
            "Group_1,Group_2,Group_3\n"
            "PLATE1,A,1,A1,sample,100,Rep1,BONCAT,Big\n"
        )
        old_format_file.write_text(content)

        with pytest.raises(ValueError, match="Missing required columns"):
            parser.parse_file(str(old_format_file))

    def test_sample_field_present_on_wellinfo(self, parser, new_format_file_path):
        """Test that WellInfo dataclass exposes the sample attribute."""
        result = parser.parse_file(str(new_format_file_path))
        first_well = next(iter(result.values()))
        assert hasattr(first_well, "sample"), "WellInfo must have a 'sample' attribute"
