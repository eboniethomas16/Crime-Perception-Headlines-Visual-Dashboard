import os
import numpy as np
import pandas as pd
from scipy.spatial.distance import jensenshannon
# print(sns.__version__)
import seaborn as sns
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# 1. INPUT PATHS
# ---------------------------------------------------------
mopac_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\MOPAC Data Cleaner\MOPAC Monthly Crime Data\All_MOPAC_HistoricalCrimeData.csv"

headline_folder = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\GDELT_pipeline\data\combined_datasets\Updated Monthly Filtered Datasets\CLEANED Combined Datasets"

# output_folder = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\GDELT_pipeline\divergence_heatmap_output"
output_folder = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Visual Python Code\divergence_heatmap_outputs"
output_csv = os.path.join(output_folder, "hybrid_sjsd_heatmap_crime_vs_headlines.csv")

os.makedirs(output_folder, exist_ok=True)


# ---------------------------------------------------------
# 2. IF CSV ALREADY EXISTS → SKIP TO HEATMAP
# ---------------------------------------------------------
if os.path.exists(output_csv):
    print("\nCSV already exists. Skipping computation and loading for visualization...\n")
    df = pd.read_csv(output_csv, parse_dates=["date"])
else:
    print("\nCSV not found. Computing Signed JSD from scratch...\n")

    # ---------------------------------------------------------
    # 3. LOAD HEADLINE DATA
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

    # Deduplicate headline–source pairs
    head = head.drop_duplicates(subset=["crime_type", "headline", "V2SOURCECOMMONNAME"])

    # Create Month field renamed to "date"
    head["date"] = head["date"].dt.to_period("M").dt.to_timestamp()

    headline_counts = (
        head.groupby(["date", "crime_type"])["headline"]
            .nunique()
            .reset_index(name="headline_count")
    )


    # ---------------------------------------------------------
    # 4. LOAD MOPAC CRIME DATA
    # ---------------------------------------------------------
    mopac = pd.read_csv(mopac_path, low_memory=False)

    mopac["date"] = pd.to_datetime(mopac["date"], errors="coerce")
    mopac = mopac.dropna(subset=["date"])

    mopac = mopac[
        (mopac["measure"].str.lower() == "offences") &
        (mopac["category_status"] == "Current Data")
    ]

    mopac_counts = (
        mopac.groupby(["date", "crime_type"])["count"]
             .sum()
             .reset_index()
             .rename(columns={"count": "crime_count"})
    )

    mopac_counts["date"] = mopac_counts["date"].dt.to_period("M").dt.to_timestamp()


    # ---------------------------------------------------------
    # 5. MERGE CRIME + HEADLINES
    # ---------------------------------------------------------
    merged = mopac_counts.merge(
        headline_counts,
        on=["date", "crime_type"],
        how="left"
    )

    merged["headline_count"] = merged["headline_count"].fillna(0)


    # ---------------------------------------------------------
    # 6. 2 ELEMENT SIGNED JENSEN–SHANNON DIVERGENCE
    # ---------------------------------------------------------
    def signed_jsd(P, Q):
        P = np.asarray(P, dtype=float)
        Q = np.asarray(Q, dtype=float)

        P = P / P.sum() if P.sum() > 0 else np.zeros_like(P)
        Q = Q / Q.sum() if Q.sum() > 0 else np.zeros_like(Q)

        jsd_value = jensenshannon(P, Q, base=2) ** 2
        direction = np.sign((Q - P).sum())

        return direction * jsd_value
    
    # ---------------------------------------------------------
    # 6. HYBRID DISTRIBUTION SIGNED-JENSEN–SHANNON DIVERGENCE
    # ---------------------------------------------------------
    
    def full_jsd(P, Q):
        """
        Compute the full-distribution Jensen–Shannon Divergence (unsigned).
        SciPy's jensenshannon returns sqrt(JSD), so we square it.
        """
        P = np.asarray(P, dtype=float)
        Q = np.asarray(Q, dtype=float)

        P = P / P.sum() if P.sum() > 0 else np.zeros_like(P)
        Q = Q / Q.sum() if Q.sum() > 0 else np.zeros_like(Q)

        return jensenshannon(P, Q, base=2) ** 2

    
    # ---------------------------------------------------------
    # 6. FULL DISTRIBUTION SIGNED-JENSEN–SHANNON DIVERGENCE
    # ---------------------------------------------------------

    def full_distribution_signed_jsd(crime_dist, headline_dist):
        """
        Compute Signed Jensen–Shannon Divergence using the FULL distributions
        across all crime types for a given month.

        crime_dist: 1D array of crime proportions across all crime types
        headline_dist: 1D array of headline proportions across all crime types

        Returns a signed JSD value in [-1, +1].
        """

        P = np.asarray(crime_dist, dtype=float)
        Q = np.asarray(headline_dist, dtype=float)

        # Normalise to probability distributions
        P = P / P.sum() if P.sum() > 0 else np.zeros_like(P)
        Q = Q / Q.sum() if Q.sum() > 0 else np.zeros_like(Q)

        # Compute unsigned JSD (SciPy returns sqrt(JSD), so square it)
        jsd_value = jensenshannon(P, Q, base=2) ** 2

        # Direction: if headlines overweight crime distribution
        direction = np.sign((Q - P).sum())

        return direction * jsd_value

    # ---------------------------------------------------------
    # 7. COMPUTE S-JSD PER MONTH × CRIME TYPE
    # ---------------------------------------------------------
    rows = []

    for date in sorted(merged["date"].unique()):
        month_df = merged[merged["date"] == date]

        # FULL distributions across all crime types
        crime_dist = month_df["crime_count"].values.astype(float)
        headline_dist = month_df["headline_count"].values.astype(float)

        # Normalise
        crime_dist_norm = crime_dist / crime_dist.sum() if crime_dist.sum() > 0 else np.zeros_like(crime_dist)
        headline_dist_norm = headline_dist / headline_dist.sum() if headline_dist.sum() > 0 else np.zeros_like(headline_dist)

        # 1. Global magnitude (same for all crime types in this month)
        global_jsd = full_jsd(crime_dist_norm, headline_dist_norm)

        # 2. Local direction per crime type
        for idx, row in month_df.iterrows():
            crime_type = row["crime_type"]

            P_i = crime_dist_norm[month_df.index == idx][0]
            Q_i = headline_dist_norm[month_df.index == idx][0]

            direction = np.sign(Q_i - P_i)

            hybrid_value = direction * global_jsd

            rows.append({
                "date": date,
                "crime_type": crime_type,
                "crime_count": row["crime_count"],
                "headline_count": row["headline_count"],
                "signed_jsd": hybrid_value
            })

    df = pd.DataFrame(rows)


    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print("Signed JSD heatmap dataset exported to:")
    print(output_csv)


# ---------------------------------------------------------
# 8. HEATMAP VISUALISATION
# ---------------------------------------------------------
print("\nLoading dataset for visualization...\n")

# Format date label
df["date"] = pd.to_datetime(df["date"])
df["date_label"] = df["date"].dt.strftime("%Y-%m")

# Pivot for heatmap
heatmap_data = df.pivot(
    index="crime_type",
    columns="date_label",
    values="signed_jsd"
).sort_index()

# Create heatmap
plt.figure(figsize=(22, 10))

sns.heatmap(
    heatmap_data,
    cmap=sns.diverging_palette(150, 10, as_cmap=True),
    center=0,
    linewidths=0.3,
    linecolor="gray",
    cbar_kws={"label": "Signed Jensen–Shannon Divergence"}
)

plt.title("Signed Jensen–Shannon Divergence: Media Headlines vs Crime (Per Crime Type × Month)", fontsize=16)
plt.xlabel("Month")
plt.ylabel("Crime Type")

plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.show()
