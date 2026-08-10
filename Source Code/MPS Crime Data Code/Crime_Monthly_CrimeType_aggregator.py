# USED IN DISSERTATION TO AGGREGATE MOPAC CRIME DATA INTO MONTHLY OFFENCES BY CRIME TYPE
import pandas as pd
from pathlib import Path

# --- Input and output paths ---
# input_path = Path(
#     r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\MOPAC Data Cleaner\MOPAC Monthly Crime Data\All_MOPAC_HistoricalCrimeData.csv"
# )   
input_path = Path(
    r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\MOPAC Data Cleaner\MOPAC Monthly Crime Data\MPS_Crime_Data.csv"
)  
output_path = Path(
    r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\MOPAC Data Cleaner\MOPAC Monthly Crime Data\All_MOPAC_CrimeData_Aggregated.csv"
)

# 1. Load dataset
df = pd.read_csv(input_path, low_memory=False)

# 2. Clean whitespace
df["date"] = df["date"].astype(str).str.strip()

# 3. Parse m/d/y, but allow failures
df["date"] = pd.to_datetime(df["date"], format="%m/%d/%Y", errors="coerce")

# 4. Report any unparsed dates
bad_dates = df[df["date"].isna()]["date"]
if len(bad_dates) > 0:
    print(bad_dates.unique())

# 5. Drop rows with invalid dates
df = df.dropna(subset=["date"])

# 6. Create month bucket
df["date"] = df["date"].dt.to_period("M").dt.to_timestamp()

# 7. Filter to CURRENT DATA + OFFENCES
df_filtered = df[
    (df["category_status"].str.strip().str.lower() == "current data".lower()) &
    (df["measure"].str.strip().str.lower() == "offences")
]
# 8. Aggregate to Month × Crime Type
agg = (
    df_filtered
    .groupby(["date", "crime_type"], as_index=False)
    .agg({"count": "sum"})
)

# 9. Rename column
agg = agg.rename(columns={"count": "Count (Monthly Offences)"})

# 10. Save
agg.to_csv(output_path, index=False)

print("Aggregation complete.")
print(f"Rows in aggregated dataset: {len(agg)}")
print(f"Saved to: {output_path}")

print("\nSample months:")
print(agg['date'].drop_duplicates().sort_values().head(24))
