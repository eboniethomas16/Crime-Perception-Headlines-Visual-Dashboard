import pandas as pd
import os

# ---------------------------------------------------------
# 1. Input + Output Paths
# ---------------------------------------------------------
input_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\MOPAC Data Cleaner\MOPAC Monthly Crime Data\All_MOPAC_HistoricalCrimeData.csv"
output_folder = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Visual Python Code\Small Multiples - Crime"

monthly_out = os.path.join(output_folder, "crime_monthly_aggregated.csv")
quarterly_out = os.path.join(output_folder, "crime_quarterly_aggregated.csv")

# ---------------------------------------------------------
# 2. Load Data
# ---------------------------------------------------------
df = pd.read_csv(input_path, low_memory=False)

# ---------------------------------------------------------
# 3. Filter for offences + Current Data
# ---------------------------------------------------------
df = df[
    (df["measure"] == "offences") &
    (df["category_status"] == "Current Data")
].copy()

# ---------------------------------------------------------
# 4. Parse date (MM/DD/YYYY)
# ---------------------------------------------------------
df["date"] = pd.to_datetime(df["date"], format="%m/%d/%Y", errors="coerce")

# ---------------------------------------------------------
# 5. Fiscal Quarter Label Function
# ---------------------------------------------------------
def get_fiscal_quarter_label(dt):
    year = dt.year
    month = dt.month

    # Determine fiscal year start/end
    if month >= 4:  # Apr–Dec
        fy_start = year
        fy_end = year + 1
    else:           # Jan–Mar
        fy_start = year - 1
        fy_end = year

    # Determine quarter number
    if month in [4, 5, 6]:
        q = 1
    elif month in [7, 8, 9]:
        q = 2
    elif month in [10, 11, 12]:
        q = 3
    else:
        q = 4

    return f"Q{q}_{str(fy_start)[-2:]}{str(fy_end)[-2:]}"

# ---------------------------------------------------------
# 6. Fiscal Quarter Start Function (corrected)
# ---------------------------------------------------------
def get_fiscal_quarter_start(dt):
    month = dt.month
    year = dt.year

    if month in [1, 2, 3]:
        start = pd.Timestamp(year, 1, 1)   # Q4
    elif month in [4, 5, 6]:
        start = pd.Timestamp(year, 4, 1)   # Q1
    elif month in [7, 8, 9]:
        start = pd.Timestamp(year, 7, 1)   # Q2
    else:
        start = pd.Timestamp(year, 10, 1)  # Q3

    return start.strftime("%m/%d/%Y")

# ---------------------------------------------------------
# 7. Apply quarter fields
# ---------------------------------------------------------
df["quarter"] = df["date"].apply(get_fiscal_quarter_label)
df["quarter_start"] = df["date"].apply(get_fiscal_quarter_start)

# ---------------------------------------------------------
# 8. MONTHLY AGGREGATION
# ---------------------------------------------------------
crime_monthly = (
    df.groupby(["date", "area_name"], as_index=False)["count"]
      .sum()
      .rename(columns={"area_name": "borough", "count": "crime_count"})
)

# ---------------------------------------------------------
# 9. QUARTERLY AGGREGATION
# ---------------------------------------------------------
crime_quarterly = (
    df.groupby(["quarter", "quarter_start", "area_name"], as_index=False)["count"]
      .sum()
      .rename(columns={"area_name": "borough", "count": "crime_count"})
)

# ---------------------------------------------------------
# 10. Save Outputs
# ---------------------------------------------------------
crime_monthly.to_csv(monthly_out, index=False)
crime_quarterly.to_csv(quarterly_out, index=False)

print("Monthly crime dataset saved to:")
print(monthly_out)

print("\nQuarterly crime dataset saved to:")
print(quarterly_out)
