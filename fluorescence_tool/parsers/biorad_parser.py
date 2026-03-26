"""
BioRad format parser.

Parses BioRad tab-separated text files with cycle-based data and user-specified cycle times.
Based on analysis of real BioRad files and proven parsing logic.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from pathlib import Path

from fluorescence_tool.core.models import FluorescenceData, FileFormat


class BioRadParser:
    """Parser for BioRad text format files."""
    
    def parse_file(self, file_path: str, cycle_time_minutes: float) -> FluorescenceData:
        """
        Parse BioRad text file.
        
        Args:
            file_path: Path to BioRad text file
            cycle_time_minutes: Time between cycles in minutes
            
        Returns:
            FluorescenceData object with parsed data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid or cycle time is invalid
        """
        # Validate inputs
        if cycle_time_minutes <= 0:
            raise ValueError("Cycle time must be positive")
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            # Read file with tab separation
            df = pd.read_csv(file_path, sep='\t')
            
            # Validate structure
            if 'Cycle' not in df.columns:
                raise ValueError("BioRad file missing 'Cycle' column")
            
            # Extract well columns (all except 'Cycle' and unnamed columns)
            well_columns = [col for col in df.columns
                          if col != 'Cycle' and not col.startswith('Unnamed')]
            
            if not well_columns:
                raise ValueError("No well data columns found")
            
            # Generate time points from cycle numbers
            cycles = df['Cycle'].values
            time_points = [(cycle - 1) * (cycle_time_minutes / 60.0) for cycle in cycles]
            
            # Extract measurements for valid wells only (transpose to get wells x timepoints)
            measurements_df = df[well_columns]
            
            # Handle any NaN values by replacing with interpolated values
            measurements_df = measurements_df.ffill().bfill()
            
            measurements = measurements_df.values.T
            
            # Create metadata
            metadata = {
                'cycle_time_minutes': cycle_time_minutes,
                'num_cycles': len(cycles),
                'plate_format': self._detect_plate_format(well_columns)
            }
            
            return FluorescenceData(
                time_points=time_points,
                wells=well_columns,
                measurements=measurements,
                metadata=metadata,
                format_type=FileFormat.BIORAD
            )
            
        except Exception as e:
            if isinstance(e, (ValueError, FileNotFoundError)):
                raise
            else:
                raise ValueError(f"Failed to parse BioRad file: {str(e)}")
    
    def _detect_plate_format(self, well_columns: List[str]) -> str:
        """Detect plate format (96-well, 384-well) from well names."""
        max_row = 'A'
        max_col = 1
        
        for well in well_columns:
            if len(well) >= 2:
                row = well[0]
                try:
                    col = int(well[1:])
                    if row > max_row:
                        max_row = row
                    if col > max_col:
                        max_col = col
                except ValueError:
                    continue
        
        # Determine format based on maximum row and column
        if max_row <= 'H' and max_col <= 12:
            return "96-well"
        elif max_row <= 'P' and max_col <= 24:
            return "384-well"
        else:
            return "unknown"