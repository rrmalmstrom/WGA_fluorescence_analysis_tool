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

from ...core.models import FluorescenceData, WellInfo, PassFailThresholds
from ...algorithms.pass_fail_analysis import PassFailAnalyzer


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
        self.show_raw_data = False  # Changed to False by default
        self.show_fitted_curves = True
        self.show_thresholds = True
        self.color_by_scheme = 'Type'  # Default color scheme
        
        # Fixed color scheme for predetermined types (matching plate view)
        self.type_colors = {
            'sample': '#2196F3',      # Blue
            'neg_cntrl': '#FF9800',   # Orange
            'pos_cntrl': '#4CAF50',   # Green
            'unused': '#E0E0E0',      # Light gray
            'unknown': '#9E9E9E',     # Gray
        }
        
        # Default color for any other well types (matching plate view pentagon shapes)
        self.default_other_color = '#9C27B0'  # Purple
        
        # Dynamic colors for Group1 (avoiding type colors)
        self.group1_palette = [
            '#9C27B0', '#E91E63', '#795548', '#607D8B', '#00BCD4',
            '#8BC34A', '#CDDC39', '#FFC107', '#FF5722', '#3F51B5',
            '#009688', '#673AB7', '#FF4081', '#536DFE', '#40C4FF'
        ]
        
        # Color management
        self.well_colors: Dict[str, str] = {}
        self.group1_colors: Dict[str, str] = {}
        
        # Pass/fail analysis
        self.pass_fail_thresholds = PassFailThresholds()
        self.pass_fail_analyzer = PassFailAnalyzer(self.pass_fail_thresholds)
        self.pass_fail_results: Dict[str, Any] = {}
        
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
        self.raw_data_var = tk.BooleanVar(value=False)  # Changed to False
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
            text="CP",
            variable=self.thresholds_var,
            command=self._update_plot_options
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # Color by radio buttons (replacing Group by Type checkbox)
        color_frame = ttk.LabelFrame(options_frame, text="Color by:", padding=2)
        color_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        self.color_by_var = tk.StringVar(value='Type')  # Default to Type
        
        ttk.Radiobutton(
            color_frame,
            text="Type",
            variable=self.color_by_var,
            value='Type',
            command=self._update_plot_options
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Radiobutton(
            color_frame,
            text="Group_1",
            variable=self.color_by_var,
            value='Group_1',
            command=self._update_plot_options
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Radiobutton(
            color_frame,
            text="Group_2",
            variable=self.color_by_var,
            value='Group_2',
            command=self._update_plot_options
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Radiobutton(
            color_frame,
            text="Group_3",
            variable=self.color_by_var,
            value='Group_3',
            command=self._update_plot_options
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # Pass/Fail threshold controls
        threshold_frame = ttk.LabelFrame(control_frame, text="Pass/Fail Thresholds", padding=5)
        threshold_frame.pack(fill=tk.X, pady=(5, 0))
        
        # CP threshold control
        cp_frame = ttk.Frame(threshold_frame)
        cp_frame.pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Label(cp_frame, text="CP Threshold (hours):").pack(side=tk.LEFT, padx=(0, 5))
        self.cp_threshold_var = tk.StringVar(value=str(self.pass_fail_thresholds.cp_threshold))
        self.cp_threshold_entry = ttk.Entry(
            cp_frame,
            textvariable=self.cp_threshold_var,
            width=8,
            validate='key',
            validatecommand=(self.register(self._validate_float), '%P')
        )
        self.cp_threshold_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.cp_threshold_entry.bind('<KeyRelease>', self._on_threshold_change)
        
        # Fluorescence change threshold control
        fluor_frame = ttk.Frame(threshold_frame)
        fluor_frame.pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Label(fluor_frame, text="Fluorescence Threshold:").pack(side=tk.LEFT, padx=(0, 5))
        self.fluor_threshold_var = tk.StringVar(value=str(self.pass_fail_thresholds.fluorescence_change_threshold))
        self.fluor_threshold_entry = ttk.Entry(
            fluor_frame,
            textvariable=self.fluor_threshold_var,
            width=8,
            validate='key',
            validatecommand=(self.register(self._validate_float), '%P')
        )
        self.fluor_threshold_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.fluor_threshold_entry.bind('<KeyRelease>', self._on_threshold_change)
        
        # Enable/disable checkbox
        self.pass_fail_enabled_var = tk.BooleanVar(value=self.pass_fail_thresholds.enabled)
        ttk.Checkbutton(
            threshold_frame,
            text="Enable Pass/Fail",
            variable=self.pass_fail_enabled_var,
            command=self._on_threshold_change
        ).pack(side=tk.LEFT, padx=(15, 0))
        
        # Pass/fail summary label
        self.pass_fail_summary_var = tk.StringVar(value="No analysis results")
        self.pass_fail_summary_label = ttk.Label(
            threshold_frame,
            textvariable=self.pass_fail_summary_var,
            foreground="blue"
        )
        self.pass_fail_summary_label.pack(side=tk.LEFT, padx=(15, 0))
        
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
        """Update plot display based on option checkboxes and radio buttons."""
        self.show_raw_data = self.raw_data_var.get()
        self.show_fitted_curves = self.fitted_curves_var.get()
        self.show_thresholds = self.thresholds_var.get()
        self.color_by_scheme = self.color_by_var.get()  # Use radio button value
        
        # Debug output
        # print(f"Plot options updated: raw={self.show_raw_data}, fitted={self.show_fitted_curves}, CP={self.show_thresholds}")
        
        if self.selected_wells and self.analysis_results:
            # print(f"Replotting {len(self.selected_wells)} wells with analysis results")
            self._plot_selected_wells()
        else:
            # print(f"No replot: selected_wells={len(self.selected_wells) if self.selected_wells else 0}, analysis_results={bool(self.analysis_results)}")
            pass
    
    def _validate_float(self, value):
        """Validate that input is a valid float."""
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def _on_threshold_change(self, event=None):
        """Handle changes to pass/fail threshold values."""
        try:
            # Get current values from GUI
            cp_threshold = float(self.cp_threshold_var.get()) if self.cp_threshold_var.get() else 6.5
            fluor_threshold = float(self.fluor_threshold_var.get()) if self.fluor_threshold_var.get() else 500.0
            enabled = self.pass_fail_enabled_var.get()
            
            # Update thresholds
            self.pass_fail_thresholds = PassFailThresholds(
                cp_threshold=cp_threshold,
                fluorescence_change_threshold=fluor_threshold,
                enabled=enabled
            )
            
            # Update analyzer
            self.pass_fail_analyzer.update_thresholds(self.pass_fail_thresholds)
            
            # Recalculate pass/fail results if we have analysis data
            if self.analysis_results:
                self._update_pass_fail_analysis()
                
        except ValueError:
            # Invalid input, ignore for now
            pass
    
    def _update_pass_fail_analysis(self):
        """Update pass/fail analysis results and notify main window."""
        if not self.analysis_results:
            return
            
        # Calculate pass/fail results
        self.pass_fail_results = self.pass_fail_analyzer.analyze_all_wells(self.analysis_results)
        
        # Update summary display
        summary_stats = self.pass_fail_analyzer.get_summary_statistics(self.pass_fail_results)
        if summary_stats['analyzed_wells'] > 0:
            summary_text = f"Pass/Fail: {summary_stats['passed_wells']}/{summary_stats['analyzed_wells']} ({summary_stats['pass_rate']:.1f}%)"
        else:
            summary_text = "No wells analyzed"
        self.pass_fail_summary_var.set(summary_text)
        
        # Notify main window to update plate view
        if hasattr(self.main_window, 'update_pass_fail_results'):
            self.main_window.update_pass_fail_results(self.pass_fail_results)
            
    def update_analysis_results(self, analysis_results: Dict[str, Any]):
        """Update with new analysis results."""
        self.analysis_results = analysis_results
        
        # Extract data references
        if 'fluorescence_data' in analysis_results:
            self.fluorescence_data = analysis_results['fluorescence_data']
        if 'layout_data' in analysis_results:
            self.layout_data = {well.well_id: well for well in analysis_results['layout_data']}
            
        self.plot_info_var.set("Analysis completed - select wells to view plots")
        
        # Trigger pass/fail analysis
        self._update_pass_fail_analysis()
        
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
        
        # Group wells by color scheme if layout data is available
        if self.layout_data:
            well_groups = self._group_wells_by_color_scheme()
        else:
            well_groups = {'All Wells': self.selected_wells}
            
        # Plot each group
        legend_elements = []
        
        for group_name, wells in well_groups.items():
            if not wells:
                continue
                
            # Get group color using consistent color scheme
            group_color = self._get_group_plot_color(group_name)
            
            # Plot wells in this group
            for i, well_id in enumerate(wells):
                if well_id not in self.fluorescence_data.wells:
                    continue
                    
                well_index = self.fluorescence_data.wells.index(well_id)
                fluorescence_values = self.fluorescence_data.measurements[well_index, :]
                
                # Determine line style and alpha
                alpha = 0.7 if len(wells) > 1 else 1.0
                raw_line_style = '--'  # Raw data now uses dashed lines
                
                # Plot raw data
                if self.show_raw_data:
                    line = ax.plot(
                        time_points, fluorescence_values,
                        color=group_color, alpha=alpha, linewidth=1.5,
                        linestyle=raw_line_style,
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
                            linestyle='-',  # Fitted curves now use solid lines
                            label=f"{group_name} (fitted)" if i == 0 else ""
                        )[0]
                        
                        if i == 0:  # Add fitted curve to legend
                            legend_elements.append(fitted_line)
                            
                # Plot crossing point indicators
                if (self.show_thresholds and
                    'curve_fits' in self.analysis_results and
                    well_id in self.analysis_results['curve_fits']):
                    
                    well_results = self.analysis_results['curve_fits'][well_id]
                    crossing_point = well_results.get('crossing_point')
                    threshold_value = well_results.get('threshold_value')

                    if crossing_point is not None:
                        # print(f"\n=== DEBUG: Plotting CP for well {well_id} ===")
                        # print(f"Crossing point time: {crossing_point:.2f}")
                        # print(f"Threshold value: {threshold_value}")
                        
                        # Get fluorescence value at crossing point for plotting
                        # CRITICAL FIX: Always use sigmoid calculation for second derivative method
                        curve_result = well_results.get('curve_result')
                        threshold_result = well_results.get('threshold_result')
                        
                        # Check if this is second derivative method (no threshold_value for plotting)
                        is_second_derivative = (threshold_result and
                                              threshold_result.crossing_method == "qc_second_derivative" and
                                              curve_result and curve_result.success and curve_result.parameters and
                                              getattr(curve_result, 'fit_type', 'sigmoid') == 'sigmoid')
                        
                        if is_second_derivative:
                            # Second derivative method: calculate fluorescence using sigmoid equation
                            # This ensures CP is plotted exactly on the fitted curve
                            from ...algorithms.curve_fitting import CurveFitter
                            curve_fitter = CurveFitter()
                            
                            # Calculate fluorescence at CP using the exact sigmoid equation
                            cp_fluorescence = curve_fitter.sigmoid_5param(
                                np.array([crossing_point]), *curve_result.parameters)[0]
                            # print(f"Calculated CP fluorescence using sigmoid: {cp_fluorescence:.2f}")
                            # print(f"Using parameters: {curve_result.parameters}")
                            
                        elif threshold_value is not None:
                            # Legacy method: use threshold value
                            cp_fluorescence = threshold_value
                            # print(f"Using legacy threshold value: {cp_fluorescence:.2f}")
                        else:
                            # Fallback: interpolate from fitted curve array
                            fitted_curve = well_results.get('fitted_curve')
                            if fitted_curve is not None:
                                cp_fluorescence = np.interp(crossing_point, time_points, fitted_curve)
                                # print(f"Interpolated from fitted curve: {cp_fluorescence:.2f}")
                            else:
                                # Final fallback: use raw data
                                cp_fluorescence = np.interp(crossing_point, time_points, fluorescence_values)
                                # print(f"Interpolated from raw data: {cp_fluorescence:.2f}")
                        
                        # print(f"Final CP coordinates: ({crossing_point:.2f}, {cp_fluorescence:.2f})")
                        
                        # Crossing point marker
                        ax.plot(
                            crossing_point, cp_fluorescence,
                            marker='o', markersize=8, color=group_color,
                            markeredgecolor='black', markeredgewidth=2,
                            zorder=10  # Ensure marker appears on top
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
        
    def _group_wells_by_color_scheme(self) -> Dict[str, List[str]]:
        """Group selected wells by the current color scheme."""
        groups = {}
        
        for well_id in self.selected_wells:
            if well_id in self.layout_data:
                well_info = self.layout_data[well_id]
                
                # Get grouping value based on selected color scheme
                if self.color_by_scheme == 'Type':
                    group_value = well_info.well_type
                elif self.color_by_scheme == 'Group_1':
                    group_value = well_info.group_1 or 'No Group_1'
                elif self.color_by_scheme == 'Group_2':
                    group_value = well_info.group_2 or 'No Group_2'
                elif self.color_by_scheme == 'Group_3':
                    group_value = well_info.group_3 or 'No Group_3'
                else:
                    group_value = 'unknown'
                    
                if group_value not in groups:
                    groups[group_value] = []
                groups[group_value].append(well_id)
            else:
                # Unknown well
                if 'unknown' not in groups:
                    groups['unknown'] = []
                groups['unknown'].append(well_id)
                
        return groups
        
    def _get_group_plot_color(self, group_name: str) -> str:
        """Get consistent color for a group in plots based on current color scheme."""
        if group_name == 'All Wells':
            return '#2196F3'  # Default blue for mixed selection
            
        # Handle colors based on current color scheme
        if self.color_by_scheme == 'Type':
            # Use fixed colors for predetermined types
            if group_name in self.type_colors:
                return self.type_colors[group_name]
            else:
                # Use purple for other types (like OTHER)
                return self.default_other_color
        else:
            # For Group_1, Group_2, Group_3 - use dynamic color assignment
            if group_name not in self.group1_colors:
                color_index = len(self.group1_colors) % len(self.group1_palette)
                self.group1_colors[group_name] = self.group1_palette[color_index]
            return self.group1_colors[group_name]
        
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
                
    def _get_plate_id(self) -> Optional[str]:
        """
        Extract the plate ID from the loaded layout data.
        
        Returns:
            The plate_id string if exactly one unique non-empty value exists,
            otherwise None.
        """
        if not self.layout_data:
            return None
        
        plate_ids = set()
        for well_info in self.layout_data.values():
            pid = well_info.plate_id
            if pid and str(pid).strip() and str(pid).strip().lower() != 'nan':
                plate_ids.add(str(pid).strip())
        
        if len(plate_ids) == 1:
            return plate_ids.pop()
        return None

    def _export_data(self):
        """Export comprehensive analysis data to CSV file using the new format."""
        if not self.analysis_results:
            tk.messagebox.showwarning("Warning", "No analysis results to export")
            return
        
        # Ask user if they want to include unused wells (default: No)
        include_unused = tk.messagebox.askyesno(
            "Export Options",
            "Include wells marked as 'unused' in the export?\n\n" +
            "• Yes: Export all wells including unused ones\n" +
            "• No: Export only analyzed wells (recommended)",
            default=tk.messagebox.NO
        )
        
        # Build the auto-generated filename from the plate_id
        plate_id = self._get_plate_id()
        
        if plate_id:
            # Sanitize plate_id for use in a filename (replace any path-unsafe chars)
            import re
            safe_plate_id = re.sub(r'[\\/:*?"<>|]', '_', plate_id)
            auto_filename = f"{safe_plate_id}_amplification_kinetics_summary.csv"
            
            # Save to the directory the script was launched from
            from pathlib import Path
            save_dir = Path.cwd()
            save_path = str(save_dir / auto_filename)
            
            # Inform the user of the auto-generated path
            proceed = tk.messagebox.askyesno(
                "Save Data",
                f"The file will be saved as:\n\n{save_path}\n\nProceed?",
                default=tk.messagebox.YES
            )
            if not proceed:
                return
            filename = save_path
        else:
            # No layout data or ambiguous plate_id — fall back to file dialog
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                title="Export Analysis Data",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            if not filename:
                return
        
        try:
            # Recalculate pass/fail results with current threshold values before export
            self._update_pass_fail_analysis()
            
            # Use the comprehensive export manager with the new format
            from ...core.export_manager import ExportManager
            export_manager = ExportManager()
            
            # Export with the latest pass/fail results and unused well preference
            export_manager.export_analysis_data(
                self.analysis_results,
                filename,
                pass_fail_results=self.pass_fail_results,
                include_unused=include_unused
            )
            
            wells_exported = "all wells" if include_unused else "analyzed wells only"
            self.main_window.update_status(f"Analysis data exported to {filename} ({wells_exported})")
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to export data:\n{str(e)}")
                
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