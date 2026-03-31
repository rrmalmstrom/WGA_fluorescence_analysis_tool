# Fluorescence Data Analysis Tool - User Guide

A comprehensive guide for laboratory scientists using the simplified fluorescence analysis tool.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Interface Overview](#interface-overview)
3. [Loading Data Files](#loading-data-files)
4. [Working with the Plate View](#working-with-the-plate-view)
5. [Analyzing Data](#analyzing-data)
6. [Understanding Results](#understanding-results)
7. [Exporting Data and Plots](#exporting-data-and-plots)
8. [Pass/Fail Analysis](#passfail-analysis)
9. [Troubleshooting](#troubleshooting)
10. [Frequently Asked Questions](#frequently-asked-questions)

---

## Getting Started

### What You Need

Before using the fluorescence analysis tool, ensure you have:

- **Data Files**: Your fluorescence measurements in BMG Omega3 (.csv) or BioRad (.txt) format
- **Layout File**: A CSV file describing your plate layout with well types and groupings
- **Python Environment**: The tool installed and ready to run (see [INSTALLATION.md](INSTALLATION.md))

### Launching the Application

1. Open your terminal or command prompt
2. Activate the conda environment:
   ```bash
   conda activate wga-fluorescence-gui
   ```
3. Navigate to the tool directory and launch:
   ```bash
   python main.py
   ```
   Or, for verbose debug output:
   ```bash
   python launch_gui.py
   ```

The application window will open with a clean interface ready for your analysis.

---

## Interface Overview

The fluorescence analysis tool uses a split-pane design optimized for scientific workflows:

### Main Window Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ Fluorescence Analysis Tool                                    [Menu] │
├─────────────────────────────────────────────────────────────────────┤
│ File Loading Panel                                                  │
│ [Load Data File] [Load Layout File] [Process] [Status: Ready]       │
├─────────────────────────────────────────────────────────────────────┤
│                                    │                                │
│  Plate View (Left Pane)           │  Plot Panel (Right Pane)       │
│                                    │                                │
│  ┌─────────────────────────────┐   │  ┌─────────────────────────────┐│
│  │    Interactive Plate       │   │  │     Time-Series Plot        ││
│  │                             │   │  │                             ││
│  │  A1  A2  A3  A4  A5  A6    │   │  │                             ││
│  │  B1  B2  B3  B4  B5  B6    │   │  │                             ││
│  │  C1  C2  C3  C4  C5  C6    │   │  │                             ││
│  │  ...                        │   │  │                             ││
│  │                             │   │  │                             ││
│  │  Color Legend:              │   │  └─────────────────────────────┘│
│  │  ■ Sample  ■ Control        │   │                                │
│  │  ■ Unused  ■ Selected       │   │  Analysis Controls:            │
│  └─────────────────────────────┘   │  [Analyze Selected] [Export]   │
│                                    │                                │
│  Selection Info:                   │  Plot Options:                 │
│  Wells: A1, A2, B3 (3 selected)   │  ☑ Raw Data  ☑ Fitted Curves  │
│                                    │  ☑ Thresholds ☑ Crossing Pts  │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Interface Elements

- **File Loading Panel**: Load your data and layout files
- **Plate View**: Interactive visualization of your plate layout
- **Plot Panel**: Real-time time-series plots of selected wells
- **Analysis Controls**: Run analysis and export results
- **Status Bar**: Shows current operation status and progress

---

## Loading Data Files

The fluorescence analysis tool supports two main instrument formats and requires a layout file for complete analysis.

### Supported File Formats

#### BMG Omega3 Format (.csv)
- **Automatic Processing**: No additional input required
- **Time Format**: Recognizes "X h Y min" format (e.g., "2 h 30 min")
- **Well Layout**: Automatically extracts from row/column data
- **Metadata**: Captures user, test name, date, and plate ID

**Example BMG File Structure:**
```
User: John Doe, Date: 2024-03-15, Time: 14:30:22
Test name: Growth Assay, Date: 2024-03-15, Time: 14:30:22
Kinetic: 0 h 0 min to 24 h 0 min, 96 cycles, 15 min interval
ID1: RM5097.96HL.BNCT.1, ID2:
Fluorescence (FI)

Well Row,Well Col,Content,Time,0 h,0 h 15 min,0 h 30 min,...
A,1,A1,Time,1234.5,1245.2,1256.8,...
A,2,A2,Time,2345.6,2356.3,2367.9,...
```

#### BioRad Format (.txt)
- **Cycle-Based Data**: Tab-separated format with cycle numbers
- **Time Conversion**: Requires cycle time input (minutes per cycle)
- **Plate Detection**: Automatically detects 96-well or 384-well format

**Example BioRad File Structure:**
```
Cycle	A1	A2	A3	A4	...	P24
1	1234.5	2345.6	3456.7	4567.8	...	9876.5
2	1245.2	2356.3	3467.4	4578.5	...	9887.2
3	1256.8	2367.9	3478.1	4589.2	...	9898.9
```

#### Layout File (.csv)
Required for both formats to provide well classification and grouping information.

**Required Columns** (must all be present — file will be rejected if any are missing):
- `Plate_ID`: Identifier for the plate. **Must contain exactly one unique, non-empty value across all rows.** Files with an empty `Plate_ID` column or with more than one distinct `Plate_ID` value will be rejected at load time.
- `Well_Row`: Row letter (A, B, C, ...)
- `Well_Col`: Column number (1, 2, 3, ...)
- `Well`: Combined well ID (A1, B2, C3, ...)
- `Sample`: Sample identifier or name (may be empty for unused wells)
- `Type`: Well classification (sample, neg_cntrl, pos_cntrl, unused, blank)

**Optional Columns:**
- `number_of_cells/capsules`: Cell count information
- `Group_1`, `Group_2`, `Group_3`: Hierarchical grouping for analysis

> **Note:** The `Sample` column must appear between `Well` and `Type` in the CSV header.
> Layout files that do not include the `Sample` column will be rejected with an error.

**Example Layout File:**
```csv
Plate_ID,Well_Row,Well_Col,Well,Sample,Type,number_of_cells/capsules,Group_1,Group_2,Group_3
Killer_plate_1,A,1,A1,,unused,,,,
Killer_plate_1,D,2,D2,TEXAS_1,neg_cntrl,0,sheath,,
Killer_plate_1,H,2,H2,TEXAS_1,pos_cntrl,0,DNA,,
Killer_plate_1,D,3,D3,TEXAS_1,sample,100,Rep1,BONCAT,Big
```

### Step-by-Step File Loading

#### Step 1: Load Fluorescence Data File

1. **Click "Load Data File"** in the file loading panel
2. **Navigate** to your fluorescence data file
3. **Select** either a BMG (.csv) or BioRad (.txt) file
4. **For BioRad files only**: Enter the cycle time in minutes
   - This is the time interval between measurements
   - Common values: 15 minutes, 30 minutes, 1 hour (60 minutes)
   - Check your instrument settings or protocol

#### Step 2: Load Layout File

1. **Click "Load Layout File"** in the file loading panel
2. **Navigate** to your layout CSV file
3. **Select** the file that corresponds to your plate setup

#### Step 3: Process Files

1. **Click "Process Files"** to load and validate the data
2. **Wait** for processing to complete (usually 1-5 seconds)
3. **Check** the status message for any warnings or errors

### File Loading Tips

#### Successful Loading Indicators
- ✅ Status shows "Files loaded successfully"
- ✅ Plate view displays colored wells
- ✅ Well count matches your expectations
- ✅ Time points are correctly parsed

#### Common Issues and Solutions

**"File format not recognized"**
- Ensure BMG files have .csv extension
- Ensure BioRad files have .txt extension
- Check that files aren't corrupted or empty

**"Layout file missing required columns"**
- Verify all required columns are present
- Check column names match exactly (case-sensitive)
- Ensure no extra spaces in column headers

**"Well mismatch between data and layout"**
- Verify plate IDs match between files
- Check that well naming is consistent (A1, A2, etc.)
- Ensure layout covers all wells in your data file

**"Invalid time format in BMG file"**
- Check that time headers follow "X h Y min" format
- Ensure no special characters in time columns
- Verify file encoding is UTF-8

#### File Validation

The tool automatically validates your files and will show warnings for:
- Missing wells in layout file
- Inconsistent time progression
- Unusual fluorescence values (negative, extremely high)
- Encoding issues or special characters

**Important**: Warnings don't prevent analysis but should be reviewed to ensure data quality.

---

## Working with the Plate View

The interactive plate view is the central hub for selecting wells and visualizing your experimental layout.

### Understanding the Plate Layout

#### Well Color Coding

Wells are automatically colored based on their type from the layout file:

- **🟢 Green (Light)**: Sample wells - your experimental samples
- **🔴 Pink (Light)**: Negative controls - baseline/background measurements
- **🔵 Blue (Sky)**: Positive controls - known positive responses
- **⚪ Gray (Light)**: Unused wells - not part of the experiment
- **⚫ Gray (Very Light)**: Blank wells - empty or buffer only

#### Multi-Layer Grouping

The tool supports hierarchical grouping through Group_1, Group_2, and Group_3 columns:

- **Group_1**: Primary experimental grouping (e.g., "Treatment", "Control")
- **Group_2**: Secondary classification (e.g., "BONCAT", "Standard")
- **Group_3**: Tertiary details (e.g., "Replicate1", "Dose_10uM")

### Selecting Wells for Analysis

#### Individual Well Selection

1. **Click** on any well in the plate view
2. **Selected wells** appear with a darker border and different visual style
3. **Click again** to deselect a well
4. **Real-time updates**: The plot panel immediately shows selected wells

#### Multiple Well Selection

**Method 1: Click Multiple Wells**
- Hold Ctrl (Windows/Linux) or Cmd (Mac) while clicking
- Each click adds or removes wells from selection

**Method 2: Use Selection Buttons**
- **"Select All"**: Selects all wells with data
- **"Clear Selection"**: Deselects all wells
- **"Select by Filter"**: Choose wells based on type or groups

#### Selection by Filtering

1. **Click "Select by Filter"** to open the filter dialog
2. **Choose criteria**:
   - **Well Type**: Select all samples, controls, etc.
   - **Group_1**: Select by primary grouping
   - **Group_2**: Select by secondary grouping
   - **Group_3**: Select by tertiary grouping
3. **Apply filters** to automatically select matching wells

### Grouping Controls

#### Dynamic Grouping Display

The grouping controls panel allows you to change how wells are colored:

**Type-Based Coloring (Default)**
- Wells colored by their type (sample, control, etc.)
- Best for understanding experimental design

**Group-Based Coloring**
- Check "Group_1" to color by primary groups
- Check "Group_2" to color by secondary groups
- Check "Group_3" to color by tertiary groups
- **Combine multiple** groupings for complex color schemes

#### Color Legend

The plate view automatically displays a color legend showing:
- Current coloring scheme
- Number of wells in each category
- Selection status indicators

### Selection Information Panel

Below the plate view, you'll see real-time selection information:

```
Selection Info:
Wells: A1, A2, B3, C4, D5 (5 selected)
Types: 3 samples, 2 neg_cntrl
Groups: Treatment (3), Control (2)
```

This helps you verify that you've selected the intended wells for analysis.

### Plate View Tips

#### Efficient Well Selection

**For Replicates**: Use grouping filters to select all replicates at once
**For Comparisons**: Select treatment and control groups together
**For Quality Check**: Start with a few representative wells before full analysis

#### Visual Verification

- **Check colors** match your experimental design
- **Verify well counts** against your protocol
- **Use grouping** to highlight experimental structure
- **Review selection** before running analysis

---

## Analyzing Data

Once you've loaded your files and selected wells, you can perform comprehensive fluorescence analysis.

### Running the Analysis

#### Basic Analysis Workflow

1. **Select Wells**: Choose wells for analysis using the plate view
2. **Click "Analyze Selected"**: Starts the analysis process
3. **Monitor Progress**: Watch the progress indicator and status messages
4. **Review Results**: Examine plots and analysis outcomes

#### What Happens During Analysis

The tool performs several sophisticated analyses automatically:

**1. Data Validation**
- Checks for sufficient data points (minimum 5 time points)
- Validates fluorescence value ranges
- Identifies potential outliers or anomalies

**2. Curve Fitting**
- Applies 5-parameter sigmoid curve fitting
- Uses multiple fitting strategies for robustness
- Calculates goodness-of-fit (R-squared) values

**3. Threshold Detection**
- Calculates baseline from early time points
- Determines threshold as 10% above baseline
- Finds precise crossing point using interpolation

**4. Quality Assessment**
- Evaluates fit quality (excellent, good, fair, poor)
- Identifies wells with analysis issues
- Provides detailed error messages when needed

### Understanding Analysis Results

#### Real-Time Plot Updates

As analysis completes, the plot panel shows:

**Raw Data Points**
- Original fluorescence measurements as circles
- Connected by lines to show time progression
- Each well gets a unique color

**Fitted Curves**
- Smooth sigmoid curves fitted to the data
- Overlaid on raw data points
- Shows the mathematical model of growth

**Threshold Lines**
- Horizontal dashed lines showing calculated thresholds
- Vertical dotted lines showing crossing points
- Intersection points marked with X symbols

#### Analysis Quality Indicators

**Excellent Fits (R² ≥ 0.95)**
- Curve closely matches data points
- Reliable threshold and crossing point values
- High confidence in results

**Good Fits (R² ≥ 0.85)**
- Reasonable curve fit with minor deviations
- Generally reliable results
- May have some noise or irregularities

**Fair Fits (R² ≥ 0.70)**
- Moderate curve fit quality
- Results should be interpreted carefully
- May indicate experimental issues

**Poor Fits (R² < 0.70)**
- Curve doesn't match data well
- Results may be unreliable
- Consider excluding from analysis or investigating issues

### Analysis Parameters

#### Curve Fitting Settings

The tool uses optimized default parameters that work well for most fluorescence assays:

**5-Parameter Sigmoid Model**
```
y = a / (1 + exp(-b * (x - c))) + d + e * x
```

Where:
- **a**: Amplitude (difference between upper and lower asymptotes)
- **b**: Slope factor (steepness of the curve)
- **c**: Inflection point (time at maximum slope)
- **d**: Baseline (minimum fluorescence)
- **e**: Linear component (accounts for drift)

#### Threshold Detection Settings

**Baseline Calculation**
- Uses time points 2-4 (skipping the first point)
- Calculates mean fluorescence of baseline points
- Threshold = baseline × 1.10 (10% above baseline)

**Crossing Point Detection**
- Uses fitted curve (not raw data) for precision
- Linear interpolation between crossing points
- Reports time in hours with high precision

### Handling Analysis Issues

#### Common Analysis Problems

**"Insufficient data variation"**
- Fluorescence values don't change enough for curve fitting
- Check if wells contain active samples
- Verify measurement conditions

**"Curve fitting failed"**
- Mathematical optimization couldn't find a solution
- May indicate unusual data patterns
- Try excluding problematic time points

**"No threshold crossing found"**
- Fluorescence never exceeds the calculated threshold
- May indicate inactive samples or low signal
- Consider adjusting experimental conditions

#### Troubleshooting Tips

**For Poor Fits**:
1. Check raw data for obvious outliers
2. Verify time progression is correct
3. Consider if experimental conditions were optimal

**For Missing Crossings**:
1. Examine if fluorescence is increasing
2. Check if measurement duration was sufficient
3. Verify sample activity and concentrations

**For Inconsistent Results**:
1. Compare replicates for consistency
2. Check control wells for expected behavior
3. Review experimental protocol for issues

---

## Understanding Results

After analysis completes, you'll have comprehensive results including curve parameters, quality metrics, and threshold values.

### Result Components

#### Curve Fitting Parameters

For each successfully analyzed well, you get:

**5-Parameter Sigmoid Coefficients**
- **a**: Amplitude - difference between maximum and minimum fluorescence
- **b**: Slope factor - how steep the growth curve is (positive or negative)
- **c**: Inflection point - time at maximum growth rate (hours)
- **d**: Baseline - minimum fluorescence level
- **e**: Linear component - accounts for linear drift over time

**Quality Metrics**
- **R-squared**: Goodness of fit (0.0 to 1.0, higher is better)
- **Fit Quality**: Categorical assessment (excellent/good/fair/poor)
- **Convergence Info**: Details about the optimization process

#### Threshold Analysis Results

**Threshold Value**: Calculated fluorescence level for crossing point detection
- Based on 10% above baseline (mean of early time points)
- Automatically calculated for each well
- Used for consistent crossing point determination

**Crossing Point**: Time when fluorescence crosses the threshold
- Reported in hours with high precision
- Calculated using fitted curve (not raw data)
- Linear interpolation for sub-timepoint accuracy

**Fluorescence Change**: Total change from start to end
- Final fluorescence minus initial fluorescence
- Indicates overall signal strength
- Used for pass/fail analysis

### Interpreting Quality Metrics

#### R-Squared Values

**R² ≥ 0.95 (Excellent)**
- Curve fits data very well
- High confidence in all parameters
- Reliable for quantitative analysis

**R² 0.85-0.94 (Good)**
- Good curve fit with minor deviations
- Generally reliable results
- Suitable for most analyses

**R² 0.70-0.84 (Fair)**
- Moderate fit quality
- Results should be interpreted carefully
- May indicate experimental variability

**R² < 0.70 (Poor)**
- Poor curve fit
- Results may be unreliable
- Consider excluding from analysis

#### Biological Interpretation

**Normal Growth Curves**
- Sigmoid shape with clear lag, exponential, and stationary phases
- Consistent crossing points among replicates
- R² values typically > 0.90

**Unusual Patterns**
- Linear growth: May indicate different growth kinetics
- No growth: Inactive samples or inhibitory conditions
- Irregular patterns: Experimental artifacts or contamination

### Comparing Results Across Wells

#### Replicate Consistency

**Good Replicates**
- Crossing points within 10-20% of each other
- Similar curve shapes and parameters
- Consistent R² values

**Variable Replicates**
- Large differences in crossing points
- Different curve shapes
- May indicate pipetting errors or sample issues

#### Control Well Validation

**Negative Controls**
- Should show minimal fluorescence increase
- Late or no threshold crossing
- Validates assay specificity

**Positive Controls**
- Should show expected growth pattern
- Consistent crossing points
- Validates assay functionality

---

## Exporting Data and Plots

The tool provides comprehensive export capabilities for both data analysis and publication.

### CSV Data Export

#### Complete Analysis Export

Click **"Export Data"** to generate a comprehensive CSV file containing:

**Well Information**
- Well ID, Plate ID, Sample name
- Well type and grouping information
- Cell count (if provided)

**Analysis Results**
- Crossing point (hours)
- Threshold value (RFU)
- Fluorescence change (final - initial)
- R-squared goodness of fit
- Fit quality assessment

**Curve Parameters**
- All 5 sigmoid parameters (a, b, c, d, e)
- Parameter confidence intervals (when available)

**Raw and Fitted Data**
- Original fluorescence measurements at each time point
- Fitted curve values at each time point
- Time points in hours

#### CSV File Structure

```csv
Well,Plate_ID,Sample,Type,Group_1,Group_2,Group_3,Cell_Count,
Crossing_Point,Threshold_Value,Delta_Fluorescence,R_Squared,
Fit_Quality,Sigmoid_A,Sigmoid_B,Sigmoid_C,Sigmoid_D,Sigmoid_E,
Raw_T0,Raw_T1,Raw_T2,...,Fitted_T0,Fitted_T1,Fitted_T2,...
A1,RM5097,Sample1,sample,Rep1,BONCAT,,100,
12.45,1456.7,2345.8,0.967,excellent,2000.5,1.23,12.1,1200.3,0.05,
1234.5,1245.2,1256.8,...,1235.1,1246.3,1257.9,...
```

### PDF Plot Export

#### Publication-Quality Plots

Click **"Export Plot"** to generate high-resolution PDF plots suitable for publications:

**Plot Features**
- 300 DPI resolution for crisp printing
- Professional axis labels and formatting
- Color-coded wells matching your selection
- Automatic legend generation
- Metadata annotation box

**Customizable Elements**
- Raw data points (circles connected by lines)
- Fitted sigmoid curves (smooth lines)
- Threshold lines (horizontal dashed)
- Crossing points (vertical dotted lines with X markers)

#### Plot Options

Before exporting, you can customize what appears in the plot:

**Data Display Options**
- ☑ **Raw Data**: Show original measurement points
- ☑ **Fitted Curves**: Show mathematical curve fits
- ☑ **Thresholds**: Show threshold lines for each well
- ☑ **Crossing Points**: Show crossing point markers

**Visual Customization**
- Automatic color assignment for clarity
- Well type-based color coding
- Group-based color schemes
- Professional formatting for publications

### Export File Naming

**CSV Data Export** — The filename is generated automatically from the `Plate_ID` in the loaded layout file:

**Format**: `{Plate_ID}_amplification_kinetics_summary.csv`

**Example**: If your layout file contains `Plate_ID = Killer_plate_1`, the exported file will be named:
```
Killer_plate_1_amplification_kinetics_summary.csv
```

The file is saved to the directory from which the application was launched. A confirmation dialog shows the full save path before writing.

> **Note:** If no layout file has been loaded, the tool falls back to a standard Save As dialog so you can choose the filename and location manually.

**Plot Export** — A standard Save As dialog is used; choose any filename and format (PDF, PNG, SVG, EPS).

### Export Tips

#### For Data Analysis
- Export CSV files for statistical analysis in R, Python, or Excel
- Include all wells for comprehensive dataset
- Use timestamps to track analysis versions

#### For Publications
- Export plots with all visual elements for complete figures
- Use high-resolution PDF for vector graphics
- Include metadata annotation for figure legends

#### For Presentations
- Export plots with clear, large fonts
- Focus on key wells for clarity
- Use consistent color schemes across slides

---

## Pass/Fail Analysis

The tool includes an advanced pass/fail analysis system for automated quality control and decision making.

### Pass/Fail Criteria

The system uses dual criteria that both must be met for a well to pass:

#### Criterion 1: Crossing Point (CP)
- **Threshold**: CP < 6.5 hours by default
- **Logic**: Faster growth indicates active/viable samples
- **Configurable**: Can be adjusted based on your assay requirements

#### Criterion 2: Fluorescence Change
- **Threshold**: Change > 500 RFU by default
- **Logic**: Sufficient signal indicates meaningful response
- **Configurable**: Can be adjusted based on your detection system

### Pass/Fail Results

#### Individual Well Results

For each analyzed well, you get:

**Overall Status**: `Pass` or `Fail`
**CP Status**: Whether crossing point criterion was met
**Fluorescence Status**: Whether fluorescence change criterion was met
**Values Used**: Actual CP and fluorescence change values
**Failure Reason**: Specific reason if well failed

> **Note:** Wells that do not pass the initial QC fluorescence-change filter (i.e. no crossing point is calculated) are automatically assigned `Fail` in the exported CSV. The `Pass_Fail` column contains only `Pass`, `Fail`, or `N/A` — no sub-categories.

#### Example Results

```
Well A1: PASS
- CP: 4.09 h (< 6.5 h) ✓
- Fluorescence Change: 1234.5 RFU (> 500 RFU) ✓

Well B2: FAIL
- CP: 7.61 h (≥ 6.5 h) ✗
- Fluorescence Change: 1876.2 RFU (> 500 RFU) ✓
- Reason: CP 7.61 >= 6.5

Well C3: FAIL
- CP: 3.90 h (< 6.5 h) ✓
- Fluorescence Change: 234.5 RFU (≤ 500 RFU) ✗
- Reason: Fluorescence change 234.5 <= 500
```

### Configuring Thresholds

#### Adjusting Default Values

The default thresholds work well for many assays, but you can customize them:

**CP Threshold Considerations**
- **Faster assays**: Lower threshold (e.g., 4.0 hours)
- **Slower assays**: Higher threshold (e.g., 8.0 hours)
- **Based on controls**: Set based on positive control performance

**Fluorescence Change Considerations**
- **High-sensitivity instruments**: Lower threshold (e.g., 200 RFU)
- **Low-sensitivity instruments**: Higher threshold (e.g., 1000 RFU)
- **Based on background**: Set relative to negative control variation

#### Assay-Specific Optimization

**Cell Viability Assays**
- CP threshold: 5.0–6.5 hours
- Fluorescence change: 500–1000 RFU
- Focus on early detection of viable cells

**Drug Screening Assays**
- CP threshold: 6.5–10.0 hours
- Fluorescence change: 200–500 RFU
- Balance sensitivity with specificity

**Quality Control Applications**
- Stricter thresholds for higher confidence
- Consider using positive control performance as reference

### Pass/Fail Summary Statistics

The tool provides comprehensive summary statistics:

**Overall Statistics**
- Total wells analyzed
- Number passed/failed
- Pass rate percentage

**Failure Analysis**
- Wells failing CP criterion only
- Wells failing fluorescence criterion only
- Wells failing both criteria

**Group-Based Analysis**
- Pass rates by well type
- Pass rates by experimental groups
- Comparison across conditions

### Using Pass/Fail Results

#### Quality Control
- Set acceptance criteria for batch release
- Identify problematic samples or conditions
- Track assay performance over time

#### Automated Decision Making
- Flag samples requiring repeat analysis
- Identify wells for further investigation
- Support high-throughput screening workflows

#### Data Interpretation
- Focus analysis on passing wells
- Investigate patterns in failing wells
- Validate experimental conditions

---

## Troubleshooting

Common issues and their solutions for smooth operation of the fluorescence analysis tool.

### File Loading Issues

#### "File format not recognized"

**Symptoms**: Error message when trying to load data files
**Causes**:
- Incorrect file extension
- Corrupted or empty files
- Unsupported file format

**Solutions**:
1. Verify file extension (.csv for BMG, .txt for BioRad)
2. Open file in text editor to check content
3. Re-export from instrument software if corrupted
4. Check file size (should not be 0 bytes)

#### "Layout file missing required columns"

**Symptoms**: Error when processing layout file
**Causes**:
- Missing required column headers (including the `Sample` column)
- Misspelled column names
- Extra spaces in headers
- Using an older layout file format that pre-dates the `Sample` column

**Solutions**:
1. Check all required columns are present: `Plate_ID`, `Well_Row`, `Well_Col`, `Well`, `Sample`, `Type`
2. Ensure `Sample` appears between `Well` and `Type` in the header row
3. Verify exact spelling (case-sensitive)
4. Remove extra spaces from column headers
5. Save as CSV with UTF-8 encoding

#### "Well mismatch between data and layout"

**Symptoms**: Warning about inconsistent wells
**Causes**:
- Different plate IDs between files
- Missing wells in layout file
- Inconsistent well naming

**Solutions**:
1. Verify Plate_ID matches between files
2. Ensure layout covers all data wells
3. Check well naming format (A1, A2, etc.)
4. Add missing wells to layout file

### Analysis Issues

#### "Insufficient data variation"

**Symptoms**: Wells skipped during analysis
**Causes**:
- Flat fluorescence curves
- Very small signal changes
- Inactive samples

**Solutions**:
1. Check if samples are viable/active
2. Verify measurement conditions
3. Consider longer measurement duration
4. Check instrument sensitivity settings

#### "Curve fitting failed"

**Symptoms**: No fitted curve for some wells
**Causes**:
- Unusual data patterns
- Insufficient data points
- Mathematical optimization issues

**Solutions**:
1. Check for obvious outliers in data
2. Verify minimum 5 time points
3. Examine raw data for irregularities
4. Consider excluding problematic time points

#### "No threshold crossing found"

**Symptoms**: Missing crossing point values
**Causes**:
- Fluorescence never exceeds threshold
- Very slow growth
- Inactive samples

**Solutions**:
1. Check if fluorescence is increasing
2. Verify measurement duration is sufficient
3. Consider lowering threshold percentage
4. Examine sample activity

### GUI and Display Issues

#### "Application won't start"

**Symptoms**: Error when launching GUI
**Causes**:
- Missing Python environment
- Incorrect dependencies
- Display/graphics issues

**Solutions**:
1. Verify conda environment is activated
2. Check all dependencies are installed
3. Update graphics drivers
4. Try running from command line for error details

#### "Plate view not displaying correctly"

**Symptoms**: Missing or incorrectly colored wells
**Causes**:
- Layout file issues
- Display scaling problems
- Memory limitations

**Solutions**:
1. Verify layout file is correctly formatted
2. Check display scaling settings
3. Restart application
4. Reduce number of wells if memory limited

#### "Plots not updating"

**Symptoms**: Plot panel shows old or no data
**Causes**:
- Selection issues
- Analysis not completed
- Display refresh problems

**Solutions**:
1. Verify wells are properly selected
2. Wait for analysis to complete
3. Try reselecting wells
4. Restart application if persistent

### Performance Issues

#### "Analysis taking too long"

**Symptoms**: Very slow curve fitting
**Causes**:
- Large number of wells
- Complex data patterns
- Insufficient system resources

**Solutions**:
1. Analyze wells in smaller batches
2. Close other applications
3. Increase available RAM
4. Consider faster computer for large datasets

#### "Export files very large"

**Symptoms**: CSV or PDF files are unexpectedly large
**Causes**:
- Many time points
- High precision numbers
- Large number of wells

**Solutions**:
1. Export only necessary wells
2. Consider data compression
3. Use summary statistics instead of full data
4. Split large datasets into multiple files

### Data Quality Issues

#### "Inconsistent replicate results"

**Symptoms**: Large variation between replicates
**Causes**:
- Pipetting errors
- Sample degradation
- Experimental variability

**Solutions**:
1. Check pipetting technique and calibration
2. Verify sample storage conditions
3. Review experimental protocol
4. Consider additional replicates

#### "Unusual curve shapes"

**Symptoms**: Non-sigmoid growth patterns
**Causes**:
- Different growth kinetics
- Experimental artifacts
- Contamination

**Solutions**:
1. Examine raw data carefully
2. Check experimental conditions
3. Verify sample preparation
4. Consider alternative analysis methods

---

## Frequently Asked Questions

### General Usage

**Q: What file formats does the tool support?**
A: BMG Omega3 CSV files and BioRad TXT files, plus CSV layout files for well information.

**Q: Can I analyze partial plates?**
A: Yes, the tool handles any number of wells from single wells to full 384-well plates.

**Q: How long does analysis take?**
A: Typically 1-30 seconds depending on the number of wells and data complexity.

**Q: Can I save my work and return later?**
A: Export your results as CSV files. The tool doesn't save sessions, but you can reload the same files.

### File Formats

**Q: My BMG file has different time format. Will it work?**
A: The tool recognizes "X h Y min" format. Contact support if your format is different.

**Q: Can I use Excel files instead of CSV?**
A: No, save Excel files as CSV format before loading.

**Q: What if my layout file has extra columns?**
A: Extra columns are ignored. Only required columns need to match exactly.

### Analysis

**Q: What does R-squared mean?**
A: R-squared measures how well the fitted curve matches your data (0-1, higher is better).

**Q: Why do some wells fail curve fitting?**
A: Usually due to insufficient signal change, unusual patterns, or data quality issues.

**Q: Can I adjust the threshold calculation?**
A: The 10% baseline method is fixed, but pass/fail thresholds are configurable.

**Q: How accurate are the crossing points?**
A: Very accurate - calculated using fitted curves with linear interpolation for sub-timepoint precision.

### Results and Export

**Q: What's the difference between raw and fitted data in exports?**
A: Raw data is your original measurements; fitted data is the calculated sigmoid curve values.

**Q: Can I import results into other software?**
A: Yes, CSV exports work with Excel, R, Python, GraphPad Prism, and other analysis tools.

**Q: How do I cite this tool in publications?**
A: Include the tool name, version, and analysis parameters used in your methods section.

### Troubleshooting

**Q: The tool crashes when I load my file. What should I do?**
A: Check file format, encoding, and size. Try with provided test data first.

**Q: My replicates give very different results. Is this normal?**
A: Some variation is expected, but large differences may indicate experimental issues.

**Q: Can I analyze time-course data with irregular intervals?**
A: Yes, the tool handles irregular time intervals automatically.

**Q: What if I need help with a specific issue?**
A: Check this guide first, then examine the test data examples for comparison.

---

*This completes the comprehensive User Guide for the Fluorescence Data Analysis Tool. For technical details, see [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md). For algorithm details, see [ALGORITHM_DOCUMENTATION.md](ALGORITHM_DOCUMENTATION.md).*