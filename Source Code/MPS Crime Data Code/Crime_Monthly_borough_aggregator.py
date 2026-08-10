# USED IN DISSERTATION TO AGGREGATE MOPAC CRIME DATA INTO MONTHLY OFFENCES BY BOROUGH
import pandas as pd
from pathlib import Path

# --- Input and output paths ---
input_path = Path(
    r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\MOPAC Data Cleaner\MOPAC Monthly Crime Data\MPS_Crime_Data.csv"
)

output_path = Path(
    r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\MOPAC Data Cleaner\MOPAC Monthly Crime Data\All_MOPAC_CrimeData_Aggregated_ByBorough.csv"
)

# 1. Load dataset
df = pd.read_csv(input_path, low_memory=False)

# 2. Clean whitespace on date column
df["date"] = df["date"].astype(str).str.strip()

# 3. Parse m/d/y, but allow failures
df["date"] = pd.to_datetime(df["date"], format="%m/%d/%Y", errors="coerce")

# 4. Report any unparsed dates
bad_dates = df[df["date"].isna()]["date"]
if len(bad_dates) > 0:
    print("Unparsed dates found:")
    print(bad_dates.unique())

# 5. Drop rows with invalid dates
df = df.dropna(subset=["date"])

# 6. Create month bucket (truncate to first of month)
df["date"] = df["date"].dt.to_period("M").dt.to_timestamp()

# 7. Filter to CURRENT DATA + OFFENCES
df_filtered = df[
    (df["category_status"].astype(str).str.strip().str.lower() == "current data") &
    (df["measure"].astype(str).str.strip().str.lower() == "offences")
].copy()

# 7a. Ensure we have an 'area_name' column; if not, fall back to 'borough' if present
if "area_name" not in df_filtered.columns:
    if "borough" in df_filtered.columns:
        df_filtered["area_name"] = df_filtered["borough"]
    else:
        raise KeyError("Neither 'area_name' nor 'borough' column found in the input CSV.")

# 7b. Clean whitespace in area_name
df_filtered["area_name"] = df_filtered["area_name"].astype(str).str.strip()

# 8. Aggregate to Month × area_name (which will be renamed to borough)
agg = (
    df_filtered
    .groupby(["date", "area_name"], as_index=False)
    .agg({"count": "sum"})
)

# 9. Rename columns: area_name -> borough, count -> Count (Monthly Offences)
agg = agg.rename(columns={
    "area_name": "borough",
    "count": "crime_count"
})

# 10. Save
agg.to_csv(output_path, index=False, encoding="utf-8")

print("Aggregation complete.")
print(f"Rows in aggregated dataset: {len(agg)}")
print(f"Saved to: {output_path}")

print("\nSample months:")
print(agg['date'].drop_duplicates().sort_values().head(24))
