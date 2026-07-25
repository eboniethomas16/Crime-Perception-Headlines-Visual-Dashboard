import pandas as pd
import os

# ---------------------------------------------------------
# 1. Input + Output Paths
# ---------------------------------------------------------
perception_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\MOPAC Data Cleaner\Public Perception Final CSV\Cleaned+Combined Perception Data\Combined_Public_Perception_Data.csv"

output_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Visual Python Code\Small Multiples - Crime\perception_long.csv"

# ---------------------------------------------------------
# 2. Load Perception Data
# ---------------------------------------------------------
df = pd.read_csv(perception_path)

# Ensure correct date parsing (MM/DD/YYYY)
df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors="coerce")

# ---------------------------------------------------------
# 3. Identify metric columns
# ---------------------------------------------------------
metric_cols = [
    "Good job",
    "Trust MPS",
    "Fair treatment",
    "Dealing issues",
    "Relied on to be there",
    "Listen to concerns",
    "Informed local",
    "Contact ward officer",
    "S&S used fairly"
]

# ---------------------------------------------------------
# 4. Convert percentage strings → decimal floats
# ---------------------------------------------------------
for col in metric_cols:
    df[col] = (
        df[col]
        .astype(str)
        .str.rstrip("%")
        .replace("", pd.NA)
        .astype(float) / 100
    )

# ---------------------------------------------------------
# 5. Melt into long format
# ---------------------------------------------------------
df_long = df.melt(
    id_vars=["Date", "Quarter", "Borough"],
    value_vars=metric_cols,
    var_name="metric",
    value_name="metric_value"
)

# ---------------------------------------------------------
# 6. REMOVE rows with missing metric_value
# ---------------------------------------------------------
df_long = df_long.dropna(subset=["metric_value"])

# ---------------------------------------------------------
# 7. Sort for readability
# ---------------------------------------------------------
df_long = df_long.sort_values(["Date", "Quarter", "Borough", "metric"])

# ---------------------------------------------------------
# 8. Save Output
# ---------------------------------------------------------
df_long.to_csv(output_path, index=False)

print("Long-format perception dataset saved to:")
print(output_path)
