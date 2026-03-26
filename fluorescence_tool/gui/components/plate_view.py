"""
Interactive plate visualization component.

This module provides an interactive visualization of 96-well or 384-well plates
with clickable wells, color coding based on sample types and groups, and
real-time selection feedback.
"""

import tkinter as tk
from tkinter import ttk
import math
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass

from ...core.models import FluorescenceData, WellInfo


@dataclass
class WellPosition:
    """Represents a well position on the plate."""
    row: int
    col: int
    well_id: str
    x: int
    y: int
    width: int
    height: int


class PlateView(ttk.Frame):
    """
    Interactive plate visualization with well selection and color coding.
    
    Supports both 96-well (8x12) and 384-well (16x24) plate formats with
    dynamic color coding based on sample types and grouping metadata.
    """
    
    def __init__(self, parent, main_window):
        """
        Initialize the plate view component.
        
        Args:
            parent: Parent tkinter widget
            main_window: Reference to main application window
        """
        super().__init__(parent)
        self.main_window = main_window
        
        # Plate configuration
        self.plate_rows = 8  # Default to 96-well
        self.plate_cols = 12
        self.well_size = 25
        self.well_spacing = 3
        
        # Data
        self.fluorescence_data: Optional[FluorescenceData] = None
        self.layout_data: Dict[str, WellInfo] = {}
        self.well_positions: Dict[str, WellPosition] = {}
        
        # Selection state
        self.selected_wells: Set[str] = set()
        self.drag_start: Optional[Tuple[int, int]] = None
        self.drag_rect: Optional[int] = None
        
        # Color scheme
        self.colors = {
            'sample': '#4CAF50',      # Green
            'neg_cntrl': '#2196F3',   # Blue
            'pos_cntrl': '#FF9800',   # Orange
            'unused': '#E0E0E0',      # Light gray
            'unknown': '#9E9E9E',     # Gray
            'selected': '#F44336',    # Red
            'border': '#333333',      # Dark gray
            'background': '#FFFFFF'   # White
        }
        
        # Grouping state
        self.active_groupings: Set[str] = {'Type'}  # Default grouping
        self.group_colors: Dict[str, str] = {}
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the plate view user interface."""
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Control panel at top
        control_frame = ttk.LabelFrame(main_frame, text="Plate Controls", padding=5)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Grouping controls
        grouping_frame = ttk.Frame(control_frame)
        grouping_frame.pack(fill=tk.X)
        
        ttk.Label(grouping_frame, text="Color by:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.grouping_vars = {}
        for group_name in ['Type', 'Group_1', 'Group_2', 'Group_3']:
            var = tk.BooleanVar(value=(group_name == 'Type'))
            self.grouping_vars[group_name] = var
            
            cb = ttk.Checkbutton(
                grouping_frame,
                text=group_name,
                variable=var,
                command=self._update_grouping
            )
            cb.pack(side=tk.LEFT, padx=(0, 10))
            
        # Selection controls
        selection_frame = ttk.Frame(control_frame)
        selection_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(
            selection_frame,
            text="Clear Selection",
            command=self._clear_selection,
            width=15
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            selection_frame,
            text="Select All",
            command=self._select_all,
            width=15
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.selection_label = ttk.Label(
            selection_frame,
            text="No wells selected"
        )
        self.selection_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Plate canvas container
        canvas_frame = ttk.LabelFrame(main_frame, text="Plate Layout", padding=5)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollable canvas
        self.canvas = tk.Canvas(
            canvas_frame,
            bg=self.colors['background'],
            highlightthickness=1,
            highlightbackground=self.colors['border']
        )
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and canvas
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind canvas events
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<Double-Button-1>", self._on_canvas_double_click)
        
        # Legend frame
        legend_frame = ttk.LabelFrame(main_frame, text="Legend", padding=5)
        legend_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.legend_frame_inner = ttk.Frame(legend_frame)
        self.legend_frame_inner.pack(fill=tk.X)
        
        self._create_default_plate()
        self._update_legend()
        
    def _create_default_plate(self):
        """Create a default empty plate layout."""
        self._calculate_plate_dimensions()
        self._create_well_positions()
        self._draw_plate()
        
    def _calculate_plate_dimensions(self):
        """Calculate plate dimensions based on well count."""
        # Determine plate format from data if available
        if self.fluorescence_data:
            well_count = len(self.fluorescence_data.wells)
            if well_count <= 96:
                self.plate_rows, self.plate_cols = 8, 12
            else:
                self.plate_rows, self.plate_cols = 16, 24
        
        # Calculate canvas size
        self.plate_width = (self.plate_cols * (self.well_size + self.well_spacing) 
                           - self.well_spacing + 40)  # 40 for margins
        self.plate_height = (self.plate_rows * (self.well_size + self.well_spacing) 
                            - self.well_spacing + 60)  # 60 for row/col labels
        
        self.canvas.configure(scrollregion=(0, 0, self.plate_width, self.plate_height))
        
    def _create_well_positions(self):
        """Create well position mappings."""
        self.well_positions.clear()
        
        start_x = 30  # Space for row labels
        start_y = 30  # Space for column labels
        
        for row in range(self.plate_rows):
            row_letter = chr(ord('A') + row)
            for col in range(self.plate_cols):
                col_number = col + 1
                well_id = f"{row_letter}{col_number}"
                
                x = start_x + col * (self.well_size + self.well_spacing)
                y = start_y + row * (self.well_size + self.well_spacing)
                
                self.well_positions[well_id] = WellPosition(
                    row=row,
                    col=col,
                    well_id=well_id,
                    x=x,
                    y=y,
                    width=self.well_size,
                    height=self.well_size
                )
                
    def _draw_plate(self):
        """Draw the complete plate layout."""
        self.canvas.delete("all")
        
        # Draw column labels
        start_x = 30
        for col in range(self.plate_cols):
            x = start_x + col * (self.well_size + self.well_spacing) + self.well_size // 2
            self.canvas.create_text(
                x, 15,
                text=str(col + 1),
                font=("TkDefaultFont", 8),
                fill=self.colors['border']
            )
            
        # Draw row labels
        start_y = 30
        for row in range(self.plate_rows):
            row_letter = chr(ord('A') + row)
            y = start_y + row * (self.well_size + self.well_spacing) + self.well_size // 2
            self.canvas.create_text(
                15, y,
                text=row_letter,
                font=("TkDefaultFont", 8),
                fill=self.colors['border']
            )
            
        # Draw wells
        for well_id, pos in self.well_positions.items():
            self._draw_well(well_id, pos)
            
    def _draw_well(self, well_id: str, pos: WellPosition):
        """Draw a single well with appropriate color coding."""
        # Determine well color
        color = self._get_well_color(well_id)
        
        # Draw well circle
        well_tag = f"well_{well_id}"
        self.canvas.create_oval(
            pos.x, pos.y,
            pos.x + pos.width, pos.y + pos.height,
            fill=color,
            outline=self.colors['border'],
            width=1,
            tags=(well_tag, "well")
        )
        
        # Add selection indicator if selected
        if well_id in self.selected_wells:
            self.canvas.create_oval(
                pos.x - 2, pos.y - 2,
                pos.x + pos.width + 2, pos.y + pos.height + 2,
                fill="",
                outline=self.colors['selected'],
                width=3,
                tags=(f"selection_{well_id}", "selection")
            )
            
        # Add well label for small plates or if zoomed in
        if self.plate_rows <= 8 or self.well_size > 20:
            text_color = "white" if self._is_dark_color(color) else "black"
            self.canvas.create_text(
                pos.x + pos.width // 2,
                pos.y + pos.height // 2,
                text=well_id,
                font=("TkDefaultFont", max(6, self.well_size // 4)),
                fill=text_color,
                tags=(well_tag, "well_label")
            )
            
    def _get_well_color(self, well_id: str) -> str:
        """Get the color for a well based on current grouping settings."""
        if well_id not in self.layout_data:
            return self.colors['unknown']
            
        well_info = self.layout_data[well_id]
        
        # Build grouping key
        group_key_parts = []
        for group_name in ['Type', 'Group_1', 'Group_2', 'Group_3']:
            if self.grouping_vars[group_name].get():
                if group_name == 'Type':
                    value = well_info.well_type
                elif group_name == 'Group_1':
                    value = well_info.group_1
                elif group_name == 'Group_2':
                    value = well_info.group_2
                elif group_name == 'Group_3':
                    value = well_info.group_3
                else:
                    value = None
                    
                if value:
                    group_key_parts.append(f"{group_name}:{value}")
                    
        group_key = "|".join(group_key_parts) if group_key_parts else "unknown"
        
        # Get or assign color for this group
        if group_key not in self.group_colors:
            self.group_colors[group_key] = self._assign_group_color(group_key)
            
        return self.group_colors[group_key]
        
    def _assign_group_color(self, group_key: str) -> str:
        """Assign a color to a new group combination."""
        # Check for standard well types first
        if "Type:sample" in group_key:
            return self.colors['sample']
        elif "Type:neg_cntrl" in group_key:
            return self.colors['neg_cntrl']
        elif "Type:pos_cntrl" in group_key:
            return self.colors['pos_cntrl']
        elif "Type:unused" in group_key:
            return self.colors['unused']
            
        # Generate color for complex groupings
        color_palette = [
            '#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336',
            '#00BCD4', '#8BC34A', '#FFC107', '#E91E63', '#3F51B5',
            '#009688', '#CDDC39', '#FF5722', '#795548', '#607D8B'
        ]
        
        # Use hash of group key to consistently assign colors
        color_index = hash(group_key) % len(color_palette)
        return color_palette[color_index]
        
    def _is_dark_color(self, color: str) -> bool:
        """Check if a color is dark (for text contrast)."""
        # Simple brightness check
        if color.startswith('#'):
            hex_color = color[1:]
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            return brightness < 128
        return False
        
    def _on_canvas_click(self, event):
        """Handle canvas click events."""
        self.drag_start = (event.x, event.y)
        
        # Check if clicking on a well
        well_id = self._get_well_at_position(event.x, event.y)
        if well_id:
            # Toggle well selection
            if well_id in self.selected_wells:
                self.selected_wells.remove(well_id)
            else:
                self.selected_wells.add(well_id)
            self._update_well_display(well_id)
            self._update_selection_display()
            
    def _on_canvas_drag(self, event):
        """Handle canvas drag events for rectangle selection."""
        if self.drag_start:
            # Remove previous drag rectangle
            if self.drag_rect:
                self.canvas.delete(self.drag_rect)
                
            # Draw new drag rectangle
            x1, y1 = self.drag_start
            x2, y2 = event.x, event.y
            
            self.drag_rect = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline=self.colors['selected'],
                width=2,
                fill="",
                tags="drag_rect"
            )
            
    def _on_canvas_release(self, event):
        """Handle canvas release events to complete rectangle selection."""
        if self.drag_start and self.drag_rect:
            # Get wells within drag rectangle
            x1, y1 = self.drag_start
            x2, y2 = event.x, event.y
            
            # Ensure proper rectangle bounds
            min_x, max_x = min(x1, x2), max(x1, x2)
            min_y, max_y = min(y1, y2), max(y1, y2)
            
            # Find wells in rectangle
            wells_in_rect = []
            for well_id, pos in self.well_positions.items():
                well_center_x = pos.x + pos.width // 2
                well_center_y = pos.y + pos.height // 2
                
                if (min_x <= well_center_x <= max_x and 
                    min_y <= well_center_y <= max_y):
                    wells_in_rect.append(well_id)
                    
            # Update selection
            if wells_in_rect:
                # Add to selection (could modify for toggle behavior)
                for well_id in wells_in_rect:
                    self.selected_wells.add(well_id)
                self._update_plate_display()
                self._update_selection_display()
                
            # Clean up
            self.canvas.delete(self.drag_rect)
            self.drag_rect = None
            
        self.drag_start = None
        
    def _on_canvas_double_click(self, event):
        """Handle double-click to select wells by type."""
        well_id = self._get_well_at_position(event.x, event.y)
        if well_id and well_id in self.layout_data:
            well_type = self.layout_data[well_id].well_type
            
            # Select all wells of the same type
            for wid, well_info in self.layout_data.items():
                if well_info.well_type == well_type:
                    self.selected_wells.add(wid)
                    
            self._update_plate_display()
            self._update_selection_display()
            
    def _get_well_at_position(self, x: int, y: int) -> Optional[str]:
        """Get the well ID at the given canvas position."""
        for well_id, pos in self.well_positions.items():
            if (pos.x <= x <= pos.x + pos.width and 
                pos.y <= y <= pos.y + pos.height):
                return well_id
        return None
        
    def _clear_selection(self):
        """Clear all well selections."""
        self.selected_wells.clear()
        self._update_plate_display()
        self._update_selection_display()
        
    def _select_all(self):
        """Select all available wells."""
        if self.fluorescence_data:
            self.selected_wells.update(self.fluorescence_data.wells)
        else:
            self.selected_wells.update(self.well_positions.keys())
        self._update_plate_display()
        self._update_selection_display()
        
    def _update_grouping(self):
        """Update color grouping based on checkbox states."""
        self.group_colors.clear()  # Reset color assignments
        self._update_plate_display()
        self._update_legend()
        
    def _update_well_display(self, well_id: str):
        """Update the display of a specific well."""
        if well_id in self.well_positions:
            pos = self.well_positions[well_id]
            
            # Remove existing well graphics
            self.canvas.delete(f"well_{well_id}")
            self.canvas.delete(f"selection_{well_id}")
            
            # Redraw well
            self._draw_well(well_id, pos)
            
    def _update_plate_display(self):
        """Update the entire plate display."""
        self._draw_plate()
        
    def _update_selection_display(self):
        """Update the selection count display."""
        count = len(self.selected_wells)
        if count == 0:
            text = "No wells selected"
        elif count == 1:
            text = f"1 well selected: {list(self.selected_wells)[0]}"
        else:
            text = f"{count} wells selected"
            
        self.selection_label.config(text=text)
        
        # Notify main window of selection change
        self.main_window.on_well_selection_changed(list(self.selected_wells))
        
    def _update_legend(self):
        """Update the color legend display."""
        # Clear existing legend
        for widget in self.legend_frame_inner.winfo_children():
            widget.destroy()
            
        # Create legend entries
        legend_items = []
        for group_key, color in self.group_colors.items():
            legend_items.append((group_key, color))
            
        # Sort legend items
        legend_items.sort(key=lambda x: x[0])
        
        # Display legend items
        for i, (group_key, color) in enumerate(legend_items):
            frame = ttk.Frame(self.legend_frame_inner)
            frame.pack(side=tk.LEFT, padx=(0, 15))
            
            # Color indicator
            color_canvas = tk.Canvas(frame, width=15, height=15, highlightthickness=0)
            color_canvas.pack(side=tk.LEFT, padx=(0, 5))
            color_canvas.create_oval(2, 2, 13, 13, fill=color, outline=self.colors['border'])
            
            # Label
            label_text = group_key.replace("|", ", ").replace(":", ": ")
            ttk.Label(frame, text=label_text, font=("TkDefaultFont", 8)).pack(side=tk.LEFT)
            
    def update_data(self, fluorescence_data: FluorescenceData):
        """Update with new fluorescence data."""
        self.fluorescence_data = fluorescence_data
        self._calculate_plate_dimensions()
        self._create_well_positions()
        self._update_plate_display()
        
    def update_layout(self, layout_data: Dict[str, WellInfo]):
        """Update with new layout data."""
        self.layout_data = layout_data
        self.group_colors.clear()  # Reset color assignments
        self._update_plate_display()
        self._update_legend()
        
    def clear_selection(self):
        """Clear well selection (called from main window)."""
        self._clear_selection()
        
    def get_selected_wells(self) -> List[str]:
        """Get list of currently selected wells."""
        return list(self.selected_wells)