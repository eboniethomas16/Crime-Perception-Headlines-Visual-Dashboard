import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as Rectangle
import pandas as pd
import numpy as np


crime_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\MOPAC Data Cleaner\MOPAC Monthly Crime Data\All_MOPAC_HistoricalCrimeData.csv"

perception_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\MOPAC Data Cleaner\Public Perception Final CSV\Cleaned+Combined Perception Data\Combined_Public_Perception_Data.csv"

geojson_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Visual Python Code\Bivariate_Chloropleth Map Outputs\london_boroughs.geojson"

output_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Visual Python Code\Bivariate_Chloropleth Map Outputs"

def get_fiscal_quarter_label(dt):
    year = dt.year
    month = dt.month

    # Fiscal year start/end
    if month <= 3:          # Jan–Mar → Q4 of previous FY
        fy_start = year - 1
    else:                   # Apr–Dec → Q1–Q3 of current FY
        fy_start = year

    fy_end = fy_start + 1

    # Quarter number
    if month in [4, 5, 6]:
        q = 1
    elif month in [7, 8, 9]:
        q = 2
    elif month in [10, 11, 12]:
        q = 3
    else:  # 1, 2, 3
        q = 4

    return f"Q{q}_{str(fy_start)[-2:]}{str(fy_end)[-2:]}"



def get_fiscal_quarter_start(dt):
    month = dt.month
    year = dt.year

    if month in [1, 2, 3]:
        start = pd.Timestamp(year, 1, 1)   # Q4
    elif month in [4, 5, 6]:
        start = pd.Timestamp(year, 4, 1)   # Q1
    elif month in [7, 8, 9]:
        start = pd.Timestamp(year, 7, 1)   # Q2
    else:  # 10, 11, 12
        start = pd.Timestamp(year, 10, 1)  # Q3

    return start.strftime("%m/%d/%Y")


def assign_bins(df):
    df = df.copy()
    df["crime_bin"] = pd.qcut(df["crime_count"], 3, labels=["low", "med", "high"])
    df["perc_bin"]  = pd.qcut(df["perception_value"], 3, labels=["low", "med", "high"])
    return df

# LOAD GEOJSON DATA
gdf = gpd.read_file(geojson_path)
#gdf["name"] = gdf["name"].str.strip().str.lower()
gdf = gdf.drop(columns=["color"])

# LOAD CRIME DATA
crime = pd.read_csv(crime_path)

# FITLER FOR ONLY "offences" AND "Current Data"
crime = crime[
    (crime["measure"].str.lower() == "offences") &
    (crime["category_status"] == "Current Data")
]

crime["date"] = pd.to_datetime(crime["date"], format="%m/%d/%Y", errors="coerce")
crime["quarter"] = crime["date"].apply(get_fiscal_quarter_label)
crime["quarter_start"] = crime["date"].apply(get_fiscal_quarter_start)

crime_q = (
    crime.groupby(["quarter", "quarter_start", "area_name"])["count"]
         .sum()
         .reset_index()
         .rename(columns={"area_name": "borough", "count": "crime_count"})
)

# LOAD PERCEPTION DATA
perception = pd.read_csv(perception_path)

perception = perception.rename(columns={"Date": "date"})
perception["date"] = pd.to_datetime(perception["date"])


# DATE == QUARTER_START ALREADY
perception["date"] = perception["date"].apply(get_fiscal_quarter_start)
perception = perception[perception["Borough"] != "MPS"]

metric_cols = [
    "Good job", "Trust MPS", "Fair treatment", "Dealing issues",
    "Relied on to be there", "Listen to concerns", "Informed local",
    "Contact ward officer", "S&S used fairly"
]

# CONVERT PERCENTAGE TO DECIMAL/FLOAT
for col in metric_cols:
    perception[col] = (
        perception[col].astype(str).str.rstrip("%").replace("", np.nan).astype(float) / 100
    )

perception_long = perception.melt(
    id_vars=["Borough", "Quarter", "date"],
    value_vars=metric_cols,
    var_name="metric",
    value_name="perception_value")


# ------------------------------------------------------------
# 1. MERGE CRIME + PERCEPTION (ALL QUARTERS × ALL METRICS)
# ------------------------------------------------------------
full = crime_q.merge(
    perception_long,
    left_on=["quarter", "borough"],
    right_on=["Quarter", "Borough"],
    how="inner"
)

# Keep only needed columns
full = full[[
    "date",
    "Quarter",
    "Borough",
    "metric",
    "crime_count",
    "perception_value"
]]

# Drop missing perception values
full = full.dropna(subset=["perception_value"])
# Standardise borough names
#full["Borough"] = full["Borough"].str.strip().str.lower()


full["crime_bin"] = (
    full.groupby(["Quarter", "metric"])["crime_count"]
        .transform(lambda s: pd.qcut(s, 3, labels=["low","med","high"]))
)

full["perc_bin"] = (
    full.groupby(["Quarter", "metric"])["perception_value"]
        .transform(lambda s: pd.qcut(s, 3, labels=["low","med","high"]))
)


palette = {
    ("low", "low"):   "#e8e8e8",
    ("med", "low"):   "#ace4e4",
    ("high", "low"):  "#5ac8c8",
    ("low", "med"):   "#dfb0d6",
    ("med", "med"):   "#a5add3",
    ("high", "med"):  "#5698b9",
    ("low", "high"):  "#be64ac",
    ("med", "high"):  "#8c62aa",
    ("high", "high"): "#3b4994",
}

# APPLY THE COLOR PALETTE
full["color"] = full.apply(
    lambda r: palette[(r["crime_bin"], r["perc_bin"])],
    axis=1
)

# ------------------------------------------------------------
# 2. MERGE FULL DATASET WITH GEOJSON (ALL ROWS)
# ------------------------------------------------------------
full_map_df = gdf.merge(
    full,
    left_on="name",
    right_on="Borough",
    how="left"
).drop(columns=["name"])

# ------------------------------------------------------------
# 3. REORDER COLUMNS
# ------------------------------------------------------------


full_map_df = full_map_df[
    [
        "date",
        "Quarter",
        "Borough",
        "metric",
        "crime_count",
        "perception_value",
        "crime_bin",
        "perc_bin",
        "color",
        "geometry"
    ]
]

# ------------------------------------------------------------
# 4. EXPORT FULL DATASET
# ------------------------------------------------------------
export_df = full_map_df.drop(columns=["geometry"]) # Remove Geometry just for the csv output
export_df.to_csv(
    rf"{output_path}\FULL_crime_perception_bins_colors.csv",
    index=False
)
# ------------------------------------------------------------
# 5. FILTER FOR SELECTED METRIC + QUARTER
# ------------------------------------------------------------
metric  = "Good job" #CHECK SPELLING
quarter = "Q1_2526"

metric_selection = full_map_df[
    (full_map_df["Quarter"] == quarter) &
    (full_map_df["metric"] == metric)
].copy()



palette = {
    ("low", "low"):   "#e8e8e8",
    ("med", "low"):   "#ace4e4",
    ("high", "low"):  "#5ac8c8",
    ("low", "med"):   "#dfb0d6",
    ("med", "med"):   "#a5add3",
    ("high", "med"):  "#5698b9",
    ("low", "high"):  "#be64ac",
    ("med", "high"):  "#8c62aa",
    ("high", "high"): "#3b4994",
}

metric_selection = full_map_df[
    (full_map_df["Quarter"] == quarter) &
    (full_map_df["metric"] == metric)
].copy()
print(metric_selection)


map_df = metric_selection[
    [
        "date",
        "Quarter",
        "Borough",
        "metric",
        "crime_count",
        "perception_value",
        "crime_bin",
        "perc_bin",
        "color",
        "geometry"
    ]
]


# ------------------------------------------------------------
# CREATE SAMPLE BIVARIATE CHOROPLETH MAP
# ------------------------------------------------------------
fig, ax = plt.subplots(1, 1, figsize=(10, 10))

map_df.plot(
    ax=ax,
    color=map_df["color"].fillna("#d9d9d9"),  # grey for missing boroughs
    edgecolor="black",
    linewidth=0.5
)

ax.set_title(f"Bivariate Map\n{metric}\n{quarter}", fontsize=16)
ax.axis("off")


# Create a small inset axis for the legend
legend_ax = fig.add_axes([0.72, 0.15, 0.18, 0.18])  # adjust position as needed
legend_ax.set_xticks([])
legend_ax.set_yticks([])
legend_ax.set_title("Crime × Perception", fontsize=10)


# Order of bins for grid
crime_bins = ["low", "med", "high"]
perc_bins  = ["low", "med", "high"]

# Draw the 3×3 grid
for i, p in enumerate(perc_bins):
    for j, c in enumerate(crime_bins):
        color = palette[(c, p)]
        legend_ax.add_patch(
            Rectangle.Rectangle(
                (j/3, i/3), 1/3, 1/3,
                facecolor=color,
                edgecolor="black"
            )
        )

# Axis labels
legend_ax.text(0.5, -0.1, "Crime Count →", ha="center", va="top", fontsize=9)
legend_ax.text(-0.1, 0.5, "Perception % →", ha="right", va="center", fontsize=9, rotation=90)

legend_ax.set_xlim(0, 1)
legend_ax.set_ylim(0, 1)

plt.show()
