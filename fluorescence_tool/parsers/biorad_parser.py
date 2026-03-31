"""
BioRad format parser.

Supports two BioRad file formats:

1. Legacy tab-separated .txt format (cycle-based, user-supplied cycle time).
2. New Bio-Rad CFX Maestro .xlsx format (SYBR sheet + Run Information sheet).
   - Cycle time is auto-computed from Run Started/Ended timestamps (rounded to
     nearest minute) unless the caller supplies cycle_time_minutes explicitly.
   - Plate ID is extracted from the Run Information sheet (cell B1, .pcrd
     extension stripped) and stored in metadata for downstream validation.

The .xlsx files produced by CFX Maestro use a non-standard zip structure
(lowercase [content_types].xml, Windows backslash paths, lowercase
sharedstrings.xml).  This parser reads the internal XML directly via
zipfile + xml.etree.ElementTree, bypassing openpyxl entirely, which makes
it robust to the non-standard structure.
"""

import re
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fluorescence_tool.core.models import FluorescenceData, FileFormat


# ---------------------------------------------------------------------------
# XML namespace used throughout OOXML spreadsheet files
# ---------------------------------------------------------------------------
_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"

# Timestamp format used by CFX Maestro in the Run Information sheet
_TIMESTAMP_FMT = "%m/%d/%Y %H:%M:%S UTC"


class BioRadParser:
    """Parser for BioRad fluorescence data files (.txt and .xlsx)."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse_file(
        self,
        file_path: str,
        cycle_time_minutes: Optional[float] = None,
    ) -> FluorescenceData:
        """
        Parse a BioRad data file.

        Dispatches to the appropriate sub-parser based on file extension:
        - ``.txt``  → legacy tab-separated format (cycle_time_minutes required)
        - ``.xlsx`` → CFX Maestro xlsx format (cycle_time_minutes optional;
                      auto-computed from timestamps when not supplied)

        Args:
            file_path: Path to the BioRad data file.
            cycle_time_minutes: Time between cycles in minutes.
                - For .txt files: **required** (raises ValueError if None).
                - For .xlsx files: optional; auto-computed from Run Information
                  timestamps when not provided.  If provided, overrides the
                  auto-computed value.

        Returns:
            FluorescenceData with time_points in hours, wells, measurements,
            metadata, and format_type == FileFormat.BIORAD.

        Raises:
            FileNotFoundError: File does not exist.
            ValueError: Unsupported extension, invalid cycle time, or
                        malformed file content.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = file_path.suffix.lower()

        if ext == ".txt":
            return self._parse_txt(file_path, cycle_time_minutes)
        elif ext == ".xlsx":
            return self._parse_xlsx(file_path, cycle_time_minutes)
        else:
            raise ValueError(
                f"Unsupported BioRad file format: '{ext}'. "
                "Expected '.txt' or '.xlsx'."
            )

    # ------------------------------------------------------------------
    # Legacy .txt parser (unchanged logic)
    # ------------------------------------------------------------------

    def _parse_txt(
        self,
        file_path: Path,
        cycle_time_minutes: Optional[float],
    ) -> FluorescenceData:
        """Parse legacy tab-separated BioRad .txt file."""
        if cycle_time_minutes is None:
            raise ValueError(
                "cycle_time_minutes is required for .txt format files. "
                "Please supply the time between cycles in minutes."
            )
        if cycle_time_minutes <= 0:
            raise ValueError("Cycle time must be positive")

        try:
            df = pd.read_csv(file_path, sep="\t")

            if "Cycle" not in df.columns:
                raise ValueError("BioRad file missing 'Cycle' column")

            well_columns = [
                col
                for col in df.columns
                if col != "Cycle" and not col.startswith("Unnamed")
            ]

            if not well_columns:
                raise ValueError("No well data columns found")

            cycles = df["Cycle"].values
            time_points = [
                (cycle - 1) * (cycle_time_minutes / 60.0) for cycle in cycles
            ]

            measurements_df = df[well_columns].ffill().bfill()
            measurements = measurements_df.values.T

            metadata = {
                "cycle_time_minutes": cycle_time_minutes,
                "num_cycles": len(cycles),
                "plate_format": self._detect_plate_format(well_columns),
            }

            return FluorescenceData(
                time_points=time_points,
                wells=well_columns,
                measurements=measurements,
                metadata=metadata,
                format_type=FileFormat.BIORAD,
            )

        except Exception as e:
            if isinstance(e, (ValueError, FileNotFoundError)):
                raise
            raise ValueError(f"Failed to parse BioRad .txt file: {e}")

    # ------------------------------------------------------------------
    # New .xlsx parser
    # ------------------------------------------------------------------

    def _parse_xlsx(
        self,
        file_path: Path,
        cycle_time_minutes: Optional[float],
    ) -> FluorescenceData:
        """
        Parse Bio-Rad CFX Maestro .xlsx file.

        Reads the SYBR sheet for fluorescence data and the Run Information
        sheet for timestamps and plate ID.
        """
        # Validate cycle time override if provided
        if cycle_time_minutes is not None and cycle_time_minutes <= 0:
            raise ValueError("Cycle time must be positive")

        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                shared_strings = self._read_shared_strings(zf)
                sybr_rows = self._read_sheet_rows(zf, "sheet1", shared_strings)
                run_info_rows = self._read_sheet_rows(zf, "sheet2", shared_strings)

        except KeyError as e:
            raise ValueError(
                f"Failed to read BioRad .xlsx file — expected internal file "
                f"not found: {e}. Is this a valid CFX Maestro export?"
            )
        except zipfile.BadZipFile as e:
            raise ValueError(f"File is not a valid .xlsx archive: {e}")

        # --- Parse Run Information sheet ---
        run_info = self._parse_run_info(run_info_rows)

        # --- Extract plate ID from B1 (File Name, strip .pcrd) ---
        raw_file_name = run_info.get("File Name", "")
        plate_id = Path(raw_file_name).stem if raw_file_name else None

        # --- Compute cycle time ---
        if cycle_time_minutes is None:
            cycle_time_minutes = self._compute_cycle_time(
                run_info, num_cycles=len(sybr_rows) - 1
            )

        # --- Parse SYBR sheet ---
        if not sybr_rows:
            raise ValueError("SYBR sheet is empty or could not be read")

        header_row = sybr_rows[0]
        # header_row is a dict {col_index: value}
        # col 0 = None (empty), col 1 = 'Cycle', col 2+ = well names
        well_col_map: Dict[int, str] = {
            idx: name
            for idx, name in header_row.items()
            if idx >= 2 and name and name not in (None, "Cycle")
        }

        if not well_col_map:
            raise ValueError(
                "SYBR sheet header does not contain well columns. "
                "Expected columns like 'A1', 'A2', etc."
            )

        # Validate that 'Cycle' column is present
        if 1 not in header_row or header_row[1] != "Cycle":
            raise ValueError(
                "SYBR sheet is missing the 'Cycle' column in position B."
            )

        well_names: List[str] = [well_col_map[i] for i in sorted(well_col_map)]
        num_cycles = len(sybr_rows) - 1  # exclude header

        # Build measurements array: shape (num_wells, num_cycles)
        measurements = np.full((len(well_names), num_cycles), np.nan)

        for cycle_idx, data_row in enumerate(sybr_rows[1:]):
            for well_idx, col_idx in enumerate(sorted(well_col_map)):
                val = data_row.get(col_idx)
                if val is not None:
                    try:
                        measurements[well_idx, cycle_idx] = float(val)
                    except (ValueError, TypeError):
                        pass  # leave as NaN; forward-fill below

        # Forward-fill then back-fill any NaN values (same as .txt parser)
        for i in range(measurements.shape[0]):
            row = measurements[i]
            # ffill
            mask = np.isnan(row)
            idx = np.where(~mask, np.arange(len(row)), 0)
            np.maximum.accumulate(idx, out=idx)
            row[:] = row[idx]
            # bfill
            mask = np.isnan(row)
            idx = np.where(~mask, np.arange(len(row)), len(row) - 1)
            idx = np.minimum.accumulate(idx[::-1])[::-1]
            row[:] = row[idx]

        # Build time points in hours: cycle 1 → 0.0 h, cycle 2 → dt h, …
        time_points = [i * (cycle_time_minutes / 60.0) for i in range(num_cycles)]

        metadata = {
            "cycle_time_minutes": cycle_time_minutes,
            "num_cycles": num_cycles,
            "plate_format": self._detect_plate_format(well_names),
            "plate_id": plate_id,
            "run_started": run_info.get("Run Started"),
            "run_ended": run_info.get("Run Ended"),
            "protocol_file": run_info.get("Protocol File Name"),
            "cfx_version": run_info.get("CFX Maestro Version", "").strip(),
            "instrument_serial": run_info.get("Base Serial Number"),
        }

        return FluorescenceData(
            time_points=time_points,
            wells=well_names,
            measurements=measurements,
            metadata=metadata,
            format_type=FileFormat.BIORAD,
        )

    # ------------------------------------------------------------------
    # Internal xlsx helpers
    # ------------------------------------------------------------------

    def _read_shared_strings(self, zf: zipfile.ZipFile) -> List[str]:
        """
        Read the shared strings table from an xlsx zip archive.

        CFX Maestro stores this as ``xl\\sharedstrings.xml`` (lowercase,
        backslash path).  We read it by its actual name.
        """
        # Try both the non-standard (CFX Maestro) and standard names
        candidates = [
            "xl\\sharedstrings.xml",   # CFX Maestro non-standard
            "xl/sharedStrings.xml",    # OOXML standard
            "xl/sharedstrings.xml",    # lowercase standard variant
        ]
        raw = None
        for name in candidates:
            try:
                raw = zf.read(name)
                break
            except KeyError:
                continue

        if raw is None:
            # No shared strings table — return empty list (all values are inline)
            return []

        root = ET.fromstring(raw)
        strings: List[str] = []
        for si in root.findall(f"{{{_NS}}}si"):
            t_el = si.find(f"{{{_NS}}}t")
            if t_el is not None:
                strings.append(t_el.text or "")
            else:
                # Rich text: concatenate all <t> children
                parts = si.findall(f".//{{{_NS}}}t")
                strings.append("".join(p.text or "" for p in parts))
        return strings

    def _read_sheet_rows(
        self,
        zf: zipfile.ZipFile,
        sheet_filename: str,
        shared_strings: List[str],
    ) -> List[Dict[int, object]]:
        """
        Read a worksheet XML and return rows as a list of dicts.

        Each dict maps 0-based column index → cell value (str or float).
        Empty cells are omitted (sparse representation).

        Args:
            zf: Open ZipFile for the xlsx archive.
            sheet_filename: Bare sheet filename, e.g. ``"sheet1"``.
            shared_strings: Shared strings table from _read_shared_strings().

        Returns:
            List of row dicts, one per row in the sheet.

        Raises:
            ValueError: If the sheet cannot be found in the archive.
        """
        candidates = [
            f"xl\\worksheets\\{sheet_filename}.xml",   # CFX Maestro
            f"xl/worksheets/{sheet_filename}.xml",     # standard
        ]
        raw = None
        for name in candidates:
            try:
                raw = zf.read(name)
                break
            except KeyError:
                continue

        if raw is None:
            raise ValueError(
                f"Sheet '{sheet_filename}' not found in xlsx archive. "
                "Expected 'SYBR' and 'Run Information' sheets."
            )

        root = ET.fromstring(raw)
        rows: List[Dict[int, object]] = []

        for row_el in root.findall(f".//{{{_NS}}}row"):
            row_dict: Dict[int, object] = {}
            for c in row_el.findall(f"{{{_NS}}}c"):
                ref = c.get("r", "")
                col_str_match = re.match(r"([A-Z]+)", ref)
                if not col_str_match:
                    continue
                col_idx = self._col_letters_to_index(col_str_match.group(1))

                cell_type = c.get("t", "")
                v_el = c.find(f"{{{_NS}}}v")

                if v_el is None:
                    row_dict[col_idx] = None
                elif cell_type == "s":
                    # Shared string reference
                    try:
                        row_dict[col_idx] = shared_strings[int(v_el.text)]
                    except (IndexError, ValueError, TypeError):
                        row_dict[col_idx] = None
                else:
                    # Numeric or inline string
                    try:
                        row_dict[col_idx] = float(v_el.text)
                    except (ValueError, TypeError):
                        row_dict[col_idx] = v_el.text

            rows.append(row_dict)

        return rows

    def _parse_run_info(
        self, rows: List[Dict[int, object]]
    ) -> Dict[str, object]:
        """
        Convert Run Information sheet rows into a key→value dict.

        Column A (index 0) = key, column B (index 1) = value.
        """
        info: Dict[str, object] = {}
        for row in rows:
            key = row.get(0)
            val = row.get(1)
            if key and isinstance(key, str):
                info[key.strip()] = val
        return info

    def _compute_cycle_time(
        self,
        run_info: Dict[str, object],
        num_cycles: int,
    ) -> float:
        """
        Compute cycle time in minutes from Run Started/Ended timestamps.

        The CFX Maestro protocol includes a ~10-minute post-run extension step
        that is not part of the amplification cycles.  Subtracting this constant
        before dividing by the number of cycles gives a more accurate per-cycle
        estimate.

        Formula: round((total_minutes - POST_RUN_EXTENSION_MINUTES) / num_cycles)

        Returns the value rounded to the nearest whole minute.

        Raises:
            ValueError: If timestamps are missing or cannot be parsed.
        """
        # Constant post-run extension added by CFX Maestro (not an amplification cycle)
        POST_RUN_EXTENSION_MINUTES = 10.0

        start_str = run_info.get("Run Started")
        end_str = run_info.get("Run Ended")

        if not start_str or not end_str:
            raise ValueError(
                "Cannot auto-compute cycle time: 'Run Started' and/or "
                "'Run Ended' are missing from the Run Information sheet. "
                "Please supply cycle_time_minutes explicitly."
            )

        try:
            start = datetime.strptime(str(start_str), _TIMESTAMP_FMT)
            end = datetime.strptime(str(end_str), _TIMESTAMP_FMT)
        except ValueError as e:
            raise ValueError(
                f"Cannot parse timestamps from Run Information sheet: {e}. "
                "Please supply cycle_time_minutes explicitly."
            )

        if num_cycles <= 0:
            raise ValueError(
                "Cannot compute cycle time: no data cycles found in SYBR sheet."
            )

        total_minutes = (end - start).total_seconds() / 60.0
        adjusted_minutes = max(total_minutes - POST_RUN_EXTENSION_MINUTES, 0.0)
        return round(adjusted_minutes / num_cycles)

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _col_letters_to_index(col_str: str) -> int:
        """Convert Excel column letters (A, B, AA, …) to 0-based index."""
        result = 0
        for ch in col_str:
            result = result * 26 + (ord(ch) - ord("A") + 1)
        return result - 1

    def _detect_plate_format(self, well_columns: List[str]) -> str:
        """Detect plate format (96-well, 384-well) from well names."""
        max_row = "A"
        max_col = 1

        for well in well_columns:
            if len(well) >= 2:
                row = well[0]
                try:
                    col = int(well[1:])
                    if row > max_row:
                        max_row = row
                    if col > max_col:
                        max_col = col
                except ValueError:
                    continue

        if max_row <= "H" and max_col <= 12:
            return "96-well"
        elif max_row <= "P" and max_col <= 24:
            return "384-well"
        else:
            return "unknown"
