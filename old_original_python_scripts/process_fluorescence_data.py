import pandas as pd

def read_metadata(file_path):
    """Read the metadata CSV file and return a DataFrame."""
    df = pd.read_csv(file_path)
    # Rename columns to match fluorescence DataFrame
    df.rename(columns={
        'Well Row': 'Well_Row',
        'Well Col': 'Well_Col',
        'Well': 'Well'
    }, inplace=True)
    return df

def read_fluorescence_data(file_path):
    """Read the fluorescence data file with special format and return a DataFrame."""
    # Read the file with custom header rows
    df = pd.read_csv(file_path, header=7)  # Use row 7 for headers, data starts at row 8

    # Rename the first three columns
    df.columns.values[0:3] = ["Well_Row", "Well_Col", "Well"]

    # Convert time-based column headers (from column 4 onwards) to decimal hours
    new_columns = list(df.columns)
    for i in range(3, len(new_columns)):
        col_name = new_columns[i]
        if isinstance(col_name, str) and 'h' in col_name:
            # Handle format with hours only (e.g., "7 h")
            if 'min' not in col_name:
                hours = int(col_name.split()[0])
                new_columns[i] = str(hours)
            # Handle format with hours and minutes (e.g., "7 h 30 min")
            elif 'min' in col_name:
                parts = col_name.split()
                if len(parts) >= 3:
                    hours = int(parts[0])
                    minutes = int(parts[2])
                    # Convert to decimal hours
                    decimal_hours = hours + minutes / 60
                    new_columns[i] = str(decimal_hours)

    df.columns = new_columns

    return df

def merge_dataframes(metadata_df, fluorescence_df):
    """Merge the metadata and fluorescence DataFrames."""
    # Check if required columns exist in both DataFrames
    required_cols = ['Well_Row', 'Well_Col']
    for df, name in [(metadata_df, 'Metadata'), (fluorescence_df, 'Fluorescence')]:
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"{name} DataFrame is missing required columns: {missing_cols}")

    # Reset index for both DataFrames to use them as columns for merging
    metadata_df_reset = metadata_df.reset_index()
    fluorescence_df_reset = fluorescence_df.reset_index()

    # Merge on Well_Row and Well_Col
    merged_df = pd.merge(
        metadata_df_reset,
        fluorescence_df_reset,
        left_on=['Well_Row', 'Well_Col'],
        right_on=['Well_Row', 'Well_Col'],
        how='inner'
    )

    # Remove columns with "_y" suffix
    cols_to_drop = [col for col in merged_df.columns if col.endswith('_y')]
    merged_df.drop(columns=cols_to_drop, inplace=True)

    merged_df.rename(columns={'Well_x': 'Well'}, inplace=True)

    # Reset index to match index_x and remove index_x
    if 'index_x' in merged_df.columns:
        merged_df.set_index('index_x', inplace=True)
        merged_df.index.name = None  # Remove index name

    return merged_df

def save_merged_dataframe(df, output_path):
    """Save the merged DataFrame to a CSV file."""
    df.to_csv(output_path, index=False)

def main():
    # File paths
    metadata_path = 'RM5097_layout.csv'
    fluorescence_path = 'RM5097.96HL.BNCT.1.CSV'
    output_path = 'merged_fluorescence_data.csv'

    # Read data
    metadata_df = read_metadata(metadata_path)
    fluorescence_df = read_fluorescence_data(fluorescence_path)

    # Merge data
    merged_df = merge_dataframes(metadata_df, fluorescence_df)

    # Save result
    save_merged_dataframe(merged_df, output_path)
    print(f"Merged data saved to {output_path}")

if __name__ == "__main__":
    main()