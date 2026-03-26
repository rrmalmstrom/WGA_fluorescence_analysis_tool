#!/usr/bin/env python3
"""
Interactive Manual Verification Script for Fluorescence Analysis Tool

This script provides an interactive session to manually verify that the 
fluorescence analysis algorithms are working correctly with real data.

Usage:
    python verification/interactive_verification.py
"""

import sys
import os
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fluorescence_tool.parsers.bmg_parser import BMGOmega3Parser
from fluorescence_tool.parsers.biorad_parser import BioRadParser
from fluorescence_tool.parsers.layout_parser import LayoutParser
from fluorescence_tool.algorithms.curve_fitting import CurveFitter
from fluorescence_tool.algorithms.threshold_analysis import ThresholdAnalyzer
from fluorescence_tool.algorithms.statistical_analysis import StatisticalAnalyzer
from fluorescence_tool.core.models import FluorescenceData, WellInfo


class InteractiveVerifier:
    """Interactive verification session for fluorescence analysis algorithms."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "example_input_files"
        self.output_dir = self.project_root / "curve_fitting_output"
        self.verification_output = Path(__file__).parent / "verification_output"
        self.verification_output.mkdir(exist_ok=True)
        
        # Initialize components
        self.curve_fitter = CurveFitter()
        self.threshold_analyzer = ThresholdAnalyzer()
        self.statistical_analyzer = StatisticalAnalyzer()
        
        # Data storage
        self.bmg_data: Optional[FluorescenceData] = None
        self.biorad_data: Optional[FluorescenceData] = None
        self.bmg_layout: Optional[Dict[str, WellInfo]] = None
        self.biorad_layout: Optional[Dict[str, WellInfo]] = None
        
    def print_header(self, title: str):
        """Print a formatted header."""
        print("\n" + "=" * 80)
        print(f" {title}")
        print("=" * 80)
        
    def print_section(self, title: str):
        """Print a formatted section header."""
        print(f"\n--- {title} ---")
        
    def wait_for_user(self, message: str = "Press Enter to continue..."):
        """Wait for user input before proceeding."""
        input(f"\n{message}")
        
    def ask_user_validation(self, question: str) -> bool:
        """Ask user for validation (y/n)."""
        while True:
            response = input(f"\n{question} (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' or 'n'")
                
    def verify_file_processing(self):
        """Verify file parsing and data loading."""
        self.print_header("FILE PROCESSING VERIFICATION")
        
        # Test BMG Omega3 data parsing
        self.print_section("BMG Omega3 Data Parsing")
        bmg_file = self.data_dir / "RM5097.96HL.BNCT.1.CSV"
        bmg_layout_file = self.data_dir / "RM5097_layout.csv"
        
        print(f"Loading BMG file: {bmg_file}")
        print(f"Loading layout file: {bmg_layout_file}")
        
        try:
            # Parse BMG data
            bmg_parser = BMGOmega3Parser()
            self.bmg_data = bmg_parser.parse_file(str(bmg_file))
            
            # Parse layout
            layout_parser = LayoutParser()
            self.bmg_layout = layout_parser.parse_file(str(bmg_layout_file))
            
            # Display parsed data structure
            print(f"\nBMG Data Structure:")
            print(f"  - Metadata: {self.bmg_data.metadata}")
            print(f"  - Number of wells: {len(self.bmg_data.wells)}")
            print(f"  - Time points: {len(self.bmg_data.time_points)}")
            print(f"  - Time range: {self.bmg_data.time_points[0]:.1f} - {self.bmg_data.time_points[-1]:.1f} minutes")
            
            print(f"\nLayout Data Structure:")
            print(f"  - Number of wells: {len(self.bmg_layout)}")
            print(f"  - Well types: {set(w.well_type for w in self.bmg_layout.values())}")
            
            # Show sample well data
            sample_well_id = self.bmg_data.wells[0]
            sample_measurements = self.bmg_data.measurements[0]
            print(f"\nSample well ({sample_well_id}):")
            print(f"  - Measurements: {len(sample_measurements)} values")
            print(f"  - First 5 values: {sample_measurements[:5]}")
            print(f"  - Last 5 values: {sample_measurements[-5:]}")
            
            if not self.ask_user_validation("Does the BMG data structure look correct?"):
                print("❌ BMG data parsing verification failed!")
                return False
                
        except Exception as e:
            print(f"❌ Error parsing BMG data: {e}")
            return False
            
        # Test BioRad data parsing
        self.print_section("BioRad Data Parsing")
        biorad_file = self.data_dir / "TEST01.BIORAD.FORMAT.1.txt"
        biorad_layout_file = self.data_dir / "TEST01.BIORAD_layout.csv"
        
        print(f"Loading BioRad file: {biorad_file}")
        print(f"Loading layout file: {biorad_layout_file}")
        
        try:
            # Parse BioRad data
            biorad_parser = BioRadParser()
            self.biorad_data = biorad_parser.parse_file(str(biorad_file), cycle_time_minutes=15.0)
            
            # Parse layout (if exists)
            if biorad_layout_file.exists():
                self.biorad_layout = layout_parser.parse_file(str(biorad_layout_file))
            
            # Display parsed data structure
            print(f"\nBioRad Data Structure:")
            print(f"  - Metadata: {self.biorad_data.metadata}")
            print(f"  - Number of wells: {len(self.biorad_data.wells)}")
            print(f"  - Time points: {len(self.biorad_data.time_points)}")
            print(f"  - Time range: {self.biorad_data.time_points[0]:.1f} - {self.biorad_data.time_points[-1]:.1f} minutes")
            
            # Show sample well data
            sample_well_id = self.biorad_data.wells[0]
            sample_measurements = self.biorad_data.measurements[0]
            print(f"\nSample well ({sample_well_id}):")
            print(f"  - Measurements: {len(sample_measurements)} values")
            print(f"  - First 5 values: {sample_measurements[:5]}")
            print(f"  - Last 5 values: {sample_measurements[-5:]}")
            
            if not self.ask_user_validation("Does the BioRad data structure look correct?"):
                print("❌ BioRad data parsing verification failed!")
                return False
                
        except Exception as e:
            print(f"❌ Error parsing BioRad data: {e}")
            return False
            
        print("✅ File processing verification completed successfully!")
        return True
        
    def verify_curve_fitting(self):
        """Verify curve fitting algorithms with visual plots."""
        self.print_header("CURVE FITTING VERIFICATION")
        
        if self.bmg_data is None:
            print("❌ BMG data not loaded. Run file processing verification first.")
            return False
            
        self.print_section("BMG Data Curve Fitting")
        
        # Select a few representative wells for detailed analysis
        wells_to_analyze = []
        for i, well_id in enumerate(self.bmg_data.wells):
            if len(self.bmg_data.measurements[i]) > 10:  # Ensure sufficient data
                wells_to_analyze.append((i, well_id))
                if len(wells_to_analyze) >= 6:  # Analyze 6 wells
                    break
                    
        well_ids = [well_id for _, well_id in wells_to_analyze]
        print(f"Analyzing curve fitting for wells: {well_ids}")
        
        # Create plots for curve fitting verification
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()
        
        fit_results = {}
        
        for plot_idx, (well_idx, well_id) in enumerate(wells_to_analyze):
            measurements = self.bmg_data.measurements[well_idx]
            
            # Perform curve fitting
            try:
                result = self.curve_fitter.fit_curve(
                    time_points=self.bmg_data.time_points,
                    measurements=measurements
                )
                
                fit_results[well_id] = result
                
                # Plot raw data and fitted curve
                ax = axes[plot_idx]
                ax.scatter(self.bmg_data.time_points, measurements,
                          alpha=0.7, s=20, label='Raw data')
                
                if result.success:
                    # Generate fitted curve
                    fitted_values = [
                        self.curve_fitter.sigmoid_5param(t, *result.parameters)
                        for t in self.bmg_data.time_points
                    ]
                    ax.plot(self.bmg_data.time_points, fitted_values,
                           'r-', linewidth=2, label=f'Fitted (R²={result.r_squared:.3f})')
                    
                    ax.set_title(f'Well {well_id}\nR²={result.r_squared:.3f}, RMSE={result.rmse:.1f}')
                else:
                    ax.set_title(f'Well {well_id}\nFit Failed: {result.error_message}')
                    
                ax.set_xlabel('Time (minutes)')
                ax.set_ylabel('Fluorescence')
                ax.legend()
                ax.grid(True, alpha=0.3)
                
            except Exception as e:
                print(f"❌ Error fitting well {well_id}: {e}")
                ax = axes[plot_idx]
                ax.text(0.5, 0.5, f'Error: {str(e)[:50]}...',
                       transform=ax.transAxes, ha='center', va='center')
                ax.set_title(f'Well {well_id} - Error')
                
        plt.tight_layout()
        plt.savefig(self.verification_output / 'bmg_curve_fitting_verification.png', 
                   dpi=150, bbox_inches='tight')
        plt.show()
        
        # Display fitting statistics
        successful_fits = [r for r in fit_results.values() if r.success]
        failed_fits = [r for r in fit_results.values() if not r.success]
        
        print(f"\nCurve Fitting Results:")
        print(f"  - Successful fits: {len(successful_fits)}/{len(fit_results)}")
        print(f"  - Failed fits: {len(failed_fits)}")
        
        if successful_fits:
            r_squared_values = [r.r_squared for r in successful_fits]
            rmse_values = [r.rmse for r in successful_fits]
            
            print(f"  - R² range: {min(r_squared_values):.3f} - {max(r_squared_values):.3f}")
            print(f"  - R² mean: {np.mean(r_squared_values):.3f}")
            print(f"  - RMSE range: {min(rmse_values):.1f} - {max(rmse_values):.1f}")
            print(f"  - RMSE mean: {np.mean(rmse_values):.1f}")
            
        if not self.ask_user_validation("Do the curve fits look reasonable? Are R² values good (>0.9)?"):
            print("❌ Curve fitting verification failed!")
            return False
            
        print("✅ Curve fitting verification completed successfully!")
        return True
        
    def verify_threshold_detection(self):
        """Verify threshold detection algorithms."""
        self.print_header("THRESHOLD DETECTION VERIFICATION")
        
        if self.bmg_data is None:
            print("❌ BMG data not loaded. Run file processing verification first.")
            return False
            
        self.print_section("Threshold Detection Analysis")
        
        # Select wells for threshold analysis
        wells_to_analyze = []
        for well_id, well in self.bmg_data.wells.items():
            if len(well.measurements) > 10:
                wells_to_analyze.append(well_id)
                if len(wells_to_analyze) >= 6:
                    break
                    
        print(f"Analyzing threshold detection for wells: {wells_to_analyze}")
        
        # Create plots for threshold detection verification
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()
        
        threshold_results = {}
        
        for i, well_id in enumerate(wells_to_analyze):
            well = self.bmg_data.wells[well_id]
            
            try:
                # Perform threshold detection
                result = self.threshold_analyzer.detect_threshold_crossing(
                    time_points=self.bmg_data.time_points,
                    measurements=well.measurements,
                    method='baseline_std'
                )
                
                threshold_results[well_id] = result
                
                # Plot data with threshold line
                ax = axes[i]
                ax.plot(self.bmg_data.time_points, well.measurements, 
                       'b-', linewidth=1, label='Fluorescence')
                
                if result.success:
                    # Draw threshold line
                    ax.axhline(y=result.threshold_value, color='r', linestyle='--', 
                              label=f'Threshold: {result.threshold_value:.1f}')
                    
                    # Mark crossing point
                    if result.crossing_time is not None:
                        ax.axvline(x=result.crossing_time, color='g', linestyle=':', 
                                  label=f'Crossing: {result.crossing_time:.1f} min')
                        ax.plot(result.crossing_time, result.threshold_value, 
                               'ro', markersize=8, label='Crossing point')
                    
                    ax.set_title(f'Well {well_id}\nCrossing: {result.crossing_time:.1f} min')
                else:
                    ax.set_title(f'Well {well_id}\nNo crossing detected')
                    
                ax.set_xlabel('Time (minutes)')
                ax.set_ylabel('Fluorescence')
                ax.legend()
                ax.grid(True, alpha=0.3)
                
            except Exception as e:
                print(f"❌ Error in threshold detection for well {well_id}: {e}")
                ax = axes[i]
                ax.text(0.5, 0.5, f'Error: {str(e)[:50]}...', 
                       transform=ax.transAxes, ha='center', va='center')
                ax.set_title(f'Well {well_id} - Error')
                
        plt.tight_layout()
        plt.savefig(self.verification_output / 'bmg_threshold_detection_verification.png', 
                   dpi=150, bbox_inches='tight')
        plt.show()
        
        # Display threshold detection statistics
        successful_detections = [r for r in threshold_results.values() if r.success]
        failed_detections = [r for r in threshold_results.values() if not r.success]
        
        print(f"\nThreshold Detection Results:")
        print(f"  - Successful detections: {len(successful_detections)}/{len(threshold_results)}")
        print(f"  - Failed detections: {len(failed_detections)}")
        
        if successful_detections:
            crossing_times = [r.crossing_time for r in successful_detections if r.crossing_time is not None]
            threshold_values = [r.threshold_value for r in successful_detections]
            
            if crossing_times:
                print(f"  - Crossing time range: {min(crossing_times):.1f} - {max(crossing_times):.1f} minutes")
                print(f"  - Crossing time mean: {np.mean(crossing_times):.1f} minutes")
            
            print(f"  - Threshold value range: {min(threshold_values):.1f} - {max(threshold_values):.1f}")
            print(f"  - Threshold value mean: {np.mean(threshold_values):.1f}")
            
        if not self.ask_user_validation("Do the threshold detections look biologically reasonable?"):
            print("❌ Threshold detection verification failed!")
            return False
            
        print("✅ Threshold detection verification completed successfully!")
        return True
        
    def verify_statistical_analysis(self):
        """Verify statistical analysis algorithms."""
        self.print_header("STATISTICAL ANALYSIS VERIFICATION")
        
        if self.bmg_data is None or self.bmg_layout is None:
            print("❌ BMG data or layout not loaded. Run file processing verification first.")
            return False
            
        self.print_section("Statistical Analysis")
        
        # Group wells by layout metadata
        grouped_wells = self.statistical_analyzer.group_wells_by_layout(
            fluorescence_data=self.bmg_data,
            layout_data=self.bmg_layout,
            group_by='Type'
        )
        
        print(f"Wells grouped by Type:")
        for group_name, wells in grouped_wells.items():
            print(f"  - {group_name}: {len(wells)} wells")
            
        # Calculate statistics for each group
        group_stats = {}
        for group_name, wells in grouped_wells.items():
            if len(wells) > 0:
                # Get final fluorescence values for each well
                final_values = []
                for well in wells:
                    if len(well.measurements) > 0:
                        final_values.append(well.measurements[-1])
                        
                if final_values:
                    stats = self.statistical_analyzer.calculate_descriptive_statistics(final_values)
                    group_stats[group_name] = stats
                    
                    print(f"\n{group_name} group statistics (final fluorescence values):")
                    print(f"  - Count: {stats['count']}")
                    print(f"  - Mean: {stats['mean']:.1f}")
                    print(f"  - Std: {stats['std']:.1f}")
                    print(f"  - Min: {stats['min']:.1f}")
                    print(f"  - Max: {stats['max']:.1f}")
                    print(f"  - Median: {stats['median']:.1f}")
                    
        # Create visualization of group statistics
        if len(group_stats) > 1:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # Box plot of final values by group
            group_names = list(group_stats.keys())
            group_values = []
            
            for group_name in group_names:
                wells = grouped_wells[group_name]
                values = [well.measurements[-1] for well in wells if len(well.measurements) > 0]
                group_values.append(values)
                
            ax1.boxplot(group_values, labels=group_names)
            ax1.set_title('Final Fluorescence Values by Group')
            ax1.set_ylabel('Fluorescence')
            ax1.grid(True, alpha=0.3)
            
            # Bar plot of means with error bars
            means = [group_stats[name]['mean'] for name in group_names]
            stds = [group_stats[name]['std'] for name in group_names]
            
            ax2.bar(group_names, means, yerr=stds, capsize=5, alpha=0.7)
            ax2.set_title('Mean Final Fluorescence by Group')
            ax2.set_ylabel('Fluorescence')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(self.verification_output / 'bmg_statistical_analysis_verification.png', 
                       dpi=150, bbox_inches='tight')
            plt.show()
            
        if not self.ask_user_validation("Do the statistical groupings and calculations look correct?"):
            print("❌ Statistical analysis verification failed!")
            return False
            
        print("✅ Statistical analysis verification completed successfully!")
        return True
        
    def compare_with_existing_outputs(self):
        """Compare results with existing tool outputs."""
        self.print_header("COMPARISON WITH EXISTING OUTPUTS")
        
        print("Comparing with existing curve fitting outputs...")
        
        # Read existing summary
        summary_file = self.output_dir / "curve_fitting_analysis_summary.txt"
        if summary_file.exists():
            print(f"\nExisting analysis summary from: {summary_file}")
            with open(summary_file, 'r') as f:
                content = f.read()
                print(content[:1000] + "..." if len(content) > 1000 else content)
                
            if not self.ask_user_validation("Does our analysis match the existing results?"):
                print("❌ Comparison with existing outputs failed!")
                return False
        else:
            print("⚠️  No existing summary file found for comparison")
            
        print("✅ Comparison with existing outputs completed!")
        return True
        
    def run_verification_session(self):
        """Run the complete interactive verification session."""
        self.print_header("FLUORESCENCE ANALYSIS TOOL - INTERACTIVE VERIFICATION")
        
        print("This interactive session will verify that the fluorescence analysis")
        print("algorithms are working correctly with real data.")
        print("\nVerification steps:")
        print("1. File Processing Verification")
        print("2. Curve Fitting Verification")
        print("3. Threshold Detection Verification")
        print("4. Statistical Analysis Verification")
        print("5. Comparison with Existing Outputs")
        
        self.wait_for_user("Press Enter to start verification...")
        
        # Run verification steps
        steps = [
            ("File Processing", self.verify_file_processing),
            ("Curve Fitting", self.verify_curve_fitting),
            ("Threshold Detection", self.verify_threshold_detection),
            ("Statistical Analysis", self.verify_statistical_analysis),
            ("Comparison with Existing Outputs", self.compare_with_existing_outputs),
        ]
        
        results = {}
        
        for step_name, step_func in steps:
            try:
                print(f"\n{'='*20} Starting {step_name} {'='*20}")
                results[step_name] = step_func()
                
                if results[step_name]:
                    print(f"✅ {step_name} completed successfully!")
                else:
                    print(f"❌ {step_name} failed!")
                    if not self.ask_user_validation(f"Continue with remaining steps despite {step_name} failure?"):
                        break
                        
            except Exception as e:
                print(f"❌ Error in {step_name}: {e}")
                results[step_name] = False
                if not self.ask_user_validation(f"Continue despite error in {step_name}?"):
                    break
                    
        # Final summary
        self.print_header("VERIFICATION SUMMARY")
        
        total_steps = len(results)
        successful_steps = sum(1 for success in results.values() if success)
        
        print(f"Verification Results: {successful_steps}/{total_steps} steps successful")
        print()
        
        for step_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {step_name}: {status}")
            
        if successful_steps == total_steps:
            print(f"\n🎉 ALL VERIFICATION STEPS PASSED!")
            print("The fluorescence analysis algorithms are working correctly.")
        else:
            print(f"\n⚠️  {total_steps - successful_steps} verification steps failed.")
            print("Please review the failed steps and fix any issues before proceeding.")
            
        print(f"\nVerification outputs saved to: {self.verification_output}")
        
        return successful_steps == total_steps


def main():
    """Main entry point for interactive verification."""
    verifier = InteractiveVerifier()
    success = verifier.run_verification_session()
    
    if success:
        print("\n✅ Verification completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Verification completed with failures!")
        sys.exit(1)


if __name__ == "__main__":
    main()