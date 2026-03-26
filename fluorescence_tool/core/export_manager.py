"""
Export manager for fluorescence analysis results.

This module handles exporting analysis results to various formats including
CSV data files, PDF plots, and comprehensive analysis reports.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from .models import FluorescenceData, WellInfo


class ExportManager:
    """
    Manages export of analysis results to various file formats.
    
    Provides functionality to export raw data, analysis results,
    statistical summaries, and formatted reports.
    """
    
    def __init__(self):
        """Initialize the export manager."""
        pass
        
    def export_analysis_data(self, analysis_results: Dict[str, Any], filename: str):
        """
        Export comprehensive analysis data to CSV.
        
        Args:
            analysis_results: Dictionary containing analysis results
            filename: Output CSV filename
        """
        # Extract data components
        fluorescence_data = analysis_results.get('fluorescence_data')
        layout_data = analysis_results.get('layout_data', [])
        curve_fits = analysis_results.get('curve_fits', {})
        
        if not fluorescence_data:
            raise ValueError("No fluorescence data found in analysis results")
            
        # Create layout lookup
        layout_dict = {well.well_id: well for well in layout_data} if layout_data else {}
        
        # Prepare export data
        export_rows = []
        
        for well_id in fluorescence_data.wells:
            well_index = fluorescence_data.wells.index(well_id)
            fluorescence_values = fluorescence_data.measurements[well_index, :]
            
            # Base row data
            row_data = {
                'Well': well_id,
                'Plate_ID': '',
                'Sample': '',
                'Type': '',
                'Cell_Count': '',
                'Group_1': '',
                'Group_2': '',
                'Group_3': ''
            }
            
            # Add layout information if available
            if well_id in layout_dict:
                well_info = layout_dict[well_id]
                row_data.update({
                    'Plate_ID': well_info.plate_id,
                    'Sample': well_info.sample,
                    'Type': well_info.well_type,
                    'Cell_Count': well_info.cell_count or '',
                    'Group_1': well_info.group_1 or '',
                    'Group_2': well_info.group_2 or '',
                    'Group_3': well_info.group_3 or ''
                })
                
            # Add curve fitting results if available
            if well_id in curve_fits:
                fit_result = curve_fits[well_id]
                row_data.update({
                    'Crossing_Point': getattr(fit_result, 'crossing_point', ''),
                    'Threshold_Value': getattr(fit_result, 'threshold_value', ''),
                    'Delta_Fluorescence': getattr(fit_result, 'fluorescence_change', ''),
                    'R_Squared': getattr(fit_result, 'r_squared', ''),
                    'Fit_Quality': getattr(fit_result, 'fit_quality', ''),
                })
                
                # Add sigmoid parameters if available
                if hasattr(fit_result, 'fitted_params') and fit_result.fitted_params is not None:
                    params = fit_result.fitted_params
                    if len(params) >= 5:
                        row_data.update({
                            'Sigmoid_A': params[0],
                            'Sigmoid_B': params[1],
                            'Sigmoid_C': params[2],
                            'Sigmoid_D': params[3],
                            'Sigmoid_E': params[4]
                        })
            else:
                # Add empty analysis columns
                row_data.update({
                    'Crossing_Point': '',
                    'Threshold_Value': '',
                    'Delta_Fluorescence': '',
                    'R_Squared': '',
                    'Fit_Quality': '',
                    'Sigmoid_A': '',
                    'Sigmoid_B': '',
                    'Sigmoid_C': '',
                    'Sigmoid_D': '',
                    'Sigmoid_E': ''
                })
                
            # Add raw fluorescence data
            for i, time_point in enumerate(fluorescence_data.time_points):
                row_data[f'Raw_T{i:03d}_{time_point:.2f}h'] = fluorescence_values[i]
                
            # Add fitted curve data if available
            if well_id in curve_fits:
                fit_result = curve_fits[well_id]
                if hasattr(fit_result, 'fitted_curve') and fit_result.fitted_curve is not None:
                    for i, fitted_value in enumerate(fit_result.fitted_curve):
                        time_point = fluorescence_data.time_points[i]
                        row_data[f'Fitted_T{i:03d}_{time_point:.2f}h'] = fitted_value
                        
            export_rows.append(row_data)
            
        # Create DataFrame and save
        df = pd.DataFrame(export_rows)
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