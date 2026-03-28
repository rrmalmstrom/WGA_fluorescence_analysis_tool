"""
Diagnostic script to time curve fitting per-well for both CSV files.
Run this from the project root: python diagnose_performance.py
"""
import sys
import time
import signal
import numpy as np

# Add project to path
sys.path.insert(0, '.')

from fluorescence_tool.parsers.bmg_parser import BMGOmega3Parser
from fluorescence_tool.parsers.layout_parser import LayoutParser
from fluorescence_tool.algorithms.curve_fitting import CurveFitter

FAST_FILE = "test_data/RM5097.96HL.BNCT.1.CSV"
SLOW_FILE = "test_data/RM5097.96HL.BNCTECCNTRL.2.CSV"
LAYOUT_FILE = "test_data/RM5097_layout.csv"

def time_file(fluorescence_file: str, layout_file: str, label: str):
    print(f"\n{'='*60}")
    print(f"Timing: {label}")
    print(f"File: {fluorescence_file}")
    print(f"{'='*60}")

    parser = BMGOmega3Parser()
    layout_parser = LayoutParser()

    t0 = time.perf_counter()
    fluo_data = parser.parse_file(fluorescence_file)
    layout_data = layout_parser.parse_file(layout_file)
    parse_time = time.perf_counter() - t0
    print(f"Parse time: {parse_time:.3f}s")
    print(f"Wells in file: {len(fluo_data.wells)}")

    # Count active wells
    active_wells = []
    for well_id in fluo_data.wells:
        if well_id in layout_data:
            if layout_data[well_id].well_type != "unused":
                active_wells.append(well_id)
        else:
            active_wells.append(well_id)
    print(f"Active wells (non-unused): {len(active_wells)}")

    curve_fitter = CurveFitter(timeout_seconds=2)
    time_points = np.array(fluo_data.time_points)

    well_times = []
    timeout_counts = []
    slow_wells = []

    t_total_start = time.perf_counter()

    for i, well_id in enumerate(fluo_data.wells):
        if well_id not in active_wells:
            continue

        fluo_values = fluo_data.measurements[i, :]

        t_well_start = time.perf_counter()
        result = curve_fitter.fit_curve(time_points, fluo_values)
        t_well_end = time.perf_counter()

        elapsed = t_well_end - t_well_start
        well_times.append(elapsed)

        if elapsed > 1.0:
            slow_wells.append((well_id, elapsed, result.success, result.strategy_used))

    total_fit_time = time.perf_counter() - t_total_start

    print(f"\nCurve fitting total: {total_fit_time:.3f}s")
    print(f"Wells timed: {len(well_times)}")
    if well_times:
        print(f"  Min per well:  {min(well_times)*1000:.1f}ms")
        print(f"  Max per well:  {max(well_times)*1000:.1f}ms")
        print(f"  Mean per well: {np.mean(well_times)*1000:.1f}ms")
        print(f"  Median:        {np.median(well_times)*1000:.1f}ms")

    if slow_wells:
        print(f"\nSlow wells (>1s):")
        for well_id, elapsed, success, strategy in slow_wells:
            print(f"  {well_id}: {elapsed:.2f}s  success={success}  strategy={strategy}")
    else:
        print("\nNo slow wells (all < 1s)")

    return total_fit_time


if __name__ == "__main__":
    print("=== SCIPY WARM-UP (first call overhead) ===")
    # Warm up scipy so we measure steady-state performance
    dummy_x = np.linspace(0, 10, 32)
    dummy_y = 1000 / (1 + np.exp(-1.0 * (dummy_x - 5))) + 2000
    warmup_fitter = CurveFitter(timeout_seconds=2)
    t_warmup = time.perf_counter()
    warmup_fitter.fit_curve(dummy_x, dummy_y)
    print(f"Scipy warm-up took: {time.perf_counter() - t_warmup:.3f}s")

    print("\n=== NOW TIMING BOTH FILES (scipy already warm) ===")
    t1 = time_file(FAST_FILE, LAYOUT_FILE, "FAST FILE (BNCT.1)")
    t2 = time_file(SLOW_FILE, LAYOUT_FILE, "SLOW FILE (BNCTECCNTRL.2)")

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Fast file total fit time: {t1:.3f}s")
    print(f"Slow file total fit time: {t2:.3f}s")
    print(f"Ratio (slow/fast):        {t2/t1:.1f}x")

    print("\n=== NOW REVERSING ORDER (slow first, then fast) ===")
    t2b = time_file(SLOW_FILE, LAYOUT_FILE, "SLOW FILE (second run)")
    t1b = time_file(FAST_FILE, LAYOUT_FILE, "FAST FILE (second run)")
    print(f"\nSlow file (2nd run): {t2b:.3f}s")
    print(f"Fast file (2nd run): {t1b:.3f}s")
