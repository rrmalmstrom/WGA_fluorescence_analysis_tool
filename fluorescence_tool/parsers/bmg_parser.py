"""
BMG Omega3 format parser.

Parses BMG Omega3 CSV files with automatic time conversion and metadata extraction.
Based on analysis of real BMG files and proven parsing logic from existing code.
"""

import re
import csv
import numpy as np
from typing import List, Dict, Any, Tuple
from pathlib import Path

from fluorescence_tool.core.models import FluorescenceData, FileFormat


class BMGOmega3Parser:
    """Parser for BMG Omega3 CSV format files."""
    
    def __init__(self):
        """Initialize parser with time parsing patterns."""
        # Regex patterns for time parsing (from existing proven code)
        self.time_pattern = re.compile(r'^(\d+)\s*h(?:\s*(\d+)\s*min)?$')
        self.min_pattern = re.compile(r'^(\d+)\s*min$')
    
    def parse_file(self, file_path: str) -> FluorescenceData:
        """
        Parse BMG Omega3 CSV file.
        
        Args:
            file_path: Path to BMG CSV file
            
        Returns:
            FluorescenceData object with parsed data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            # Read all lines from the file
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
            
            # Validate minimum file length
            if len(lines) < 9:
                raise ValueError("BMG file too short, minimum 9 lines required")
            
            # Extract metadata from header lines (rows 1-6)
            metadata = self._extract_metadata(lines[:6])
            
            # Parse time headers from row 8 (index 7)
            time_points = self._parse_time_headers(lines[7])
            
            # Parse well data from rows 9+ (index 8+)
            wells, measurements = self._parse_well_data(lines[8:], len(time_points))
            
            return FluorescenceData(
                time_points=time_points,
                wells=wells,
                measurements=measurements,
                metadata=metadata,
                format_type=FileFormat.BMG_OMEGA3
            )
            
        except Exception as e:
            raise ValueError(f"Failed to parse BMG file: {str(e)}")
    
    def _extract_metadata(self, header_lines: List[str]) -> Dict[str, Any]:
        """Extract metadata from header lines."""
        metadata = {}
        
        # Row 1: User info
        if len(header_lines) > 0:
            user_line = header_lines[0].strip()
            user_match = re.search(r'User:\s*([^,]+)', user_line)
            if user_match:
                metadata['user'] = user_match.group(1).strip()
        
        # Row 2: Test info
        if len(header_lines) > 1:
            test_line = header_lines[1].strip()
            test_match = re.search(r'Test name:\s*([^,]+)', test_line)
            date_match = re.search(r'Date:\s*([^,]+)', test_line)
            time_match = re.search(r'Time:\s*([^,]+)', test_line)
            
            if test_match:
                metadata['test_name'] = test_match.group(1).strip()
            if date_match:
                metadata['date'] = date_match.group(1).strip()
            if time_match:
                metadata['time'] = time_match.group(1).strip()
        
        # Row 4: Plate ID (ID1)
        if len(header_lines) > 3:
            id_line = header_lines[3].strip()
            id_match = re.search(r'ID1:\s*([^,]+)', id_line)
            if id_match:
                metadata['plate_id'] = id_match.group(1).strip()
        
        return metadata
    
    def _parse_time_headers(self, time_header_line: str) -> List[float]:
        """Parse time point headers into decimal hours."""
        # Split by comma and clean up
        parts = [part.strip() for part in time_header_line.split(',')]
        
        # Skip first 3 columns (Well Row, Well Col, Content) and find time headers
        time_headers = []
        for part in parts[3:]:
            if part and part.lower() != 'time':
                time_headers.append(part)
        
        # Convert time strings to decimal hours
        time_points = []
        for header in time_headers:
            try:
                time_hours = self._parse_time_string(header)
                time_points.append(time_hours)
            except ValueError as e:
                # Skip invalid time headers but warn
                print(f"Warning: Skipping invalid time header '{header}': {e}")
                continue
        
        if not time_points:
            raise ValueError("No valid time points found in header")
        
        return time_points
    
    def _parse_time_string(self, time_str: str) -> float:
        """
        Parse BMG time format strings into decimal hours.
        
        Supports formats:
        - "1 h 30 min" → 1.5 hours
        - "2 h" → 2.0 hours
        - "45 min" → 0.75 hours
        """
        time_str = time_str.strip()
        
        if not time_str:
            raise ValueError("Empty time string")
        
        # Try full pattern (hours with optional minutes)
        match = self.time_pattern.match(time_str)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2)) if match.group(2) else 0
            
            if minutes >= 60:
                raise ValueError(f"Invalid minutes value: {minutes}")
            
            return hours + (minutes / 60.0)
        
        # Try minutes-only pattern
        match = self.min_pattern.match(time_str)
        if match:
            minutes = int(match.group(1))
            return minutes / 60.0
        
        raise ValueError(f"Invalid time format: '{time_str}'")
    
    def _parse_well_data(self, data_lines: List[str], num_timepoints: int) -> Tuple[List[str], np.ndarray]:
        """Parse well data from data lines."""
        wells = []
        measurements_list = []
        
        for line in data_lines:
            line = line.strip()
            if not line:
                continue
                
            # Split by comma
            parts = [part.strip() for part in line.split(',')]
            
            if len(parts) < 4:  # Need at least row, col, well, and one measurement
                continue
            
            # Extract well information
            well_row = parts[0]
            well_col = parts[1]
            well_id = parts[2]
            
            if not well_row or not well_col or not well_id:
                continue
            
            # Extract measurements (skip first 3 columns)
            measurement_strs = parts[3:3+num_timepoints]
            
            try:
                # Convert to float, handling empty strings
                measurements = []
                for m_str in measurement_strs:
                    if m_str.strip():
                        measurements.append(float(m_str.strip()))
                    else:
                        # Handle missing values - could use interpolation or skip
                        measurements.append(np.nan)
                
                # Only include wells with the expected number of measurements
                if len(measurements) == num_timepoints:
                    wells.append(well_id)
                    measurements_list.append(measurements)
                    
            except ValueError:
                # Skip wells with invalid measurement data
                print(f"Warning: Skipping well {well_id} due to invalid measurements")
                continue
        
        if not wells:
            raise ValueError("No valid well data found")
        
        # Convert to numpy array
        measurements_array = np.array(measurements_list)
        
        # Handle any NaN values by interpolation or removal
        if np.any(np.isnan(measurements_array)):
            print("Warning: Found NaN values in measurements, attempting to clean")
            measurements_array = self._clean_measurements(measurements_array)
        
        return wells, measurements_array
    
    def _clean_measurements(self, measurements: np.ndarray) -> np.ndarray:
        """Clean measurements by handling NaN values."""
        # Simple approach: replace NaN with interpolated values
        for i in range(measurements.shape[0]):
            row = measurements[i]
            if np.any(np.isnan(row)):
                # Use linear interpolation for missing values
                valid_indices = ~np.isnan(row)
                if np.sum(valid_indices) >= 2:  # Need at least 2 points to interpolate
                    x_valid = np.where(valid_indices)[0]
                    y_valid = row[valid_indices]
                    x_all = np.arange(len(row))
                    row_interpolated = np.interp(x_all, x_valid, y_valid)
                    measurements[i] = row_interpolated
                else:
                    # If too few valid points, use mean of valid values
                    mean_val = np.nanmean(row)
                    measurements[i] = np.where(np.isnan(row), mean_val, row)
        
        return measurements