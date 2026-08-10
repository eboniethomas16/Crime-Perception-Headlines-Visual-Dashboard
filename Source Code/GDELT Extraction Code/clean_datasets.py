# USED IN DISSERTATION TO EXPLODE CRIME_TYPES COLUMN INTO INDIVIDUAL CRIME TYPE
import os
import pandas as pd
import re


# -------------------------------
# Helper: create _CLEANED filename
# -------------------------------
def make_cleaned_filename(path):
    base, ext = os.path.splitext(path)
    return f"{base}_CLEANED{ext}"


def normalize_commas(s):
    if not isinstance(s, str):
        return s
    return (
        s.replace("，", ",")
         .replace("﹐", ",")
         .replace("､", ",")
         .replace("‚", ",")
         .replace("ˏ", ",")
         .replace("\u00A0", " ")
    )


# Explode function for crime_types column
def explode_crime_types(df):
    if 'crime_types' not in df.columns:
        print("No 'crime_types' column found — skipping explode step.")
        return df
    df = df.copy()
    ct = df['crime_types'].fillna('').astype(str)
    # Remove surrounding quotes
    ct = ct.str.replace(r'^"|"$', '', regex=True)
    # Replace unicode comma variants with ASCII comma
    ct = ct.str.replace(r'[，﹐﹑､]', ',', regex=True)
    # Remove duplicate commas
    ct = ct.str.replace(r',+', ',', regex=True)
    # Remove apostrophes / curly quotes
    ct = ct.str.replace(r"[’‘‛ʻʽ`´']", "", regex=True)
    df['crime_types'] = ct
    # Split into list
    df['crime_type'] = df['crime_types'].str.split(r'\s*,\s*')
    # Explode the list
    df = df.explode('crime_type')
    #print(df[['crime_types', 'crime_type']].iloc[158:190])
    print(f"# ofExploded crime types: {len(df)} rows")
    return df


# Cleaning function for a single file
def clean_file(input_csv_path):

    print(f"\nLoading CSV:\n{input_csv_path}")
    df = pd.read_csv(input_csv_path, encoding="utf-8-sig",low_memory=False)
    
    # Step 1 — Optional: truncate to 24 columns
    if df.shape[1] > 24:
        df = df.iloc[:, :24]
    
    numeric_cols = [
    "tone", "daily_avg_tone", "london_mentions",
    "crime_mentions", "crime_keyword_count"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Step 2 — Save as Parquet
    parquet_path = input_csv_path.replace(".csv", ".parquet")
    print(f"Saving as Parquet:\n{parquet_path}")
    df.to_parquet(parquet_path, index=False)

    # Step 2 — Reload from Parquet
    print("Reloading from Parquet...")
    df = pd.read_parquet(parquet_path)

    df = explode_crime_types(df)

    # Step 5 — Reorder columns
    cols = list(df.columns)
    if 'crime_types' in cols and 'crime_type' in cols:
        cols.remove('crime_type')
        idx = cols.index('crime_types') + 1
        cols.insert(idx, 'crime_type')
        df = df[cols]

    # Step 6 — Save final cleaned CSV into the CLEANED Combined Datasets folder
    FINAL_OUTPUT_FOLDER = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\GDELT_pipeline\data\combined_datasets\Updated Monthly Filtered Datasets\CLEANED Combined Datasets"
    os.makedirs(FINAL_OUTPUT_FOLDER, exist_ok=True)

    # Build output filename inside the CLEANED folder
    output_csv = os.path.join(
        FINAL_OUTPUT_FOLDER,
        os.path.basename(make_cleaned_filename(input_csv_path))
    )

    print(f"Saving final cleaned CSV:\n{output_csv}")
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")

    print("Finished")


# -------------------------------
# Run through every CSV in folder
# -------------------------------
FOLDER = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\GDELT_pipeline\data\combined_datasets\Updated Monthly Filtered Datasets"

for filename in os.listdir(FOLDER):
    if filename.lower().endswith(".csv"):
        full_path = os.path.join(FOLDER, filename)
        clean_file(full_path)
