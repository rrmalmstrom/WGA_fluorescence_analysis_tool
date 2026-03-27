import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

# Define the 5 parameter logistic function with overflow protection
def sigmoid_5param(x, a, b, c, d, e):
    try:
        # Limit b to prevent overflow in exp
        b = max(min(b, 10), -10)
        # Calculate exponent with overflow protection
        exp_val = np.exp(-b * (x - c))
        # Handle division by zero or very small numbers
        denom = 1 + exp_val
        result = a / denom + d + e * x
        # Check for NaN or inf values
        if not np.all(np.isfinite(result)):
            raise ValueError("Overflow detected in sigmoid calculation")
        return result
    except Exception as e:
        print(f"Error in sigmoid calculation: {e}")
        return np.full_like(x, np.nan)

# Function to calculate fit error (sum of squared residuals)
def calculate_fit_error(time_points, fluo_values, params):
    fitted_values = sigmoid_5param(time_points, *params)
    residuals = fluo_values - fitted_values
    return np.sum(residuals**2)

def calculate_threshold(fluo_values):
    """Calculate threshold as 20% greater than average of time points 2-4"""
    avg = np.mean(fluo_values[1:4])
    return avg * 1.10

def fit_curve_and_find_crossing(time_points, fluo_values, threshold):
    """Fit sigmoidal curve and find when it crosses the threshold using adaptive fitting"""
    try:
        # Check if there's enough variation in the data to fit a curve
        if np.max(fluo_values) - np.min(fluo_values) < 0.1:
            return None

        # Define fit attempts with different parameters
        fit_attempts = [
            {
                "name": "Standard fit",
                "initial_guess": [
                    np.max(fluo_values) - np.min(fluo_values),  # a: range of values
                    1.0,  # b: growth rate
                    time_points[np.argmax(fluo_values)],  # c: midpoint
                    np.min(fluo_values),  # d: baseline
                    0.0  # e: linear component
                ],
                "bounds": ([0, 0, min(time_points), min(fluo_values), -np.inf],
                          [np.inf, np.inf, max(time_points), max(fluo_values), np.inf])
            },
            {
                "name": "Steep curve fit",
                "initial_guess": [
                    np.max(fluo_values) - np.min(fluo_values),
                    -1.0,  # Try negative growth rate for steeper curve
                    time_points[np.argmax(fluo_values)],
                    np.min(fluo_values),
                    0.0
                ],
                "bounds": ([0, -10, min(time_points), min(fluo_values), -np.inf],
                          [np.inf, 10, max(time_points), max(fluo_values), np.inf])
            },
            {
                "name": "Wide range fit",
                "initial_guess": [
                    np.max(fluo_values) - np.min(fluo_values),
                    0.5,  # Different initial growth rate
                    time_points[len(time_points)//2],  # Midpoint estimate
                    np.min(fluo_values),
                    0.0
                ],
                "bounds": ([0, -5, min(time_points), min(fluo_values), -np.inf],
                          [np.inf, 5, max(time_points), max(fluo_values), np.inf])
            }
        ]

        # Set a timeout for curve fitting
        import signal

        class TimeoutException(Exception): pass

        def handler(signum, frame):
            raise TimeoutException("Curve fitting timed out")

        best_fit = None
        best_error = float('inf')

        # Try each fit attempt
        for attempt in fit_attempts:
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(2)  # Set 2 second timeout

            try:
                popt, pcov = curve_fit(
                    sigmoid_5param, time_points, fluo_values,
                    p0=attempt["initial_guess"], maxfev=5000,
                    bounds=attempt["bounds"]
                )
                signal.alarm(0)  # Cancel alarm

                # Check if covariance could be estimated
                if pcov is None or not np.all(np.isfinite(pcov)):
                    print(f"Warning: {attempt['name']} - Covariance could not be estimated")
                    continue

                # Check if parameters are reasonable
                if not np.all(np.isfinite(popt)) or any(p == 0 for p in popt[:4]):
                    print(f"Warning: {attempt['name']} - Unreasonable parameters")
                    continue

                # Calculate fit error
                error = calculate_fit_error(time_points, fluo_values, popt)

                # Update best fit if this one has lower error
                if error < best_error:
                    best_error = error
                    best_fit = (popt, error)

            except TimeoutException:
                print(f"Warning: {attempt['name']} - Curve fitting timed out")
            except Exception as e:
                print(f"Warning: {attempt['name']} - Error fitting curve: {e}")

        # If no good fit was found, return None
        if best_fit is None:
            return None

        popt, error = best_fit

        # Find where the fitted curve crosses the threshold
        fitted_values = sigmoid_5param(time_points, *popt)

        # Check if fitted values are valid
        if not np.all(np.isfinite(fitted_values)):
            print("Warning: Fitted values contain NaN or inf")
            return None, None

        # Interpolate to find exact crossing time
        crossing_time = None
        for i in range(1, len(fitted_values)):
            if fitted_values[i] > threshold and fitted_values[i-1] <= threshold:
                t1, y1 = time_points[i-1], fitted_values[i-1]
                t2, y2 = time_points[i], fitted_values[i]
                crossing_time = t1 + (threshold - y1) * (t2 - t1) / (y2 - y1)
                break

        return crossing_time, popt

    except Exception as e:
        print(f"Error fitting curve: {e}")
        return None

def process_fluorescence_data(input_file, output_file):
    # Load data
    df = pd.read_csv(input_file)

    # Add column for crossing times
    df['Crossing_Time'] = np.nan

    # Process each row (well)
    for idx, row in df.iterrows():
        # Skip rows where Type is 'empty'
        if row['Type'] == 'empty':
            continue

        # Extract time points and fluorescence values
        time_points = np.arange(8, len(row))  # Columns 9 onwards are time points
        fluo_values = row[8:].values

        # Convert to float and handle NaN/inf values
        try:
            fluo_values = fluo_values.astype(float)
            # Replace NaN or inf values with interpolation or nearest valid value
            fluo_values = pd.Series(fluo_values).interpolate().ffill().bfill().values

            # Check if all values are valid after cleaning
            if not np.all(np.isfinite(fluo_values)):
                print(f"Skipping row {idx} due to invalid fluorescence values")
                continue
        except (ValueError, TypeError) as e:
            print(f"Skipping row {idx} due to error: {e}")
            continue

        # Calculate threshold
        threshold = calculate_threshold(fluo_values)

        # Fit curve and find crossing time
        crossing_time, popt = fit_curve_and_find_crossing(
            time_points, fluo_values, threshold)

        # Visualize the fit with the best parameters
        visualize_fit(
            time_points, fluo_values,
            popt,
            threshold, crossing_time,
            row['Well']
        )

        # Store result
        df.at[idx, 'Crossing_Time'] = crossing_time

    # Save results
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")

def visualize_fit(time_points, fluo_values, popt, threshold, crossing_time, well_id, output_dir="visualizations"):
    """Create a plot of the raw data and fitted curve"""
    import os

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Create plot
    plt.figure(figsize=(10, 6))

    # Plot raw fluorescence data
    plt.plot(time_points, fluo_values, 'bo-', label='Raw Data')

    # Plot fitted curve if parameters exist
    if popt is not None:
        fitted_values = sigmoid_5param(time_points, *popt)
        plt.plot(time_points, fitted_values, 'r-', label='Fitted Curve')

        # Mark crossing time if found
        if crossing_time is not None:
            plt.axvline(x=crossing_time, color='g', linestyle='--',
                       label=f'Crossing Time: {crossing_time:.2f}')
            plt.scatter(crossing_time, threshold, color='green', zorder=5)

    # Mark threshold
    plt.axhline(y=threshold, color='orange', linestyle='--',
               label=f'Threshold: {threshold:.2f}')

    # Add labels and title
    plt.xlabel('Time')
    plt.ylabel('Fluorescence')
    plt.title(f'Well {well_id}')
    plt.legend()
    plt.grid(True)

    # Save plot
    plot_file = os.path.join(output_dir, f'well_{well_id}.png')
    plt.savefig(plot_file)
    plt.close()

    print(f"Saved plot for well {well_id} to {plot_file}")


if __name__ == "__main__":
    input_file = "merged_fluorescence_data.csv"
    output_file = "analyzed_fluorescence_data.csv"
    process_fluorescence_data(input_file, output_file)