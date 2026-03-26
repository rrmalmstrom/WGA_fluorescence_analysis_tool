"""
Real-time plot panel with matplotlib integration.

This module provides interactive plotting capabilities for fluorescence data
with real-time updates based on well selection, curve fitting visualization,
and export functionality.
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import colorsys

from ...core.models import FluorescenceData, WellInfo, CurveFitResult


class PlotPanel(ttk.Frame):
    """
    Real-time plotting panel with matplotlib integration.
    
    Provides interactive plotting of fluorescence time series data with
    curve fitting overlays, threshold indicators, and export capabilities.
    """
    
    def __init__(self, parent, main_window):
        """
        Initialize the plot panel component.
        
        Args:
            parent: Parent tkinter widget
            main_window: Reference to main application window
        """
        super().__init__(parent)
        self.main_window = main_window
        
        # Data references
        self.fluorescence_data: Optional[FluorescenceData] = None
        self.layout_data: Dict[str, WellInfo] = {}
        self.analysis_results: Dict[str, Any] = {}
        self.selected_wells: List[str] = []
        
        # Plot configuration
        self.show_raw_data = True
        self.show_fitted_curves = True
        self.show_thresholds = True
        self.group_by_type = True
        
        # Color management
        self.well_colors: Dict[str, str] = {}
        self.color_palette = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the plot panel user interface."""
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Control panel at top
        control_frame = ttk.LabelFrame(main_frame, text="Plot Controls", padding=5)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Plot options
        options_frame = ttk.Frame(control_frame)
        options_frame.pack(fill=tk.X)
        
        # Checkboxes for plot elements
        self.raw_data_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Raw Data",
            variable=self.raw_data_var,
            command=self._update_plot_options
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.fitted_curves_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Fitted Curves",
            variable=self.fitted_curves_var,
            command=self._update_plot_options
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.thresholds_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Thresholds",
            variable=self.thresholds_var,
            command=self._update_plot_options
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.group_by_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Group by Type",
            variable=self.group_by_var,
            command=self._update_plot_options
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # Export controls
        export_frame = ttk.Frame(control_frame)
        export_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(
            export_frame,
            text="Export Plot",
            command=self._export_plot,
            width=12
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            export_frame,
            text="Save Data",
            command=self._export_data,
            width=12
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # Plot info label
        self.plot_info_var = tk.StringVar(value="No data to display")
        self.plot_info_label = ttk.Label(
            export_frame,
            textvariable=self.plot_info_var,
            foreground="gray"
        )
        self.plot_info_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # Matplotlib figure and canvas
        plot_frame = ttk.LabelFrame(main_frame, text="Fluorescence Plots", padding=5)
        plot_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(10, 6), dpi=100, facecolor='white')
        self.canvas = FigureCanvasTkAgg(self.figure, plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Navigation toolbar
        toolbar_frame = ttk.Frame(plot_frame)
        toolbar_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
        
        # Initialize empty plot
        self._create_empty_plot()
        
    def _create_empty_plot(self):
        """Create an empty plot with instructions."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        ax.text(0.5, 0.5, 'Select wells from the plate view to display plots',
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=12, color='gray')
        
        ax.set_xlabel('Time (hours)')
        ax.set_ylabel('Fluorescence (RFU)')
        ax.set_title('Fluorescence Time Series')
        ax.grid(True, alpha=0.3)
        
        self.canvas.draw()
        
    def _update_plot_options(self):
        """Update plot display based on option checkboxes."""
        self.show_raw_data = self.raw_data_var.get()
        self.show_fitted_curves = self.fitted_curves_var.get()
        self.show_thresholds = self.thresholds_var.get()
        self.group_by_type = self.group_by_var.get()
        
        # Debug output
        print(f"Plot options updated: raw={self.show_raw_data}, fitted={self.show_fitted_curves}, thresholds={self.show_thresholds}")
        
        if self.selected_wells and self.analysis_results:
            print(f"Replotting {len(self.selected_wells)} wells with analysis results")
            self._plot_selected_wells()
        else:
            print(f"No replot: selected_wells={len(self.selected_wells) if self.selected_wells else 0}, analysis_results={bool(self.analysis_results)}")
            
    def update_analysis_results(self, analysis_results: Dict[str, Any]):
        """Update with new analysis results."""
        self.analysis_results = analysis_results
        
        # Extract data references
        if 'fluorescence_data' in analysis_results:
            self.fluorescence_data = analysis_results['fluorescence_data']
        if 'layout_data' in analysis_results:
            self.layout_data = {well.well_id: well for well in analysis_results['layout_data']}
            
        self.plot_info_var.set("Analysis completed - select wells to view plots")
        
    def update_selected_wells(self, selected_wells: List[str]):
        """Update plot with newly selected wells."""
        self.selected_wells = selected_wells
        
        if selected_wells and self.analysis_results:
            self._plot_selected_wells()
        else:
            self._create_empty_plot()
            
    def _plot_selected_wells(self):
        """Plot fluorescence data for selected wells."""
        if not self.selected_wells or not self.fluorescence_data:
            self._create_empty_plot()
            return
            
        self.figure.clear()
        
        # Create subplot
        ax = self.figure.add_subplot(111)
        
        # Get time points
        time_points = np.array(self.fluorescence_data.time_points)
        
        # Group wells by type if requested
        if self.group_by_type and self.layout_data:
            well_groups = self._group_wells_by_type()
        else:
            well_groups = {'All Wells': self.selected_wells}
            
        # Plot each group
        legend_elements = []
        color_index = 0
        
        for group_name, wells in well_groups.items():
            if not wells:
                continue
                
            # Get group color
            group_color = self.color_palette[color_index % len(self.color_palette)]
            color_index += 1
            
            # Plot wells in this group
            for i, well_id in enumerate(wells):
                if well_id not in self.fluorescence_data.wells:
                    continue
                    
                well_index = self.fluorescence_data.wells.index(well_id)
                fluorescence_values = self.fluorescence_data.measurements[well_index, :]
                
                # Determine line style and alpha
                alpha = 0.7 if len(wells) > 1 else 1.0
                line_style = '-' if i == 0 else '-'  # Could vary for different wells
                
                # Plot raw data
                if self.show_raw_data:
                    line = ax.plot(
                        time_points, fluorescence_values,
                        color=group_color, alpha=alpha, linewidth=1.5,
                        linestyle=line_style,
                        label=f"{group_name}" if i == 0 else ""
                    )[0]
                    
                    if i == 0:  # Add to legend only once per group
                        legend_elements.append(line)
                        
                # Plot fitted curve if available
                if (self.show_fitted_curves and
                    'curve_fits' in self.analysis_results and
                    well_id in self.analysis_results['curve_fits']):
                    
                    well_results = self.analysis_results['curve_fits'][well_id]
                    fitted_curve = well_results.get('fitted_curve')
                    
                    if fitted_curve is not None:
                        fitted_line = ax.plot(
                            time_points, fitted_curve,
                            color=group_color, alpha=0.9, linewidth=2,
                            linestyle='--',
                            label=f"{group_name} (fitted)" if i == 0 else ""
                        )[0]
                        
                        if i == 0:  # Add fitted curve to legend
                            legend_elements.append(fitted_line)
                            
                # Plot threshold indicators
                if (self.show_thresholds and
                    'curve_fits' in self.analysis_results and
                    well_id in self.analysis_results['curve_fits']):
                    
                    well_results = self.analysis_results['curve_fits'][well_id]
                    crossing_point = well_results.get('crossing_point')
                    threshold_value = well_results.get('threshold_value')
                    
                    if crossing_point is not None and threshold_value is not None:
                        # Threshold crossing point
                        ax.plot(
                            crossing_point, threshold_value,
                            marker='o', markersize=6, color=group_color,
                            markeredgecolor='black', markeredgewidth=1
                        )
                        
        # Customize plot
        ax.set_xlabel('Time (hours)', fontsize=12)
        ax.set_ylabel('Fluorescence (RFU)', fontsize=12)
        ax.set_title(f'Fluorescence Time Series ({len(self.selected_wells)} wells)', fontsize=14)
        ax.grid(True, alpha=0.3)
        
        # Add legend if we have multiple groups
        if len(legend_elements) > 1:
            ax.legend(handles=legend_elements, loc='best', framealpha=0.9)
            
        # Auto-scale axes
        ax.relim()
        ax.autoscale()
        
        # Update plot info
        self.plot_info_var.set(f"Displaying {len(self.selected_wells)} wells")
        
        # Refresh canvas
        self.figure.tight_layout()
        self.canvas.draw()
        
    def _group_wells_by_type(self) -> Dict[str, List[str]]:
        """Group selected wells by their type from layout data."""
        groups = {}
        
        for well_id in self.selected_wells:
            if well_id in self.layout_data:
                well_type = self.layout_data[well_id].well_type
                if well_type not in groups:
                    groups[well_type] = []
                groups[well_type].append(well_id)
            else:
                # Unknown type
                if 'unknown' not in groups:
                    groups['unknown'] = []
                groups['unknown'].append(well_id)
                
        return groups
        
    def _generate_colors(self, n_colors: int) -> List[str]:
        """Generate n distinct colors using HSV color space."""
        colors = []
        for i in range(n_colors):
            hue = i / n_colors
            saturation = 0.7
            value = 0.9
            rgb = colorsys.hsv_to_rgb(hue, saturation, value)
            hex_color = '#{:02x}{:02x}{:02x}'.format(
                int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
            )
            colors.append(hex_color)
        return colors
        
    def _export_plot(self):
        """Export current plot to file."""
        if not self.selected_wells:
            tk.messagebox.showwarning("Warning", "No wells selected to export")
            return
            
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            title="Export Plot",
            defaultextension=".pdf",
            filetypes=[
                ("PDF files", "*.pdf"),
                ("PNG files", "*.png"),
                ("SVG files", "*.svg"),
                ("EPS files", "*.eps"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            try:
                # Save with high DPI for publication quality
                self.figure.savefig(
                    filename,
                    dpi=300,
                    bbox_inches='tight',
                    facecolor='white',
                    edgecolor='none'
                )
                self.main_window.update_status(f"Plot exported to {filename}")
            except Exception as e:
                tk.messagebox.showerror("Error", f"Failed to export plot:\\n{str(e)}")
                
    def _export_data(self):
        """Export plot data to CSV file."""
        if not self.selected_wells or not self.fluorescence_data:
            tk.messagebox.showwarning("Warning", "No data to export")
            return
            
        from tkinter import filedialog
        import pandas as pd
        
        filename = filedialog.asksaveasfilename(
            title="Export Plot Data",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # Prepare data for export
                time_points = self.fluorescence_data.time_points
                export_data = {'Time_hours': time_points}
                
                # Add raw data for selected wells
                for well_id in self.selected_wells:
                    if well_id in self.fluorescence_data.wells:
                        well_index = self.fluorescence_data.wells.index(well_id)
                        fluorescence_values = self.fluorescence_data.measurements[well_index, :]
                        export_data[f'{well_id}_raw'] = fluorescence_values
                        
                        # Add fitted data if available
                        if ('curve_fits' in self.analysis_results and
                            well_id in self.analysis_results['curve_fits']):
                            well_results = self.analysis_results['curve_fits'][well_id]
                            fitted_curve = well_results.get('fitted_curve')
                            if fitted_curve is not None:
                                export_data[f'{well_id}_fitted'] = fitted_curve
                                
                # Create DataFrame and save
                df = pd.DataFrame(export_data)
                df.to_csv(filename, index=False)
                
                self.main_window.update_status(f"Plot data exported to {filename}")
            except Exception as e:
                tk.messagebox.showerror("Error", f"Failed to export data:\\n{str(e)}")
                
    def clear_plots(self):
        """Clear all plots and reset to empty state."""
        self.selected_wells.clear()
        self._create_empty_plot()
        self.plot_info_var.set("No data to display")
        
    def export_plot(self, filename: str):
        """Export plot to specified filename (called from main window)."""
        if not self.selected_wells:
            raise ValueError("No wells selected to export")
            
        # Save with high DPI for publication quality
        self.figure.savefig(
            filename,
            dpi=300,
            bbox_inches='tight',
            facecolor='white',
            edgecolor='none'
        )