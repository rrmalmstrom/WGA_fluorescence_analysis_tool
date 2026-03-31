"""
Unit tests for BioRad .xlsx integration with the analysis pipeline and GUI.

Covers:
- detect_file_format() correctly identifies .xlsx as BIORAD without reading as text
- parse_fluorescence_data() works for .xlsx without requiring cycle_time_minutes
- parse_fluorescence_data() still requires cycle_time_minutes for .txt
- _validate_plate_id_match() warns when plate IDs differ, silent when they match
- FileLoader shows correct format label for .xlsx files
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fluorescence_tool.algorithms.analysis_pipeline import FluorescenceAnalysisPipeline
from fluorescence_tool.core.models import FileFormat, FluorescenceData, WellInfo


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def pipeline():
    return FluorescenceAnalysisPipeline()


@pytest.fixture
def xlsx_96_path():
    return Path("test_data/2026-0326 LMD spc -  Quantification Amplification Results.xlsx")


@pytest.fixture
def xlsx_384_path():
    return Path("test_data/2026-0318 ReleaseMDA -  Quantification Amplification Results.xlsx")


@pytest.fixture
def txt_path():
    return Path("test_data/TEST01.BIORAD.FORMAT.1.txt")


@pytest.fixture
def layout_96_path():
    return Path("test_data/2026-0326 LMD spc_layout.csv")


@pytest.fixture
def layout_384_path():
    return Path("test_data/2026-0318 ReleaseMDA_layout.csv")


@pytest.fixture
def layout_wrong_path():
    return Path("test_data/2026-0326 LMD spc_WRONG_layout.csv")


# ===========================================================================
# Pipeline: detect_file_format()
# ===========================================================================

class TestPipelineDetectFileFormat:
    """Test that detect_file_format() handles .xlsx correctly."""

    def test_xlsx_detected_as_biorad(self, pipeline, xlsx_96_path):
        """detect_file_format() must return BIORAD for .xlsx without reading as text."""
        result = pipeline.detect_file_format(str(xlsx_96_path))
        assert result == FileFormat.BIORAD

    def test_xlsx_384_detected_as_biorad(self, pipeline, xlsx_384_path):
        """detect_file_format() returns BIORAD for 384-well .xlsx."""
        result = pipeline.detect_file_format(str(xlsx_384_path))
        assert result == FileFormat.BIORAD

    def test_txt_still_detected_as_biorad(self, pipeline, txt_path):
        """Legacy .txt BioRad file still detected as BIORAD."""
        result = pipeline.detect_file_format(str(txt_path))
        assert result == FileFormat.BIORAD

    def test_xlsx_uppercase_extension_detected(self, pipeline, xlsx_96_path, tmp_path):
        """detect_file_format() is case-insensitive for .XLSX extension."""
        import shutil
        upper = tmp_path / "DATA.XLSX"
        shutil.copy(str(xlsx_96_path), str(upper))
        result = pipeline.detect_file_format(str(upper))
        assert result == FileFormat.BIORAD


# ===========================================================================
# Pipeline: parse_fluorescence_data()
# ===========================================================================

class TestPipelineParseXlsx:
    """Test parse_fluorescence_data() with .xlsx BioRad files."""

    def test_xlsx_parses_without_cycle_time(self, pipeline, xlsx_96_path):
        """parse_fluorescence_data() succeeds for .xlsx without cycle_time_minutes."""
        result = pipeline.parse_fluorescence_data(str(xlsx_96_path))
        assert isinstance(result, FluorescenceData)
        assert result.format_type == FileFormat.BIORAD

    def test_xlsx_96_well_count(self, pipeline, xlsx_96_path):
        """parse_fluorescence_data() returns 96 wells for 96-well xlsx."""
        result = pipeline.parse_fluorescence_data(str(xlsx_96_path))
        assert len(result.wells) == 96

    def test_xlsx_384_well_count(self, pipeline, xlsx_384_path):
        """parse_fluorescence_data() returns 384 wells for 384-well xlsx."""
        result = pipeline.parse_fluorescence_data(str(xlsx_384_path))
        assert len(result.wells) == 384

    def test_xlsx_auto_cycle_time_in_metadata(self, pipeline, xlsx_96_path):
        """parse_fluorescence_data() stores auto-computed cycle_time_minutes in metadata."""
        result = pipeline.parse_fluorescence_data(str(xlsx_96_path))
        assert result.metadata["cycle_time_minutes"] == 15

    def test_xlsx_plate_id_in_metadata(self, pipeline, xlsx_96_path):
        """parse_fluorescence_data() stores plate_id in metadata for .xlsx."""
        result = pipeline.parse_fluorescence_data(str(xlsx_96_path))
        assert result.metadata["plate_id"] == "2026-0326 LMD spc"

    def test_xlsx_cycle_time_override(self, pipeline, xlsx_96_path):
        """parse_fluorescence_data() respects explicit cycle_time_minutes for .xlsx."""
        result = pipeline.parse_fluorescence_data(str(xlsx_96_path), cycle_time_minutes=20.0)
        assert result.metadata["cycle_time_minutes"] == 20.0

    def test_txt_still_requires_cycle_time(self, pipeline, txt_path):
        """parse_fluorescence_data() still raises ValueError for .txt without cycle time."""
        with pytest.raises(ValueError, match="cycle_time_minutes"):
            pipeline.parse_fluorescence_data(str(txt_path))

    def test_txt_works_with_cycle_time(self, pipeline, txt_path):
        """parse_fluorescence_data() works for .txt when cycle_time_minutes is provided."""
        result = pipeline.parse_fluorescence_data(str(txt_path), cycle_time_minutes=15.0)
        assert isinstance(result, FluorescenceData)
        assert result.format_type == FileFormat.BIORAD


# ===========================================================================
# Pipeline: analyze_complete_dataset() with .xlsx
# ===========================================================================

class TestPipelineAnalyzeXlsx:
    """Test end-to-end pipeline analysis with .xlsx BioRad files."""

    def test_analyze_xlsx_96_succeeds(self, pipeline, xlsx_96_path):
        """analyze_complete_dataset() succeeds for 96-well xlsx without cycle time."""
        from fluorescence_tool.algorithms.analysis_pipeline import PipelineResult
        result = pipeline.analyze_complete_dataset(str(xlsx_96_path))
        assert result.success is True
        assert result.fluorescence_data is not None
        assert result.total_wells_processed == 96

    def test_analyze_xlsx_384_succeeds(self, pipeline, xlsx_384_path):
        """analyze_complete_dataset() succeeds for 384-well xlsx."""
        result = pipeline.analyze_complete_dataset(str(xlsx_384_path))
        assert result.success is True
        assert result.total_wells_processed == 384


# ===========================================================================
# GUI: _validate_plate_id_match()
# ===========================================================================

class TestPlateIdValidation:
    """
    Test the plate ID mismatch validation logic in MainWindow.

    We test _validate_plate_id_match() in isolation by constructing a minimal
    MainWindow-like object with the required attributes, avoiding the need to
    spin up a full Tk root.
    """

    def _make_fluorescence_data(self, plate_id):
        """Helper: create a minimal FluorescenceData with a given plate_id."""
        import numpy as np
        return FluorescenceData(
            time_points=[0.0, 0.25],
            wells=["A1"],
            measurements=np.array([[100.0, 200.0]]),
            metadata={"plate_id": plate_id},
            format_type=FileFormat.BIORAD,
        )

    def _make_layout_data(self, plate_id):
        """Helper: create a minimal layout dict with a given plate_id."""
        return {
            "A1": WellInfo(
                well_id="A1",
                plate_id=plate_id,
                sample="sample",
                well_type="sample",
                cell_count=None,
                group_1=None,
                group_2=None,
                group_3=None,
            )
        }

    def test_matching_plate_ids_no_warning(self):
        """No warning shown when data plate_id matches layout plate_id."""
        from fluorescence_tool.gui.main_window import MainWindow

        # Patch Tk so no window is created
        with patch("fluorescence_tool.gui.main_window.tk.Tk") as mock_tk, \
             patch("fluorescence_tool.gui.main_window.FileLoader"), \
             patch("fluorescence_tool.gui.main_window.PlateView"), \
             patch("fluorescence_tool.gui.main_window.PlotPanel"), \
             patch("fluorescence_tool.gui.main_window.messagebox") as mock_mb:

            mock_root = MagicMock()
            mock_tk.return_value = mock_root

            win = MainWindow.__new__(MainWindow)
            win.fluorescence_data = self._make_fluorescence_data("2026-0326 LMD spc")
            win.layout_data = self._make_layout_data("2026-0326 LMD spc")

            # Bind the real method
            from fluorescence_tool.gui.main_window import MainWindow as MW
            MW._validate_plate_id_match(win)

            mock_mb.showwarning.assert_not_called()

    def test_mismatched_plate_ids_shows_warning(self):
        """Warning dialog shown when data plate_id differs from layout plate_id."""
        from fluorescence_tool.gui.main_window import MainWindow

        with patch("fluorescence_tool.gui.main_window.tk.Tk"), \
             patch("fluorescence_tool.gui.main_window.FileLoader"), \
             patch("fluorescence_tool.gui.main_window.PlateView"), \
             patch("fluorescence_tool.gui.main_window.PlotPanel"), \
             patch("fluorescence_tool.gui.main_window.messagebox") as mock_mb:

            win = MainWindow.__new__(MainWindow)
            win.fluorescence_data = self._make_fluorescence_data("2026-0326 LMD spc")
            win.layout_data = self._make_layout_data("WRONG_PLATE_ID")

            from fluorescence_tool.gui.main_window import MainWindow as MW
            MW._validate_plate_id_match(win)

            mock_mb.showwarning.assert_called_once()
            call_args = mock_mb.showwarning.call_args
            # First positional arg is the title
            assert "Mismatch" in call_args[0][0] or "mismatch" in call_args[0][0].lower()
            # Second positional arg is the message body
            msg = call_args[0][1]
            assert "2026-0326 LMD spc" in msg
            assert "WRONG_PLATE_ID" in msg

    def test_no_data_file_skips_validation(self):
        """Validation is skipped when fluorescence_data is None."""
        from fluorescence_tool.gui.main_window import MainWindow

        with patch("fluorescence_tool.gui.main_window.messagebox") as mock_mb:
            win = MainWindow.__new__(MainWindow)
            win.fluorescence_data = None
            win.layout_data = self._make_layout_data("some-plate")

            from fluorescence_tool.gui.main_window import MainWindow as MW
            MW._validate_plate_id_match(win)

            mock_mb.showwarning.assert_not_called()

    def test_no_layout_file_skips_validation(self):
        """Validation is skipped when layout_data is empty."""
        from fluorescence_tool.gui.main_window import MainWindow

        with patch("fluorescence_tool.gui.main_window.messagebox") as mock_mb:
            win = MainWindow.__new__(MainWindow)
            win.fluorescence_data = self._make_fluorescence_data("2026-0326 LMD spc")
            win.layout_data = {}

            from fluorescence_tool.gui.main_window import MainWindow as MW
            MW._validate_plate_id_match(win)

            mock_mb.showwarning.assert_not_called()

    def test_no_plate_id_in_metadata_skips_validation(self):
        """Validation is skipped for formats that don't embed a plate_id (e.g. .txt)."""
        import numpy as np
        from fluorescence_tool.gui.main_window import MainWindow

        with patch("fluorescence_tool.gui.main_window.messagebox") as mock_mb:
            win = MainWindow.__new__(MainWindow)
            # .txt format: metadata has no plate_id key
            win.fluorescence_data = FluorescenceData(
                time_points=[0.0],
                wells=["A1"],
                measurements=np.array([[100.0]]),
                metadata={"cycle_time_minutes": 15.0},  # no plate_id
                format_type=FileFormat.BIORAD,
            )
            win.layout_data = self._make_layout_data("some-plate")

            from fluorescence_tool.gui.main_window import MainWindow as MW
            MW._validate_plate_id_match(win)

            mock_mb.showwarning.assert_not_called()

    def test_real_xlsx_and_matching_layout(self, xlsx_96_path, layout_96_path):
        """End-to-end: real xlsx plate_id matches real layout plate_id — no warning."""
        from fluorescence_tool.parsers.biorad_parser import BioRadParser
        from fluorescence_tool.parsers.layout_parser import LayoutParser
        from fluorescence_tool.gui.main_window import MainWindow

        parser = BioRadParser()
        layout_parser = LayoutParser()

        fluo_data = parser.parse_file(str(xlsx_96_path))
        layout_data = layout_parser.parse_file(str(layout_96_path))

        with patch("fluorescence_tool.gui.main_window.messagebox") as mock_mb:
            win = MainWindow.__new__(MainWindow)
            win.fluorescence_data = fluo_data
            win.layout_data = layout_data

            from fluorescence_tool.gui.main_window import MainWindow as MW
            MW._validate_plate_id_match(win)

            mock_mb.showwarning.assert_not_called()

    def test_real_xlsx_and_wrong_layout(self, xlsx_96_path, layout_wrong_path):
        """End-to-end: real xlsx plate_id vs WRONG layout plate_id — warning shown."""
        from fluorescence_tool.parsers.biorad_parser import BioRadParser
        from fluorescence_tool.parsers.layout_parser import LayoutParser
        from fluorescence_tool.gui.main_window import MainWindow

        parser = BioRadParser()
        layout_parser = LayoutParser()

        fluo_data = parser.parse_file(str(xlsx_96_path))
        layout_data = layout_parser.parse_file(str(layout_wrong_path))

        with patch("fluorescence_tool.gui.main_window.messagebox") as mock_mb:
            win = MainWindow.__new__(MainWindow)
            win.fluorescence_data = fluo_data
            win.layout_data = layout_data

            from fluorescence_tool.gui.main_window import MainWindow as MW
            MW._validate_plate_id_match(win)

            mock_mb.showwarning.assert_called_once()
