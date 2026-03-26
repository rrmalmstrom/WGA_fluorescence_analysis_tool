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
class PassFailThresholds:
    """
    Pass/fail threshold criteria for analysis results.
    
    Defines the criteria for determining whether a well passes or fails
    based on crossing point (CP) and fluorescence change values.
    """
    cp_threshold: float = 400.0        # CP threshold in minutes (below = PASS)
    fluorescence_change_threshold: float = 500.0  # Fluorescence change threshold (above = PASS)
    enabled: bool = True               # Whether pass/fail analysis is enabled
    
    def __post_init__(self):
        """Validate threshold values."""
        if self.cp_threshold <= 0:
            raise ValueError("CP threshold must be positive")
        if self.fluorescence_change_threshold <= 0:
            raise ValueError("Fluorescence change threshold must be positive")


@dataclass
class PassFailResult:
    """
    Pass/fail analysis result for a single well.
    
    Contains the pass/fail determination based on threshold criteria
    and the values used for the determination.
    """
    well_id: str
    passed: bool                       # True if well passed, False if failed
    cp_value: Optional[float]          # Crossing point value used (minutes)
    fluorescence_change_value: Optional[float] # Fluorescence change value used
    cp_passed: bool                    # Whether CP criterion was met (CP < threshold)
    fluorescence_change_passed: bool   # Whether fluorescence change criterion was met (change > threshold)
    analysis_available: bool           # Whether analysis results were available
    failure_reason: Optional[str]      # Reason for failure if applicable