"""
Unit tests for BioRad format parser.

Tests cover both the legacy tab-separated .txt format and the new
Bio-Rad CFX Maestro .xlsx format (SYBR sheet + Run Information sheet).

Following TDD methodology.
"""

import pytest
import numpy as np
from pathlib import Path
from fluorescence_tool.parsers.biorad_parser import BioRadParser
from fluorescence_tool.core.models import FluorescenceData, FileFormat


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def parser():
    """Create parser instance."""
    return BioRadParser()


@pytest.fixture
def txt_file_path():
    """Path to legacy BioRad .txt test data file (384-well)."""
    return Path("test_data/TEST01.BIORAD.FORMAT.1.txt")


@pytest.fixture
def xlsx_96_file_path():
    """Path to new BioRad .xlsx test data file (96-well)."""
    return Path("test_data/2026-0326 LMD spc -  Quantification Amplification Results.xlsx")


@pytest.fixture
def xlsx_384_file_path():
    """Path to new BioRad .xlsx test data file (384-well)."""
    return Path("test_data/2026-0318 ReleaseMDA -  Quantification Amplification Results.xlsx")


# ===========================================================================
# LEGACY .txt FORMAT TESTS (must remain passing — no changes to .txt path)
# ===========================================================================

class TestBioRadParserTxt:
    """Test BioRad legacy tab-separated .txt format parser."""

    def test_parser_creation(self, parser):
        """Test parser can be created."""
        assert isinstance(parser, BioRadParser)

    def test_parse_real_biorad_file(self, parser, txt_file_path):
        """Test parsing real BioRad .txt file with cycle time."""
        cycle_time_minutes = 15.0
        result = parser.parse_file(str(txt_file_path), cycle_time_minutes)

        assert isinstance(result, FluorescenceData)
        assert result.format_type == FileFormat.BIORAD
        assert len(result.wells) > 0
        assert len(result.time_points) > 0
        assert result.measurements.shape[0] == len(result.wells)
        assert result.measurements.shape[1] == len(result.time_points)

    def test_cycle_time_conversion(self, parser, txt_file_path):
        """Test cycle time to hours conversion for .txt format."""
        cycle_time_minutes = 15.0
        result = parser.parse_file(str(txt_file_path), cycle_time_minutes)

        expected_times = [0.0, 0.25, 0.5, 0.75, 1.0]
        assert len(result.time_points) >= 5
        for i, expected in enumerate(expected_times):
            assert abs(result.time_points[i] - expected) < 0.01

    def test_well_identification_384_format(self, parser, txt_file_path):
        """Test well identification for 384-well .txt format."""
        result = parser.parse_file(str(txt_file_path), 15.0)

        assert "A1" in result.wells
        assert "A24" in result.wells
        assert "P1" in result.wells
        assert "P24" in result.wells
        assert result.metadata["plate_format"] == "384-well"

    def test_fluorescence_values_biorad(self, parser, txt_file_path):
        """Test fluorescence value extraction from .txt format."""
        result = parser.parse_file(str(txt_file_path), 15.0)

        assert np.all(result.measurements >= 0)
        assert np.all(result.measurements < 10000)
        assert np.all(result.measurements > 100)
        assert np.all(np.isfinite(result.measurements))

    def test_metadata_extraction_biorad(self, parser, txt_file_path):
        """Test metadata extraction for .txt format."""
        cycle_time = 15.0
        result = parser.parse_file(str(txt_file_path), cycle_time)

        assert result.metadata["cycle_time_minutes"] == cycle_time
        assert "num_cycles" in result.metadata
        assert result.metadata["num_cycles"] > 0
        assert "plate_format" in result.metadata

    def test_different_cycle_times(self, parser, txt_file_path):
        """Test parsing .txt with different cycle times."""
        for cycle_time in [10.0, 15.0, 20.0, 30.0]:
            result = parser.parse_file(str(txt_file_path), cycle_time)
            expected_second_time = cycle_time / 60.0
            assert abs(result.time_points[1] - expected_second_time) < 0.01

    def test_invalid_cycle_time(self, parser, txt_file_path):
        """Test handling of invalid cycle times for .txt format."""
        with pytest.raises(ValueError):
            parser.parse_file(str(txt_file_path), 0.0)

        with pytest.raises(ValueError):
            parser.parse_file(str(txt_file_path), -5.0)

    def test_txt_requires_cycle_time(self, parser, txt_file_path):
        """Test that .txt format raises ValueError when cycle_time_minutes is None."""
        with pytest.raises(ValueError, match="cycle_time_minutes.*required.*txt"):
            parser.parse_file(str(txt_file_path), None)

    def test_file_validation_biorad(self, parser):
        """Test file validation for non-existent files."""
        with pytest.raises(FileNotFoundError):
            parser.parse_file("nonexistent_biorad.txt", 15.0)

    def test_invalid_biorad_format(self, parser, tmp_path):
        """Test handling of invalid BioRad .txt file format."""
        invalid_file = tmp_path / "invalid_biorad.txt"
        invalid_file.write_text("A1\tA2\tA3\n1\t2\t3\n")

        with pytest.raises(ValueError, match="missing 'Cycle' column"):
            parser.parse_file(str(invalid_file), 15.0)

    def test_plate_format_detection(self, parser):
        """Test automatic plate format detection."""
        assert parser._detect_plate_format(["A1", "A12", "H1", "H12"]) == "96-well"
        assert parser._detect_plate_format(["A1", "A24", "P1", "P24"]) == "384-well"
        assert parser._detect_plate_format(["A1", "Z50"]) == "unknown"

    def test_data_consistency_biorad(self, parser, txt_file_path):
        """Test that parsed .txt data maintains consistency."""
        result = parser.parse_file(str(txt_file_path), 15.0)

        for i, well in enumerate(result.wells):
            well_measurements = result.measurements[i]
            assert len(well_measurements) == len(result.time_points)
            assert np.all(np.isfinite(well_measurements))
            if len(well_measurements) > 1:
                assert np.std(well_measurements) > 0


# ===========================================================================
# NEW .xlsx FORMAT TESTS
# ===========================================================================

class TestBioRadParserXlsx:
    """Test BioRad new CFX Maestro .xlsx format parser."""

    # --- Basic parsing ---

    def test_parse_xlsx_96_well(self, parser, xlsx_96_file_path):
        """Test parsing 96-well .xlsx file returns valid FluorescenceData."""
        result = parser.parse_file(str(xlsx_96_file_path))

        assert isinstance(result, FluorescenceData)
        assert result.format_type == FileFormat.BIORAD

    def test_parse_xlsx_384_well(self, parser, xlsx_384_file_path):
        """Test parsing 384-well .xlsx file returns valid FluorescenceData."""
        result = parser.parse_file(str(xlsx_384_file_path))

        assert isinstance(result, FluorescenceData)
        assert result.format_type == FileFormat.BIORAD

    # --- Well identification ---

    def test_xlsx_96_well_identification(self, parser, xlsx_96_file_path):
        """Test well identification for 96-well .xlsx format."""
        result = parser.parse_file(str(xlsx_96_file_path))

        assert len(result.wells) == 96
        assert "A1" in result.wells
        assert "A12" in result.wells
        assert "H1" in result.wells
        assert "H12" in result.wells
        assert result.metadata["plate_format"] == "96-well"

    def test_xlsx_384_well_identification(self, parser, xlsx_384_file_path):
        """Test well identification for 384-well .xlsx format."""
        result = parser.parse_file(str(xlsx_384_file_path))

        assert len(result.wells) == 384
        assert "A1" in result.wells
        assert "A24" in result.wells
        assert "P1" in result.wells
        assert "P24" in result.wells
        assert result.metadata["plate_format"] == "384-well"

    # --- Time points ---

    def test_xlsx_auto_cycle_time_96(self, parser, xlsx_96_file_path):
        """Test auto-computed cycle time for 96-well file rounds to 15 min."""
        result = parser.parse_file(str(xlsx_96_file_path))

        assert result.metadata["cycle_time_minutes"] == 15
        # First time point is 0.0 hours (cycle 1)
        assert abs(result.time_points[0] - 0.0) < 0.001
        # Second time point is 15 min = 0.25 hours
        assert abs(result.time_points[1] - 0.25) < 0.001

    def test_xlsx_auto_cycle_time_384(self, parser, xlsx_384_file_path):
        """Test auto-computed cycle time for 384-well file rounds to 15 min."""
        result = parser.parse_file(str(xlsx_384_file_path))

        assert result.metadata["cycle_time_minutes"] == 15

    def test_xlsx_cycle_time_override(self, parser, xlsx_96_file_path):
        """Test that user-supplied cycle_time_minutes overrides auto-computation."""
        result = parser.parse_file(str(xlsx_96_file_path), cycle_time_minutes=20.0)

        assert result.metadata["cycle_time_minutes"] == 20.0
        # Second time point should be 20 min = 0.333... hours
        assert abs(result.time_points[1] - 20.0 / 60.0) < 0.001

    def test_xlsx_48_cycles(self, parser, xlsx_96_file_path):
        """Test that 48 cycles are parsed from the xlsx file."""
        result = parser.parse_file(str(xlsx_96_file_path))

        assert len(result.time_points) == 48
        assert result.metadata["num_cycles"] == 48

    def test_xlsx_time_points_sequence(self, parser, xlsx_96_file_path):
        """Test time points form a correct sequence at 15 min intervals."""
        result = parser.parse_file(str(xlsx_96_file_path))

        expected = [i * 15.0 / 60.0 for i in range(48)]
        for i, (actual, exp) in enumerate(zip(result.time_points, expected)):
            assert abs(actual - exp) < 0.001, f"Time point {i}: expected {exp}, got {actual}"

    # --- Fluorescence values ---

    def test_xlsx_fluorescence_values_positive(self, parser, xlsx_96_file_path):
        """Test all fluorescence values are positive finite numbers."""
        result = parser.parse_file(str(xlsx_96_file_path))

        assert np.all(result.measurements > 0)
        assert np.all(np.isfinite(result.measurements))

    def test_xlsx_measurement_shape_96(self, parser, xlsx_96_file_path):
        """Test measurement array shape for 96-well file."""
        result = parser.parse_file(str(xlsx_96_file_path))

        assert result.measurements.shape == (96, 48)

    def test_xlsx_measurement_shape_384(self, parser, xlsx_384_file_path):
        """Test measurement array shape for 384-well file."""
        result = parser.parse_file(str(xlsx_384_file_path))

        assert result.measurements.shape == (384, 48)

    def test_xlsx_specific_well_value(self, parser, xlsx_96_file_path):
        """Test a specific known fluorescence value from the 96-well file."""
        result = parser.parse_file(str(xlsx_96_file_path))

        # A1, cycle 1 = 2491.877... (verified from raw data inspection)
        a1_idx = result.wells.index("A1")
        assert abs(result.measurements[a1_idx, 0] - 2491.878) < 0.1

    # --- Metadata / plate ID ---

    def test_xlsx_plate_id_in_metadata_96(self, parser, xlsx_96_file_path):
        """Test plate_id extracted from Run Information B1 for 96-well file."""
        result = parser.parse_file(str(xlsx_96_file_path))

        assert "plate_id" in result.metadata
        assert result.metadata["plate_id"] == "2026-0326 LMD spc"

    def test_xlsx_plate_id_in_metadata_384(self, parser, xlsx_384_file_path):
        """Test plate_id extracted from Run Information B1 for 384-well file."""
        result = parser.parse_file(str(xlsx_384_file_path))

        assert "plate_id" in result.metadata
        assert result.metadata["plate_id"] == "2026-0318 ReleaseMDA"

    def test_xlsx_run_timestamps_in_metadata(self, parser, xlsx_96_file_path):
        """Test run start/end timestamps stored in metadata."""
        result = parser.parse_file(str(xlsx_96_file_path))

        assert "run_started" in result.metadata
        assert "run_ended" in result.metadata
        assert result.metadata["run_started"] == "03/26/2026 23:45:08 UTC"
        assert result.metadata["run_ended"] == "03/27/2026 11:58:10 UTC"

    def test_xlsx_instrument_metadata(self, parser, xlsx_96_file_path):
        """Test instrument metadata stored from Run Information sheet."""
        result = parser.parse_file(str(xlsx_96_file_path))

        assert "cfx_version" in result.metadata
        assert "protocol_file" in result.metadata

    def test_xlsx_num_cycles_in_metadata(self, parser, xlsx_96_file_path):
        """Test num_cycles stored in metadata."""
        result = parser.parse_file(str(xlsx_96_file_path))

        assert "num_cycles" in result.metadata
        assert result.metadata["num_cycles"] == 48

    # --- Data consistency ---

    def test_xlsx_data_consistency(self, parser, xlsx_96_file_path):
        """Test each well has measurements for all time points."""
        result = parser.parse_file(str(xlsx_96_file_path))

        assert result.measurements.shape[0] == len(result.wells)
        assert result.measurements.shape[1] == len(result.time_points)
        for i in range(len(result.wells)):
            assert np.all(np.isfinite(result.measurements[i]))

    # --- Error handling ---

    def test_xlsx_file_not_found(self, parser):
        """Test FileNotFoundError for non-existent .xlsx file."""
        with pytest.raises(FileNotFoundError):
            parser.parse_file("nonexistent.xlsx")

    def test_xlsx_invalid_cycle_time_zero(self, parser, xlsx_96_file_path):
        """Test ValueError for zero cycle time override."""
        with pytest.raises(ValueError):
            parser.parse_file(str(xlsx_96_file_path), cycle_time_minutes=0.0)

    def test_xlsx_invalid_cycle_time_negative(self, parser, xlsx_96_file_path):
        """Test ValueError for negative cycle time override."""
        with pytest.raises(ValueError):
            parser.parse_file(str(xlsx_96_file_path), cycle_time_minutes=-5.0)

    def test_unsupported_file_extension(self, parser, tmp_path):
        """Test ValueError for unsupported file extension."""
        bad_file = tmp_path / "data.csv"
        bad_file.write_text("some,data\n")

        with pytest.raises(ValueError, match="Unsupported BioRad file format"):
            parser.parse_file(str(bad_file))

    def test_xlsx_missing_sybr_sheet(self, parser, tmp_path):
        """Test ValueError when SYBR sheet is missing from xlsx."""
        import zipfile, io
        # Create a minimal xlsx-like zip without a SYBR sheet
        bad_xlsx = tmp_path / "no_sybr.xlsx"
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as z:
            z.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>')
            z.writestr('xl/workbook.xml', '<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheets><sheet name="Sheet1" sheetId="1"/></sheets></workbook>')
        bad_xlsx.write_bytes(buf.getvalue())

        with pytest.raises(ValueError, match="SYBR"):
            parser.parse_file(str(bad_xlsx))


# ===========================================================================
# FILE EXTENSION DISPATCH TESTS
# ===========================================================================

class TestBioRadParserDispatch:
    """Test that parse_file() correctly dispatches based on file extension."""

    def test_txt_extension_uses_txt_parser(self, parser, txt_file_path):
        """Test .txt extension routes to legacy parser."""
        result = parser.parse_file(str(txt_file_path), cycle_time_minutes=15.0)
        assert result.format_type == FileFormat.BIORAD
        # .txt parser stores cycle_time_minutes as provided
        assert result.metadata["cycle_time_minutes"] == 15.0

    def test_xlsx_extension_uses_xlsx_parser(self, parser, xlsx_96_file_path):
        """Test .xlsx extension routes to new xlsx parser."""
        result = parser.parse_file(str(xlsx_96_file_path))
        assert result.format_type == FileFormat.BIORAD
        # xlsx parser auto-computes cycle time
        assert "run_started" in result.metadata

    def test_xlsx_extension_case_insensitive(self, parser, xlsx_96_file_path, tmp_path):
        """Test .XLSX (uppercase) extension is handled."""
        import shutil
        upper_path = tmp_path / "DATA.XLSX"
        shutil.copy(str(xlsx_96_file_path), str(upper_path))
        result = parser.parse_file(str(upper_path))
        assert result.format_type == FileFormat.BIORAD
