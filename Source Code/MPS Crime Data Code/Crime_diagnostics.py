import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
import argparse
import os
# -----------------------------
# 5. TEMPORAL ANALYSIS
# -----------------------------
import os
import re
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller

# -----------------------------
# CONFIG
# -----------------------------
RAW_CRIME_CSV = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\MOPAC Data Cleaner\MOPAC Monthly Crime Data\MPS_Crime_Data.csv"
MONTHLY_CAT_CSV = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Data_Visuals\Scrollytelling_draft\data\diagnostics\monthly_category_totals.csv"
MONTHLY_BORO_CSV = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Data_Visuals\Scrollytelling_draft\data\diagnostics\monthly_borough_totals.csv"
BOROUGH_POP_CSV = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Visual Python Code\2021_census_by_sex.csv"  # expected columns: borough, population
OUTPUT_FIG_DIR = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Data_Visuals\Scrollytelling_draft\data\diagnostics"
os.makedirs(OUTPUT_FIG_DIR, exist_ok=True)

DATE_COL = "date"
AREA_NAME_COL = "area_name"
CRIME_TYPE_COL = "crime_type"
CATEGORY_STATUS_COL = "category_status"
MEASURE_COL = "measure"
COUNT_COL = "count"

START_DATE = "2017-04-01"  # 4/1/2017
CATEGORIES_FOR_EVAL = [
    "DOMESTIC ABUSE",
    "GUN CRIME",
    "HATE CRIME",
    "KNIFE CRIME",
    "LETHAL BARREL DISCHARGE",
    "ARSON AND CRIMINAL DAMAGE",
    "BURGLARY",
    "DRUG OFFENCES",
    "PUBLIC ORDER OFFENCES",
    "ROBBERY",
    "SEXUAL OFFENCES",
    "THEFT",
    "VEHICLE OFFENCES",
    "VIOLENCE AGAINST THE PERSON",
    "POSSESSION OF WEAPONS",
    "FRAUD AND FORGERY",
]

# -----------------------------
# 1. LOAD & CLEAN RAW CRIME
# -----------------------------
def load_and_clean_raw(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    # rename for analysis
    df = df.rename(columns={
        AREA_NAME_COL: "borough",
        CRIME_TYPE_COL: "crime category",
        DATE_COL: "date"
    })
    df = df[df["measure"] == "offences"].copy()
    # parse date
    df["date"] = pd.to_datetime(df["date"], format="%m/%d/%Y", errors="coerce")

    # filter date range
    df = df[df["date"] >= pd.to_datetime(START_DATE)]

    # keep borough level only
    df = df[df["area_type"] == "Borough"]

    # filter category_status: only current data
    df = df[df[CATEGORY_STATUS_COL].str.lower() == "current data"]

    # drop MISCELLANEOUS categories
    df = df[~df["crime category"].str.upper().eq("MISCELLANEOUS")]

    # keep offences only
    df = df[df[MEASURE_COL] == "offences"]

    # numeric count, allow NA with nullable Int64 to avoid IntCastingNaNError
    df[COUNT_COL] = pd.to_numeric(df[COUNT_COL], errors="coerce")
    df[COUNT_COL] = df[COUNT_COL].astype("Int64")

    # restrict to evaluation categories (optional but recommended)
    df = df[df["crime category"].isin(CATEGORIES_FOR_EVAL)]

    # add year_month
    df["year_month"] = df["date"].dt.to_period("M").dt.to_timestamp()

    return df
def load_census(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    ltla_col = "Lower tier local authorities"
    obs_col = "Observation"
    if ltla_col not in df.columns or obs_col not in df.columns:
        raise ValueError(f"Input CSV must contain columns: '{ltla_col}' and '{obs_col}'")
    # Convert Observation to numeric (remove commas), coerce errors to NaN
    df[obs_col] = pd.to_numeric(df[obs_col].str.replace(",", "").str.strip(), errors="coerce")
    # Drop rows with missing LTLA names
    df = df.dropna(subset=[ltla_col])
    # Rename LTLA column to 'borough'
    df = df.rename(columns={ltla_col: "borough", obs_col: "observation"})
    return df[["borough", "observation"]]

def aggregate_by_borough(df: pd.DataFrame) -> pd.DataFrame:
    agg = df.groupby("borough", as_index=False)["observation"].sum()
    agg = agg.rename(columns={"observation": "population"})
    # Ensure integer population where possible
    agg["population"] = agg["population"].fillna(0).round().astype(int)
    return agg

def main(args):
    df = load_census(args.census)
    agg = aggregate_by_borough(df)
    out_path = args.output or "borough_population.csv"
    agg.to_csv(out_path, index=False)
    print(f"Saved borough population file to: {out_path} (rows: {len(agg)})")
# -----------------------------
# 2. AGGREGATE: CATEGORY & BOROUGH
# -----------------------------
def build_monthly_category_totals(df: pd.DataFrame) -> pd.DataFrame:
    cat_month = (
        df.groupby(["year_month", "crime category"], as_index=False)[COUNT_COL]
          .sum()
          .rename(columns={COUNT_COL: "category_month_total"})
    )
    return cat_month

def build_monthly_borough_totals(df: pd.DataFrame) -> pd.DataFrame:
    boro_month = (
        df.groupby(["year_month", "borough"], as_index=False)[COUNT_COL]
          .sum()
          .rename(columns={COUNT_COL: "borough_month_total"})
    )
    return boro_month

# -----------------------------
# 3. DATA QUALITY & DESCRIPTIVE SUMMARY
# -----------------------------
def data_quality_summary(df_raw: pd.DataFrame,
                         cat_month: pd.DataFrame,
                         boro_month: pd.DataFrame) -> None:
    print("\n=== Missingness (raw) ===")
    print(df_raw.isna().sum())

    print("\n=== Date range (raw) ===")
    print(df_raw["date"].min(), "->", df_raw["date"].max())

    total_incidents = df_raw[COUNT_COL].sum()
    print("\n=== Total incidents (raw) ===")
    print(total_incidents)

    print("\n=== Incidents per borough (raw) ===")
    print(df_raw.groupby("borough")[COUNT_COL].sum().sort_values(ascending=False))

    print("\n=== Incidents per category (raw) ===")
    print(df_raw.groupby("crime category")[COUNT_COL].sum().sort_values(ascending=False))

    print("\n=== Monthly category totals (head) ===")
    print(cat_month.head())

    print("\n=== Monthly borough totals (head) ===")
    print(boro_month.head())

# -----------------------------
# 4. COUNTS & RATES TABLES
# -----------------------------
def counts_and_rates(cat_month: pd.DataFrame,
                     boro_month: pd.DataFrame,
                     pop_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    # overall period totals
    cat_tot = (
        cat_month.groupby("crime category", as_index=False)["category_month_total"]
        .sum()
        .rename(columns={"category_month_total": "total_count"})
    )

    boro_tot = (
        boro_month.groupby("borough", as_index=False)["borough_month_total"]
        .sum()
        .rename(columns={"borough_month_total": "total_count"})
    )
    

    # merge population for rates
   
    pop_df = pop_df.rename(columns={"observation": "population"})
    boro_tot = boro_tot.merge(pop_df, on="borough", how="left")

    boro_tot["rate_per_10k"] = (boro_tot["total_count"] / boro_tot["population"]) * 10000

    # for categories, you may want overall London population or per‑borough later;
    # here we just keep counts (rates can be added once denominator is chosen)
    cat_tot["rate_per_10k"] = np.nan  # placeholder

    print("\n=== Borough counts & rates per 10,000 ===")
    print(boro_tot.sort_values("rate_per_10k", ascending=False).head())

    print("\n=== Category counts (rates placeholder) ===")
    print(cat_tot.sort_values("total_count", ascending=False).head())

    return cat_tot, boro_tot



# -----------------------------
# FIGURE OUTPUT CONFIG
# -----------------------------


def _safe_filename(s: str) -> str:
    s = s.strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "_", s)
    return s[:200]

def save_fig(fig_or_plt, title: str, fmt: str = "png", dpi: int = 150):
    fname = f"{_safe_filename(title)}.{fmt}"
    path = os.path.join(OUTPUT_FIG_DIR, fname)

    # If a Figure object is passed
    if isinstance(fig_or_plt, mpl.figure.Figure):
        fig_or_plt.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close(fig_or_plt)
    else:
        # Assume pyplot state (plt)
        plt.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close()  # close current figure

    print(f"Saved figure: {path}")

# -----------------------------
# Example usage inside temporal_analysis
# -----------------------------
def temporal_analysis(cat_month: pd.DataFrame, boro_month: pd.DataFrame) -> None:
    """
    Extended temporal analysis:
      - overall London monthly series (saved)
      - time series + seasonal decomposition + summary stats for selected crime categories
        (THEFT, VIOLENCE AGAINST THE PERSON, LETHAL BARREL DISCHARGE, GUN CRIME)
      - time series + seasonal decomposition + summary stats for selected boroughs
        (Westminster, Kingston upon Thames, Richmond upon Thames, Sutton)
      - saves plots and peak/trough CSVs to OUTPUT_FIG_DIR via save_fig()
    Assumes:
      - year_month is a datetime-like column (period start)
      - cat_month has columns: year_month, crime category, category_month_total
      - boro_month has columns: year_month, borough, borough_month_total
    """
    # --- overall London series ---
    overall = (
        boro_month.groupby("year_month", as_index=False)["borough_month_total"]
        .sum()
        .rename(columns={"borough_month_total": "total_monthly_offences"})
    )

    plt.figure(figsize=(10, 4))
    plt.plot(overall["year_month"], overall["total_monthly_offences"], color="tab:blue")
    plt.title("Monthly total offences (London)")
    plt.xlabel("Month")
    plt.ylabel("Offences")
    plt.grid(True)
    save_fig(plt, "Monthly_total_offences_London")

    # prepare ts for decomposition and stats
    ts_overall = overall.set_index("year_month")["total_monthly_offences"].asfreq("MS")

    # seasonal decomposition (overall)
    try:
        decomposition = sm.tsa.seasonal_decompose(ts_overall, model="additive", period=12)
        fig = decomposition.plot()
        save_fig(fig, "Seasonal_decomposition_overall_monthly_offences")
    except Exception as e:
        print("Seasonal decomposition (overall) failed:", e)

    # overall summary stats (text figure)
    plt.figure(figsize=(6, 3))
    stats_text = ts_overall.describe().to_string()
    plt.axis("off")
    plt.text(0, 0.5, stats_text, fontsize=10, family="monospace")
    save_fig(plt, "Time_series_summary_statistics_overall")

    # save peaks/troughs for overall
    top5 = ts_overall.nlargest(5)
    bottom5 = ts_overall.nsmallest(5)
    top5.to_csv(os.path.join(OUTPUT_FIG_DIR, "top5_peaks_overall.csv"))
    bottom5.to_csv(os.path.join(OUTPUT_FIG_DIR, "bottom5_troughs_overall.csv"))
    print("Saved overall peak/trough CSVs to:", OUTPUT_FIG_DIR)

    # --- category-level analysis (selected categories) ---
    categories = ["THEFT", "VIOLENCE AGAINST THE PERSON", "LETHAL BARREL DISCHARGE", "GUN CRIME"]
    for cat in categories:
        sub = cat_month[cat_month["crime category"] == cat].copy()
        if sub.empty:
            print(f"No data for category: {cat}")
            continue
        sub = sub.sort_values("year_month")
        # time series plot
        plt.figure(figsize=(10, 4))
        plt.plot(sub["year_month"], sub["category_month_total"], label=cat, color="tab:orange")
        plt.title(f"Monthly offences: {cat}")
        plt.xlabel("Month")
        plt.ylabel("Offences")
        plt.grid(True)
        save_fig(plt, f"Monthly_offences_{cat.replace(' ', '_')}")

        # convert to ts
        ts_cat = sub.set_index("year_month")["category_month_total"].asfreq("MS")
        # decomposition
        try:
            dec_cat = sm.tsa.seasonal_decompose(ts_cat, model="additive", period=12)
            fig = dec_cat.plot()
            save_fig(fig, f"Seasonal_decomposition_{cat.replace(' ', '_')}")
        except Exception as e:
            print(f"Seasonal decomposition failed for {cat}:", e)

        # summary stats and peaks/troughs
        plt.figure(figsize=(6, 3))
        stats_text = ts_cat.describe().to_string()
        plt.axis("off")
        plt.text(0, 0.5, stats_text, fontsize=10, family="monospace")
        save_fig(plt, f"Time_series_summary_stats_{cat.replace(' ', '_')}")

        top = ts_cat.nlargest(5)
        bot = ts_cat.nsmallest(5)
        top.to_csv(os.path.join(OUTPUT_FIG_DIR, f"top5_peaks_{cat.replace(' ', '_')}.csv"))
        bot.to_csv(os.path.join(OUTPUT_FIG_DIR, f"bottom5_troughs_{cat.replace(' ', '_')}.csv"))

        # ADF test (print and save small text file)
        try:
            adf_res = adfuller(ts_cat.dropna(), autolag="AIC")
            adf_text = (
                f"ADF statistic: {adf_res[0]:.4f}\n"
                f"p-value: {adf_res[1]:.4f}\n"
                f"Used lags: {adf_res[2]}\n"
                f"Number of obs: {adf_res[3]}\n"
            )
            print(f"ADF for {cat}:\n", adf_text)
            with open(os.path.join(OUTPUT_FIG_DIR, f"ADF_{cat.replace(' ', '_')}.txt"), "w") as f:
                f.write(adf_text)
        except Exception as e:
            print(f"ADF test failed for {cat}:", e)

    # --- borough-level analysis (selected boroughs) ---
    boroughs = ["Westminster", "Kingston upon Thames", "Richmond upon Thames", "Sutton"]
    for b in boroughs:
        sub_b = boro_month[boro_month["borough"] == b].copy()
        if sub_b.empty:
            print(f"No data for borough: {b}")
            continue
        sub_b = sub_b.sort_values("year_month")
        # time series plot
        plt.figure(figsize=(10, 4))
        plt.plot(sub_b["year_month"], sub_b["borough_month_total"], label=b, color="tab:green")
        plt.title(f"Monthly offences: {b}")
        plt.xlabel("Month")
        plt.ylabel("Offences")
        plt.grid(True)
        save_fig(plt, f"Monthly_offences_{b.replace(' ', '_')}")

        # ts and decomposition
        ts_b = sub_b.set_index("year_month")["borough_month_total"].asfreq("MS")
        try:
            dec_b = sm.tsa.seasonal_decompose(ts_b, model="additive", period=12)
            fig = dec_b.plot()
            save_fig(fig, f"Seasonal_decomposition_{b.replace(' ', '_')}")
        except Exception as e:
            print(f"Seasonal decomposition failed for borough {b}:", e)

        # summary stats and peaks/troughs
        plt.figure(figsize=(6, 3))
        stats_text = ts_b.describe().to_string()
        plt.axis("off")
        plt.text(0, 0.5, stats_text, fontsize=10, family="monospace")
        save_fig(plt, f"Time_series_summary_stats_{b.replace(' ', '_')}")

        top = ts_b.nlargest(5)
        bot = ts_b.nsmallest(5)
        top.to_csv(os.path.join(OUTPUT_FIG_DIR, f"top5_peaks_{b.replace(' ', '_')}.csv"))
        bot.to_csv(os.path.join(OUTPUT_FIG_DIR, f"bottom5_troughs_{b.replace(' ', '_')}.csv"))

        # ADF test
        try:
            adf_res = adfuller(ts_b.dropna(), autolag="AIC")
            adf_text = (
                f"ADF statistic: {adf_res[0]:.4f}\n"
                f"p-value: {adf_res[1]:.4f}\n"
                f"Used lags: {adf_res[2]}\n"
                f"Number of obs: {adf_res[3]}\n"
            )
            print(f"ADF for {b}:\n", adf_text)
            with open(os.path.join(OUTPUT_FIG_DIR, f"ADF_{b.replace(' ', '_')}.txt"), "w") as f:
                f.write(adf_text)
        except Exception as e:
            print(f"ADF test failed for borough {b}:", e)

    print("Temporal analysis complete. Figures and CSVs saved to:", OUTPUT_FIG_DIR)

# -----------------------------
# Integrate save_fig into other plotting calls similarly
# -----------------------------
# Replace other plt.show() calls in your script with save_fig(plt, "Descriptive Title")
# and for statsmodels figures use the returned Figure object and save_fig(fig, "Title").


# -----------------------------
# 6. SPATIAL ANALYSIS (TABULAR)
# -----------------------------
def spatial_analysis(boro_tot: pd.DataFrame) -> None:
    # top/bottom by rate
    top_rate = boro_tot.sort_values("rate_per_10k", ascending=False).head(5)
    bottom_rate = boro_tot.sort_values("rate_per_10k", ascending=True).head(5)

    print("\n=== Top 5 boroughs by rate per 10,000 ===")
    print(top_rate[["borough", "total_count", "rate_per_10k"]])

    print("\n=== Bottom 5 boroughs by rate per 10,000 ===")
    print(bottom_rate[["borough", "total_count", "rate_per_10k"]])

    # top/bottom by counts
    top_counts = boro_tot.sort_values("total_count", ascending=False).head(5)
    bottom_counts = boro_tot.sort_values("total_count", ascending=True).head(5)

    print("\n=== Top 5 boroughs by total offences ===")
    print(top_counts[["borough", "total_count"]])

    print("\n=== Bottom 5 boroughs by total offences ===")
    print(bottom_counts[["borough", "total_count"]])

    # choropleth would require a GeoJSON/shape file; here we just note that
    print("\n(Choropleth maps can be generated by merging these rates with borough boundary geometries.)")

# -----------------------------
# 7. TREND SUMMARIES & DIAGNOSTICS
# -----------------------------
def linear_trend_for_category(cat_month: pd.DataFrame, category: str) -> None:
    sub = cat_month[cat_month["crime category"] == category].copy()
    sub = sub.sort_values("year_month")
    sub["t"] = np.arange(len(sub))  # simple time index

    y = sub["category_month_total"].values
    X = sm.add_constant(sub["t"].values)
    model = sm.OLS(y, X).fit()

    slope_per_step = model.params[1]
    # convert to slope per year (12 months)
    slope_per_year = slope_per_step * 12

    print(f"\n=== Linear trend for {category} ===")
    print("Slope per month:", slope_per_step)
    print("Slope per year:", slope_per_year)
    print(model.summary())

    # ADF test for stationarity
    adf_res = adfuller(y, autolag="AIC")
    print("\nADF statistic:", adf_res[0])
    print("p-value:", adf_res[1])

def trend_summaries(cat_month: pd.DataFrame) -> None:
    key_cats = ["THEFT", "VIOLENCE AGAINST THE PERSON", "KNIFE CRIME", "DOMESTIC ABUSE"]
    for cat in key_cats:
        linear_trend_for_category(cat_month, cat)

# -----------------------------
# 8. PREPARED INPUTS FOR LATER MODELLING
# -----------------------------
def prepare_modelling_inputs(cat_month: pd.DataFrame,
                             boro_month: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    # time series: wide category panel (one column per category)
    cat_wide = (
        cat_month.pivot(index="year_month", columns="crime category", values="category_month_total")
        .sort_index()
    )

    # borough‑level panel: one row per (month, borough)
    boro_panel = boro_month.copy().sort_values(["year_month", "borough"])

    # save if needed
    cat_wide.to_csv("ts_categories_panel.csv")
    boro_panel.to_csv("ts_borough_panel.csv", index=False)

    print("\n=== Prepared modelling inputs ===")
    print("ts_categories_panel.csv shape:", cat_wide.shape)
    print("ts_borough_panel.csv shape:", boro_panel.shape)

    return cat_wide, boro_panel

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    # p = argparse.ArgumentParser(description="Aggregate census Observation by LTLA to borough population")
    # p.add_argument("--census", required=True, help="Path to census CSV (must contain 'Lower tier local authorities' and 'Observation')")
    # p.add_argument("--output", required=False, help="Output CSV path (default borough_population.csv)")
    # args = p.parse_args()
    # main(args)
    # # 1. load & clean raw
    df_raw = load_and_clean_raw(RAW_CRIME_CSV)

    # # 2. aggregate
    # cat_month = build_monthly_category_totals(df_raw)
    # boro_month = build_monthly_borough_totals(df_raw)

    # (optional) overwrite existing monthly_category_totals.csv / monthly_borough_totals.csv
    cat_month = pd.read_csv(MONTHLY_CAT_CSV, parse_dates=["year_month"])
    boro_month = pd.read_csv(MONTHLY_BORO_CSV, parse_dates=["year_month"])

    
    
    # 3. data quality
    data_quality_summary(df_raw, cat_month, boro_month)

    # 4. counts & rates
        #aggregate census by borough
    pop_df = pd.read_csv(BOROUGH_POP_CSV)
    pop_df = load_census(BOROUGH_POP_CSV)
    cat_tot, boro_tot = counts_and_rates(cat_month, boro_month, pop_df)

    # 5. temporal analysis
    temporal_analysis(cat_month, boro_month)

    # 6. spatial analysis
    spatial_analysis(boro_tot)

    # 7. trend summaries & diagnostics
    trend_summaries(cat_month)

    # 8. prepared inputs
    prepare_modelling_inputs(cat_month, boro_month)
