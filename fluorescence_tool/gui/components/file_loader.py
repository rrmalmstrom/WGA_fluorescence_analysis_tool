"""
File loading interface component.

This module provides a clean interface for loading fluorescence data files
and layout files with visual status indicators and format detection.
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Optional, Callable


class FileLoader(ttk.Frame):
    """
    File loading interface with status indicators.
    
    Provides buttons for loading data and layout files, displays current
    file status, and includes a process button to trigger analysis.
    """
    
    def __init__(self, parent, main_window):
        """
        Initialize the file loader component.
        
        Args:
            parent: Parent tkinter widget
            main_window: Reference to main application window
        """
        super().__init__(parent)
        self.main_window = main_window
        
        # File status variables
        self.data_file_var = tk.StringVar(value="No data file loaded")
        self.layout_file_var = tk.StringVar(value="No layout file loaded")
        self.data_file_status = False
        self.layout_file_status = False
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the file loader user interface."""
        # Main container with padding
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="File Loading", 
            font=("TkDefaultFont", 10, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))
        
        # Data file section
        ttk.Label(main_frame, text="Data File:").grid(row=1, column=0, sticky="w", padx=(0, 10))
        
        self.data_file_button = ttk.Button(
            main_frame,
            text="Load Data File...",
            command=self.main_window._load_data_file,
            width=15
        )
        self.data_file_button.grid(row=1, column=1, padx=(0, 10))
        
        self.data_file_label = ttk.Label(
            main_frame,
            textvariable=self.data_file_var,
            foreground="gray"
        )
        self.data_file_label.grid(row=1, column=2, sticky="w", padx=(0, 10))
        
        self.data_status_label = ttk.Label(main_frame, text="●", foreground="red")
        self.data_status_label.grid(row=1, column=3, sticky="w")
        
        # Layout file section
        ttk.Label(main_frame, text="Layout File:").grid(row=2, column=0, sticky="w", padx=(0, 10), pady=(5, 0))
        
        self.layout_file_button = ttk.Button(
            main_frame,
            text="Load Layout File...",
            command=self.main_window._load_layout_file,
            width=15
        )
        self.layout_file_button.grid(row=2, column=1, padx=(0, 10), pady=(5, 0))
        
        self.layout_file_label = ttk.Label(
            main_frame,
            textvariable=self.layout_file_var,
            foreground="gray"
        )
        self.layout_file_label.grid(row=2, column=2, sticky="w", padx=(0, 10), pady=(5, 0))
        
        self.layout_status_label = ttk.Label(main_frame, text="●", foreground="red")
        self.layout_status_label.grid(row=2, column=3, sticky="w", pady=(5, 0))
        
        # Process button and status
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=4, sticky="w", pady=(15, 0))
        
        self.process_button = ttk.Button(
            button_frame,
            text="Process & Analyze",
            command=self._process_files,
            state="disabled",
            width=20
        )
        self.process_button.pack(side=tk.LEFT, padx=(0, 15))
        
        self.status_label = ttk.Label(
            button_frame,
            text="Load both files to enable processing",
            foreground="gray"
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Configure grid weights for responsive layout
        main_frame.columnconfigure(2, weight=1)
        
    def update_data_file_status(self, filename: str, success: bool):
        """
        Update data file status display.
        
        Args:
            filename: Path to the loaded file
            success: Whether the file was loaded successfully
        """
        self.data_file_status = success
        
        if success:
            file_path = Path(filename)
            display_name = file_path.name
            if len(display_name) > 50:
                display_name = display_name[:47] + "..."
                
            self.data_file_var.set(f"{display_name}")
            self.data_file_label.config(foreground="black")
            self.data_status_label.config(foreground="green")
            
            # Add format indicator
            if file_path.suffix.lower() == '.csv':
                format_text = " (BMG Omega3)"
            elif file_path.suffix.lower() == '.txt':
                format_text = " (BioRad)"
            else:
                format_text = ""
            self.data_file_var.set(f"{display_name}{format_text}")
        else:
            self.data_file_var.set("Error loading data file")
            self.data_file_label.config(foreground="red")
            self.data_status_label.config(foreground="red")
            
        self._update_process_button()
        
    def update_layout_file_status(self, filename: str, success: bool):
        """
        Update layout file status display.
        
        Args:
            filename: Path to the loaded file
            success: Whether the file was loaded successfully
        """
        self.layout_file_status = success
        
        if success:
            file_path = Path(filename)
            display_name = file_path.name
            if len(display_name) > 50:
                display_name = display_name[:47] + "..."
                
            self.layout_file_var.set(f"{display_name}")
            self.layout_file_label.config(foreground="black")
            self.layout_status_label.config(foreground="green")
        else:
            self.layout_file_var.set("Error loading layout file")
            self.layout_file_label.config(foreground="red")
            self.layout_status_label.config(foreground="red")
            
        self._update_process_button()
        
    def _update_process_button(self):
        """Update the process button state based on file loading status."""
        if self.data_file_status and self.layout_file_status:
            self.process_button.config(state="normal")
            self.status_label.config(
                text="Ready to process - click to run analysis",
                foreground="green"
            )
        elif self.data_file_status:
            self.process_button.config(state="disabled")
            self.status_label.config(
                text="Load layout file to enable processing",
                foreground="orange"
            )
        elif self.layout_file_status:
            self.process_button.config(state="disabled")
            self.status_label.config(
                text="Load data file to enable processing",
                foreground="orange"
            )
        else:
            self.process_button.config(state="disabled")
            self.status_label.config(
                text="Load both files to enable processing",
                foreground="gray"
            )
            
    def _process_files(self):
        """Process the loaded files and run analysis."""
        if self.data_file_status and self.layout_file_status:
            self.main_window._run_analysis()
            
    def reset_status(self):
        """Reset all file loading status indicators."""
        self.data_file_status = False
        self.layout_file_status = False
        
        self.data_file_var.set("No data file loaded")
        self.layout_file_var.set("No layout file loaded")
        
        self.data_file_label.config(foreground="gray")
        self.layout_file_label.config(foreground="gray")
        
        self.data_status_label.config(foreground="red")
        self.layout_status_label.config(foreground="red")
        
        self._update_process_button()
        
    def set_processing_state(self, processing: bool):
        """
        Set the processing state to disable/enable buttons during analysis.
        
        Args:
            processing: True if analysis is running, False otherwise
        """
        state = "disabled" if processing else "normal"
        
        self.data_file_button.config(state=state)
        self.layout_file_button.config(state=state)
        
        if processing:
            self.process_button.config(state="disabled")
            self.status_label.config(
                text="Processing... please wait",
                foreground="blue"
            )
        else:
            self._update_process_button()