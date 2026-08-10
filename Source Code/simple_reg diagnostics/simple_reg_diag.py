"""
Residual diagnostics for borough-level regression output.

Inputs:
    borough_residual_diagnostics_summary.csv
        Must contain: date, borough, metric, residual

Outputs:
    diagnostics_output/
        borough_plots/
            <borough>_<metric>_residual_timeseries.png
        aggregated/
            residual_aggregate_timeseries.png
            residual_aggregate_variance.png
            residual_distribution.png
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# -------------------------
# USER SETTINGS
# -------------------------
INPUT_CSV = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Data_Visuals\Scrollytelling_draft\data\simple_reg diagnostics\borough_residual_diagnostics_summary.csv"   # update path
OUTPUT_DIR = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Data_Visuals\Scrollytelling_draft\data\simple_reg diagnostics\residual_diagnostics_output"
BOROUGH_DIR = os.path.join(OUTPUT_DIR, "borough_plots")
AGG_DIR = os.path.join(OUTPUT_DIR, "aggregated")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(BOROUGH_DIR, exist_ok=True)
os.makedirs(AGG_DIR, exist_ok=True)

# -------------------------
# LOAD DATA
# -------------------------
df = pd.read_csv(INPUT_CSV)

# Ensure required columns exist
required = {"date", "borough", "metric", "residuals"}
missing = required - set(df.columns)
if missing:
    raise ValueError(f"Missing required columns: {missing}")

df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])

df = df.sort_values(["metric", "borough", "date"])

# -------------------------
# PROCESS EACH METRIC
# -------------------------
metrics = sorted(df["metric"].unique())

for metric in metrics:
    df_m = df[df["metric"] == metric].copy()

    boroughs = sorted(df_m["borough"].unique())

    for borough in boroughs:
        df_b = df_m[df_m["borough"] == borough].copy()

        if df_b.empty:
            continue

        # Rolling mean for smoothing
        df_b["rolling"] = df_b["residuals"].rolling(window=4, min_periods=1).mean()

        # -------------------------
        # Borough residual plot
        # -------------------------
        plt.figure(figsize=(10, 4))
        plt.plot(df_b["date"], df_b["residuals"], label="Residual", color="tab:red", marker="o")
        plt.plot(df_b["date"], df_b["rolling"], label="Rolling mean (4q)", color="tab:blue", linewidth=2)

        plt.axhline(0, color="black", linewidth=1, linestyle="--")

        plt.title(f"{borough} — Residuals for {metric}")
        plt.xlabel("Quarter")
        plt.ylabel("Residuals")
        plt.grid(alpha=0.3)
        plt.legend()

        safe_b = "".join(c if c.isalnum() or c in " _-" else "_" for c in borough)
        safe_m = "".join(c if c.isalnum() or c in " _-" else "_" for c in metric)

        out_path = os.path.join(BOROUGH_DIR, f"{safe_b}__{safe_m}_residual_timeseries.png")
        plt.tight_layout()
        plt.savefig(out_path, dpi=150)
        plt.close()

        print(f"Saved borough residual plot: {out_path}")

# -------------------------
# AGGREGATED ANALYSIS
# -------------------------

# Pivot: date × borough → residual
pivot = df.pivot(index="date", columns="borough", values="residuals").sort_index()

# Mean residual across boroughs
agg_mean = pivot.mean(axis=1)

# Variance (heterogeneity)
agg_var = pivot.var(axis=1, ddof=0)

# -------------------------
# Aggregated residual time series
# -------------------------
plt.figure(figsize=(12, 5))
plt.plot(agg_mean.index, agg_mean.values, label="Mean residual", color="black", linewidth=2)
plt.axhline(0, color="gray", linestyle="--")
plt.title("Aggregated Mean Residual Across Boroughs")
plt.xlabel("Quarter")
plt.ylabel("Mean Residual")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(AGG_DIR, "residual_aggregate_timeseries.png"), dpi=150)
plt.close()

# -------------------------
# Aggregated heterogeneity (variance)
# -------------------------
plt.figure(figsize=(12, 5))
plt.plot(agg_var.index, agg_var.values, label="Residual variance", color="tab:purple", linewidth=2)
plt.title("Residual Heterogeneity Across Boroughs")
plt.xlabel("Quarter")
plt.ylabel("Variance")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(AGG_DIR, "residual_aggregate_variance.png"), dpi=150)
plt.close()

# -------------------------
# Distribution plot (optional)
# -------------------------
plt.figure(figsize=(10, 5))
plt.boxplot(pivot.values, vert=True)
plt.title("Distribution of Borough Residuals (All Quarters)")
plt.ylabel("Residual")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(AGG_DIR, "residual_distribution.png"), dpi=150)
plt.close()

print("\nAll residual diagnostics complete.")
print(f"Outputs saved in: {OUTPUT_DIR}")
