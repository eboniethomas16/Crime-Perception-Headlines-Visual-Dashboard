import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# ---------------------------------------------------------
# 1. INPUT PATHS
# ---------------------------------------------------------
crime_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Data_Visuals\Scrollytelling_draft\data\crime_types_monthly.csv"

headline_folder = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\GDELT_pipeline\data\combined_datasets\Updated Monthly Filtered Datasets\CLEANED Combined Datasets"

output_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Data_Visuals\Scrollytelling_draft\data"

crime_type_output = os.path.join(output_path, "crime_type_residuals_monthly.csv")
aggregated_output = os.path.join(output_path, "aggregated_residuals_monthly.csv")

# ---------------------------------------------------------
# 2. LOAD CRIME DATA
# ---------------------------------------------------------
crime_df = pd.read_csv(crime_path)
crime_df["date"] = pd.to_datetime(crime_df["date"])
crime_df["crime_type"] = crime_df["crime_type"].str.strip()

monthly_crime = (
    crime_df.groupby(["crime_type", crime_df["date"].dt.to_period("M")])["crime_count"]
    .sum()
    .reset_index()
)

monthly_crime["date"] = monthly_crime["date"].dt.to_timestamp()

# ---------------------------------------------------------
# 3. LOAD CLEANED HEADLINE FILES FROM FOLDER
# ---------------------------------------------------------
headline_files = [f for f in os.listdir(headline_folder) if f.endswith(".csv")]
headline_dfs = []

for file in headline_files:
    df_temp = pd.read_csv(os.path.join(headline_folder, file), low_memory=False)

    required = {"headline", "V2SOURCECOMMONNAME", "date", "crime_type"}
    if required.issubset(df_temp.columns):
        headline_dfs.append(df_temp)

head = pd.concat(headline_dfs, ignore_index=True)

head["date"] = pd.to_datetime(head["date"], errors="coerce")
head = head.dropna(subset=["date"])
head = head[head["crime_type"] != "UNKNOWN"]
head["crime_type"] = head["crime_type"].str.strip()

# Deduplicate headline–source pairs
head = head.drop_duplicates(subset=["crime_type", "headline", "V2SOURCECOMMONNAME"])

# Convert to monthly
head["date"] = head["date"].dt.to_period("M").dt.to_timestamp()

monthly_headlines = (
    head.groupby(["crime_type", "date"])["headline"]
        .nunique()
        .reset_index(name="headline_count")
)

# ---------------------------------------------------------
# 4. MERGE CRIME + HEADLINE MONTHLY DATA
# ---------------------------------------------------------
merged = pd.merge(
    monthly_crime,
    monthly_headlines,
    on=["crime_type", "date"],
    how="left"
).sort_values(["crime_type", "date"])

merged["headline_count"] = merged["headline_count"].fillna(0)

# ---------------------------------------------------------
# 5. COMPUTE RESIDUALS PER CRIME TYPE
# ---------------------------------------------------------
rows = []

for crime_type, group in merged.groupby("crime_type"):

    if len(group) < 3:
        continue

    X = group[["crime_count"]].values
    y = group["headline_count"].values

    model = LinearRegression().fit(X, y)
    predicted = model.predict(X)
    residual = y - predicted

    out = pd.DataFrame({
        "crime_type": crime_type,
        "date": group["date"],
        "residual": residual
    })

    rows.append(out)

crime_type_residuals = pd.concat(rows, ignore_index=True)

# Format date
crime_type_residuals["date"] = crime_type_residuals["date"].dt.strftime("%-m/%-d/%Y")

# ---------------------------------------------------------
# 6. AGGREGATED MONTHLY RESIDUALS (mean across crime types)
# ---------------------------------------------------------
aggregated = (
    crime_type_residuals.groupby("date")["residual"]
    .mean()
    .reset_index()
)

# ---------------------------------------------------------
# 7. SAVE OUTPUT FILES
# ---------------------------------------------------------
crime_type_residuals.to_csv(crime_type_output, index=False)
aggregated.to_csv(aggregated_output, index=False)

print("Residual CSVs created successfully:")
print(" - Crime-type residuals:", crime_type_output)
print(" - Aggregated residuals:", aggregated_output)
