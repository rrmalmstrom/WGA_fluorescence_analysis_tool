"""
Dialog components for export and settings.

This module provides various dialog windows for export functionality,
settings configuration, and user interactions.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Optional, Dict, Any, Callable


class ExportDialog(tk.Toplevel):
    """
    Export dialog for configuring plot and data export options.
    """
    
    def __init__(self, parent, export_callback: Callable):
        """
        Initialize the export dialog.
        
        Args:
            parent: Parent window
            export_callback: Function to call with export settings
        """
        super().__init__(parent)
        self.export_callback = export_callback
        self.result = None
        
        self.title("Export Options")
        self.geometry("400x300")
        self.transient(parent)
        self.grab_set()
        
        # Center the dialog
        self.geometry("+%d+%d" % (
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the export dialog interface."""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Export type selection
        type_frame = ttk.LabelFrame(main_frame, text="Export Type", padding=10)
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.export_type = tk.StringVar(value="plot")
        
        ttk.Radiobutton(
            type_frame,
            text="Plot (PDF/PNG)",
            variable=self.export_type,
            value="plot",
            command=self._update_options
        ).pack(anchor=tk.W)
        
        ttk.Radiobutton(
            type_frame,
            text="Data (CSV)",
            variable=self.export_type,
            value="data",
            command=self._update_options
        ).pack(anchor=tk.W)
        
        ttk.Radiobutton(
            type_frame,
            text="Both",
            variable=self.export_type,
            value="both",
            command=self._update_options
        ).pack(anchor=tk.W)
        
        # Plot options
        self.plot_options_frame = ttk.LabelFrame(main_frame, text="Plot Options", padding=10)
        self.plot_options_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.include_raw = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.plot_options_frame,
            text="Include raw data",
            variable=self.include_raw
        ).pack(anchor=tk.W)
        
        self.include_fitted = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.plot_options_frame,
            text="Include fitted curves",
            variable=self.include_fitted
        ).pack(anchor=tk.W)
        
        self.include_thresholds = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.plot_options_frame,
            text="Include threshold markers",
            variable=self.include_thresholds
        ).pack(anchor=tk.W)
        
        # Format selection
        format_frame = ttk.Frame(self.plot_options_frame)
        format_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(format_frame, text="Format:").pack(side=tk.LEFT)
        
        self.plot_format = tk.StringVar(value="pdf")
        format_combo = ttk.Combobox(
            format_frame,
            textvariable=self.plot_format,
            values=["pdf", "png", "svg", "eps"],
            state="readonly",
            width=10
        )
        format_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Data options
        self.data_options_frame = ttk.LabelFrame(main_frame, text="Data Options", padding=10)
        self.data_options_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.include_metadata = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.data_options_frame,
            text="Include well metadata",
            variable=self.include_metadata
        ).pack(anchor=tk.W)
        
        self.include_analysis = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.data_options_frame,
            text="Include analysis results",
            variable=self.include_analysis
        ).pack(anchor=tk.W)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Export",
            command=self._export,
            width=12
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel,
            width=12
        ).pack(side=tk.RIGHT)
        
        self._update_options()
        
    def _update_options(self):
        """Update option visibility based on export type."""
        export_type = self.export_type.get()
        
        if export_type in ["plot", "both"]:
            self.plot_options_frame.pack(fill=tk.X, pady=(0, 10))
        else:
            self.plot_options_frame.pack_forget()
            
        if export_type in ["data", "both"]:
            self.data_options_frame.pack(fill=tk.X, pady=(0, 10))
        else:
            self.data_options_frame.pack_forget()
            
    def _export(self):
        """Execute export with current settings."""
        settings = {
            'type': self.export_type.get(),
            'plot_options': {
                'include_raw': self.include_raw.get(),
                'include_fitted': self.include_fitted.get(),
                'include_thresholds': self.include_thresholds.get(),
                'format': self.plot_format.get()
            },
            'data_options': {
                'include_metadata': self.include_metadata.get(),
                'include_analysis': self.include_analysis.get()
            }
        }
        
        self.result = settings
        self.destroy()
        
    def _cancel(self):
        """Cancel export."""
        self.result = None
        self.destroy()


class SettingsDialog(tk.Toplevel):
    """
    Settings dialog for application configuration.
    """
    
    def __init__(self, parent, current_settings: Dict[str, Any]):
        """
        Initialize the settings dialog.
        
        Args:
            parent: Parent window
            current_settings: Current application settings
        """
        super().__init__(parent)
        self.current_settings = current_settings.copy()
        self.result = None
        
        self.title("Application Settings")
        self.geometry("450x400")
        self.transient(parent)
        self.grab_set()
        
        # Center the dialog
        self.geometry("+%d+%d" % (
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the settings dialog interface."""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabbed interface
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Analysis settings tab
        analysis_frame = ttk.Frame(notebook, padding=10)
        notebook.add(analysis_frame, text="Analysis")
        
        # Curve fitting settings
        fitting_frame = ttk.LabelFrame(analysis_frame, text="Curve Fitting", padding=10)
        fitting_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Max iterations
        iter_frame = ttk.Frame(fitting_frame)
        iter_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(iter_frame, text="Max iterations:").pack(side=tk.LEFT)
        self.max_iterations = tk.StringVar(value=str(self.current_settings.get('max_iterations', 1000)))
        ttk.Entry(iter_frame, textvariable=self.max_iterations, width=10).pack(side=tk.RIGHT)
        
        # Tolerance
        tol_frame = ttk.Frame(fitting_frame)
        tol_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(tol_frame, text="Tolerance:").pack(side=tk.LEFT)
        self.tolerance = tk.StringVar(value=str(self.current_settings.get('tolerance', 1e-8)))
        ttk.Entry(tol_frame, textvariable=self.tolerance, width=15).pack(side=tk.RIGHT)
        
        # Threshold method
        threshold_frame = ttk.LabelFrame(analysis_frame, text="Threshold Detection", padding=10)
        threshold_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.threshold_method = tk.StringVar(value=self.current_settings.get('threshold_method', 'derivative'))
        
        ttk.Radiobutton(
            threshold_frame,
            text="Maximum derivative",
            variable=self.threshold_method,
            value="derivative"
        ).pack(anchor=tk.W)
        
        ttk.Radiobutton(
            threshold_frame,
            text="Baseline percentage",
            variable=self.threshold_method,
            value="baseline_percent"
        ).pack(anchor=tk.W)
        
        # Display settings tab
        display_frame = ttk.Frame(notebook, padding=10)
        notebook.add(display_frame, text="Display")
        
        # Plot settings
        plot_frame = ttk.LabelFrame(display_frame, text="Plot Appearance", padding=10)
        plot_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Default DPI
        dpi_frame = ttk.Frame(plot_frame)
        dpi_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(dpi_frame, text="Export DPI:").pack(side=tk.LEFT)
        self.export_dpi = tk.StringVar(value=str(self.current_settings.get('export_dpi', 300)))
        ttk.Entry(dpi_frame, textvariable=self.export_dpi, width=10).pack(side=tk.RIGHT)
        
        # Color scheme
        color_frame = ttk.Frame(plot_frame)
        color_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(color_frame, text="Color scheme:").pack(side=tk.LEFT)
        self.color_scheme = tk.StringVar(value=self.current_settings.get('color_scheme', 'default'))
        
        color_combo = ttk.Combobox(
            color_frame,
            textvariable=self.color_scheme,
            values=["default", "colorblind", "high_contrast"],
            state="readonly",
            width=15
        )
        color_combo.pack(side=tk.RIGHT)
        
        # Plate settings
        plate_frame = ttk.LabelFrame(display_frame, text="Plate View", padding=10)
        plate_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Well size
        size_frame = ttk.Frame(plate_frame)
        size_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(size_frame, text="Well size:").pack(side=tk.LEFT)
        self.well_size = tk.StringVar(value=str(self.current_settings.get('well_size', 25)))
        ttk.Entry(size_frame, textvariable=self.well_size, width=10).pack(side=tk.RIGHT)
        
        # Show well labels
        self.show_well_labels = tk.BooleanVar(value=self.current_settings.get('show_well_labels', True))
        ttk.Checkbutton(
            plate_frame,
            text="Show well labels",
            variable=self.show_well_labels
        ).pack(anchor=tk.W)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(
            button_frame,
            text="OK",
            command=self._ok,
            width=12
        ).pack(side=tk.RIGHT, padx=(10, 0))
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel,
            width=12
        ).pack(side=tk.RIGHT)
        
        ttk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self._reset_defaults,
            width=15
        ).pack(side=tk.LEFT)
        
    def _ok(self):
        """Apply settings and close dialog."""
        try:
            # Validate and collect settings
            settings = {
                'max_iterations': int(self.max_iterations.get()),
                'tolerance': float(self.tolerance.get()),
                'threshold_method': self.threshold_method.get(),
                'export_dpi': int(self.export_dpi.get()),
                'color_scheme': self.color_scheme.get(),
                'well_size': int(self.well_size.get()),
                'show_well_labels': self.show_well_labels.get()
            }
            
            self.result = settings
            self.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid setting value: {str(e)}")
            
    def _cancel(self):
        """Cancel settings changes."""
        self.result = None
        self.destroy()
        
    def _reset_defaults(self):
        """Reset all settings to defaults."""
        defaults = {
            'max_iterations': 1000,
            'tolerance': 1e-8,
            'threshold_method': 'derivative',
            'export_dpi': 300,
            'color_scheme': 'default',
            'well_size': 25,
            'show_well_labels': True
        }
        
        self.max_iterations.set(str(defaults['max_iterations']))
        self.tolerance.set(str(defaults['tolerance']))
        self.threshold_method.set(defaults['threshold_method'])
        self.export_dpi.set(str(defaults['export_dpi']))
        self.color_scheme.set(defaults['color_scheme'])
        self.well_size.set(str(defaults['well_size']))
        self.show_well_labels.set(defaults['show_well_labels'])


class ProgressDialog(tk.Toplevel):
    """
    Progress dialog for long-running operations.
    """
    
    def __init__(self, parent, title: str = "Processing"):
        """
        Initialize the progress dialog.
        
        Args:
            parent: Parent window
            title: Dialog title
        """
        super().__init__(parent)
        self.title(title)
        self.geometry("400x150")
        self.transient(parent)
        self.grab_set()
        
        # Center the dialog
        self.geometry("+%d+%d" % (
            parent.winfo_rootx() + 100,
            parent.winfo_rooty() + 100
        ))
        
        # Prevent closing
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the progress dialog interface."""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status label
        self.status_var = tk.StringVar(value="Initializing...")
        self.status_label = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            font=("TkDefaultFont", 10)
        )
        self.status_label.pack(pady=(0, 10))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            length=350,
            mode='determinate'
        )
        self.progress_bar.pack(pady=(0, 10))
        
        # Cancel button (optional)
        self.cancel_callback = None
        self.cancel_button = ttk.Button(
            main_frame,
            text="Cancel",
            command=self._cancel,
            state="disabled"
        )
        self.cancel_button.pack()
        
    def update_progress(self, value: float, status: str = None):
        """
        Update progress bar and status.
        
        Args:
            value: Progress value (0-100)
            status: Optional status message
        """
        self.progress_var.set(value)
        if status:
            self.status_var.set(status)
        self.update_idletasks()
        
    def set_cancel_callback(self, callback: Callable):
        """
        Set callback for cancel button.
        
        Args:
            callback: Function to call when cancel is clicked
        """
        self.cancel_callback = callback
        self.cancel_button.config(state="normal")
        
    def _cancel(self):
        """Handle cancel button click."""
        if self.cancel_callback:
            self.cancel_callback()
        self.destroy()
        
    def close(self):
        """Close the progress dialog."""
        self.destroy()