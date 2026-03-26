"""
Core data models for fluorescence analysis.

These models define the fundamental data structures used throughout the application.
Based on the technical specifications and designed to handle both BMG Omega3 and BioRad formats.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np
from enum import Enum


class FileFormat(Enum):
    """Supported file formats for fluorescence data."""
    BMG_OMEGA3 = "bmg_omega3"
    BIORAD = "biorad"
    UNKNOWN = "unknown"


@dataclass
class FluorescenceData:
    """
    Normalized fluorescence data structure for both file formats.
    
    This class represents processed fluorescence data in a standardized format,
    regardless of the original file format (BMG Omega3 or BioRad).
    """
    time_points: List[float]        # Time values in hours
    wells: List[str]                # Well identifiers (A1, A2, etc.)
    measurements: np.ndarray        # Raw fluorescence values [wells x timepoints]
    metadata: Dict[str, Any]        # File format, instrument info, etc.
    format_type: FileFormat         # Source file format
    
    def __post_init__(self):
        """Validate data consistency after initialization."""
        if len(self.wells) != self.measurements.shape[0]:
            raise ValueError("Number of wells must match measurement rows")
        if len(self.time_points) != self.measurements.shape[1]:
            raise ValueError("Number of time points must match measurement columns")


@dataclass
class WellInfo:
    """
    Well layout information from layout file.
    
    Contains metadata about each well including sample information,
    well type classification, and grouping for analysis.
    """
    well_id: str                    # A1, B2, etc.
    plate_id: str                   # From layout file
    sample: str                     # Sample identifier
    well_type: str                  # sample, neg_cntrl, unused, etc.
    cell_count: Optional[int]       # Number of cells/capsules
    group_1: Optional[str]          # Primary grouping
    group_2: Optional[str]          # Secondary grouping  
    group_3: Optional[str]          # Tertiary grouping


@dataclass
class CurveFitResult:
    """
    Curve fitting analysis results.
    
    Contains the results of 5-parameter sigmoid curve fitting including
    fitted parameters, quality metrics, and derived values.
    """
    well_id: str
    fitted_params: np.ndarray       # Sigmoid parameters [a, b, c, d, e]
    fitted_curve: np.ndarray        # Fitted y-values
    r_squared: float                # Goodness of fit
    crossing_point: float           # Time at threshold crossing
    threshold_value: float          # Fluorescence threshold
    delta_fluorescence: float       # End - Start fluorescence
    fit_quality: str               # "excellent", "good", "fair", "poor", "failed"
    convergence_info: Dict[str, Any] # Optimization details