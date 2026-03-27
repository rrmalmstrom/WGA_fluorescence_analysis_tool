"""
Export manager for fluorescence analysis results.

This module handles exporting analysis results to various formats including
CSV data files, PDF plots, and comprehensive analysis reports.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as pdf_backend
from matplotlib.figure import Figure
import colorsys

from .models import FluorescenceData, WellInfo, PassFailThresholds


class ExportManager:
    """
    Manages export of analysis results to various file formats.
    
    Provides functionality to export raw data, analysis results,
    statistical summaries, and formatted reports.
    """
    
    def __init__(self):
        """Initialize the export manager."""
        pass
        
    def export_analysis_data(self, analysis_results: Dict[str, Any], filename: str,
                            pass_fail_results: Optional[Dict[str, Any]] = None,
                            include_unused: bool = False):
        """
        Export comprehensive analysis data to CSV in the specified format.
        
        Format: Layout columns | Delta_Fluorescence | CP | Pass_Fail | Raw fluorescence data | Curve fit stats
        
        Args:
            analysis_results: Dictionary containing analysis results
            filename: Output CSV filename
            pass_fail_results: Optional pass/fail analysis results
            include_unused: Whether to include wells marked as 'unused' (default: False)
        """
        # Extract data components
        fluorescence_data = analysis_results.get('fluorescence_data')
        layout_data = analysis_results.get('layout_data', [])
        curve_fits = analysis_results.get('curve_fits', {})
        
        if not fluorescence_data:
            raise ValueError("No fluorescence data found in analysis results")
            
        # Create layout lookup
        layout_dict = {well.well_id: well for well in layout_data} if layout_data else {}
        
        # Create pass/fail lookup from GUI threshold analysis
        pass_fail_dict = {}
        if pass_fail_results:
            # Handle direct PassFailResult objects from GUI analyzer
            if isinstance(pass_fail_results, dict):
                for well_id, result in pass_fail_results.items():
                    if hasattr(result, 'passed'):
                        # This is a PassFailResult object
                        if result.passed:
                            pass_fail_dict[well_id] = 'Pass'
                        else:
                            pass_fail_dict[well_id] = 'Fail'
                    elif isinstance(result, dict) and 'overall_result' in result:
                        # Legacy format
                        pass_fail_dict[well_id] = result.get('overall_result', 'N/A')
            # Handle legacy format with 'well_results' key
            elif 'well_results' in pass_fail_results:
                for well_id, result in pass_fail_results['well_results'].items():
                    pass_fail_dict[well_id] = result.get('overall_result', 'N/A')
        
        # Prepare export data
        export_rows = []
        
        for well_id in fluorescence_data.wells:
            well_index = fluorescence_data.wells.index(well_id)
            fluorescence_values = fluorescence_data.measurements[well_index, :]
            
            # Check if we should skip unused wells
            if not include_unused and well_id in layout_dict:
                well_info = layout_dict[well_id]
                if well_info.well_type == 'unused':
                    continue  # Skip this well
            
            # Start with layout information
            row_data = {}
            
            # Extract row and column from well_id for sorting (e.g., A1 -> A, 1)
            if len(well_id) >= 2:
                well_row = well_id[0]  # First character (A, B, C, etc.)
                try:
                    well_col = int(well_id[1:])  # Remaining characters as number
                except ValueError:
                    well_col = 0
            else:
                well_row = ''
                well_col = 0
            
            if well_id in layout_dict:
                well_info = layout_dict[well_id]
                row_data.update({
                    'Plate_ID': well_info.plate_id or '',
                    'Well': well_id,
                    'Type': well_info.well_type or '',
                    'Cell_Count': well_info.cell_count or '',
                    'Group_1': well_info.group_1 or '',
                    'Group_2': well_info.group_2 or '',
                    'Group_3': well_info.group_3 or '',
                    'Sample': well_info.sample or '',
                    # Add sorting columns temporarily
                    '_Well_Row': well_row,
                    '_Well_Col': well_col
                })
            else:
                # Default layout columns if no layout data
                row_data.update({
                    'Plate_ID': '',
                    'Well': well_id,
                    'Type': '',
                    'Cell_Count': '',
                    'Group_1': '',
                    'Group_2': '',
                    'Group_3': '',
                    'Sample': '',
                    # Add sorting columns temporarily
                    '_Well_Row': well_row,
                    '_Well_Col': well_col
                })
            
            # Add analysis results
            delta_fluor = ''
            crossing_point = ''
            r_squared = ''
            fit_quality = ''
            
            if well_id in curve_fits:
                fit_data = curve_fits[well_id]
                
                # Handle different result structures
                if isinstance(fit_data, dict):
                    # New structure from main_window analysis
                    threshold_result = fit_data.get('threshold_result')
                    curve_result = fit_data.get('curve_result')
                    
                    if threshold_result and hasattr(threshold_result, 'fluorescence_change'):
                        delta_fluor = threshold_result.fluorescence_change
                    
                    # Handle crossing point with QC filter logic
                    if threshold_result:
                        if hasattr(threshold_result, 'crossing_time'):
                            if threshold_result.crossing_time is not None:
                                crossing_point = threshold_result.crossing_time
                            else:
                                # Well failed QC filter - no CP value
                                crossing_point = 'Failed QC'
                        elif hasattr(threshold_result, 'success') and not threshold_result.success:
                            # Alternative check for failed analysis
                            crossing_point = 'Failed QC'
                    if curve_result and hasattr(curve_result, 'r_squared'):
                        r_squared = curve_result.r_squared
                    if curve_result and hasattr(curve_result, 'success'):
                        fit_quality = 'Good' if curve_result.success else 'Poor'
                else:
                    # Legacy structure - direct fit result object
                    if hasattr(fit_data, 'fluorescence_change'):
                        delta_fluor = fit_data.fluorescence_change
                    if hasattr(fit_data, 'crossing_point'):
                        crossing_point = fit_data.crossing_point
                    if hasattr(fit_data, 'r_squared'):
                        r_squared = fit_data.r_squared
                    if hasattr(fit_data, 'fit_quality'):
                        fit_quality = fit_data.fit_quality
            
            # Determine pass/fail status using correct logic:
            # 1. QC filter determines if CP exists (FIXED - never changes)
            # 2. GUI thresholds determine pass/fail for wells WITH CP values (DYNAMIC)
            pass_fail_status = 'N/A'
            
            if threshold_result and hasattr(threshold_result, 'success'):
                if threshold_result.success and threshold_result.crossing_time is not None:
                    # Well PASSED QC filter and has a CP value
                    # Apply current GUI threshold values to determine final pass/fail
                    gui_result = pass_fail_dict.get(well_id)
                    if gui_result and gui_result != 'N/A':
                        pass_fail_status = gui_result  # Use current GUI threshold result
                    else:
                        pass_fail_status = 'Pass'  # Default pass if no GUI thresholds applied
                        
                elif not threshold_result.success:
                    # Well FAILED QC filter - no CP calculated, automatic fail
                    if hasattr(threshold_result, 'error_message') and threshold_result.error_message:
                        if 'QC filter failed' in threshold_result.error_message:
                            pass_fail_status = 'Fail (QC)'  # Failed QC filter
                        else:
                            pass_fail_status = 'Fail (Analysis)'  # Other analysis error
                    else:
                        pass_fail_status = 'Fail (QC)'
                else:
                    # Edge case: success=False but no error message
                    pass_fail_status = 'Fail (Analysis)'
            else:
                # No threshold result - fallback to GUI thresholds only
                pass_fail_status = pass_fail_dict.get(well_id, 'N/A')

            # Add analysis columns
            row_data.update({
                'Delta_Fluorescence': delta_fluor,
                'Crossing_Point': crossing_point,
                'Pass_Fail': pass_fail_status
            })
            
            # Add raw fluorescence data (one column per time point)
            for i, time_point in enumerate(fluorescence_data.time_points):
                # Use time point as column name for clarity
                row_data[f'T_{time_point:.2f}h'] = fluorescence_values[i]
            
            # Add curve fitting statistics
            row_data.update({
                'R_Squared': r_squared,
                'Fit_Quality': fit_quality
            })
            
            # Add sigmoid parameters if available
            if well_id in curve_fits:
                fit_data = curve_fits[well_id]
                params = None
                
                if isinstance(fit_data, dict):
                    curve_result = fit_data.get('curve_result')
                    if curve_result and hasattr(curve_result, 'parameters'):
                        params = curve_result.parameters
                else:
                    if hasattr(fit_data, 'fitted_params'):
                        params = fit_data.fitted_params
                
                if params and len(params) >= 5:
                    row_data.update({
                        'Sigmoid_A': params[0],
                        'Sigmoid_B': params[1],
                        'Sigmoid_C': params[2],
                        'Sigmoid_D': params[3],
                        'Sigmoid_E': params[4]
                    })
                else:
                    row_data.update({
                        'Sigmoid_A': '',
                        'Sigmoid_B': '',
                        'Sigmoid_C': '',
                        'Sigmoid_D': '',
                        'Sigmoid_E': ''
                    })
            else:
                row_data.update({
                    'Sigmoid_A': '',
                    'Sigmoid_B': '',
                    'Sigmoid_C': '',
                    'Sigmoid_D': '',
                    'Sigmoid_E': ''
                })
                
            export_rows.append(row_data)
            
        # Create DataFrame
        df = pd.DataFrame(export_rows)
        
        # Sort by column number first, then by row letter
        if '_Well_Col' in df.columns and '_Well_Row' in df.columns:
            # Convert well column to numeric for proper sorting
            df['_Well_Col'] = pd.to_numeric(df['_Well_Col'], errors='coerce').fillna(0)
            # Sort by column number first, then by row letter
            df = df.sort_values(['_Well_Col', '_Well_Row'], ascending=[True, True])
            # Remove the temporary sorting columns
            df = df.drop(columns=['_Well_Row', '_Well_Col'])
        
        # Save to CSV
        df.to_csv(filename, index=False)
        
    def export_statistical_summary(self, analysis_results: Dict[str, Any], filename: str):
        """
        Export statistical summary by groups.
        
        Args:
            analysis_results: Dictionary containing analysis results
            filename: Output CSV filename
        """
        layout_data = analysis_results.get('layout_data', [])
        curve_fits = analysis_results.get('curve_fits', {})
        
        if not layout_data or not curve_fits:
            raise ValueError("Insufficient data for statistical summary")
            
        # Group wells by type and groups
        groups = {}
        for well_info in layout_data:
            well_id = well_info.well_id
            if well_id not in curve_fits:
                continue
                
            # Create group key
            group_key = (
                well_info.well_type,
                well_info.group_1 or '',
                well_info.group_2 or '',
                well_info.group_3 or ''
            )
            
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(well_id)
            
        # Calculate statistics for each group
        summary_rows = []
        for group_key, well_ids in groups.items():
            well_type, group_1, group_2, group_3 = group_key
            
            # Collect metrics for this group
            crossing_points = []
            delta_fluors = []
            r_squareds = []
            
            for well_id in well_ids:
                if well_id in curve_fits:
                    fit_result = curve_fits[well_id]
                    
                    if hasattr(fit_result, 'crossing_point') and fit_result.crossing_point is not None:
                        crossing_points.append(fit_result.crossing_point)
                    if hasattr(fit_result, 'fluorescence_change') and fit_result.fluorescence_change is not None:
                        delta_fluors.append(fit_result.fluorescence_change)
                    if hasattr(fit_result, 'r_squared') and fit_result.r_squared is not None:
                        r_squareds.append(fit_result.r_squared)
                        
            # Calculate statistics
            summary_row = {
                'Group_Type': well_type,
                'Group_1': group_1,
                'Group_2': group_2,
                'Group_3': group_3,
                'N_Wells': len(well_ids),
                'N_Analyzed': len([w for w in well_ids if w in curve_fits])
            }
            
            # Crossing point statistics
            if crossing_points:
                summary_row.update({
                    'Mean_Crossing_Point': np.mean(crossing_points),
                    'Std_Crossing_Point': np.std(crossing_points),
                    'Median_Crossing_Point': np.median(crossing_points),
                    'Min_Crossing_Point': np.min(crossing_points),
                    'Max_Crossing_Point': np.max(crossing_points)
                })
            else:
                summary_row.update({
                    'Mean_Crossing_Point': '',
                    'Std_Crossing_Point': '',
                    'Median_Crossing_Point': '',
                    'Min_Crossing_Point': '',
                    'Max_Crossing_Point': ''
                })
                
            # Delta fluorescence statistics
            if delta_fluors:
                summary_row.update({
                    'Mean_Delta_Fluor': np.mean(delta_fluors),
                    'Std_Delta_Fluor': np.std(delta_fluors),
                    'Median_Delta_Fluor': np.median(delta_fluors),
                    'Min_Delta_Fluor': np.min(delta_fluors),
                    'Max_Delta_Fluor': np.max(delta_fluors)
                })
            else:
                summary_row.update({
                    'Mean_Delta_Fluor': '',
                    'Std_Delta_Fluor': '',
                    'Median_Delta_Fluor': '',
                    'Min_Delta_Fluor': '',
                    'Max_Delta_Fluor': ''
                })
                
            # R-squared statistics
            if r_squareds:
                summary_row.update({
                    'Mean_R_Squared': np.mean(r_squareds),
                    'Std_R_Squared': np.std(r_squareds),
                    'Median_R_Squared': np.median(r_squareds),
                    'Min_R_Squared': np.min(r_squareds),
                    'Max_R_Squared': np.max(r_squareds)
                })
            else:
                summary_row.update({
                    'Mean_R_Squared': '',
                    'Std_R_Squared': '',
                    'Median_R_Squared': '',
                    'Min_R_Squared': '',
                    'Max_R_Squared': ''
                })
                
            summary_rows.append(summary_row)
            
        # Create DataFrame and save
        df = pd.DataFrame(summary_rows)
        df.to_csv(filename, index=False)
        
    def export_time_series_data(self, analysis_results: Dict[str, Any], 
                               selected_wells: List[str], filename: str):
        """
        Export time series data for selected wells.
        
        Args:
            analysis_results: Dictionary containing analysis results
            selected_wells: List of well IDs to export
            filename: Output CSV filename
        """
        fluorescence_data = analysis_results.get('fluorescence_data')
        curve_fits = analysis_results.get('curve_fits', {})
        
        if not fluorescence_data:
            raise ValueError("No fluorescence data found in analysis results")
            
        # Prepare export data
        export_data = {'Time_hours': fluorescence_data.time_points}
        
        for well_id in selected_wells:
            if well_id not in fluorescence_data.wells:
                continue
                
            well_index = fluorescence_data.wells.index(well_id)
            fluorescence_values = fluorescence_data.measurements[well_index, :]
            
            # Add raw data
            export_data[f'{well_id}_raw'] = fluorescence_values
            
            # Add fitted data if available
            if well_id in curve_fits:
                fit_result = curve_fits[well_id]
                if hasattr(fit_result, 'fitted_curve') and fit_result.fitted_curve is not None:
                    export_data[f'{well_id}_fitted'] = fit_result.fitted_curve
                    
        # Create DataFrame and save
        df = pd.DataFrame(export_data)
        df.to_csv(filename, index=False)
        
    def export_analysis_report(self, analysis_results: Dict[str, Any], filename: str):
        """
        Export comprehensive analysis report.
        
        Args:
            analysis_results: Dictionary containing analysis results
            filename: Output text filename
        """
        fluorescence_data = analysis_results.get('fluorescence_data')
        layout_data = analysis_results.get('layout_data', [])
        curve_fits = analysis_results.get('curve_fits', {})
        
        with open(filename, 'w') as f:
            # Header
            f.write("Fluorescence Data Analysis Report\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Data summary
            f.write("Data Summary:\n")
            f.write("-" * 20 + "\n")
            if fluorescence_data:
                f.write(f"Total wells: {len(fluorescence_data.wells)}\n")
                f.write(f"Time points: {len(fluorescence_data.time_points)}\n")
                f.write(f"Time range: {min(fluorescence_data.time_points):.2f} - {max(fluorescence_data.time_points):.2f} hours\n")
                f.write(f"File format: {fluorescence_data.format_type.value}\n")
            f.write(f"Layout wells: {len(layout_data)}\n")
            f.write(f"Analyzed wells: {len(curve_fits)}\n\n")
            
            # Analysis summary
            if curve_fits:
                f.write("Analysis Summary:\n")
                f.write("-" * 20 + "\n")
                
                # Quality distribution
                quality_counts = {}
                crossing_points = []
                r_squareds = []
                
                for fit_result in curve_fits.values():
                    if hasattr(fit_result, 'fit_quality'):
                        quality = fit_result.fit_quality
                        quality_counts[quality] = quality_counts.get(quality, 0) + 1
                        
                    if hasattr(fit_result, 'crossing_point') and fit_result.crossing_point is not None:
                        crossing_points.append(fit_result.crossing_point)
                        
                    if hasattr(fit_result, 'r_squared') and fit_result.r_squared is not None:
                        r_squareds.append(fit_result.r_squared)
                        
                f.write("Fit Quality Distribution:\n")
                for quality, count in quality_counts.items():
                    f.write(f"  {quality}: {count} wells\n")
                f.write("\n")
                
                if crossing_points:
                    f.write("Crossing Point Statistics:\n")
                    f.write(f"  Mean: {np.mean(crossing_points):.2f} hours\n")
                    f.write(f"  Std: {np.std(crossing_points):.2f} hours\n")
                    f.write(f"  Range: {np.min(crossing_points):.2f} - {np.max(crossing_points):.2f} hours\n\n")
                    
                if r_squareds:
                    f.write("R-squared Statistics:\n")
                    f.write(f"  Mean: {np.mean(r_squareds):.4f}\n")
                    f.write(f"  Std: {np.std(r_squareds):.4f}\n")
                    f.write(f"  Range: {np.min(r_squareds):.4f} - {np.max(r_squareds):.4f}\n\n")
                    
            # Group analysis if layout data available
            if layout_data and curve_fits:
                f.write("Group Analysis:\n")
                f.write("-" * 20 + "\n")
                
                # Group by type
                type_groups = {}
                for well_info in layout_data:
                    well_type = well_info.well_type
                    if well_type not in type_groups:
                        type_groups[well_type] = []
                    type_groups[well_type].append(well_info.well_id)
                    
                for well_type, well_ids in type_groups.items():
                    analyzed_wells = [w for w in well_ids if w in curve_fits]
                    f.write(f"{well_type}: {len(well_ids)} wells, {len(analyzed_wells)} analyzed\n")
                    
                    if analyzed_wells:
                        type_crossing_points = []
                        for well_id in analyzed_wells:
                            fit_result = curve_fits[well_id]
                            if hasattr(fit_result, 'crossing_point') and fit_result.crossing_point is not None:
                                type_crossing_points.append(fit_result.crossing_point)
                                
                        if type_crossing_points:
                            f.write(f"  Mean crossing point: {np.mean(type_crossing_points):.2f} ± {np.std(type_crossing_points):.2f} hours\n")
                f.write("\n")
                
            f.write("End of Report\n")