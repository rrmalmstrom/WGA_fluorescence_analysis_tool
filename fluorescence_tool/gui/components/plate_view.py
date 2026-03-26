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
        
        # Fixed color scheme for predetermined types
        self.type_colors = {
            'sample': '#2196F3',      # Blue (outline)
            'neg_cntrl': '#FF9800',   # Orange (outline)
            'pos_cntrl': '#4CAF50',   # Green (outline)
            'unused': '#E0E0E0',      # Light gray
            'unknown': '#9E9E9E',     # Gray
        }
        
        # Default color for any other well types (pentagon shapes)
        self.default_other_color = '#9C27B0'  # Purple
        
        # Softer, muted colors for Group1 (fill colors, avoiding type colors)
        self.group1_palette = [
            '#B39DDB', '#F8BBD9', '#BCAAA4', '#90A4AE', '#80DEEA',
            '#C5E1A5', '#F0F4C3', '#FFE0B2', '#FFCDD2', '#C5CAE9',
            '#B2DFDB', '#D1C4E9', '#F8BBD9', '#BBDEFB', '#B3E5FC'
        ]
        
        # Group2: 6 truly distinct symbols (filled vs open variants)
        self.group2_symbols = [
            'plus',           # Plus symbol (+)
            'filled_circle',  # Solid circle (●)
            'open_circle',    # Open circle (○)
            'filled_star',    # Solid star (★)
            'open_star',      # Open star (☆)
            'cross'           # X-shaped cross (✕)
        ]
        
        # No predefined mappings - all assignments are dynamic based on data order
        
        # Group3: 4 truly distinct patterns (simplified for reliability)
        self.group3_patterns = [
            '|||',       # Vertical lines
            '---',       # Horizontal lines
            '///',       # Forward diagonal lines
            '...'        # Dot pattern
        ]
        
        # UI colors
        self.ui_colors = {
            'selected': '#F44336',    # Red
            'border': '#333333',      # Dark gray
            'background': '#FFFFFF'   # White
        }
        
        # Grouping state and color assignments
        self.active_groupings: Set[str] = {'Type'}  # Default grouping
        self.group1_colors: Dict[str, str] = {}
        self.group2_symbol_assignments: Dict[str, str] = {}  # Track symbol assignments
        self.group3_pattern_assignments: Dict[str, str] = {}  # Track pattern assignments
        
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
            bg=self.ui_colors['background'],
            highlightthickness=1,
            highlightbackground=self.ui_colors['border']
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
                fill=self.ui_colors['border']
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
                fill=self.ui_colors['border']
            )
            
        # Draw wells
        for well_id, pos in self.well_positions.items():
            self._draw_well(well_id, pos)
            
    def _draw_well(self, well_id: str, pos: WellPosition):
        """Draw a single well with multi-layer visualization system."""
        well_tag = f"well_{well_id}"
        
        # Get visual properties for this well
        fill_color, outline_color, symbol, pattern = self._get_well_visual_properties(well_id)
        
        # Get well type for shape determination
        well_type = 'unknown'
        if well_id in self.layout_data:
            well_type = self.layout_data[well_id].well_type
        
        # Draw base well shape based on type
        self._draw_well_shape(well_id, pos, well_type, fill_color, outline_color)
        
        # Draw Group3 pattern/texture if specified and checkbox checked
        if pattern and self.grouping_vars['Group_3'].get():
            self._draw_well_pattern(well_id, pos, pattern, outline_color)
            
        # Draw Group2 symbol if specified and checkbox checked
        if symbol and self.grouping_vars['Group_2'].get():
            self._draw_well_symbol(well_id, pos, symbol, outline_color)
        
        # Add selection indicator if selected
        if well_id in self.selected_wells:
            self._draw_selection_indicator(well_id, pos, well_type)
            
        # Remove well labels to avoid interference with symbols and patterns
        # Well labels (H2, etc.) are not displayed to keep wells clean for visual encoding
        pass
        
    def _draw_well_shape(self, well_id: str, pos: WellPosition, well_type: str, fill_color: str, outline_color: str):
        """Draw the base well shape based on type."""
        well_tag = f"well_{well_id}"
        
        if well_type == 'sample':
            # Circular wells for samples
            self.canvas.create_oval(
                pos.x, pos.y,
                pos.x + pos.width, pos.y + pos.height,
                fill=fill_color,
                outline=outline_color,
                width=2,
                tags=(well_tag, "well")
            )
        elif well_type == 'neg_cntrl':
            # Triangular wells for negative controls
            center_x = pos.x + pos.width // 2
            center_y = pos.y + pos.height // 2
            radius = min(pos.width, pos.height) // 2 - 1
            
            # Equilateral triangle points
            points = [
                center_x, center_y - radius,  # Top
                center_x - radius * 0.866, center_y + radius * 0.5,  # Bottom left
                center_x + radius * 0.866, center_y + radius * 0.5   # Bottom right
            ]
            self.canvas.create_polygon(
                points,
                fill=fill_color,
                outline=outline_color,
                width=2,
                tags=(well_tag, "well")
            )
        elif well_type == 'pos_cntrl':
            # Square wells for positive controls
            margin = 2
            self.canvas.create_rectangle(
                pos.x + margin, pos.y + margin,
                pos.x + pos.width - margin, pos.y + pos.height - margin,
                fill=fill_color,
                outline=outline_color,
                width=2,
                tags=(well_tag, "well")
            )
        elif well_type == 'unused':
            # Default circular shape for unused wells
            self.canvas.create_oval(
                pos.x, pos.y,
                pos.x + pos.width, pos.y + pos.height,
                fill=fill_color,
                outline=outline_color,
                width=1,
                tags=(well_tag, "well")
            )
        else:
            # Pentagon shape for any other well type (not sample, neg_cntrl, pos_cntrl, or unused)
            center_x = pos.x + pos.width // 2
            center_y = pos.y + pos.height // 2
            radius = min(pos.width, pos.height) // 2 - 1
            
            # Create pentagon points (5 sides)
            import math
            points = []
            for i in range(5):
                angle = i * 2 * math.pi / 5 - math.pi / 2  # Start from top, 72 degrees between points
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                points.extend([x, y])
            
            self.canvas.create_polygon(
                points,
                fill=fill_color,
                outline=outline_color,
                width=2,
                tags=(well_tag, "well")
            )
            
    def _draw_selection_indicator(self, well_id: str, pos: WellPosition, well_type: str):
        """Draw selection indicator matching the well shape."""
        if well_type == 'sample' or well_type == 'unused' or well_type == 'unknown':
            # Circular selection for circular wells
            self.canvas.create_oval(
                pos.x - 3, pos.y - 3,
                pos.x + pos.width + 3, pos.y + pos.height + 3,
                fill="",
                outline=self.ui_colors['selected'],
                width=3,
                tags=(f"selection_{well_id}", "selection")
            )
        elif well_type == 'neg_cntrl':
            # Triangular selection for triangular wells
            center_x = pos.x + pos.width // 2
            center_y = pos.y + pos.height // 2
            radius = min(pos.width, pos.height) // 2 + 2
            
            points = [
                center_x, center_y - radius,
                center_x - radius * 0.866, center_y + radius * 0.5,
                center_x + radius * 0.866, center_y + radius * 0.5
            ]
            self.canvas.create_polygon(
                points,
                fill="",
                outline=self.ui_colors['selected'],
                width=3,
                tags=(f"selection_{well_id}", "selection")
            )
        elif well_type == 'pos_cntrl':
            # Square selection for square wells
            self.canvas.create_rectangle(
                pos.x - 3, pos.y - 3,
                pos.x + pos.width + 3, pos.y + pos.height + 3,
                fill="",
                outline=self.ui_colors['selected'],
                width=3,
                tags=(f"selection_{well_id}", "selection")
            )
        else:
            # Pentagon selection for pentagon wells
            center_x = pos.x + pos.width // 2
            center_y = pos.y + pos.height // 2
            radius = min(pos.width, pos.height) // 2 + 2
            
            # Create pentagon points for selection (slightly larger)
            import math
            points = []
            for i in range(5):
                angle = i * 2 * math.pi / 5 - math.pi / 2  # Start from top, 72 degrees between points
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                points.extend([x, y])
            
            self.canvas.create_polygon(
                points,
                fill="",
                outline=self.ui_colors['selected'],
                width=3,
                tags=(f"selection_{well_id}", "selection")
            )
            
    def _get_well_visual_properties(self, well_id: str) -> tuple:
        """Get visual properties (fill_color, outline_color, symbol, pattern) for a well."""
        if well_id not in self.layout_data:
            return self.type_colors['unknown'], self.ui_colors['border'], None, None
            
        well_info = self.layout_data[well_id]
        
        # 1. Get outline color based on well type (for pentagon shapes)
        if well_info.well_type in self.type_colors:
            outline_color = self.ui_colors['border']
        else:
            # For other well types (pentagon shapes), use the default color as outline
            outline_color = self.default_other_color
        
        # 2. Fill color from Group1 (dynamic colors, only if checkbox checked)
        if self.grouping_vars['Group_1'].get():
            fill_color = self._get_group1_color(well_info.group_1)
        else:
            fill_color = '#F5F5F5'  # Light gray when Group1 not displayed
        
        # 3. Symbol from Group2
        symbol = self._get_group2_symbol(well_info.group_2)
        
        # 4. Pattern from Group3
        pattern = self._get_group3_pattern(well_info.group_3)
        
        return fill_color, outline_color, symbol, pattern
        
    def _get_group1_color(self, group1_value: str) -> str:
        """Get fill color for Group1 value."""
        if not group1_value or group1_value.lower() in ['', 'none', 'null']:
            return '#F5F5F5'  # Light gray for no group
            
        if group1_value not in self.group1_colors:
            # Assign next available color
            color_index = len(self.group1_colors) % len(self.group1_palette)
            self.group1_colors[group1_value] = self.group1_palette[color_index]
            
        return self.group1_colors[group1_value]
        
    def _get_group2_symbol(self, group2_value: str) -> str:
        """Get symbol for Group2 value, ensuring unique symbols for unique values."""
        if not group2_value or group2_value.lower() in ['', 'none', 'null']:
            return None
            
        # Check if this value already has an assigned symbol
        if group2_value in self.group2_symbol_assignments:
            return self.group2_symbol_assignments[group2_value]
            
        # Get all available symbols from the list
        used_symbols = set(self.group2_symbol_assignments.values())
        
        # Find first unused symbol from the list
        for symbol in self.group2_symbols:
            if symbol not in used_symbols:
                self.group2_symbol_assignments[group2_value] = symbol
                return symbol
        
        # If all symbols are used, this shouldn't happen with 6 symbols for typical data
        # But as fallback, cycle through them
        symbol_index = len(self.group2_symbol_assignments) % len(self.group2_symbols)
        symbol = self.group2_symbols[symbol_index]
        self.group2_symbol_assignments[group2_value] = symbol
        return symbol
            
    def _get_group3_pattern(self, group3_value: str) -> str:
        """Get pattern for Group3 value, ensuring unique patterns for unique values."""
        if not group3_value or group3_value.lower() in ['', 'none', 'null']:
            return None
            
        # Check if this value already has an assigned pattern
        if group3_value in self.group3_pattern_assignments:
            return self.group3_pattern_assignments[group3_value]
            
        # Get all available patterns from the list
        used_patterns = set(self.group3_pattern_assignments.values())
        
        # Find first unused pattern from the list
        for pattern in self.group3_patterns:
            if pattern not in used_patterns:
                self.group3_pattern_assignments[group3_value] = pattern
                return pattern
        
        # If all patterns are used, this shouldn't happen with 4 patterns for typical data
        # But as fallback, cycle through them
        pattern_index = len(self.group3_pattern_assignments) % len(self.group3_patterns)
        pattern = self.group3_patterns[pattern_index]
        self.group3_pattern_assignments[group3_value] = pattern
        return pattern
            
    def _draw_well_symbol(self, well_id: str, pos: WellPosition, symbol: str, color: str):
        """Draw a smaller, distinct solid symbol in the center of the well (Group2)."""
        center_x = pos.x + pos.width // 2
        center_y = pos.y + pos.height // 2
        symbol_size = min(pos.width, pos.height) // 4  # Smaller symbols (was //3)
        
        symbol_tag = f"symbol_{well_id}"
        
        if symbol == 'filled_circle':
            self.canvas.create_oval(
                center_x - symbol_size//2, center_y - symbol_size//2,
                center_x + symbol_size//2, center_y + symbol_size//2,
                fill=color, outline=color,
                tags=(symbol_tag, "symbol")
            )
        elif symbol == 'open_circle':
            self.canvas.create_oval(
                center_x - symbol_size//2, center_y - symbol_size//2,
                center_x + symbol_size//2, center_y + symbol_size//2,
                fill="", outline=color, width=2,
                tags=(symbol_tag, "symbol")
            )
        elif symbol == 'filled_star':
            # 5-pointed star (filled)
            import math
            points = []
            for i in range(10):  # 5 outer points + 5 inner points
                angle = i * math.pi / 5  # 36 degrees between points
                if i % 2 == 0:  # Outer points
                    radius = symbol_size
                else:  # Inner points
                    radius = symbol_size * 0.4
                x = center_x + radius * math.cos(angle - math.pi/2)
                y = center_y + radius * math.sin(angle - math.pi/2)
                points.extend([x, y])
            self.canvas.create_polygon(
                points, fill=color, outline=color,
                tags=(symbol_tag, "symbol")
            )
        elif symbol == 'open_star':
            # 5-pointed star (outline only)
            import math
            points = []
            for i in range(10):  # 5 outer points + 5 inner points
                angle = i * math.pi / 5  # 36 degrees between points
                if i % 2 == 0:  # Outer points
                    radius = symbol_size
                else:  # Inner points
                    radius = symbol_size * 0.4
                x = center_x + radius * math.cos(angle - math.pi/2)
                y = center_y + radius * math.sin(angle - math.pi/2)
                points.extend([x, y])
            self.canvas.create_polygon(
                points, fill="", outline=color, width=2,
                tags=(symbol_tag, "symbol")
            )
        elif symbol == 'plus':
            # Plus symbol for BONCAT
            self.canvas.create_rectangle(
                center_x - symbol_size//4, center_y - symbol_size,
                center_x + symbol_size//4, center_y + symbol_size,
                fill=color, outline=color,
                tags=(symbol_tag, "symbol")
            )
            self.canvas.create_rectangle(
                center_x - symbol_size, center_y - symbol_size//4,
                center_x + symbol_size, center_y + symbol_size//4,
                fill=color, outline=color,
                tags=(symbol_tag, "symbol")
            )
        elif symbol == 'cross':
            # X-shaped cross
            # Draw two diagonal lines to form an X
            self.canvas.create_line(
                center_x - symbol_size, center_y - symbol_size,
                center_x + symbol_size, center_y + symbol_size,
                fill=color, width=3,
                tags=(symbol_tag, "symbol")
            )
            self.canvas.create_line(
                center_x - symbol_size, center_y + symbol_size,
                center_x + symbol_size, center_y - symbol_size,
                fill=color, width=3,
                tags=(symbol_tag, "symbol")
            )
            
    def _draw_well_pattern(self, well_id: str, pos: WellPosition, pattern: str, color: str):
        """Draw a matplotlib-style hatch pattern as well fill texture (Group3)."""
        pattern_tag = f"pattern_{well_id}"
        spacing = 3  # Tighter spacing for better visibility
        
        if pattern == '///':  # Forward diagonal lines
            for i in range(-pos.height//spacing, pos.width//spacing + 1):
                x1 = pos.x + i * spacing
                y1 = pos.y
                x2 = pos.x + pos.width
                y2 = pos.y + pos.height - i * spacing
                
                # Clip to well bounds (circular)
                if x1 < pos.x:
                    y1 += (pos.x - x1)
                    x1 = pos.x
                if y2 > pos.y + pos.height:
                    x2 -= (y2 - pos.y - pos.height)
                    y2 = pos.y + pos.height
                    
                if x1 <= pos.x + pos.width and y2 >= pos.y:
                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill=color, width=1,
                        tags=(pattern_tag, "pattern")
                    )
                    
        elif pattern == '\\\\\\':  # Backward diagonal lines
            for i in range(-pos.width//spacing, pos.height//spacing + 1):
                x1 = pos.x
                y1 = pos.y + i * spacing
                x2 = pos.x + pos.width - i * spacing
                y2 = pos.y + pos.height
                
                # Clip to well bounds
                if y1 < pos.y:
                    x1 += (pos.y - y1)
                    y1 = pos.y
                if x2 > pos.x + pos.width:
                    y2 -= (x2 - pos.x - pos.width)
                    x2 = pos.x + pos.width
                    
                if y1 <= pos.y + pos.height and x2 >= pos.x:
                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill=color, width=1,
                        tags=(pattern_tag, "pattern")
                    )
                    
        elif pattern == '|||':  # Vertical lines
            x = pos.x + spacing
            while x < pos.x + pos.width - spacing:
                self.canvas.create_line(
                    x, pos.y + 2, x, pos.y + pos.height - 2,
                    fill=color, width=1,
                    tags=(pattern_tag, "pattern")
                )
                x += spacing
                
        elif pattern == '---':  # Horizontal lines
            y = pos.y + spacing
            while y < pos.y + pos.height - spacing:
                self.canvas.create_line(
                    pos.x + 2, y, pos.x + pos.width - 2, y,
                    fill=color, width=1,
                    tags=(pattern_tag, "pattern")
                )
                y += spacing
                
        elif pattern == '+++':  # Plus pattern
            # Vertical lines
            x = pos.x + spacing
            while x < pos.x + pos.width - spacing:
                self.canvas.create_line(
                    x, pos.y + 2, x, pos.y + pos.height - 2,
                    fill=color, width=1,
                    tags=(pattern_tag, "pattern")
                )
                x += spacing * 2
            # Horizontal lines
            y = pos.y + spacing
            while y < pos.y + pos.height - spacing:
                self.canvas.create_line(
                    pos.x + 2, y, pos.x + pos.width - 2, y,
                    fill=color, width=1,
                    tags=(pattern_tag, "pattern")
                )
                y += spacing * 2
                
        elif pattern == 'xxx':  # X pattern (crosshatch)
            # Forward diagonals
            self._draw_well_pattern(well_id, pos, '///', color)
            # Backward diagonals
            self._draw_well_pattern(well_id, pos, '\\\\\\', color)
            
        elif pattern == 'ooo':  # Circle pattern
            for x in range(pos.x + spacing*2, pos.x + pos.width, spacing * 3):
                for y in range(pos.y + spacing*2, pos.y + pos.height, spacing * 3):
                    # Check if point is within well circle
                    center_x = pos.x + pos.width // 2
                    center_y = pos.y + pos.height // 2
                    radius = min(pos.width, pos.height) // 2 - 2
                    if (x - center_x)**2 + (y - center_y)**2 <= radius**2:
                        self.canvas.create_oval(
                            x - 1, y - 1, x + 1, y + 1,
                            outline=color, width=1,
                            tags=(pattern_tag, "pattern")
                        )
                        
        elif pattern == '...':  # Dot pattern
            for x in range(pos.x + spacing, pos.x + pos.width, spacing * 2):
                for y in range(pos.y + spacing, pos.y + pos.height, spacing * 2):
                    # Check if point is within well circle
                    center_x = pos.x + pos.width // 2
                    center_y = pos.y + pos.height // 2
                    radius = min(pos.width, pos.height) // 2 - 2
                    if (x - center_x)**2 + (y - center_y)**2 <= radius**2:
                        self.canvas.create_oval(
                            x, y, x + 1, y + 1,
                            fill=color, outline=color,
                            tags=(pattern_tag, "pattern")
                        )
            
    def _get_well_color(self, well_id: str) -> str:
        """Legacy method - now redirects to visual properties system."""
        fill_color, outline_color, symbol, pattern = self._get_well_visual_properties(well_id)
        return fill_color  # Return fill color for backward compatibility
        
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
                outline=self.ui_colors['selected'],
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
        """Update visualization grouping based on checkbox states."""
        self.group1_colors.clear()  # Reset Group1 color assignments
        self.group2_symbol_assignments.clear()  # Reset Group2 symbol assignments
        self.group3_pattern_assignments.clear()  # Reset Group3 pattern assignments
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
        """Update the multi-layer visualization legend display."""
        # Clear existing legend
        for widget in self.legend_frame_inner.winfo_children():
            widget.destroy()
            
        # Create legend sections
        legend_frame = ttk.Frame(self.legend_frame_inner)
        legend_frame.pack(fill=tk.X)
        
        # Type legend (well shapes) - auto-populate based on actual data
        if self.layout_data:
            # Get actual types from data
            actual_types = set()
            for well in self.layout_data.values():
                if well.well_type and well.well_type != 'unused':
                    actual_types.add(well.well_type)
            
            if actual_types:
                type_frame = ttk.LabelFrame(legend_frame, text="Type (Shape)", padding=5)
                type_frame.pack(side=tk.LEFT, padx=(0, 10), fill=tk.Y)
                
                for well_type in sorted(actual_types):
                    item_frame = ttk.Frame(type_frame)
                    item_frame.pack(anchor=tk.W, pady=1)
                    
                    # Shape indicator
                    shape_canvas = tk.Canvas(item_frame, width=20, height=15, highlightthickness=0)
                    shape_canvas.pack(side=tk.LEFT, padx=(0, 5))
                    
                    # Get color for this well type
                    if well_type in self.type_colors:
                        color = self.type_colors[well_type]
                    else:
                        color = self.default_other_color  # Use purple for other types
                    
                    self._draw_legend_shape(shape_canvas, well_type, color)
                    
                    ttk.Label(item_frame, text=well_type, font=("TkDefaultFont", 8)).pack(side=tk.LEFT)
            
        # Group1 legend (fill colors) - auto-populate based on data, show/hide based on checkbox
        if self.layout_data:
            # Get actual Group1 values from data
            group1_values = set()
            for well in self.layout_data.values():
                if well.group_1 and well.group_1.strip():
                    group1_values.add(well.group_1)
            
            if group1_values and self.grouping_vars['Group_1'].get():
                group1_frame = ttk.LabelFrame(legend_frame, text="Group1 (Fill)", padding=5)
                group1_frame.pack(side=tk.LEFT, padx=(0, 10), fill=tk.Y)
                
                # Only assign colors when Group1 checkbox is checked
                for group_value in group1_values:
                    if group_value not in self.group1_colors:
                        # Assign next available color
                        color_index = len(self.group1_colors) % len(self.group1_palette)
                        self.group1_colors[group_value] = self.group1_palette[color_index]
                
                for group_value in sorted(group1_values):
                    item_frame = ttk.Frame(group1_frame)
                    item_frame.pack(anchor=tk.W, pady=1)
                    
                    # Color indicator
                    color_canvas = tk.Canvas(item_frame, width=15, height=15, highlightthickness=0)
                    color_canvas.pack(side=tk.LEFT, padx=(0, 5))
                    color = self.group1_colors.get(group_value, '#F5F5F5')
                    color_canvas.create_oval(2, 2, 13, 13, fill=color, outline=self.ui_colors['border'])
                    
                    ttk.Label(item_frame, text=group_value, font=("TkDefaultFont", 8)).pack(side=tk.LEFT)
                
        # Group2 legend (symbols) - only show if checkbox is checked AND there's Group2 data
        if (self.grouping_vars['Group_2'].get() and
            self.layout_data and
            any(well.group_2 for well in self.layout_data.values() if well.group_2)):
            
            group2_frame = ttk.LabelFrame(legend_frame, text="Group2 (Symbols)", padding=5)
            group2_frame.pack(side=tk.LEFT, padx=(0, 10), fill=tk.Y)
            
            # Get actual Group2 values from data
            group2_values = set()
            for well in self.layout_data.values():
                if well.group_2 and well.group_2.strip():
                    group2_values.add(well.group_2)
            
            # Show symbols for actual data values
            for i, group_value in enumerate(sorted(group2_values)):
                item_frame = ttk.Frame(group2_frame)
                item_frame.pack(anchor=tk.W, pady=1)
                
                # Get symbol for this group value
                symbol = self._get_group2_symbol(group_value)
                
                # Symbol indicator - larger canvas for better visibility
                symbol_canvas = tk.Canvas(item_frame, width=20, height=20, highlightthickness=0)
                symbol_canvas.pack(side=tk.LEFT, padx=(0, 5))
                symbol_canvas.create_oval(2, 2, 18, 18, fill='#F5F5F5', outline=self.ui_colors['border'])
                if symbol:
                    self._draw_legend_symbol(symbol_canvas, 10, 10, symbol, self.ui_colors['border'])
                
                ttk.Label(item_frame, text=group_value, font=("TkDefaultFont", 8)).pack(side=tk.LEFT)
                
        # Group3 legend (patterns) - only show if checkbox is checked AND there's Group3 data
        if (self.grouping_vars['Group_3'].get() and
            self.layout_data and
            any(well.group_3 for well in self.layout_data.values() if well.group_3)):
            
            group3_frame = ttk.LabelFrame(legend_frame, text="Group3 (Patterns)", padding=5)
            group3_frame.pack(side=tk.LEFT, padx=(0, 10), fill=tk.Y)
            
            # Get actual Group3 values from data
            group3_values = set()
            for well in self.layout_data.values():
                if well.group_3 and well.group_3.strip():
                    group3_values.add(well.group_3)
            
            # Show patterns for actual data values
            for group_value in sorted(group3_values):
                item_frame = ttk.Frame(group3_frame)
                item_frame.pack(anchor=tk.W, pady=1)
                
                # Get pattern for this group value
                pattern = self._get_group3_pattern(group_value)
                
                # Pattern indicator
                pattern_canvas = tk.Canvas(item_frame, width=15, height=15, highlightthickness=0)
                pattern_canvas.pack(side=tk.LEFT, padx=(0, 5))
                pattern_canvas.create_oval(2, 2, 13, 13, fill='#F5F5F5', outline=self.ui_colors['border'])
                if pattern:
                    self._draw_legend_pattern(pattern_canvas, pattern, self.ui_colors['border'])
                
                ttk.Label(item_frame, text=group_value, font=("TkDefaultFont", 8)).pack(side=tk.LEFT)
                
    def _draw_legend_shape(self, canvas, well_type, color):
        """Draw a small well shape for the legend."""
        if well_type == 'sample':
            # Circle for samples
            canvas.create_oval(3, 3, 17, 12, fill='#F5F5F5', outline=color, width=2)
        elif well_type == 'neg_cntrl':
            # Triangle for negative controls
            points = [10, 3, 5, 12, 15, 12]
            canvas.create_polygon(points, fill='#F5F5F5', outline=color, width=2)
        elif well_type == 'pos_cntrl':
            # Square for positive controls
            canvas.create_rectangle(4, 4, 16, 11, fill='#F5F5F5', outline=color, width=2)
        elif well_type == 'unused':
            # Default circle for unused
            canvas.create_oval(3, 3, 17, 12, fill='#F5F5F5', outline=color, width=1)
        else:
            # Pentagon for other well types
            center_x = 10
            center_y = 7.5
            radius = 6
            
            # Create pentagon points for legend
            import math
            points = []
            for i in range(5):
                angle = i * 2 * math.pi / 5 - math.pi / 2  # Start from top, 72 degrees between points
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                points.extend([x, y])
            
            canvas.create_polygon(points, fill='#F5F5F5', outline=color, width=2)
            
    def _draw_legend_symbol(self, canvas, x, y, symbol, color):
        """Draw a larger, more visible solid symbol for the legend."""
        size = 6  # Increased from 5 to 6 for better visibility
        if symbol == 'filled_circle':
            canvas.create_oval(x-size//2, y-size//2, x+size//2, y+size//2, fill=color, outline=color)
        elif symbol == 'open_circle':
            canvas.create_oval(x-size//2, y-size//2, x+size//2, y+size//2, fill="", outline=color, width=2)
        elif symbol == 'filled_star':
            # 5-pointed star (filled) for legend
            import math
            points = []
            for i in range(10):  # 5 outer points + 5 inner points
                angle = i * math.pi / 5  # 36 degrees between points
                if i % 2 == 0:  # Outer points
                    radius = size
                else:  # Inner points
                    radius = size * 0.4
                px = x + radius * math.cos(angle - math.pi/2)
                py = y + radius * math.sin(angle - math.pi/2)
                points.extend([px, py])
            canvas.create_polygon(points, fill=color, outline=color)
        elif symbol == 'open_star':
            # 5-pointed star (outline only) for legend
            import math
            points = []
            for i in range(10):  # 5 outer points + 5 inner points
                angle = i * math.pi / 5  # 36 degrees between points
                if i % 2 == 0:  # Outer points
                    radius = size
                else:  # Inner points
                    radius = size * 0.4
                px = x + radius * math.cos(angle - math.pi/2)
                py = y + radius * math.sin(angle - math.pi/2)
                points.extend([px, py])
            canvas.create_polygon(points, fill="", outline=color, width=2)
        elif symbol == 'plus':
            # Draw plus symbol for BONCAT
            canvas.create_rectangle(x-size//4, y-size, x+size//4, y+size, fill=color, outline=color)
            canvas.create_rectangle(x-size, y-size//4, x+size, y+size//4, fill=color, outline=color)
        elif symbol == 'cross':
            # Draw X-shaped cross symbol
            canvas.create_line(x-size, y-size, x+size, y+size, fill=color, width=3)
            canvas.create_line(x-size, y+size, x+size, y-size, fill=color, width=3)
            
    def _draw_legend_pattern(self, canvas, pattern, color):
        """Draw a small matplotlib-style hatch pattern for the legend."""
        if pattern == '---':  # Horizontal lines
            for y in range(4, 12, 2):
                canvas.create_line(3, y, 12, y, fill=color, width=1)
        elif pattern == '|||':  # Vertical lines
            for x in range(4, 12, 2):
                canvas.create_line(x, 3, x, 12, fill=color, width=1)
        elif pattern == '///':  # Forward diagonal lines
            for i in range(-5, 6, 2):
                canvas.create_line(3+i, 3, 12+i, 12, fill=color, width=1)
        elif pattern == '\\\\\\':  # Backward diagonal lines
            for i in range(-5, 6, 2):
                canvas.create_line(3+i, 12, 12+i, 3, fill=color, width=1)
        elif pattern == '...':  # Dots
            for x in range(4, 12, 3):
                for y in range(4, 12, 3):
                    canvas.create_oval(x, y, x+1, y+1, fill=color, outline=color)
        elif pattern == 'ooo':  # Circles
            for x in range(4, 12, 3):
                for y in range(4, 12, 3):
                    canvas.create_oval(x-1, y-1, x+1, y+1, outline=color, width=1)
            
    def update_data(self, fluorescence_data: FluorescenceData):
        """Update with new fluorescence data."""
        self.fluorescence_data = fluorescence_data
        self._calculate_plate_dimensions()
        self._create_well_positions()
        self._update_plate_display()
        
    def update_layout(self, layout_data: Dict[str, WellInfo]):
        """Update with new layout data and auto-check boxes for groups with data."""
        self.layout_data = layout_data
        self.group1_colors.clear()  # Reset Group1 color assignments
        self.group2_symbol_assignments.clear()  # Reset Group2 symbol assignments
        self.group3_pattern_assignments.clear()  # Reset Group3 pattern assignments
        
        # Auto-check boxes for groups that have data in the layout
        if layout_data:
            # Check if Group_1 has data
            has_group1_data = any(well.group_1 and well.group_1.strip()
                                for well in layout_data.values())
            if has_group1_data:
                self.grouping_vars['Group_1'].set(True)
            
            # Check if Group_2 has data
            has_group2_data = any(well.group_2 and well.group_2.strip()
                                for well in layout_data.values())
            if has_group2_data:
                self.grouping_vars['Group_2'].set(True)
            
            # Check if Group_3 has data
            has_group3_data = any(well.group_3 and well.group_3.strip()
                                for well in layout_data.values())
            if has_group3_data:
                self.grouping_vars['Group_3'].set(True)
        
        self._update_plate_display()
        self._update_legend()
        
    def clear_selection(self):
        """Clear well selection (called from main window)."""
        self._clear_selection()
        
    def get_selected_wells(self) -> List[str]:
        """Get list of currently selected wells."""
        return list(self.selected_wells)