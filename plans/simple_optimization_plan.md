# Simple Fluorescence Tool Optimization Plan

## Problem: 1-2 minute processing time for 96 wells

## Root Cause Analysis
From [`main_window.py:396-467`](fluorescence_tool/gui/main_window.py:396):
1. **Sequential processing** - wells processed one by one
2. **Redundant curve fitting** - each well fitted twice (lines 422 and 441)
3. **GUI blocking** - everything runs on main thread

## Simple 3-Step Solution

### Step 1: Fix Redundant Curve Fitting (1 day) 🎯
**Problem:** Each well is curve-fitted twice
- Once in [`CurveFitter.fit_curve()`](fluorescence_tool/algorithms/curve_fitting.py:186) 
- Again in [`calculate_second_derivative_crossing_point()`](fluorescence_tool/algorithms/threshold_analysis.py:178)

**Fix:** Pass fitted parameters from step 1 to step 2
**Expected Speedup:** 2x (eliminates 50% of curve fitting)
**Risk:** Very Low

### Step 2: Add Thread Pool (2-3 days) 🚀
**Problem:** 96 wells processed sequentially
**Fix:** Use `ThreadPoolExecutor` to process 6-8 wells simultaneously

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

# Replace the sequential loop in main_window.py:396-467
with ThreadPoolExecutor(max_workers=6) as executor:
    futures = {executor.submit(analyze_well, well_id): well_id 
               for well_id in wells_to_analyze}
    
    for future in as_completed(futures):
        result = future.result()
        # Update progress and results
```

**Expected Speedup:** 6x (parallel processing)
**Risk:** Low

### Step 3: Move to Background Thread (1-2 days) 📱
**Problem:** GUI freezes during processing
**Fix:** Run analysis in background thread with progress updates

```python
class AnalysisWorker(threading.Thread):
    def run(self):
        # Run Steps 1 & 2 here
        # Emit progress signals to update GUI
```

**Expected Speedup:** No speed gain, but responsive GUI
**Risk:** Low

## Expected Results
- **Step 1:** 2x speedup (60-120 seconds → 30-60 seconds)
- **Step 2:** 6x additional speedup (30-60 seconds → 5-10 seconds)  
- **Step 3:** Responsive GUI during 5-10 second processing

**Total:** **12x speedup** from 1-2 minutes to **5-10 seconds**

## Implementation Order
1. **Week 1:** Fix redundant curve fitting
2. **Week 2:** Add thread pool processing  
3. **Week 3:** Move to background thread

Each step can be tested and deployed independently.