import pandas as pd
import numpy as np
from scipy.spatial.distance import jensenshannon
import seaborn as sns
import matplotlib.pyplot as plt
import os

crime_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\MOPAC Data Cleaner\MOPAC Monthly Crime Data\All_MOPAC_HistoricalCrimeData.csv"
perception_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\MOPAC Data Cleaner\Public Perception Final CSV\Cleaned+Combined Perception Data\Combined_Public_Perception_Data.csv"

output_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\GDELT_pipeline\divergence_heatmap_output\s-jsd_hybrid_heatmap_perception_crime.csv"

crime = pd.read_csv(crime_path)

# Filter crime dataset for offences under the "current data" categories
crime = crime[
    (crime["measure"].str.lower() == "offences") &
    (crime["category_status"] == "Current Data")
]

def full_jsd(P, Q):
    """
    Compute full-distribution Jensen–Shannon Divergence (unsigned).
    SciPy returns sqrt(JSD), so we square it.
    """
    P = np.asarray(P, dtype=float)
    Q = np.asarray(Q, dtype=float)

    P = P / P.sum() if P.sum() > 0 else np.zeros_like(P)
    Q = Q / Q.sum() if Q.sum() > 0 else np.zeros_like(Q)

    return jensenshannon(P, Q, base=2) ** 2


# Convert to fiscal quarters (Q1_2122 etc.)
# Map crime monthly dates → fiscal quarters
def get_fiscal_quarter_label(dt):
    """
    Convert a datetime to a UK fiscal quarter label like Q1_2122.
    Fiscal year runs Apr 1 – Mar 31.
    """
    year = dt.year
    month = dt.month

    # Determine fiscal year start
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



# Map fiscal quarters → quarter start dates
def get_fiscal_quarter_start(dt):
    """
    Return the first day of the fiscal quarter
    for a given datetime, formatted as MM/DD/YYYY.
    """
    month = dt.month
    year = dt.year

    if month in [4, 5, 6]:
        start = pd.Timestamp(year, 4, 1)
    elif month in [7, 8, 9]:
        start = pd.Timestamp(year, 7, 1)
    elif month in [10, 11, 12]:
        start = pd.Timestamp(year, 10, 1)
    else:  # Jan–Mar
        start = pd.Timestamp(year - 1, 1, 1)

    return start.strftime("%m/%d/%Y")


crime["date"] = pd.to_datetime(crime["date"])

crime["quarter"] = crime["date"].apply(get_fiscal_quarter_label)
crime["quarter_start"] = crime["date"].apply(get_fiscal_quarter_start)
crime_q = (
    crime.groupby(["quarter", "quarter_start", "area_name"])["count"]
         .sum()
         .reset_index()
         .rename(columns={"area_name": "borough", "count": "crime_count"}))


# ----------------------------------------------
# PERCEPTION DATSET PREP
# ----------------------------------------------
perception = pd.read_csv(perception_path)

metric_cols = [
    "Good job", "Trust MPS", "Fair treatment", "Dealing issues",
    "Relied on to be there", "Listen to concerns",
    "Informed local", "Contact ward officer", "S&S used fairly"
]
perception["Date"] = pd.to_datetime(perception["Date"])
perception["quarter"] = perception["Date"].apply(get_fiscal_quarter_label)
perception["quarter_start"] = perception["Date"].apply(get_fiscal_quarter_start)


# Convert "46%" → 0.46
for col in metric_cols:
    perception[col] = perception[col].str.rstrip("%").astype(float) / 100

perception_long = perception.melt(
    id_vars=["Date", "Quarter", "Borough"],
    value_vars=metric_cols,
    var_name="metric",
    value_name="perception_value"
)

# REMOVE "MPS" AVERAGE ROWS IN THE DATASET
perception_long = perception_long[perception_long["Borough"] != "MPS"]


merged = crime_q.merge(
    perception_long,
    left_on=["quarter", "borough"],
    right_on=["Quarter", "Borough"],
    how="inner"
)

merged = merged.rename(columns={"quarter_start": "date"})
merged = merged[["date", "quarter", "borough", "crime_count", "metric", "perception_value"]]


rows = []

for (quarter, metric), df_qm in merged.groupby(["quarter", "metric"]):
    df_qm = df_qm.dropna(subset=["perception_value"])
    if df_qm.empty:
        continue

    crime_dist = df_qm["crime_count"].values.astype(float)
    perc_dist = df_qm["perception_value"].values.astype(float)

    crime_dist_norm = crime_dist / crime_dist.sum()
    perc_dist_norm = perc_dist / perc_dist.sum()

    global_jsd = full_jsd(crime_dist_norm, perc_dist_norm)

    for idx, row in df_qm.iterrows():
        P_i = row["crime_count"] / crime_dist.sum()
        Q_i = row["perception_value"] / perc_dist.sum()

        direction = np.sign(Q_i - P_i)
        hybrid_value = direction * global_jsd

        rows.append({
            "date": row["date"],
            "quarter": quarter,
            "borough": row["borough"],
            "metric": metric,   
            "crime_count": row["crime_count"],
            "perception_value": row["perception_value"],
            "hybrid_sjsd": hybrid_value
        })

hybrid_df = pd.DataFrame(rows)
print(hybrid_df.columns.tolist())

if os.path.exists(output_path):
    print("\nCSV already exists. Skipping computation and loading for visualization...\n")
else:
    hybrid_df.to_csv(output_path, index=False)

# OUTPUT FORMAT:
# date        quarter    borough    metric    hybrid_sjsd
# 01/01/2022  Q4_2122    Camden     Trust MPS   +0.0412
# 10/01/2021  Q3_2122    Camden     Trust MPS   -0.0389


metric_df = hybrid_df[hybrid_df["metric"] == "Trust MPS"]

heatmap_data = metric_df.pivot(
    index="borough",
    columns="date",   # or "quarter"
    values="hybrid_sjsd"
)



print("\nLoading dataset for visualization...\n")

# Ensure date is datetime
hybrid_df["date"] = pd.to_datetime(hybrid_df["date"])

# Format date label for heatmap columns
hybrid_df["date_label"] = hybrid_df["date"].dt.strftime("%Y-%m")

# Choose a perception metric to visualize
metric_name = "S&S used fairly"   # <-- change this to any of the 9 metrics

metric_df = hybrid_df[hybrid_df["metric"] == metric_name]

# Pivot for heatmap: boroughs × dates
heatmap_data = metric_df.pivot(
    index="borough",
    columns="date_label",
    values="hybrid_sjsd"
).sort_index()

# Create heatmap
plt.figure(figsize=(22, 10))

sns.heatmap(
    heatmap_data,
    cmap=sns.diverging_palette(150, 10, as_cmap=True),  # green → white → red
    center=0,
    linewidths=0.3,
    linecolor="gray",
    cbar_kws={"label": "Hybrid S‑JSD (Perception vs Crime)"}
)

plt.title(f"Hybrid S‑JSD: Perception vs Crime\nMetric: {metric_name}", fontsize=16)
plt.xlabel("Quarter")
plt.ylabel("Borough")

plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.show()
