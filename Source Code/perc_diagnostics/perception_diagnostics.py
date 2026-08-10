import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import seasonal_decompose

# -------------------------
# USER SETTINGS
# -------------------------
INPUT_CSV = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Data_Visuals\Scrollytelling_draft\data\MOPAC_FULL_LONG_Public_Perception.csv"   # <-- replace with your file
OUTPUT_DIR = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Data_Visuals\Scrollytelling_draft\data\perc_diagnostics"
os.makedirs(OUTPUT_DIR, exist_ok=True)

PLOTS_DIR = os.path.join(OUTPUT_DIR, "plots")
INDIV_PLOTS_DIR = os.path.join(PLOTS_DIR, "borough_plots")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)
os.makedirs(INDIV_PLOTS_DIR, exist_ok=True)

DIAGNOSTICS_CSV = os.path.join(OUTPUT_DIR, "perc_diagnostics.csv")

# -------------------------
# Load and prepare data
# -------------------------
df = pd.read_csv(INPUT_CSV, dtype=str)
df.columns = [c.strip() for c in df.columns]

required = {"date", "quarter", "borough", "metric", "metric_value"}
missing = required - set(df.columns)
if missing:
    raise ValueError(f"Input file missing required columns: {missing}")

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])
df["metric_value"] = pd.to_numeric(df["metric_value"], errors="coerce")

df["quarter"] = df["quarter"].astype(str).str.strip()
df["borough"] = df["borough"].astype(str).str.strip()
df["metric"] = df["metric"].astype(str).str.strip()

# Aggregate duplicates (date, quarter, borough, metric) by mean
df = (
    df.groupby(["date", "quarter", "borough", "metric"], dropna=False, as_index=False)["metric_value"]
      .mean()
)

# -------------------------
# Helper: build quarter index (QS-APR fallback)
# -------------------------
def build_quarter_index(min_date, max_date, observed_dates):
    idx = pd.date_range(start=min_date, end=max_date, freq="QS-APR")
    if not set(observed_dates).issubset(set(idx)):
        idx = pd.to_datetime(sorted(pd.Series(observed_dates).unique()))
    return idx

# -------------------------
# Diagnostics accumulation
# -------------------------
rows = []
metrics = sorted(df["metric"].unique())

for metric in metrics:
    df_m = df[df["metric"] == metric].copy()
    if df_m.empty:
        continue

    pivot = df_m.pivot(index="date", columns="borough", values="metric_value")
    pivot = pivot[~pivot.index.duplicated(keep="first")]

    min_date = pivot.index.min()
    max_date = pivot.index.max()
    full_idx = build_quarter_index(min_date, max_date, pivot.index)
    pivot = pivot.reindex(full_idx)

    borough_count = pivot.count(axis=1)
    heterogeneity = pivot.var(axis=1, ddof=0)
    london_mean = pivot.mean(axis=1)

    series = london_mean.copy()
    if series.dropna().shape[0] >= 8:
        try:
            decomposition = seasonal_decompose(series, model="additive", period=4, extrapolate_trend="freq")
            trend = decomposition.trend
            seasonal = decomposition.seasonal
            resid = decomposition.resid
        except Exception:
            trend = pd.Series(index=series.index, data=np.nan)
            seasonal = pd.Series(index=series.index, data=np.nan)
            resid = pd.Series(index=series.index, data=np.nan)
    else:
        trend = pd.Series(index=series.index, data=np.nan)
        seasonal = pd.Series(index=series.index, data=np.nan)
        resid = pd.Series(index=series.index, data=np.nan)

    # Build diagnostics rows: one row per quarter × metric × borough
    for dt in series.index:
        q_label = ""
        qrows = df_m[df_m["date"] == dt]
        if not qrows.empty:
            q_label = qrows["quarter"].iloc[0]

        london_val = float(series.loc[dt]) if pd.notna(series.loc[dt]) else np.nan
        trend_val = float(trend.loc[dt]) if pd.notna(trend.loc[dt]) else np.nan
        seasonal_val = float(seasonal.loc[dt]) if pd.notna(seasonal.loc[dt]) else np.nan
        resid_val = float(resid.loc[dt]) if pd.notna(resid.loc[dt]) else np.nan
        hetero_val = float(heterogeneity.loc[dt]) if pd.notna(heterogeneity.loc[dt]) else np.nan
        bcount = int(borough_count.loc[dt]) if pd.notna(borough_count.loc[dt]) else 0

        for borough in pivot.columns:
            borough_val = pivot.loc[dt, borough] if dt in pivot.index else np.nan
            borough_val = float(borough_val) if pd.notna(borough_val) else np.nan

            borough_deviation = borough_val - london_val if (pd.notna(borough_val) and pd.notna(london_val)) else np.nan
            borough_residual = (borough_val - (trend_val + seasonal_val)) if (pd.notna(borough_val) and pd.notna(trend_val) and pd.notna(seasonal_val)) else np.nan

            rows.append({
                "date": pd.to_datetime(dt).strftime("%Y-%m-%d"),
                "quarter": q_label,
                "metric": metric,
                "borough": borough,
                "borough_value": borough_val,
                "london_mean": london_val,
                "trend": trend_val,
                "seasonal": seasonal_val,
                "residual": resid_val,
                "borough_deviation": borough_deviation,
                "borough_residual": borough_residual,
                "heterogeneity": hetero_val,
                "borough_count": bcount
            })

    # -------------------------
    # Overall decomposition plot (title includes metric)
    # -------------------------
    plt.figure(figsize=(12, 7))
    x = series.index
    plt.plot(x, series.values, label="London mean", color="black", marker="o")
    plt.plot(x, trend.values, label="Trend", color="tab:blue", linewidth=2)
    plt.plot(x, seasonal.values, label="Seasonal", color="tab:green", linestyle="--")
    plt.plot(x, resid.values, label="Residual", color="tab:red", linestyle=":")
    plt.title(f"Overall seasonal decomposition — Metric: {metric}")
    plt.xlabel("Date")
    plt.ylabel("Metric value")
    plt.legend()
    plt.grid(alpha=0.2)
    plt.tight_layout()
    safe_metric = "".join(c if c.isalnum() or c in " _-" else "_" for c in metric)[:120]
    overall_png = os.path.join(PLOTS_DIR, f"{safe_metric}_overall_decomposition.png")
    plt.savefig(overall_png, dpi=150)
    plt.close()

    # -------------------------
    # Borough grid: each subplot title includes "Borough — Metric"
    # -------------------------
    boroughs = list(pivot.columns)
    n = len(boroughs)
    cols = 6
    rows_grid = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows_grid, cols, figsize=(cols * 3.2, rows_grid * 2.6), sharex=True, sharey=True)
    axes = axes.flatten()

    for i, b in enumerate(boroughs):
        ax = axes[i]
        series_b = pivot[b]
        ax.plot(series_b.index, series_b.values, label=b, color="tab:gray", marker="o", markersize=3)
        if not trend.isna().all():
            ax.plot(trend.index, trend.values, label="London trend", color="tab:blue", linewidth=1.2)
        ax.set_title(f"{b} — {metric}", fontsize=8)
        ax.tick_params(axis='x', labelrotation=45, labelsize=7)
        ax.tick_params(axis='y', labelsize=7)

        # Save individual borough plot (clear title with borough + metric)
        fig_b, ax_b = plt.subplots(figsize=(6, 3.5))
        ax_b.plot(series_b.index, series_b.values, label=b, color="tab:gray", marker="o")
        if not trend.isna().all():
            ax_b.plot(trend.index, trend.values, label="London trend", color="tab:blue", linewidth=1.5)
        ax_b.set_title(f"{b} — Metric: {metric}")
        ax_b.set_xlabel("Date")
        ax_b.set_ylabel("Metric value")
        ax_b.legend()
        ax_b.grid(alpha=0.2)
        safe_b = "".join(c if c.isalnum() or c in " _-" else "_" for c in b)[:80]
        indiv_path = os.path.join(INDIV_PLOTS_DIR, f"{safe_metric}__{safe_b}_timeseries.png")
        fig_b.tight_layout()
        fig_b.savefig(indiv_path, dpi=150)
        plt.close(fig_b)

    for j in range(n, len(axes)):
        fig.delaxes(axes[j])

    fig.suptitle(f"Borough time series — Metric: {metric}", fontsize=12)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    boroughs_png = os.path.join(PLOTS_DIR, f"{safe_metric}_boroughs_timeseries_grid.png")
    fig.savefig(boroughs_png, dpi=150)
    plt.close(fig)
    print(f"Saved plots for metric '{metric}': overall -> {overall_png}, borough grid -> {boroughs_png}, individual boroughs -> {INDIV_PLOTS_DIR}")

# -------------------------
# Save diagnostics CSV (one row per quarter × metric × borough)
# -------------------------
diagnostics_df = pd.DataFrame(rows)
cols_out = [
    "date", "quarter", "metric", "borough", "borough_value",
    "london_mean", "trend", "seasonal", "residual",
    "borough_deviation", "borough_residual",
    "heterogeneity", "borough_count"
]
diagnostics_df = diagnostics_df[cols_out]
diagnostics_df.to_csv(DIAGNOSTICS_CSV, index=False, float_format="%.6g")
print(f"Saved diagnostics CSV to: {DIAGNOSTICS_CSV}")