"""
Unit tests for core data models.

Tests validate the current data model implementations in models.py.
"""

import pytest
import numpy as np
from fluorescence_tool.core.models import (
    FileFormat,
    FluorescenceData,
    WellInfo,
)


class TestFileFormat:
    """Test FileFormat enum."""
    
    def test_file_format_enum_values(self):
        """Test that FileFormat enum has expected values."""
        assert FileFormat.BMG_OMEGA3.value == "bmg_omega3"
        assert FileFormat.BIORAD.value == "biorad"
        assert FileFormat.UNKNOWN.value == "unknown"


class TestFluorescenceData:
    """Test FluorescenceData dataclass."""
    
    def test_fluorescence_data_creation(self):
        """Test basic FluorescenceData creation."""
        time_points = [0.0, 0.25, 0.5, 1.0]
        wells = ["A1", "A2", "B1"]
        measurements = np.array([
            [100, 105, 110, 120],  # A1
            [95, 100, 108, 115],   # A2
            [102, 107, 112, 125]   # B1
        ])
        metadata = {"plate_id": "TEST001", "user": "test_user"}
        
        data = FluorescenceData(
            time_points=time_points,
            wells=wells,
            measurements=measurements,
            metadata=metadata,
            format_type=FileFormat.BMG_OMEGA3
        )
        
        assert data.time_points == time_points
        assert data.wells == wells
        assert np.array_equal(data.measurements, measurements)
        assert data.metadata == metadata
        assert data.format_type == FileFormat.BMG_OMEGA3
    
    def test_fluorescence_data_validation_well_count_mismatch(self):
        """Test validation fails when well count doesn't match measurement rows."""
        time_points = [0.0, 0.25, 0.5]
        wells = ["A1", "A2"]  # 2 wells
        measurements = np.array([
            [100, 105, 110],  # A1
            [95, 100, 108],   # A2
            [102, 107, 112]   # Extra row - should cause validation error
        ])
        metadata = {}
        
        with pytest.raises(ValueError, match="Number of wells must match measurement rows"):
            FluorescenceData(
                time_points=time_points,
                wells=wells,
                measurements=measurements,
                metadata=metadata,
                format_type=FileFormat.BMG_OMEGA3
            )
    
    def test_fluorescence_data_validation_time_count_mismatch(self):
        """Test validation fails when time point count doesn't match measurement columns."""
        time_points = [0.0, 0.25]  # 2 time points
        wells = ["A1", "A2"]
        measurements = np.array([
            [100, 105, 110],  # 3 measurements - should cause validation error
            [95, 100, 108]
        ])
        metadata = {}
        
        with pytest.raises(ValueError, match="Number of time points must match measurement columns"):
            FluorescenceData(
                time_points=time_points,
                wells=wells,
                measurements=measurements,
                metadata=metadata,
                format_type=FileFormat.BMG_OMEGA3
            )


class TestWellInfo:
    """Test WellInfo dataclass."""
    
    def test_well_info_creation_complete(self):
        """Test WellInfo creation with all fields."""
        well_info = WellInfo(
            well_id="A1",
            plate_id="TEST001",
            sample="Sample1",
            well_type="sample",
            cell_count=100,
            group_1="Rep1",
            group_2="BONCAT",
            group_3="Treatment1"
        )
        
        assert well_info.well_id == "A1"
        assert well_info.plate_id == "TEST001"
        assert well_info.sample == "Sample1"
        assert well_info.well_type == "sample"
        assert well_info.cell_count == 100
        assert well_info.group_1 == "Rep1"
        assert well_info.group_2 == "BONCAT"
        assert well_info.group_3 == "Treatment1"
    
    def test_well_info_creation_minimal(self):
        """Test WellInfo creation with minimal required fields."""
        well_info = WellInfo(
            well_id="B2",
            plate_id="TEST002",
            sample="",
            well_type="unused",
            cell_count=None,
            group_1=None,
            group_2=None,
            group_3=None
        )
        
        assert well_info.well_id == "B2"
        assert well_info.plate_id == "TEST002"
        assert well_info.sample == ""
        assert well_info.well_type == "unused"
        assert well_info.cell_count is None
        assert well_info.group_1 is None
        assert well_info.group_2 is None
        assert well_info.group_3 is None

