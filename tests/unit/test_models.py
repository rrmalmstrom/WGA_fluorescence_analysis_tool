"""
Unit tests for core data models.

Following TDD methodology - these tests are written first and should initially fail.
"""

import pytest
import numpy as np
from fluorescence_tool.core.models import (
    FileFormat,
    FluorescenceData,
    WellInfo,
    CurveFitResult
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


class TestCurveFitResult:
    """Test CurveFitResult dataclass."""
    
    def test_curve_fit_result_creation(self):
        """Test CurveFitResult creation."""
        well_id = "A1"
        fitted_params = np.array([1000.0, 2.0, 5.0, 100.0, 0.1])  # [a, b, c, d, e]
        fitted_curve = np.array([100, 120, 200, 500, 800, 950])
        r_squared = 0.95
        crossing_point = 4.2
        threshold_value = 150.0
        delta_fluorescence = 850.0
        fit_quality = "excellent"
        convergence_info = {"iterations": 25, "success": True}
        
        result = CurveFitResult(
            well_id=well_id,
            fitted_params=fitted_params,
            fitted_curve=fitted_curve,
            r_squared=r_squared,
            crossing_point=crossing_point,
            threshold_value=threshold_value,
            delta_fluorescence=delta_fluorescence,
            fit_quality=fit_quality,
            convergence_info=convergence_info
        )
        
        assert result.well_id == well_id
        assert np.array_equal(result.fitted_params, fitted_params)
        assert np.array_equal(result.fitted_curve, fitted_curve)
        assert result.r_squared == r_squared
        assert result.crossing_point == crossing_point
        assert result.threshold_value == threshold_value
        assert result.delta_fluorescence == delta_fluorescence
        assert result.fit_quality == fit_quality
        assert result.convergence_info == convergence_info
    
    def test_curve_fit_result_quality_values(self):
        """Test that fit quality accepts expected values."""
        valid_qualities = ["excellent", "good", "fair", "poor", "failed"]
        
        for quality in valid_qualities:
            result = CurveFitResult(
                well_id="A1",
                fitted_params=np.array([1, 2, 3, 4, 5]),
                fitted_curve=np.array([1, 2, 3]),
                r_squared=0.9,
                crossing_point=2.0,
                threshold_value=100.0,
                delta_fluorescence=500.0,
                fit_quality=quality,
                convergence_info={}
            )
            assert result.fit_quality == quality