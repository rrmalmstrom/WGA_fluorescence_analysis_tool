"""
Layout file parser.

Parses layout CSV files containing well metadata, types, and grouping information.
Based on analysis of real layout files and proven parsing logic.
"""

import pandas as pd
from typing import Dict, Optional
from pathlib import Path

from fluorescence_tool.core.models import WellInfo


class LayoutParser:
    """Parser for layout CSV files."""
    
    REQUIRED_COLUMNS = ['Plate_ID', 'Well_Row', 'Well_Col', 'Well', 'Type']
    OPTIONAL_COLUMNS = ['number_of_cells/capsules', 'Group_1', 'Group_2', 'Group_3', 'Sample']
    
    def parse_file(self, file_path: str) -> Dict[str, WellInfo]:
        """
        Parse layout CSV file.
        
        Args:
            file_path: Path to layout CSV file
            
        Returns:
            Dictionary mapping well IDs to WellInfo objects
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            # Read CSV with flexible encoding detection (handles BOM)
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            
            # Validate required columns
            missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            # Parse well information
            well_info_dict = {}
            
            for _, row in df.iterrows():
                well_id = str(row['Well']).strip()
                
                # Skip empty or invalid well IDs
                if not well_id or well_id.lower() == 'nan':
                    continue
                
                # Extract optional fields with safe defaults
                cell_count = self._safe_int(row.get('number_of_cells/capsules'))
                group_1 = self._safe_str(row.get('Group_1'))
                group_2 = self._safe_str(row.get('Group_2'))
                group_3 = self._safe_str(row.get('Group_3'))
                sample = self._safe_str(row.get('Sample', ''))
                
                well_info = WellInfo(
                    well_id=well_id,
                    plate_id=str(row['Plate_ID']).strip(),
                    sample=sample or "",
                    well_type=str(row['Type']).strip().lower(),
                    cell_count=cell_count,
                    group_1=group_1,
                    group_2=group_2,
                    group_3=group_3
                )
                
                well_info_dict[well_id] = well_info
            
            if not well_info_dict:
                raise ValueError("No valid well information found")
            
            return well_info_dict
            
        except Exception as e:
            if isinstance(e, (ValueError, FileNotFoundError)):
                raise
            else:
                raise ValueError(f"Failed to parse layout file: {str(e)}")
    
    def _safe_str(self, value) -> Optional[str]:
        """Safely convert value to string, handling NaN and empty values."""
        if pd.isna(value) or str(value).strip() == '' or str(value).lower() == 'nan':
            return None
        return str(value).strip()
    
    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to integer, handling NaN and invalid values."""
        if pd.isna(value):
            return None
        try:
            # Handle string representations of numbers
            if isinstance(value, str):
                value = value.strip()
                if not value or value.lower() == 'nan':
                    return None
            return int(float(value))
        except (ValueError, TypeError):
            return None