import os
import pandas as pd
import re
from config import CACHE_FILTERED,OUTPUT_DIR


def csv_to_parquet_auto(input_csv_path: str) -> str:
    """
    Convert a CSV file to Parquet.
    Output filename is auto-generated based on the date range in the input filename.
    Returns the full output Parquet path.
    """

    # Extract filename only
    filename = os.path.basename(input_csv_path)

    # Extract date range: YYYY-MM-DD_to_YYYY-MM-DD
    match = re.search(r"(\d{4}-\d{2}-\d{2})_to_(\d{4}-\d{2}-\d{2})", filename)
    if not match:
        raise ValueError("Could not extract date range from filename.")

    start_date, end_date = match.groups()

    # Build output folder and filename
    output_folder = os.path.join(CACHE_FILTERED, "parquet")
    os.makedirs(output_folder, exist_ok=True)

    output_filename = f"{start_date}_to_{end_date}_23-59-59.parquet"
    output_path = os.path.join(output_folder, output_filename)

    # Convert CSV → Parquet
    df = pd.read_csv(input_csv_path)
    df.to_parquet(output_path, index=False)

    return output_path

# def parquet_to_csv_auto(input_parquet_path: str) -> str:
#     """
#     Convert a Parquet file to CSV.
#     Output filename is auto-generated based on the date range in the input filename.
#     Returns the full output CSV path.
#     """

#     # Extract filename only
#     filename = os.path.basename(input_parquet_path)

#     # Extract date range: YYYY-MM-DD_to_YYYY-MM-DD
#     match = re.search(r"(\d{4}-\d{2}-\d{2})_to_(\d{4}-\d{2}-\d{2})", filename)
#     if not match:
#         raise ValueError("Could not extract date range from filename.")

#     start_date, end_date = match.groups()

#     # Build output folder inside CACHE_FILTERED
    
    

#     # Build output filename
#     output_filename = f"London_Crime_combined_df_{start_date}_to_{end_date}.csv"
#     output_path = os.path.join(OUTPUT_DIR, output_filename)
#     os.makedirs(output_path, exist_ok=True)
#     # Convert Parquet → CSV
#     #df = pd.read_parquet(input_parquet_path)
#     #df.to_csv(output_path, index=False,encoding="utf-8-sig")

#     return output_path


#-------ONLY TAKES A DF
def parquet_df_to_csv_auto(df, start, end):


    """
    Takes a filtered parquet DataFrame and saves it as a CSV.
    Output filename is auto-generated based on the min/max date in the DataFrame.
    Returns the full output CSV path.
    """
    
    def safe_save(base_path):
        """
        Returns a unique file path by appending (1), (2), ... if needed.
        """
        if not os.path.exists(base_path):
            return base_path

        root, ext = os.path.splitext(base_path)
        counter = 1

        while True:
            new_path = f"{root} ({counter}){ext}"
            if not os.path.exists(new_path):
                return new_path
            counter += 1

    # Detect the date column
    date_col = None
    for col in df.columns:
        if col.lower() in ("date", "v2date", "v1date"):
            date_col = col
            break

    if date_col is None:
        raise ValueError("No date column found in DataFrame.")

    # Convert to datetime if needed
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    valid_mask = df["headline_is_duplicate"].astype(str).isin(["True", "False", "TRUE", "FALSE"])
    df = df[valid_mask].copy()


    # Build output folder
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Build filename

    output_filename = f"London_Crime_combined_df_{start}_to_{end}.csv"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    output_path = safe_save(output_path)
    # Save CSV
    df.to_csv(output_path, index=False,encoding="utf-8-sig")


    return output_path

def safe_save(base_path):
        """
        Returns a unique file path by appending (1), (2), ... if needed.
        """
        if not os.path.exists(base_path):
            return base_path

        root, ext = os.path.splitext(base_path)
        counter = 1

        while True:
            new_path = f"{root} ({counter}){ext}"
            if not os.path.exists(new_path):
                return new_path
            counter += 1
    



