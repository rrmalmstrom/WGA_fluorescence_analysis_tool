"""
Main application window for the fluorescence analysis tool.

This module implements the primary GUI window with split-pane layout:
- Left pane: Interactive plate visualization
- Right pane: Real-time plot panel with controls
- Top: File loading interface and menu system
- Bottom: Status bar and progress indicators

Based on the architecture design in simplified_fluorescence_tool_architecture.md
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
from pathlib import Path
from typing import Optional, Dict, List, Any

# Import core components
from ..core.models import FluorescenceData, WellInfo, FileFormat
from ..parsers.bmg_parser import BMGOmega3Parser
from ..parsers.biorad_parser import BioRadParser
from ..parsers.layout_parser import LayoutParser
from ..algorithms.analysis_pipeline import FluorescenceAnalysisPipeline

# Import GUI components (will be created)
from .components.plate_view import PlateView
from .components.plot_panel import PlotPanel
from .components.file_loader import FileLoader
from .components.dialogs import ExportDialog


class MainWindow:
    """
    Main application window implementing the fluorescence analysis tool GUI.
    
    Provides a clean, desktop-based interface for loading fluorescence data,
    visualizing plate layouts, analyzing curves, and exporting results.
    """
    
    def __init__(self):
        """Initialize the main application window."""
        self.root = tk.Tk()
        self.root.title("Fluorescence Data Analysis Tool")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 600)
        
        # Application state
        self.fluorescence_data: Optional[FluorescenceData] = None
        self.layout_data: Dict[str, WellInfo] = {}
        self.analysis_results: Dict[str, Any] = {}
        self.selected_wells: List[str] = []
        self.pass_fail_results: Dict[str, Any] = {}
        
        # Initialize parsers and analysis pipeline
        self.bmg_parser = BMGOmega3Parser()
        self.biorad_parser = BioRadParser()
        self.layout_parser = LayoutParser()
        self.analysis_pipeline = FluorescenceAnalysisPipeline()
        
        # Setup GUI components
        self._setup_menu()
        self._setup_main_layout()
        self._setup_status_bar()
        
        # Bind events
        self._bind_events()
        
    def _setup_menu(self):
        """Create the main menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Data File...", command=self._load_data_file)
        file_menu.add_command(label="Load Layout File...", command=self._load_layout_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Analysis menu
        analysis_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(label="Run Analysis", command=self._run_analysis)
        analysis_menu.add_command(label="Clear Selection", command=self._clear_selection)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
        
    def _setup_main_layout(self):
        """Create the main split-pane layout."""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Top frame for file loader and quit button
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 5))
        
        # File loading panel at top left
        self.file_loader = FileLoader(top_frame, self)
        self.file_loader.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Quit button at top right - always visible
        quit_frame = ttk.Frame(top_frame)
        quit_frame.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Create a custom Canvas-based button that will definitely show red on macOS
        self.quit_canvas = tk.Canvas(
            quit_frame,
            width=80,
            height=40,
            highlightthickness=0,
            cursor="hand2"
        )
        self.quit_canvas.pack(pady=5)
        
        # Draw the red button background
        self.quit_rect = self.quit_canvas.create_rectangle(
            2, 2, 78, 38,
            fill="#FF0000",
            outline="#CC0000",
            width=2
        )
        
        # Add the text
        self.quit_text = self.quit_canvas.create_text(
            40, 20,
            text="QUIT",
            fill="white",
            font=("Arial", 12, "bold")
        )
        
        # Bind click events
        def on_quit_click(event):
            self._on_closing()
            
        def on_quit_enter(event):
            # Darker red on hover
            self.quit_canvas.itemconfig(self.quit_rect, fill="#CC0000")
            
        def on_quit_leave(event):
            # Back to normal red
            self.quit_canvas.itemconfig(self.quit_rect, fill="#FF0000")
            
        self.quit_canvas.bind("<Button-1>", on_quit_click)
        self.quit_canvas.bind("<Enter>", on_quit_enter)
        self.quit_canvas.bind("<Leave>", on_quit_leave)
        
        # Also bind to the text and rectangle for better click detection
        self.quit_canvas.tag_bind(self.quit_rect, "<Button-1>", on_quit_click)
        self.quit_canvas.tag_bind(self.quit_text, "<Button-1>", on_quit_click)
        
        # Create horizontal paned window for split layout
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Left pane: Plate visualization
        left_frame = ttk.LabelFrame(paned_window, text="Plate View", padding=10)
        paned_window.add(left_frame, weight=1)
        
        self.plate_view = PlateView(left_frame, self)
        self.plate_view.pack(fill=tk.BOTH, expand=True)
        
        # Right pane: Plot panel and controls
        right_frame = ttk.LabelFrame(paned_window, text="Analysis & Plots", padding=10)
        paned_window.add(right_frame, weight=2)
        
        self.plot_panel = PlotPanel(right_frame, self)
        self.plot_panel.pack(fill=tk.BOTH, expand=True)
        
        # Set initial pane sizes (30% left, 70% right)
        self.root.after(100, lambda: paned_window.sashpos(0, 420))
        
    def _setup_status_bar(self):
        """Create the status bar at the bottom."""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self.status_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT, padx=5, pady=2)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.status_frame,
            variable=self.progress_var,
            length=200
        )
        self.progress_bar.pack(side=tk.RIGHT, padx=5, pady=2)
        
    def _bind_events(self):
        """Bind application events."""
        # Window close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self._load_data_file())
        self.root.bind('<Control-l>', lambda e: self._load_layout_file())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        
    def _load_data_file(self):
        """Load fluorescence data file."""
        filetypes = [
            ("BMG Omega3 files", "*.csv"),
            ("BioRad files", "*.txt"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Load Fluorescence Data File",
            filetypes=filetypes
        )
        
        if filename:
            self._process_data_file(filename)
            
    def _load_layout_file(self):
        """Load layout file."""
        filetypes = [
            ("CSV files", "*.csv"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Load Layout File",
            filetypes=filetypes
        )
        
        if filename:
            self._process_layout_file(filename)
            
    def _process_data_file(self, filename: str):
        """Process the loaded data file."""
        try:
            self.update_status("Loading data file...")
            self.progress_var.set(10)
            
            # Detect file format and parse
            file_path = Path(filename)
            if file_path.suffix.lower() == '.csv':
                # BMG Omega3 format
                self.fluorescence_data = self.bmg_parser.parse_file(filename)
                self.update_status(f"Loaded BMG data: {len(self.fluorescence_data.wells)} wells")
            elif file_path.suffix.lower() == '.txt':
                # BioRad format - need cycle time
                cycle_time = self._get_cycle_time()
                if cycle_time:
                    self.fluorescence_data = self.biorad_parser.parse_file(filename, cycle_time)
                    self.update_status(f"Loaded BioRad data: {len(self.fluorescence_data.wells)} wells")
                else:
                    return
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
                
            self.progress_var.set(50)
            
            # Update GUI components
            self.file_loader.update_data_file_status(filename, True)
            self.plate_view.update_data(self.fluorescence_data)
            
            self.progress_var.set(100)
            self.update_status("Data file loaded successfully - ready for analysis")
            
        except Exception as e:
            self.progress_var.set(0)
            self.update_status("Error loading data file")
            messagebox.showerror("Error", f"Failed to load data file:\\n{str(e)}")
            
    def _process_layout_file(self, filename: str):
        """Process the loaded layout file."""
        try:
            self.update_status("Loading layout file...")
            self.progress_var.set(10)
            
            # Parse layout file - returns Dict[str, WellInfo]
            self.layout_data = self.layout_parser.parse_file(filename)
            
            self.progress_var.set(50)
            
            # Update GUI components
            self.file_loader.update_layout_file_status(filename, True)
            self.plate_view.update_layout(self.layout_data)
            
            self.progress_var.set(100)
            self.update_status("Layout file loaded successfully - ready for analysis")
            
        except Exception as e:
            self.progress_var.set(0)
            self.update_status("Error loading layout file")
            messagebox.showerror("Error", f"Failed to load layout file:\\n{str(e)}")
            
    def _get_cycle_time(self) -> Optional[float]:
        """Get cycle time for BioRad data."""
        dialog = tk.Toplevel(self.root)
        dialog.title("BioRad Cycle Time")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))
        
        result = [None]
        
        # Create dialog content
        ttk.Label(dialog, text="Enter cycle time (minutes):").pack(pady=10)
        
        entry_var = tk.StringVar(value="2.0")
        entry = ttk.Entry(dialog, textvariable=entry_var, width=10)
        entry.pack(pady=5)
        entry.focus()
        
        def ok_clicked():
            try:
                result[0] = float(entry_var.get())
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number")
                
        def cancel_clicked():
            dialog.destroy()
            
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="OK", command=ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=cancel_clicked).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key
        entry.bind('<Return>', lambda e: ok_clicked())
        
        # Wait for dialog to close
        dialog.wait_window()
        
        return result[0]
        
    def _run_analysis(self, qc_threshold_percent=10.0):
        """
        Run curve fitting analysis on the data using verified algorithms.
        
        Args:
            qc_threshold_percent: QC threshold percentage for signal quality check (default 10.0)
        """
        if not self.fluorescence_data:
            messagebox.showwarning("Warning", "Please load fluorescence data first")
            return
            
        try:
            self.update_status(f"Running analysis (QC threshold: {qc_threshold_percent}%)...")
            self.progress_var.set(10)
            
            # Use the verified analysis pipeline
            from ..algorithms.curve_fitting import CurveFitter
            from ..algorithms.threshold_analysis import ThresholdAnalyzer
            import numpy as np
            
            # Initialize analysis components with user-specified QC threshold
            curve_fitter = CurveFitter(timeout_seconds=2)
            threshold_analyzer = ThresholdAnalyzer(baseline_percentage=qc_threshold_percent/100.0)
            
            self.progress_var.set(20)
            
            # Prepare results structure
            self.analysis_results = {
                'fluorescence_data': self.fluorescence_data,
                'layout_data': list(self.layout_data.values()) if self.layout_data else [],
                'curve_fits': {}
            }
            
            # Process each well (skip unused wells to save time)
            total_wells = len(self.fluorescence_data.wells)
            time_points = np.array(self.fluorescence_data.time_points)
            
            # Count wells to analyze (excluding unused)
            wells_to_analyze = []
            for well_id in self.fluorescence_data.wells:
                if well_id in self.layout_data:
                    well_info = self.layout_data[well_id]
                    if well_info.well_type != "unused":
                        wells_to_analyze.append(well_id)
                else:
                    # If no layout data, analyze all wells
                    wells_to_analyze.append(well_id)
            
            # print(f"Analyzing {len(wells_to_analyze)} wells (skipping {total_wells - len(wells_to_analyze)} unused wells)")
            
            for i, well_id in enumerate(self.fluorescence_data.wells):
                try:
                    # Update progress
                    progress = 20 + (i / total_wells) * 60
                    self.progress_var.set(progress)
                    self.root.update_idletasks()
                    
                    # Skip unused wells
                    if well_id not in wells_to_analyze:
                        self.update_status(f"Skipping unused well {well_id}...")
                        # Store empty results for unused wells
                        self.analysis_results['curve_fits'][well_id] = {
                            'curve_result': None,
                            'threshold_result': None,
                            'fitted_curve': None,
                            'crossing_point': None,
                            'threshold_value': None
                        }
                        continue
                    
                    self.update_status(f"Analyzing well {well_id}...")
                    
                    # Extract fluorescence values for this well
                    fluo_values = self.fluorescence_data.measurements[i, :]
                    
                    # Perform curve fitting (two-path: polynomial for QC-failing, sigmoid for QC-passing)
                    curve_result = curve_fitter.fit_curve(
                        time_points, fluo_values,
                        qc_threshold_percent=qc_threshold_percent
                    )
                    
                    # Generate fitted curve array for display
                    fitted_curve = None
                    if curve_result.parameters:
                        try:
                            if curve_result.fit_type == "polynomial":
                                # Polynomial: use numpy polyval with stored coefficients
                                fitted_curve = np.polyval(curve_result.parameters, time_points)
                            else:
                                # Sigmoid: use 5-parameter sigmoid function
                                fitted_curve = curve_fitter.sigmoid_5param(
                                    time_points, *curve_result.parameters)
                        except Exception:
                            pass
                    
                    # Perform crossing point analysis — only for sigmoid fits that passed QC
                    if (curve_result.success and
                            curve_result.parameters and
                            curve_result.fit_type == "sigmoid"):
                        # Use the same fitted curve for CP calculation as for plotting
                        threshold_result = threshold_analyzer.analyze_threshold_crossing_with_fitted_curve(
                            time_points, fluo_values, curve_result.parameters, method="qc_second_derivative")
                    else:
                        # Polynomial fits and failed sigmoid fits get no CP
                        from ..algorithms.threshold_analysis import ThresholdResult
                        threshold_result = ThresholdResult(
                            success=False,
                            error_message="No CP: well did not pass QC threshold or sigmoid fit failed"
                        )
                    
                    # Store results
                    self.analysis_results['curve_fits'][well_id] = {
                        'curve_result': curve_result,
                        'threshold_result': threshold_result,
                        'fitted_curve': fitted_curve,
                        'crossing_point': threshold_result.crossing_time if threshold_result.success else None,
                        'threshold_value': threshold_result.threshold_value if threshold_result.success else None
                    }
                    
                except Exception as e:
                    # print(f"Warning: Analysis failed for well {well_id}: {e}")
                    # Continue with other wells
                    continue
            
            self.progress_var.set(90)
            
            # Update plot panel with results
            self.plot_panel.update_analysis_results(self.analysis_results)
            
            self.progress_var.set(100)
            
            # Count successful analyses (excluding unused wells)
            successful_fits = sum(1 for result in self.analysis_results['curve_fits'].values()
                                if result['curve_result'] is not None and result['curve_result'].success)
            
            self.update_status(f"Analysis completed: {successful_fits}/{total_wells} wells fitted successfully")
            
        except Exception as e:
            self.progress_var.set(0)
            self.update_status("Error during analysis")
            messagebox.showerror("Error", f"Analysis failed:\\n{str(e)}")
            import traceback
            traceback.print_exc()
            
    def _clear_selection(self):
        """Clear well selection."""
        self.selected_wells.clear()
        self.plate_view.clear_selection()
        self.plot_panel.clear_plots()
        self.update_status("Selection cleared")
        
                
    def _show_about(self):
        """Show about dialog."""
        about_text = """Fluorescence Data Analysis Tool
        
A simplified, reliable tool for analyzing fluorescence data from BMG Omega3 and BioRad instruments.

Features:
• Interactive plate visualization
• Real-time curve fitting analysis
• Publication-ready plot exports
• Comprehensive data analysis

Version: 1.0.0"""
        
        messagebox.showinfo("About", about_text)
        
    def _on_closing(self):
        """Handle application closing gracefully."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            # Clean up any resources
            self.update_status("Shutting down...")
            self.root.update_idletasks()
            
            # Proper tkinter shutdown - just quit the mainloop
            # This allows the run() method to complete normally
            self.root.quit()
            
    def update_status(self, message: str):
        """Update status bar message."""
        self.status_var.set(message)
        self.root.update_idletasks()
        
    def on_well_selection_changed(self, selected_wells: List[str]):
        """Handle well selection changes from plate view."""
        self.selected_wells = selected_wells
        
        # Update plot panel with selected wells
        if self.analysis_results and selected_wells:
            self.plot_panel.update_selected_wells(selected_wells)
            self.update_status(f"Selected {len(selected_wells)} wells")
        else:
            self.plot_panel.clear_plots()
            self.update_status("No wells selected")
    
    def update_pass_fail_results(self, pass_fail_results: Dict[str, Any]):
        """Handle pass/fail results updates from plot panel."""
        self.pass_fail_results = pass_fail_results
        
        # Update plate view with pass/fail results
        if hasattr(self.plate_view, 'update_pass_fail_results'):
            self.plate_view.update_pass_fail_results(pass_fail_results)
            
    def run(self):
        """Start the application main loop."""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.root.destroy()


if __name__ == "__main__":
    app = MainWindow()
    app.run()