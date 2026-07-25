import pandas as pd
import numpy as np
import os

# ---------------------------------------------------------
# 1. Load all headline datasets
# ---------------------------------------------------------
input_folder = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\GDELT_pipeline\data\combined_datasets\Updated Monthly Filtered Datasets\CLEANED Combined Datasets"

all_files = [f for f in os.listdir(input_folder) if f.endswith(".csv")]

dfs = []
print("Extracting Each Monthly Headline File!\n")
for file in all_files:
    df = pd.read_csv(os.path.join(input_folder, file), low_memory=False)

    # Ensure required columns exist
    if not {"headline", "V2SOURCECOMMONNAME", "date", "headline_is_duplicate", "crime_type", "crime_types"}.issubset(df.columns):
        continue

    dfs.append(df)

print("EXTRACTION FINISHED!\n")
df = pd.concat(dfs, ignore_index=True)

# ---------------------------------------------------------
# 2. Clean + prepare
# ---------------------------------------------------------
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])

# Only duplicated headlines
df = df[df["headline_is_duplicate"] == True]

# Remove UNKNOWN crime types
df = df[df["crime_type"] != "UNKNOWN"]

# Deduplicate by headline + source (your rule)
df = df.drop_duplicates(subset=["headline", "V2SOURCECOMMONNAME"])

# ---------------------------------------------------------
# 3. Compute monthly distinct headline counts
# ---------------------------------------------------------
df["Month"] = df["date"].dt.to_period("M").dt.to_timestamp()

monthly_counts = (
    df.groupby("Month")["headline"]
      .nunique()
      .reset_index(name="distinct_headline_count")
)

# ---------------------------------------------------------
# 4. Identify the MOST duplicated headline per month
# ---------------------------------------------------------
headline_month_counts = (
    df.groupby(["Month", "headline"])["V2SOURCECOMMONNAME"]
      .nunique()
      .reset_index(name="source_count")
)

top_headlines = (
    headline_month_counts.sort_values(["Month", "source_count"], ascending=[True, False])
    .groupby("Month")
    .first()
    .reset_index()
)

# ---------------------------------------------------------
# 5. Add FIRST publication date for each top headline
# ---------------------------------------------------------
first_dates = (
    df.groupby("headline")["date"]
      .min()
      .reset_index()
      .rename(columns={"date": "headline_date"})
)

top_headlines = top_headlines.merge(first_dates, on="headline", how="left")
top_headlines["headline_date"] = top_headlines["headline_date"].dt.strftime("%m/%d/%Y")

# ---------------------------------------------------------
# 6. Add CRIME TYPES for each top headline
# ---------------------------------------------------------
# Deduplicate headline + crime_types pairs
crime_type_map = (
    df.drop_duplicates(subset=["headline", "crime_types"])
      .groupby("headline")["crime_types"]
      .apply(lambda x: ", ".join(sorted(set(x))))
      .reset_index()
      .rename(columns={"crime_types": "Crime Types"})
)


# Merge into top_headlines
top_headlines = top_headlines.merge(crime_type_map, on="headline", how="left")

# ---------------------------------------------------------
# 7. Merge into final dataset for D3.js
# ---------------------------------------------------------
final = monthly_counts.merge(top_headlines, on="Month", how="left")

final = final.rename(columns={
    "headline": "Top Headline",
    "source_count": "Top Headline Count",
    "headline_date": "Headline Date"
})

# ---------------------------------------------------------
# 8. Export for D3.js (tooltip-ready)
# ---------------------------------------------------------
output_csv = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\GDELT_pipeline\annotated line chart output\annotated_line_chart.csv"
final.to_csv(output_csv, index=False, encoding="utf-8-sig")

print("Exported timeline dataset to:")
print(output_csv)
