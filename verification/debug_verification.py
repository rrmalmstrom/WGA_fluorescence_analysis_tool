#!/usr/bin/env python3
"""
Debug Verification Script - Step by step debugging
"""

import sys
import os
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test if all imports work."""
    print("Testing imports...")
    try:
        from fluorescence_tool.parsers.bmg_parser import BMGOmega3Parser
        print("✅ BMGOmega3Parser imported")
        
        from fluorescence_tool.parsers.layout_parser import LayoutParser
        print("✅ LayoutParser imported")
        
        from fluorescence_tool.algorithms.curve_fitting import CurveFitter
        print("✅ CurveFitter imported")
        
        from fluorescence_tool.algorithms.threshold_analysis import ThresholdAnalyzer
        print("✅ ThresholdAnalyzer imported")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_file_loading():
    """Test file loading."""
    print("\nTesting file loading...")
    
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "example_input_files"
    
    bmg_file = data_dir / "RM5097.96HL.BNCT.1.CSV"
    bmg_layout_file = data_dir / "RM5097_layout.csv"
    
    print(f"BMG file exists: {bmg_file.exists()}")
    print(f"Layout file exists: {bmg_layout_file.exists()}")
    
    if not bmg_file.exists():
        print(f"❌ BMG file not found: {bmg_file}")
        return False
        
    if not bmg_layout_file.exists():
        print(f"❌ Layout file not found: {bmg_layout_file}")
        return False
    
    return True

def test_bmg_parsing():
    """Test BMG file parsing."""
    print("\nTesting BMG parsing...")
    
    try:
        from fluorescence_tool.parsers.bmg_parser import BMGOmega3Parser
        
        project_root = Path(__file__).parent.parent.parent
        data_dir = project_root / "example_input_files"
        bmg_file = data_dir / "RM5097.96HL.BNCT.1.CSV"
        
        parser = BMGOmega3Parser()
        data = parser.parse_file(str(bmg_file))
        
        print(f"✅ BMG parsing successful")
        print(f"   Wells: {len(data.wells)}")
        print(f"   Time points: {len(data.time_points)}")
        print(f"   Measurements shape: {data.measurements.shape}")
        print(f"   First few wells: {data.wells[:5]}")
        print(f"   Time range: {data.time_points[0]:.1f} - {data.time_points[-1]:.1f}")
        
        # Check first well data
        if len(data.wells) > 0:
            first_well_data = data.measurements[0]
            print(f"   First well data: {len(first_well_data)} points")
            print(f"   First 5 values: {first_well_data[:5]}")
            print(f"   Last 5 values: {first_well_data[-5:]}")
        
        return data
        
    except Exception as e:
        print(f"❌ BMG parsing error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_layout_parsing():
    """Test layout file parsing."""
    print("\nTesting layout parsing...")
    
    try:
        from fluorescence_tool.parsers.layout_parser import LayoutParser
        
        project_root = Path(__file__).parent.parent.parent
        data_dir = project_root / "example_input_files"
        layout_file = data_dir / "RM5097_layout.csv"
        
        parser = LayoutParser()
        layout = parser.parse_file(str(layout_file))
        
        print(f"✅ Layout parsing successful")
        print(f"   Wells: {len(layout)}")
        
        # Show first few wells
        for i, (well_id, well_info) in enumerate(list(layout.items())[:5]):
            print(f"   {well_id}: {well_info.well_type}, Group_1: {well_info.group_1}")
        
        return layout
        
    except Exception as e:
        print(f"❌ Layout parsing error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_curve_fitting(data):
    """Test curve fitting on sample data."""
    print("\nTesting curve fitting...")
    
    if data is None:
        print("❌ No data to test curve fitting")
        return None
    
    try:
        from fluorescence_tool.algorithms.curve_fitting import CurveFitter
        
        fitter = CurveFitter()
        
        # Test on first well with sufficient data
        for i, well_id in enumerate(data.wells):
            measurements = data.measurements[i]
            if len(measurements) > 10:
                print(f"Testing curve fitting on well {well_id}")
                
                result = fitter.fit_curve(
                    time_points=np.array(data.time_points),
                    fluo_values=np.array(measurements)
                )
                
                if result.success:
                    print(f"✅ Curve fitting successful")
                    print(f"   R²: {result.r_squared:.3f}")
                    print(f"   Fit error: {result.fit_error}")
                    print(f"   Parameters: {result.parameters}")
                    print(f"   Strategy used: {result.strategy_used}")
                    return result
                else:
                    print(f"❌ Curve fitting failed: {result.error_message}")
                    
                break
        
        return None
        
    except Exception as e:
        print(f"❌ Curve fitting error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_simple_plot(data):
    """Test simple plotting."""
    print("\nTesting simple plot...")
    
    if data is None:
        print("❌ No data to plot")
        return
    
    try:
        # Create a simple plot of first well
        plt.figure(figsize=(10, 6))
        
        if len(data.wells) > 0:
            measurements = data.measurements[0]
            well_id = data.wells[0]
            
            plt.plot(data.time_points, measurements, 'b-o', markersize=4, label=f'Well {well_id}')
            plt.xlabel('Time (minutes)')
            plt.ylabel('Fluorescence')
            plt.title('Sample Fluorescence Data')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Save plot
            output_dir = Path(__file__).parent / "verification_output"
            output_dir.mkdir(exist_ok=True)
            plt.savefig(output_dir / 'debug_plot.png', dpi=150, bbox_inches='tight')
            print(f"✅ Plot saved to: {output_dir / 'debug_plot.png'}")
            
            plt.show()
        
    except Exception as e:
        print(f"❌ Plotting error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main debug function."""
    print("=" * 60)
    print(" FLUORESCENCE ANALYSIS TOOL - DEBUG VERIFICATION")
    print("=" * 60)
    
    # Test each component step by step
    if not test_imports():
        return
    
    if not test_file_loading():
        return
    
    data = test_bmg_parsing()
    layout = test_layout_parsing()
    
    if data is not None:
        fit_result = test_curve_fitting(data)
        test_simple_plot(data)
    
    print("\n" + "=" * 60)
    print(" DEBUG VERIFICATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()