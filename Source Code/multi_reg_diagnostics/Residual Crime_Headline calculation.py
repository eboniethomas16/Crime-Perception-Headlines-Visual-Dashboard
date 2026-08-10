# USED IN DISSERTATION
# two‑way residual that measures actual perception percent − predicted perception percent,
# where the prediction is a model that uses both crime offence counts and headline counts as predictors.

# Perception is a proportion (0–100%).
# Model it on the logit scale so predictions stay in (0,1) and residuals are interpretable after back‑transform.
# -------------------------------------------------------------------------
# TWO‑WAY PERCEPTION RESIDUAL
# -------------------------------------------------------------------------
# This section computes ONE two‑way residual per crime_type per quarter
# for EACH perception metric found in the raw perception dataset.

import os
import re
import ast
import pandas as pd
import numpy as np
import statsmodels.api as sm
from scipy.special import logit, expit
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import OLSInfluence
from statsmodels.stats.stattools import durbin_watson
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------------------------------------------
# 1. INPUT PATHS
# ---------------------------------------------------------
#paths must link to the monthly crime dataset (aggregated by month), 
# the list of all RAW GDELT files (to read headline crime types and volumes), 
# and the perception file for the full list of MOPAC perception data

crime_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Data_Visuals\Scrollytelling_draft\data\crime_types_monthly.csv"
headline_folder = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\GDELT_pipeline\data\combined_datasets\Updated Monthly Filtered Datasets\CLEANED FILTERED datasets"
perception_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Data_Visuals\Scrollytelling_draft\data\MOPAC_FULL_LONG_Public_Perception.csv"

output_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Data_Visuals\Scrollytelling_draft\data\multi_reg_diagnostics"
os.makedirs(output_path, exist_ok=True)
crime_type_output = os.path.join(output_path, "crime_type_residuals_monthly.csv")
aggregated_output = os.path.join(output_path, "crime_type_aggregated_residuals_monthly.csv")

# Minimum quarters required to fit the 3-parameter model (const + crime + headline).
# 3 obs would give 0 residual degrees of freedom (a perfect/degenerate fit), which
# breaks Cook's D / leverage / Durbin-Watson / Breusch-Pagan. Require a few spare df.
MIN_OBS_PER_FIT = 6

# Cutoff applied to every raw monthly/quarterly input before aggregation.
CUTOFF = pd.Timestamp("2017-04-01")

# -------------------------
# Load perception (quarterly) and identify metrics
# -------------------------
percep = pd.read_csv(perception_path, low_memory=False)
percep["date"] = pd.to_datetime(percep["date"], errors="coerce")
percep = percep.dropna(subset=["date", "metric", "metric_value"]).copy()
percep["metric"] = percep["metric"].astype(str).str.strip()

# Filter to dates on/after the cutoff
percep = percep[percep["date"] >= CUTOFF].reset_index(drop=True)

metrics = percep["metric"].unique().tolist()
if not metrics:
    raise SystemExit("No perception metrics found in perception file on/after 2017-04-01.")

# -------------------------
# Load crime monthly and aggregate to quarter
# -------------------------
crime_df = pd.read_csv(crime_path, low_memory=False)
crime_df["date"] = pd.to_datetime(crime_df["date"], errors="coerce")
crime_df = crime_df.dropna(subset=["date"])

# Filter to months on/after the cutoff
crime_df = crime_df[crime_df["date"] >= CUTOFF].reset_index(drop=True)

crime_df["crime_type"] = crime_df["crime_type"].astype(str).str.strip()
crime_df["quarter_period"] = crime_df["date"].dt.to_period("Q").dt.to_timestamp()

quarterly_crime = (
    crime_df.groupby(["crime_type", "quarter_period"])["crime_count"]
    .sum()
    .reset_index()
)

# -------------------------
# Load headlines, dedupe, aggregate to quarter
# -------------------------
headline_files = [f for f in os.listdir(headline_folder) if f.lower().endswith(".csv")]
headline_dfs = []
for file in headline_files:
    df_temp = pd.read_csv(os.path.join(headline_folder, file), low_memory=False)
    required = {"headline", "V2SOURCECOMMONNAME", "date", "crime_type"}
    if required.issubset(df_temp.columns):
        headline_dfs.append(df_temp)

if not headline_dfs:
    raise SystemExit("No headline files with required columns found in headline_folder.")

head = pd.concat(headline_dfs, ignore_index=True)
head["date"] = pd.to_datetime(head["date"], errors="coerce")
head = head.dropna(subset=["date"])

# Filter to months on/after the cutoff
head = head[head["date"] >= CUTOFF].reset_index(drop=True)

head = head[head["crime_type"].fillna("").str.strip().str.upper() != "UNKNOWN"]
head["crime_type"] = head["crime_type"].astype(str).str.strip()
head = head.drop_duplicates(subset=["crime_type", "headline", "V2SOURCECOMMONNAME"])
head["quarter_period"] = head["date"].dt.to_period("Q").dt.to_timestamp()

quarterly_headlines = (
    head.groupby(["crime_type", "quarter_period"])["headline"]
    .nunique()
    .reset_index(name="headline_count")
)


def _fmt_q(q):
    try:
        return pd.to_datetime(q).strftime("%Y%m%d")
    except Exception:
        try:
            return pd.Timestamp(q).strftime("%Y%m%d")
        except Exception:
            return str(q)


# ------------------ Diagnostics helper for multivariate OLS ------------------
def run_multivar_diagnostics(ols_res, X_df, y_arr, metric, crime_type, quarter_range=None, diag_dir=None,
                              predicted_pct=None, residual_pct=None):
    
    # ols_res: fitted statsmodels OLS result
    # X_df: pandas DataFrame used as design matrix
    # y_arr: numpy array of observed response
    # metric: metric name string
    # crime_type: crime_type string
    # quarter_range:(e.g. "20140101-20161231" or "2014Q1-2016Q4")
    # diag_dir: 
    # predicted_pct: 
    # residual_pct: 

    # Returns: dict of diagnostics (serializable) with 'diag_plot' path when plotting succeeds
   
    out = {"metric": metric, "crime_type": crime_type}
    try:
        params = ols_res.params
        pvalues = ols_res.pvalues
        rsq = float(ols_res.rsquared)
        rsq_adj = float(ols_res.rsquared_adj)
    except Exception:
        params = None
        pvalues = None
        rsq = None
        rsq_adj = None

    # robust HC3
    try:
        res_hc3 = ols_res.get_robustcov_results(cov_type="HC3")
        hc3_params = res_hc3.params.tolist()
        hc3_bse = res_hc3.bse.tolist()
        hc3_pvalues = res_hc3.pvalues.tolist()
    except Exception:
        hc3_params = None
        hc3_bse = None
        hc3_pvalues = None

    # Breusch-Pagan for heteroskedasticity (logit-scale fit diagnostics)
    try:
        bp_test = het_breuschpagan(ols_res.resid, ols_res.model.exog)
        bp = {"lm_stat": float(bp_test[0]), "lm_pvalue": float(bp_test[1]),
              "f_stat": float(bp_test[2]), "f_pvalue": float(bp_test[3])}
    except Exception:
        bp = None

    # Durbin-Watson
    try:
        dw = float(durbin_watson(ols_res.resid))
    except Exception:
        dw = None

    # Influence measures
    try:
        infl = OLSInfluence(ols_res)
        cooks_d = infl.cooks_distance[0].tolist()
        leverage = infl.hat_matrix_diag.tolist()
    except Exception:
        cooks_d = None
        leverage = None

    # Normality and moments
    try:
        shapiro_p = float(stats.shapiro(ols_res.resid)[1]) if len(ols_res.resid) >= 3 else np.nan
    except Exception:
        shapiro_p = None
    try:
        skewness = float(stats.skew(ols_res.resid))
        kurtosis = float(stats.kurtosis(ols_res.resid))
    except Exception:
        skewness = None
        kurtosis = None

    # Save a quick per-fit diagnostic plot (with title)
    plot_path = None
    try:
        fig, axes = plt.subplots(2, 2, figsize=(10, 8))

        # Observed vs Fitted
        fitted = ols_res.fittedvalues
        axes[0, 0].scatter(fitted, y_arr, s=30, alpha=0.8)
        axes[0, 0].plot([fitted.min(), fitted.max()], [fitted.min(), fitted.max()], color="C1", lw=1)
        axes[0, 0].set_title("Observed vs Fitted (logit scale)")
        axes[0, 0].set_xlabel("Fitted")
        axes[0, 0].set_ylabel("Observed")

        # Residuals vs Fitted
        axes[0, 1].scatter(fitted, ols_res.resid, s=30, alpha=0.8)
        axes[0, 1].axhline(0, color="k", lw=0.8)
        axes[0, 1].set_title("Residuals vs Fitted (logit scale)")
        axes[0, 1].set_xlabel("Fitted")
        axes[0, 1].set_ylabel("Residuals")

        # QQ plot
        sm.qqplot(ols_res.resid, line="45", ax=axes[1, 0])
        axes[1, 0].set_title("QQ plot of residuals")

        # Cook's distance
        if cooks_d is not None:
            axes[1, 1].stem(np.arange(len(cooks_d)), cooks_d, markerfmt="C1o", basefmt="k-")
        axes[1, 1].set_title("Cook's distance")
        axes[1, 1].set_xlabel("Observation")
        axes[1, 1].set_ylabel("Cook's D")

        # Build title text and add as figure suptitle
        title_parts = []
        if metric:
            title_parts.append(str(metric))
        if crime_type:
            title_parts.append(str(crime_type))
        if quarter_range:
            title_parts.append(str(quarter_range))
        full_title = "  —  ".join(title_parts)
        if len(full_title) > 120:
            full_title = full_title[:117] + "..."
        fig.suptitle(full_title, fontsize=12, fontweight="bold", y=0.99)

        plt.tight_layout(rect=[0, 0, 1, 0.96])  # leaves space for subtitle

        # build safe filename components
        safe_metric = re.sub(r"[^\w\-]", "_", str(metric))[:40] if metric else "metric"
        safe_crime = re.sub(r"[^\w\-]", "_", str(crime_type))[:60] if crime_type else "crime"
        safe_q = re.sub(r"[^\w\-]", "_", str(quarter_range))[:40] if quarter_range else "range"

        # determine directory
        target_dir = diag_dir if diag_dir else globals().get("DIAG_DIR", ".")
        os.makedirs(target_dir, exist_ok=True)

        fname = f"diag_{safe_metric}_{safe_crime}_{safe_q}.png"
        plot_path = os.path.join(target_dir, fname)
        fig.savefig(plot_path, dpi=150)
        plt.close(fig)
    except Exception:
        plot_path = None

    out.update({
        "params": params.tolist() if params is not None else None,
        "pvalues": pvalues.tolist() if pvalues is not None else None,
        "rsquared": rsq,
        "rsquared_adj": rsq_adj,
        "hc3_params": hc3_params,
        "hc3_bse": hc3_bse,
        "hc3_pvalues": hc3_pvalues,
        "breusch_pagan": bp,
        "durbin_watson": dw,
        "shapiro_p": shapiro_p,
        "skew": skewness,
        "kurtosis": kurtosis,
        "cooks_d": cooks_d,
        "leverage": leverage,
        # percentage-scale predicted/residual arrays, used by the downstream
        # Residual Diagnostics Engine (section 3 below) to build the 2x2 PNGs
        "predicted": predicted_pct.tolist() if predicted_pct is not None else None,
        "residuals": residual_pct.tolist() if residual_pct is not None else None,
        "diag_plot": plot_path
    })

    return out


# ensure diagnostics dir exists and collectors are initialized
DIAG_DIR = os.path.join(output_path, "diagnostics_multivar")
os.makedirs(DIAG_DIR, exist_ok=True)

diagnostics_list = []
all_rows = []
agg_rows = []

# -------------------------
# For each metric compute citywide quarterly perception and fit per-crime-type models
# -------------------------
for metric in metrics:
    # prepare citywide quarterly perception for this metric
    mdf = percep[percep["metric"] == metric].copy()
    if mdf.empty:
        continue

    city_perception = (
        mdf.groupby("date")["metric_value"]
        .mean()
        .reset_index()
        .rename(columns={"metric_value": "perception"})
    )

    # convert to 0-1 if values are 0-100
    if city_perception["perception"].max() > 1.1:
        city_perception["perception"] = city_perception["perception"] / 100.0

    city_perception["quarter_period"] = city_perception["date"].dt.to_period("Q").dt.to_timestamp()

    # Merge quarterly crime + headlines
    merged = pd.merge(
        quarterly_crime,
        quarterly_headlines,
        on=["crime_type", "quarter_period"],
        how="left"
    ).sort_values(["crime_type", "quarter_period"]).reset_index(drop=True)

    merged["headline_count"] = merged["headline_count"].fillna(0).astype(int)

    # Merge perception for this metric
    merged = merged.merge(
        city_perception[["quarter_period", "perception"]],
        on="quarter_period",
        how="left"
    )

    # Drop rows without perception
    merged = merged.dropna(subset=["perception"]).reset_index(drop=True)
    if merged.empty:
        continue

    # per-metric collectors
    rows = []

    # iterate crime types once, fit model, collect residual rows and diagnostics
    for crime_type, group in merged.groupby("crime_type"):
        g = group.sort_values("quarter_period").reset_index(drop=True)
        if len(g) < MIN_OBS_PER_FIT:
            continue

        # response on logit scale
        try:
            y_logit = logit(g["perception"].values)
        except Exception:
            continue
        if not np.all(np.isfinite(y_logit)):
            # perception exactly 0% or 100% makes logit +/-inf; skip this fit
            continue

        # design matrix (including const)
        X = pd.DataFrame({
            "const": 1.0,
            "crime_count_log": np.log1p(g["crime_count"].astype(float).fillna(0.0)),
            "headline_count_log": np.log1p(g["headline_count"].astype(float).fillna(0.0))
        })

        # fit OLS
        try:
            ols = sm.OLS(y_logit, X).fit()
        except Exception:
            continue

        # predictions and residuals, back-transformed to a percentage scale
        pred_logit = ols.predict(X)
        pred_prob = expit(pred_logit)

        resid_pct = (g["perception"].values - pred_prob) * 100.0
        resid_z = (resid_pct - np.nanmean(resid_pct)) / (np.nanstd(resid_pct, ddof=0) + 1e-9)

        # quarter_range (short YYYYMMDD-YYYYMMDD) for filename/title
        start_q = g['quarter_period'].min()
        end_q = g['quarter_period'].max()
        quarter_range = f"{_fmt_q(start_q)}-{_fmt_q(end_q)}"

        # call diagnostics and save the per-fit supplementary plot
        diag = run_multivar_diagnostics(
            ols_res=ols,
            X_df=X,
            y_arr=y_logit,
            metric=metric,
            crime_type=crime_type,
            quarter_range=quarter_range,
            diag_dir=DIAG_DIR,
            predicted_pct=pred_prob * 100.0,
            residual_pct=resid_pct
        )
        diagnostics_list.append(diag)

        out = pd.DataFrame({
            "metric": metric,
            "crime_type": crime_type,
            "date": g["quarter_period"],
            "residual": resid_pct,
            "residual_z": resid_z,
            "perception_obs_pct": g["perception"].values * 100.0,
            "perception_pred_pct": pred_prob * 100.0,
            "headline_count": g["headline_count"].values,
            "crime_count": g["crime_count"].values
        })

        rows.append(out)

    # if any rows for this metric, append to global lists and compute aggregated residuals
    if rows:
        metric_df = pd.concat(rows, ignore_index=True)
        all_rows.append(metric_df)

        agg = metric_df.groupby("date")["residual"].mean().reset_index()
        agg["metric"] = metric
        agg_rows.append(agg)

# after loop: save diagnostics summary (per crime_type x metric fit)
if diagnostics_list:
    try:
        diag_df = pd.json_normalize(diagnostics_list)
        diag_csv = os.path.join(DIAG_DIR, "multivar_diagnostics_summary.csv")
        diag_df.to_csv(diag_csv, index=False)
        print("Saved multivariate diagnostics summary to", diag_csv)
    except Exception as e:
        print("Failed to save diagnostics summary:", e)
else:
    print("No diagnostics were produced — check MIN_OBS_PER_FIT and data coverage.")

# combine and save residual outputs
if not all_rows:
    raise SystemExit("No metric produced any per-crime residuals. Check data coverage.")

crime_type_residuals = pd.concat(all_rows, ignore_index=True)

# format date column as quarter start like 10/1/2014
try:
    crime_type_residuals["date"] = crime_type_residuals["date"].dt.strftime("%-m/%-d/%Y")
except Exception:
    crime_type_residuals["date"] = crime_type_residuals["date"].dt.strftime("%m/%d/%Y")

aggregated = pd.concat(agg_rows, ignore_index=True)
try:
    aggregated["date"] = aggregated["date"].dt.strftime("%-m/%-d/%Y")
except Exception:
    aggregated["date"] = aggregated["date"].dt.strftime("%m/%d/%Y")

# Ensure columns order and save
cols_order = ["date", "metric", "crime_type", "residual", "residual_z",
              "perception_obs_pct", "perception_pred_pct", "headline_count", "crime_count"]
crime_type_residuals = crime_type_residuals[cols_order]
crime_type_residuals.to_csv(crime_type_output, index=False)
aggregated.to_csv(aggregated_output, index=False)

print("Per-crime quarterly perception residuals created successfully for metrics:", metrics)
print(" - Crime-type residuals:", crime_type_output)
print(" - Aggregated residuals:", aggregated_output)

# =====================================================================
# 3. Residual Diagnostics Engine (PNG outputs + diagnostics CSV)
#    — per crime_type x metric, mirrors the borough-level engine.
# =====================================================================
DIAG_SUMMARY = os.path.join(DIAG_DIR, "multivar_diagnostics_summary.csv")
OUT_PNG_DIR = os.path.join(output_path, "residual_diagnostics_pngs")
OUT_CRIME_DIR = os.path.join(OUT_PNG_DIR, "crime_type")
OUT_AGG_DIR = os.path.join(output_path, "aggregated")
OUT_DIAG_CSV = os.path.join(output_path, "residuals_diagnostics_per_crime_type_metric.csv")

os.makedirs(OUT_CRIME_DIR, exist_ok=True)
os.makedirs(OUT_AGG_DIR, exist_ok=True)

if not os.path.exists(DIAG_SUMMARY):
    raise FileNotFoundError(f"Diagnostics summary not found: {DIAG_SUMMARY}")

diag = pd.read_csv(DIAG_SUMMARY)

# Convert stringified lists back to Python lists
for col in ["predicted", "residuals", "cooks_d", "leverage"]:
    if col in diag.columns:
        diag[col] = diag[col].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# -------------------------
# Quarter labels per (crime_type, metric), taken from the long-format
# residual CSV so the x-axis on each time-series plot shows real quarters.
# -------------------------
quarter_labels_map = {}
if os.path.exists(crime_type_output):
    ctw = pd.read_csv(crime_type_output, dtype=str)
    for (ct, met), g in ctw.groupby(["crime_type", "metric"]):
        quarter_labels_map[(ct, met)] = g["date"].tolist()


# -------------------------
# Helper: safe list extraction from a (possibly stringified) cell
# -------------------------
def to_array(x):
    if x is None:
        return np.array([])
    if isinstance(x, (list, tuple, np.ndarray)):
        return np.array(x, dtype=float)
    try:
        return np.array(ast.literal_eval(x), dtype=float)
    except Exception:
        return np.array([])


def _cell_has_value(row, col):
    # Safe presence check. row.get(col) can be a scalar (NaN/float) OR a
    # list/array (already-parsed cooks_d / leverage values). Calling
    # pd.notna() directly on a list/array returns an array of booleans,
    # not a single bool, which breaks a plain `if`/ternary check with
    # "ValueError: truth value of an array is ambiguous" — so list/array
    # cells are checked by length instead of routed through pd.notna().
    if col not in row:
        return False
    val = row.get(col)
    if isinstance(val, (list, tuple, np.ndarray)):
        return len(val) > 0
    try:
        return bool(pd.notna(val))
    except (TypeError, ValueError):
        return False


diag_rows = []

# -------------------------
# Per-crime_type x metric combined PNGs
# -------------------------
for i, row in diag.iterrows():
    crime_type = row.get("crime_type", "UNKNOWN")
    metric = row.get("metric", "metric")
    predicted = to_array(row.get("predicted"))
    residuals = to_array(row.get("residuals"))
    cooks_d = to_array(row.get("cooks_d")) if _cell_has_value(row, "cooks_d") else None
    leverage = to_array(row.get("leverage")) if _cell_has_value(row, "leverage") else None

    # Skip if no residuals
    if residuals.size == 0:
        continue

    # Determine quarter labels
    quarters = quarter_labels_map.get((crime_type, metric))
    if quarters is None or len(quarters) != residuals.size:
        quarters = [f"Q{i+1}" for i in range(residuals.size)]

    # -------------------------
    # Statistical tests
    # -------------------------
    n_obs = residuals.size
    mean_resid = float(np.nanmean(residuals))
    # t-test for zero-mean errors
    try:
        t_stat, t_p = stats.ttest_1samp(residuals[~np.isnan(residuals)], 0.0)
    except Exception:
        t_stat, t_p = np.nan, np.nan

    # Durbin-Watson for independence
    try:
        dw = float(durbin_watson(residuals))
    except Exception:
        dw = np.nan

    # Breusch-Pagan for heteroskedasticity: use predicted (fitted) as exog with constant
    bp_stat = bp_p = np.nan
    try:
        if predicted.size == residuals.size and predicted.size > 1:
            exog = sm.add_constant(predicted)
            bp_test = het_breuschpagan(residuals, exog)
            bp_stat, bp_p = float(bp_test[0]), float(bp_test[1])
        else:
            exog = sm.add_constant(np.arange(n_obs))
            bp_test = het_breuschpagan(residuals, exog)
            bp_stat, bp_p = float(bp_test[0]), float(bp_test[1])
    except Exception:
        bp_stat, bp_p = np.nan, np.nan

    # Shapiro normality test (for QQ annotation)
    try:
        shapiro_stat, shapiro_p = stats.shapiro(residuals) if n_obs >= 3 else (np.nan, np.nan)
    except Exception:
        shapiro_stat, shapiro_p = np.nan, np.nan

    # skew/kurtosis
    try:
        skew = float(stats.skew(residuals))
        kurt = float(stats.kurtosis(residuals))
    except Exception:
        skew, kurt = np.nan, np.nan

    # Cook's D and leverage maxima
    max_cook = float(np.nanmax(cooks_d)) if cooks_d is not None and cooks_d.size > 0 else np.nan
    max_leverage = float(np.nanmax(leverage)) if leverage is not None and leverage.size > 0 else np.nan

    # -------------------------
    # Build 2x2 figure
    # -------------------------
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    ax_ts, ax_rvf, ax_qq, ax_lev = axes.flatten()

    # Top-left: Residual time series (x = quarter labels)
    ax_ts.plot(quarters, residuals, marker="o", color="tab:red", linewidth=1.5)
    ax_ts.axhline(0, color="black", linestyle="--", linewidth=0.8)
    ax_ts.set_title("Residual Time Series")
    ax_ts.set_xlabel("Quarter")
    ax_ts.set_ylabel("Residual (perception pct pts)")
    ax_ts.tick_params(axis='x', rotation=45)
    ax_ts.annotate(f"Mean resid = {mean_resid:.4g}\n t={t_stat:.3g}, p={t_p:.3g}",
                   xy=(0.02, 0.95), xycoords='axes fraction', fontsize=9,
                   bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8),
                   verticalalignment='top')

    # Top-right: Residual vs Fitted
    ax_rvf.scatter(predicted, residuals, color="tab:blue", s=30, alpha=0.8)
    ax_rvf.axhline(0, color="black", linestyle="--", linewidth=0.8)
    ax_rvf.set_title("Residual vs Fitted")
    ax_rvf.set_xlabel("Fitted values (predicted perception %)")
    ax_rvf.set_ylabel("Residuals")
    ax_rvf.annotate(f"Durbin-Watson = {dw:.3g}\nBP stat={bp_stat:.3g}, p={bp_p:.3g}",
                    xy=(0.02, 0.95), xycoords='axes fraction', fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8),
                    verticalalignment='top')

    # Bottom-left: QQ plot
    sm.qqplot(residuals, line="45", ax=ax_qq)
    ax_qq.set_title("QQ Plot")
    ax_qq.annotate(f"Shapiro p = {shapiro_p:.3g}\nskew={skew:.3g}, kurt={kurt:.3g}",
                   xy=(0.02, 0.95), xycoords='axes fraction', fontsize=9,
                   bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8),
                   verticalalignment='top')

    # Bottom-right: Leverage (with Cook's D markers)
    if leverage is not None:
        ax_lev.stem(range(len(leverage)), leverage, basefmt="k-", markerfmt="C2o")
    ax_lev.set_title("Leverage (with Cook's D markers)")
    ax_lev.set_xlabel("Observation index")
    ax_lev.set_ylabel("Leverage")
    if cooks_d is not None and cooks_d.size > 0:
        cd = cooks_d
        top_idx = np.argsort(-cd)[:3] if cd.size >= 3 else np.argsort(-cd)
        for ti in top_idx:
            lev_val = leverage[ti] if leverage is not None and ti < leverage.size else 0
            ax_lev.plot(ti, lev_val, marker="o", color="red")
            ax_lev.annotate(f"CookD={cd[ti]:.3g}", xy=(ti, lev_val),
                            xytext=(5, 5), textcoords='offset points', fontsize=8)

    # suptitle and save
    fig.suptitle(f"{crime_type} — {metric} — Residual Diagnostics", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])

    safe_c = re.sub(r"[^\w\-]", "_", str(crime_type))[:80]
    safe_m = re.sub(r"[^\w\-]", "_", str(metric))[:80]
    out_file = os.path.join(OUT_CRIME_DIR, f"{safe_c}__{safe_m}__residuals_diagnostics.png")
    fig.savefig(out_file, dpi=150)
    plt.close(fig)

    # -------------------------
    # Append diagnostics row
    # -------------------------
    diag_rows.append({
        "crime_type": crime_type,
        "metric": metric,
        "n_obs": int(n_obs),
        "mean_residual": mean_resid,
        "t_stat_mean": float(t_stat) if not np.isnan(t_stat) else np.nan,
        "t_p_mean": float(t_p) if not np.isnan(t_p) else np.nan,
        "durbin_watson": dw,
        "bp_stat": bp_stat,
        "bp_p": bp_p,
        "shapiro_p": shapiro_p,
        "skew": skew,
        "kurtosis": kurt,
        "max_cooks_d": max_cook,
        "max_leverage": max_leverage,
        "png_path": out_file
    })

# -------------------------
# Aggregated diagnostics across crime types (per metric, per quarter)
# -------------------------
agg_diag_rows = []
if os.path.exists(crime_type_output):
    cw = pd.read_csv(crime_type_output, dtype=str)
    cw["residual"] = pd.to_numeric(cw["residual"], errors="coerce")
    cw["date_dt"] = pd.to_datetime(cw["date"], errors="coerce")
    cw = cw[cw["date_dt"] >= CUTOFF]

    for metric_name, g in cw.groupby("metric"):
        g2 = g.sort_values("date_dt")
        agg_series = g2.groupby("date_dt")["residual"].mean().reset_index()
        agg_series = agg_series.dropna().sort_values("date_dt")
        if agg_series.empty:
            continue
        quarters = agg_series["date_dt"].dt.strftime("%-m/%-d/%Y").tolist()
        residuals = agg_series["residual"].values

        # tests on aggregated series
        n_obs = residuals.size
        mean_resid = float(np.nanmean(residuals))
        try:
            t_stat, t_p = stats.ttest_1samp(residuals[~np.isnan(residuals)], 0.0)
        except Exception:
            t_stat, t_p = np.nan, np.nan
        try:
            dw = float(durbin_watson(residuals))
        except Exception:
            dw = np.nan
        # BP using time index as exog
        try:
            exog = sm.add_constant(np.arange(n_obs))
            bp_test = het_breuschpagan(residuals, exog)
            bp_stat, bp_p = float(bp_test[0]), float(bp_test[1])
        except Exception:
            bp_stat, bp_p = np.nan, np.nan
        try:
            shapiro_stat, shapiro_p = stats.shapiro(residuals) if n_obs >= 3 else (np.nan, np.nan)
        except Exception:
            shapiro_stat, shapiro_p = np.nan, np.nan
        try:
            skew = float(stats.skew(residuals))
            kurt = float(stats.kurtosis(residuals))
        except Exception:
            skew, kurt = np.nan, np.nan

        # Plot aggregated diagnostics (2x2)
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        ax_ts, ax_rvf, ax_qq, ax_var = axes.flatten()

        ax_ts.plot(quarters, residuals, marker="o", color="black")
        ax_ts.axhline(0, color="gray", linestyle="--")
        ax_ts.set_title(f"Aggregated mean residuals — {metric_name}")
        ax_ts.set_xlabel("Quarter")
        ax_ts.set_ylabel("Mean residual (pct pts)")
        ax_ts.tick_params(axis='x', rotation=45)
        ax_ts.annotate(f"Mean resid={mean_resid:.4g}\n t={t_stat:.3g}, p={t_p:.3g}",
                       xy=(0.02, 0.95), xycoords='axes fraction', fontsize=9,
                       bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8),
                       verticalalignment='top')

        # Residual vs time index (fitted not meaningful here)
        ax_rvf.scatter(np.arange(n_obs), residuals, color="tab:blue")
        ax_rvf.axhline(0, color="black", linestyle="--")
        ax_rvf.set_title("Residuals vs Time Index")
        ax_rvf.set_xlabel("Time index")
        ax_rvf.set_ylabel("Residuals")
        ax_rvf.annotate(f"Durbin-Watson={dw:.3g}\nBP p={bp_p:.3g}",
                        xy=(0.02, 0.95), xycoords='axes fraction', fontsize=9,
                        bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8),
                        verticalalignment='top')

        sm.qqplot(residuals, line="45", ax=ax_qq)
        ax_qq.set_title("QQ Plot")
        ax_qq.annotate(f"Shapiro p={shapiro_p:.3g}\nskew={skew:.3g}, kurt={kurt:.3g}",
                       xy=(0.02, 0.95), xycoords='axes fraction', fontsize=9,
                       bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8),
                       verticalalignment='top')

        # variance/heterogeneity across crime types for each quarter (plot)
        var_by_q = g2.groupby("date_dt")["residual"].var(ddof=0).reindex(agg_series["date_dt"]).values
        ax_var.plot(quarters, var_by_q, color="tab:purple", marker="o")
        ax_var.set_title("Residual variance across crime types (by quarter)")
        ax_var.set_xlabel("Quarter")
        ax_var.set_ylabel("Variance")
        ax_var.tick_params(axis='x', rotation=45)

        fig.suptitle(f"Aggregated Residual Diagnostics — {metric_name}", fontsize=14, fontweight="bold")
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])

        safe_metric = re.sub(r"[^\w\-]", "_", str(metric_name))[:80]
        out_file = os.path.join(OUT_AGG_DIR, f"aggregated__{safe_metric}__residuals_diagnostics.png")
        fig.savefig(out_file, dpi=150)
        plt.close(fig)

        agg_diag_rows.append({
            "metric": metric_name,
            "n_obs": int(n_obs),
            "mean_residual": mean_resid,
            "t_stat_mean": float(t_stat) if not np.isnan(t_stat) else np.nan,
            "t_p_mean": float(t_p) if not np.isnan(t_p) else np.nan,
            "durbin_watson": dw,
            "bp_stat": bp_stat,
            "bp_p": bp_p,
            "shapiro_p": shapiro_p,
            "skew": skew,
            "kurtosis": kurt,
            "png_path": out_file
        })

# -------------------------
# Save diagnostics CSV (per crime_type x metric + aggregated rows)
# -------------------------
diag_df_out = pd.DataFrame(diag_rows)
agg_df_out = pd.DataFrame(agg_diag_rows)

if not diag_df_out.empty:
    diag_df_out.to_csv(OUT_DIAG_CSV, index=False)
if not agg_df_out.empty:
    agg_df_out.to_csv(os.path.join(DIAG_DIR, "aggregated_residuals_diagnostics.csv"), index=False)

print("Saved per-crime-type PNGs to:", OUT_CRIME_DIR)
print("Saved aggregated PNGs to:", OUT_AGG_DIR)
print("Saved diagnostics CSV to:", OUT_DIAG_CSV)