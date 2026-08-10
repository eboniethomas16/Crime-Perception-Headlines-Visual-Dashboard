import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import os
import numpy as np
import pandas as pd
import re
import statsmodels.api as sm
import statsmodels.stats.api as sms
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import OLSInfluence
from statsmodels.stats.stattools import durbin_watson
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
# ---------------------------------------------------------
# File paths
# ---------------------------------------------------------
crime_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Data_Visuals\Scrollytelling_draft\data\crime_borough_monthly.csv"
perception_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Data_Visuals\Scrollytelling_draft\data\MOPAC_FULL_LONG_Public_Perception.csv"
output_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Data_Visuals\Scrollytelling_draft\data\simple_reg diagnostics"
census_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Visual Python Code\2021_census_by_sex.csv"
# diagnostics directory
DIAG_DIR = os.path.join(output_path, "diagnostics")
os.makedirs(DIAG_DIR, exist_ok=True)
# ---------------------------------------------------------
# 1. Load datasets
# ---------------------------------------------------------
crime_df = pd.read_csv(crime_path)
perception_df = pd.read_csv(perception_path)

# ---------------------------------------------------------
# 2. Convert dates
# ---------------------------------------------------------
crime_df['date'] = pd.to_datetime(crime_df['date'])
perception_df['date'] = pd.to_datetime(perception_df['date'])
cutoff = pd.Timestamp("2017-04-01")

crime_df = crime_df[crime_df["date"] >= cutoff].reset_index(drop=True)
perception_df = perception_df[perception_df["date"] >= cutoff].reset_index(drop=True)

print(f"Crime rows after cutoff: {len(crime_df)}")
print(f"Perception rows after cutoff: {len(perception_df)}")

# ---------------------------------------------------------
# 3. Build fiscal quarter → date mapping
# ---------------------------------------------------------
quarter_map = (
    perception_df[['quarter', 'date']]
    .drop_duplicates()
    .sort_values('date')
    .reset_index(drop=True)
)

quarter_map['date_str'] = quarter_map['date'].dt.strftime("%-m/%-d/%Y")

# ---------------------------------------------------------
# 4. Assign fiscal quarter to each crime date
# ---------------------------------------------------------
def assign_fiscal_quarter(crime_date):
    eligible = quarter_map[quarter_map['date'] <= crime_date]
    if len(eligible) == 0:
        return None
    return eligible.iloc[-1]['quarter']

crime_df['quarter'] = crime_df['date'].apply(assign_fiscal_quarter)

crime_df = crime_df.dropna(subset=['quarter'])

# ---------------------------------------------------------
# 4. Normalize crime counts per borough
# ---------------------------------------------------------

import re
import pandas as pd

def normalize_crime_by_population(
    quarterly_crime,
    census_path,
    borough_col='borough',
    crime_col='crime_count',
    census_code_col_hint=None,
    census_name_col_hint=None,
    out_pop_col='pop_2021',
    out_rate_col='crime_per_100k',
    fill_missing_pop_with=1
):
    """
    Merge 2021 census borough populations into quarterly_crime and compute crime per 100k.
    Returns: (quarterly_crime_with_pop_and_rate, pop_by_borough)
    
    Parameters
    - quarterly_crime: pd.DataFrame with at least borough_col and crime_col
    - census_path: path to census CSV (sample columns include LTLA code, LTLA name, Observation)
    - census_code_col_hint: optional substring to help identify LTLA code column in census file
    - census_name_col_hint: optional substring to help identify LTLA name column in census file
    - out_pop_col: name for population column added to quarterly_crime
    - out_rate_col: name for crime per 100k column added to quarterly_crime
    - fill_missing_pop_with: numeric fallback for missing population to avoid div0
    """
    # load census
    census = pd.read_csv(census_path, dtype=str)
    census.columns = [c.strip() for c in census.columns]

    # heuristically map census columns
    col_map = {}
    for c in census.columns:
        lc = c.lower()
        if census_code_col_hint and census_code_col_hint.lower() in lc:
            col_map[c] = 'ltla_code'
        elif census_name_col_hint and census_name_col_hint.lower() in lc:
            col_map[c] = 'ltla_name'
        elif 'lower tier' in lc and 'code' in lc:
            col_map[c] = 'ltla_code'
        elif 'lower tier' in lc and ('authorit' in lc or 'authority' in lc or 'local' in lc):
            col_map[c] = 'ltla_name'
        elif 'observation' in lc or 'population' in lc or 'value' in lc:
            col_map[c] = 'population'
        elif 'sex' in lc and 'code' in lc and '2' in lc:
            col_map[c] = 'sex_code'
    census = census.rename(columns=col_map)


    census['population'] = pd.to_numeric(census['population'], errors='coerce').fillna(0).astype(int)

    # aggregate male+female to borough total population if necessary
    group_cols = []
    if 'ltla_code' in census.columns:
        group_cols.append('ltla_code')
    if 'ltla_name' in census.columns:
        group_cols.append('ltla_name')

    if len(group_cols) == 0:
        # fallback: aggregate by all non-numeric columns
        group_cols = [c for c in census.columns if census[c].dtype == object and c != 'population']

    pop_by_borough = (
        census.groupby(group_cols, dropna=False)['population']
        .sum()
        .reset_index()
        .rename(columns={'population': out_pop_col})
    )

    # helper to normalize names for matching
    def norm_name(s):
        if pd.isna(s): return ''
        return re.sub(r'[^a-z0-9]', '', str(s).lower())

    # create normalized name columns for matching
    if 'ltla_name' in pop_by_borough.columns:
        pop_by_borough['ltla_name_norm'] = pop_by_borough['ltla_name'].apply(norm_name)
    quarterly_crime = quarterly_crime.copy()
    quarterly_crime['borough_norm'] = quarterly_crime[borough_col].apply(norm_name)

    # attempt direct name match
    if 'ltla_name_norm' in pop_by_borough.columns:
        qc = quarterly_crime.merge(
            pop_by_borough[['ltla_name_norm', out_pop_col] + ([c for c in pop_by_borough.columns if c not in ['ltla_name_norm', out_pop_col]] if True else [])],
            left_on='borough_norm',
            right_on='ltla_name_norm',
            how='left'
        )
    else:
        qc = quarterly_crime.merge(pop_by_borough[[out_pop_col] + group_cols], left_index=True, right_index=True, how='left')

    # if missing, try matching by code if quarterly_crime has a code column
    if qc[out_pop_col].isna().any():
        if 'ltla_code' in pop_by_borough.columns and 'ltla_code' in quarterly_crime.columns:
            qc = qc.drop(columns=['ltla_name_norm'], errors='ignore').merge(
                pop_by_borough[['ltla_code', out_pop_col]],
                left_on='ltla_code',
                right_on='ltla_code',
                how='left',
                suffixes=('', '_census')
            )

    # final fallback: warn and fill missing population
    missing_pop = qc[out_pop_col].isna().sum()
    if missing_pop > 0:
        print(f"Warning: {missing_pop} quarterly_crime rows missing population after merge. Filling with {fill_missing_pop_with}.")
        qc[out_pop_col] = qc[out_pop_col].fillna(fill_missing_pop_with)

    # compute crime per 100k
    qc[out_rate_col] = qc[crime_col].astype(float) / qc[out_pop_col].astype(float) * 100000.0

    # cleanup helper cols and return
    qc = qc.drop(columns=['borough_norm'], errors='ignore')
    return qc, pop_by_borough


# ---------------------------------------------------------
# 5. Aggregate monthly crime → fiscal quarterly crime
# ---------------------------------------------------------
quarterly_crime = (
    crime_df.groupby(['borough', 'quarter'])['crime_count']
    .sum()
    .reset_index()
)

quarterly_crime = quarterly_crime.merge(
    quarter_map[['quarter', 'date_str']],
    on='quarter',
    how='left'
).rename(columns={'date_str': 'date'})

# normalize crime values
quarterly_crime, pop_by_borough = normalize_crime_by_population(
    quarterly_crime,
    census_path=census_path
)


# ---------------------------------------------------------
# 6. Prepare wide-format output tables
# ---------------------------------------------------------
all_metrics = perception_df['metric'].unique()

borough_residuals_wide = quarterly_crime[['borough', 'quarter', 'date']].copy()
aggregated_residuals_wide = (
    quarterly_crime[['quarter', 'date']]
    .drop_duplicates()
    .sort_values('quarter')
    .copy()
)

def _fmt_q(q):
    try:
        return pd.to_datetime(q).strftime("%Y%m%d")
    except Exception:
        try:
            return pd.Timestamp(q).strftime("%Y%m%d")
        except Exception:
            return str(q)

def run_borough_diagnostics(borough_name, X_raw, y_raw, min_obs=3, plot=False,
                            metric=None, quarter_range=None, diag_dir=None):
    """
    Fit OLS (with intercept) and compute diagnostics for a single borough.
    Returns: dict with diagnostics, predicted and residuals, and diag_plot path when plotted.

    Optional args:
      - metric: string used in the filename and PNG title
      - quarter_range: string used in the filename and PNG title
      - diag_dir: directory where PNG will be saved (falls back to global DIAG_DIR)
    """
    out = {"borough": borough_name}
    X = np.asarray(X_raw).astype(float).reshape(-1, 1)
    y = np.asarray(y_raw).astype(float).reshape(-1,)

    if len(y) < min_obs:
        out["skipped"] = True
        return out

    Xc = sm.add_constant(X)
    model = sm.OLS(y, Xc)
    try:
        res = model.fit()
    except Exception as e:
        out["error"] = str(e)
        return out

    pred = res.predict(Xc)
    resid = y - pred

    # Robust (HC3) standard errors
    try:
        res_hc3 = res.get_robustcov_results(cov_type="HC3")
    except Exception:
        res_hc3 = None

    # Influence measures
    try:
        infl = OLSInfluence(res)
        cooks_d = infl.cooks_distance[0]
        leverage = infl.hat_matrix_diag
    except Exception:
        cooks_d = None
        leverage = None

    # Normality test (Shapiro) and skew/kurtosis
    try:
        shapiro_p = float(stats.shapiro(res.resid)[1]) if len(res.resid) >= 3 else np.nan
    except Exception:
        shapiro_p = None
    try:
        skew = float(stats.skew(res.resid))
        kurt = float(stats.kurtosis(res.resid))
    except Exception:
        skew = None
        kurt = None

    out.update({
        "skipped": False,
        "n_obs": int(len(y)),
        "params": res.params.tolist(),
        "pvalues": res.pvalues.tolist(),
        "rsquared": float(res.rsquared),
        "rsquared_adj": float(res.rsquared_adj),
        "shapiro_p": shapiro_p,
        "skew": skew,
        "kurtosis": kurt,
        "cooks_d": cooks_d.tolist() if cooks_d is not None else None,
        "leverage": leverage.tolist() if leverage is not None else None,
        "predicted": pred.tolist(),
        "residuals": resid.tolist()
    })

    # plotting (optional) — includes title on PNG
    if plot:
        try:
            fig, axes = plt.subplots(2, 2, figsize=(10, 8))
            sns.regplot(x=X.ravel(), y=y, ci=None, ax=axes[0,0], scatter_kws={"s":30})
            axes[0,0].set_xlabel("predictor")
            axes[0,0].set_ylabel("response")

            axes[0,1].scatter(pred, resid, s=30, alpha=0.8)
            axes[0,1].axhline(0, color="k", lw=0.8)
            axes[0,1].set_title("Residuals vs Fitted")
            axes[0,1].set_xlabel("Fitted")
            axes[0,1].set_ylabel("Residuals")

            sm.qqplot(resid, line="45", ax=axes[1,0])
            axes[1,0].set_title("QQ plot of residuals")

            if cooks_d is not None:
                axes[1,1].stem(np.arange(len(cooks_d)), cooks_d, markerfmt="C1o", basefmt="k-")
            axes[1,1].set_title("Cook's distance")
            axes[1,1].set_xlabel("Observation")
            axes[1,1].set_ylabel("Cook's D")

            # Build title text and add as figure suptitle
            title_parts = []
            if metric:
                title_parts.append(str(metric))
            title_parts.append(str(borough_name))
            if quarter_range:
                title_parts.append(str(quarter_range))
            full_title = "  —  ".join(title_parts)

            # Truncate if too long
            if len(full_title) > 120:
                full_title = full_title[:117] + "..."

            fig.suptitle(full_title, fontsize=12, fontweight="bold", y=0.99)

            plt.tight_layout(rect=[0, 0, 1, 0.96])  # leave space for suptitle

            # build safe filename components
            safe_borough = re.sub(r"[^\w\-]", "_", str(borough_name))[:60]
            safe_metric = re.sub(r"[^\w\-]", "_", str(metric))[:40] if metric else "metric"
            safe_q = re.sub(r"[^\w\-]", "_", str(quarter_range))[:40] if quarter_range else "quarters"

            # determine directory
            target_dir = diag_dir if diag_dir else globals().get("DIAG_DIR", ".")
            os.makedirs(target_dir, exist_ok=True)

            fname = f"diag_{safe_metric}_{safe_borough}_{safe_q}.png"
            fig_path = os.path.join(target_dir, fname)

            fig.savefig(fig_path, dpi=150)
            plt.close(fig)
            out["diag_plot"] = fig_path
        except Exception:
            out["diag_plot"] = None

    if res_hc3 is not None:
        out["hc3_params"] = res_hc3.params.tolist()
        out["hc3_bse"] = res_hc3.bse.tolist()
        out["hc3_pvalues"] = res_hc3.pvalues.tolist()

    return out



# ---------------------------------------------------------
# 7. Loop through each perception metric and compute borough residuals with diagnostics
# ---------------------------------------------------------
diagnostics_list = []

for metric in all_metrics:
    metric_df = perception_df[perception_df['metric'] == metric].copy()
    # merge crime (quarterly) with perception by borough & quarter
    merged = pd.merge(
        quarterly_crime,
        metric_df[['borough', 'quarter', 'metric_value']],
        on=['borough', 'quarter'],
        how='inner'
    ).sort_values(['borough', 'quarter']).reset_index(drop=True)

    # ensure diagnostics dir exists
DIAG_DIR = os.path.join(output_path, "diagnostics_borough_simple")
os.makedirs(DIAG_DIR, exist_ok=True)

diagnostics_list = []

all_metrics = perception_df['metric'].unique()

for metric in all_metrics:
    metric_df = perception_df[perception_df['metric'] == metric].copy()
    if metric_df.empty:
        continue

    # merge crime (quarterly) with perception by borough & quarter
    merged = pd.merge(
        quarterly_crime,
        metric_df[['borough', 'quarter', 'metric_value']],
        on=['borough', 'quarter'],
        how='inner'
    ).sort_values(['borough', 'quarter']).reset_index(drop=True)

    if merged.empty:
        print(f"WARNING: merged empty for metric {metric}")
        continue

    metric_residuals = []

    # run diagnostics and collect residuals per borough
    for borough, group in merged.groupby('borough'):
        g = group.sort_values('quarter').reset_index(drop=True)
        if len(g) < 3:
            continue

        # predictor: crime_per_100k (added earlier)
        X = g[['crime_per_100k']].values
        y = g['metric_value'].values

        # build quarter range string for filename
        start_q = g['quarter'].min()
        end_q = g['quarter'].max()
        quarter_range = f"{_fmt_q(start_q)}-{_fmt_q(end_q)}"

        # call diagnostics (plot=True to save PNG)
        diag = run_borough_diagnostics(
            borough_name=borough,
            X_raw=X,
            y_raw=y,
            min_obs=3,
            plot=True,
            metric=metric,
            quarter_range=quarter_range,
            diag_dir=DIAG_DIR
        )

        # attach metric and quarter_range to diagnostics and store
        diag_record = {**diag, "metric": metric, "quarter_range": quarter_range}
        diagnostics_list.append(diag_record)

        # skip boroughs that were skipped or errored
        if diag.get("skipped", False) or "error" in diag:
            continue

        # use the predicted/residual arrays returned by the diagnostics function
        predicted = np.array(diag.get("predicted", []))
        resid = np.array(diag.get("residuals", []))

        borough_residuals = pd.DataFrame({
            'borough': borough,
            'quarter': g['quarter'],
            'residual': resid
        })
        metric_residuals.append(borough_residuals)

    if len(metric_residuals) == 0:
        print(f"WARNING: No residuals for metric {metric}")
        continue

    metric_residual_df = pd.concat(metric_residuals, ignore_index=True)

    metric_col = metric.replace(" ", "_") + "_residual"

    borough_residuals_wide = borough_residuals_wide.merge(
        metric_residual_df[['borough', 'quarter', 'residual']],
        on=['borough', 'quarter'],
        how='left'
    ).rename(columns={'residual': metric_col})

    agg_residual = (
        metric_residual_df.groupby('quarter')['residual']
        .mean()
        .reset_index()
    )

    aggregated_residuals_wide = aggregated_residuals_wide.merge(
        agg_residual,
        on='quarter',
        how='left'
    ).rename(columns={'residual': metric_col})

# After loop: save diagnostics summary CSV (one row per borough×metric)
try:
    if diagnostics_list:
        diag_df = pd.json_normalize(diagnostics_list)
        diag_csv = os.path.join(DIAG_DIR, "borough_diagnostics_summary.csv")
        diag_df.to_csv(diag_csv, index=False)
        print("Saved borough diagnostics summary to", diag_csv)
    else:
        print("No borough diagnostics to save")
except Exception as e:
    print("Failed to save borough diagnostics summary:", e)

# After loop: save diagnostics summary CSV (one row per borough×metric)
try:
    if diagnostics_list:
        diag_df = pd.json_normalize(diagnostics_list)
        diag_csv = os.path.join(DIAG_DIR, "borough_diagnostics_summary.csv")
        diag_df.to_csv(diag_csv, index=False)
        print("Saved borough diagnostics summary to", diag_csv)
    else:
        print("No borough diagnostics to save")
except Exception as e:
    print("Failed to save borough diagnostics summary:", e)


    metric_residual_df = pd.concat(metric_residuals, ignore_index=True)

    metric_col = metric.replace(" ", "_") + "_residual"

    borough_residuals_wide = borough_residuals_wide.merge(
        metric_residual_df[['borough', 'quarter', 'residual']],
        on=['borough', 'quarter'],
        how='left'
    ).rename(columns={'residual': metric_col})

    agg_residual = (
        metric_residual_df.groupby('quarter')['residual']
        .mean()
        .reset_index()
    )

    aggregated_residuals_wide = aggregated_residuals_wide.merge(
        agg_residual,
        on='quarter',
        how='left'
    ).rename(columns={'residual': metric_col})


#-----------------------------------------------------------------------------
# deduplicate check
# Count exact duplicates before dropping
n_before = len(borough_residuals_wide)
n_dups = borough_residuals_wide.duplicated(keep=False).sum()
if n_dups > 0:
    print(f"Found {n_dups} exact duplicate row(s) in borough_residuals_wide (total rows before = {n_before}). Dropping duplicates now.")
else:
    print(f"No exact duplicates found in borough_residuals_wide (total rows = {n_before}).")

# Drop exact duplicate rows (keeps the first occurrence)
borough_residuals_wide = borough_residuals_wide.drop_duplicates().reset_index(drop=True)

# Do the same for the aggregated table (defensive)
n_before_agg = len(aggregated_residuals_wide)
n_dups_agg = aggregated_residuals_wide.duplicated(keep=False).sum()
if n_dups_agg > 0:
    print(f"Found {n_dups_agg} exact duplicate row(s) in aggregated_residuals_wide (total rows before = {n_before_agg}). Dropping duplicates now.")
else:
    print(f"No exact duplicates found in aggregated_residuals_wide (total rows = {n_before_agg}).")

aggregated_residuals_wide = aggregated_residuals_wide.drop_duplicates().reset_index(drop=True)

# Optional quick sanity print
print(f"Rows after dedupe: borough_residuals_wide={len(borough_residuals_wide)}, aggregated_residuals_wide={len(aggregated_residuals_wide)}")
# ---------------------------------------------------------
# Save diagnostics summary and outputs
# ---------------------------------------------------------
try:
    diag_df = pd.json_normalize([d for d in diagnostics_list if not d.get("skipped", False)])
    diag_df.to_csv(os.path.join(DIAG_DIR, "borough_diagnostics_summary.csv"), index=False)
except Exception:
    # if diagnostics empty or normalization fails, continue without stopping
    pass

borough_residuals_wide.to_csv(os.path.join(output_path, "borough_residuals_wide.csv"), index=False)
aggregated_residuals_wide.to_csv(os.path.join(output_path, "aggregated_residuals_wide.csv"), index=False)

print("Residual CSVs and diagnostics created successfully.")

# =====================================================================
# 8. Residual Diagnostics Engine (PNG outputs + diagnostics CSV)
# =====================================================================

import ast

DIAG_SUMMARY = os.path.join(DIAG_DIR, "borough_diagnostics_summary.csv")
BOROUGH_WIDE = os.path.join(output_path, "borough_residuals_wide.csv")  # optional, used for quarter labels
OUT_PNG_DIR = os.path.join(output_path, "residual_diagnostics_pngs")
OUT_BOROUGH_DIR = os.path.join(OUT_PNG_DIR, "borough")
OUT_AGG_DIR = os.path.join(OUT_PNG_DIR, "aggregated")
OUT_DIAG_CSV = os.path.join(DIAG_DIR, "residuals_diagnostics_per_borough_metric.csv")

os.makedirs(OUT_BOROUGH_DIR, exist_ok=True)
os.makedirs(OUT_AGG_DIR, exist_ok=True)
os.makedirs(DIAG_DIR, exist_ok=True)

# -------------------------
# Load diagnostics summary
# -------------------------
if not os.path.exists(DIAG_SUMMARY):
    raise FileNotFoundError(f"Diagnostics summary not found: {DIAG_SUMMARY}")

diag = pd.read_csv(DIAG_SUMMARY)

# Convert stringified lists to Python lists
for col in ["predicted", "residuals", "cooks_d", "leverage"]:
    if col in diag.columns:
        diag[col] = diag[col].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

# -------------------------
# Load borough_residuals_wide if available to get quarter labels
# -------------------------
quarter_labels_map = {}  # key: (borough, metric) -> list of quarters (strings)
if os.path.exists(BOROUGH_WIDE):
    bw = pd.read_csv(BOROUGH_WIDE, dtype=str)
    # Expect columns: borough, quarter, and residual columns named like "<metric>_residual"
    # Build mapping of (borough, quarter) -> row order index for each metric by reading unique quarter order per borough
    try:
        # For each borough, get ordered quarters
        for b, g in bw.groupby("borough"):
            q_order = list(g["quarter"].astype(str).tolist())
            # store as default for borough (used if metric-specific mapping not found)
            quarter_labels_map[(b, None)] = q_order
    except Exception:
        quarter_labels_map = {}
else:
    # no borough_wide file; we'll fallback to quarter_range or index labels later
    pass

# -------------------------
# Ensure quarter_map exists in memory (from earlier pipeline)
# If not, try to build from perception_df if available in this session
# -------------------------
if 'quarter_map' not in globals():
    # try to load quarter_map from perception file if available
    try:
        perception_df = pd.read_csv(perception_path, parse_dates=["date"])
        quarter_map = (
            perception_df[['quarter', 'date']]
            .drop_duplicates()
            .sort_values('date')
            .reset_index(drop=True)
        )
    except Exception:
        quarter_map = None

# -------------------------
# Filter out pre-April-2017 at start of analysis (safety)
# -------------------------
# If diag has 'quarter' column, merge to get date; else rely on borough_residuals_wide mapping
if "quarter" in diag.columns and quarter_map is not None:
    diag = diag.merge(quarter_map[["quarter", "date"]], on="quarter", how="left")
    diag["date"] = pd.to_datetime(diag["date"], errors="coerce")
    diag = diag[diag["date"] >= pd.Timestamp("2017-04-01")].reset_index(drop=True)
else:
    # If no quarter column, try to filter using borough_residuals_wide quarters if available
    # If not possible, proceed but warn
    pass

# -------------------------
# Helper: safe list extraction
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

# -------------------------
# Diagnostics accumulator
# -------------------------
diag_rows = []

# -------------------------
# Per-borough × metric combined PNGs
# -------------------------
for i, row in diag.iterrows():
    borough = row.get("borough", "UNKNOWN")
    metric = row.get("metric", "metric")
    predicted = to_array(row.get("predicted"))
    residuals = to_array(row.get("residuals"))
    cooks_d = to_array(row.get("cooks_d")) if "cooks_d" in row and pd.notna(row.get("cooks_d")) else None
    leverage = to_array(row.get("leverage")) if "leverage" in row and pd.notna(row.get("leverage")) else None

    # Determine quarter labels:
    quarters = None
    # 1) Try borough_residuals_wide mapping for this borough
    if (borough, metric) in quarter_labels_map:
        quarters = quarter_labels_map[(borough, metric)]
    elif (borough, None) in quarter_labels_map:
        # fallback to borough-level quarter order
        quarters = quarter_labels_map[(borough, None)]
    # 2) Try quarter_range field if present and matches length
    if quarters is None and "quarter_range" in row and pd.notna(row["quarter_range"]):
        # quarter_range may be like "20170101-20201201" or "Q1_1718-Q4_2020"
        # If it's a dash-separated list of two endpoints, we cannot reconstruct all quarters reliably.
        # So only use if it's a comma-separated list or a pipe; otherwise fallback to index labels.
        qr = str(row["quarter_range"])
        if "," in qr:
            qlist = [q.strip() for q in qr.split(",")]
            if len(qlist) == len(residuals):
                quarters = qlist
    # 3) If still None or length mismatch, fallback to index labels "Q1, Q2, ..."
    if quarters is None or len(quarters) != len(residuals):
        quarters = [f"Q{i+1}" for i in range(len(residuals))]

    # Skip if no residuals
    if residuals.size == 0:
        continue

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

    # Breusch-Pagan for heteroskedasticity: need exog; use predicted (fitted) as exog with constant
    bp_stat = bp_p = np.nan
    try:
        if predicted.size == residuals.size and predicted.size > 1:
            exog = sm.add_constant(predicted)
            bp_test = het_breuschpagan(residuals, exog)
            # returns (lm_stat, lm_pvalue, f_stat, f_pvalue)
            bp_stat, bp_p = float(bp_test[0]), float(bp_test[1])
        else:
            # try using index as exog (time) if predicted not available
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
    ax_ts.set_ylabel("Residual")
    ax_ts.tick_params(axis='x', rotation=45)
    # annotate mean and t-test
    ax_ts.annotate(f"Mean resid = {mean_resid:.4g}\n t={t_stat:.3g}, p={t_p:.3g}",
                   xy=(0.02, 0.95), xycoords='axes fraction', fontsize=9,
                   bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8),
                   verticalalignment='top')

    # Top-right: Residual vs Fitted
    ax_rvf.scatter(predicted, residuals, color="tab:blue", s=30, alpha=0.8)
    ax_rvf.axhline(0, color="black", linestyle="--", linewidth=0.8)
    ax_rvf.set_title("Residual vs Fitted")
    ax_rvf.set_xlabel("Fitted values")
    ax_rvf.set_ylabel("Residuals")
    # annotate DW and BP
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
    # overlay Cook's D as red dots scaled
    if cooks_d is not None:
        # scale cooks for visibility
        cd = cooks_d
        # mark top influential points
        top_idx = np.argsort(-cd)[:3] if cd.size >= 3 else np.argsort(-cd)
        for ti in top_idx:
            ax_lev.plot(ti, leverage[ti] if leverage is not None and ti < leverage.size else 0,
                        marker="o", color="red")
            ax_lev.annotate(f"CookD={cd[ti]:.3g}", xy=(ti, (leverage[ti] if leverage is not None and ti < leverage.size else 0)),
                            xytext=(5, 5), textcoords='offset points', fontsize=8)

    # suptitle and save
    fig.suptitle(f"{borough} — {metric} — Residual Diagnostics", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])

    safe_b = re.sub(r"[^\w\-]", "_", str(borough))[:80]
    safe_m = re.sub(r"[^\w\-]", "_", str(metric))[:80]
    out_file = os.path.join(OUT_BOROUGH_DIR, f"{safe_b}__{safe_m}__residuals_diagnostics.png")
    fig.savefig(out_file, dpi=150)
    plt.close(fig)

    # -------------------------
    # Append diagnostics row
    # -------------------------
    diag_rows.append({
        "borough": borough,
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
# Aggregated diagnostics across boroughs (by quarter)
# -------------------------
# If borough_residuals_wide exists, use it to build residuals per borough per quarter
agg_diag_rows = []
if os.path.exists(BOROUGH_WIDE):
    bw = pd.read_csv(BOROUGH_WIDE, dtype=str)
    # find residual columns (ending with _residual)
    residual_cols = [c for c in bw.columns if c.endswith("_residual")]
    # melt to long form: borough, quarter, metric, residual
    melted = bw.melt(id_vars=["borough", "quarter", "date"], value_vars=residual_cols,
                     var_name="metric_col", value_name="residual")
    # metric name from column
    melted["metric"] = melted["metric_col"].str.replace("_residual", "").str.replace("_", " ")
    melted["residual"] = pd.to_numeric(melted["residual"], errors="coerce")
    # filter date >= 2017-04-01 if date column exists
    if "date" in melted.columns:
        melted["date"] = pd.to_datetime(melted["date"], errors="coerce")
        melted = melted[melted["date"] >= pd.Timestamp("2017-04-01")]
    # compute mean residual per quarter across boroughs for each metric
    for metric_name, g in melted.groupby("metric"):
        g2 = g.sort_values("quarter")
        # pivot by quarter -> mean residual
        agg_series = g2.groupby("quarter")["residual"].mean().reset_index()
        agg_series = agg_series.dropna()
        if agg_series.empty:
            continue
        quarters = agg_series["quarter"].astype(str).tolist()
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
        ax_ts.set_ylabel("Mean residual")
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

        # variance/heterogeneity across boroughs for each quarter (plot)
        var_by_q = g2.groupby("quarter")["residual"].var(ddof=0).reindex(agg_series["quarter"]).values
        ax_var.plot(quarters, var_by_q, color="tab:purple", marker="o")
        ax_var.set_title("Residual variance across boroughs (by quarter)")
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
# Save diagnostics CSV (per borough×metric + aggregated rows)
# -------------------------
diag_df_out = pd.DataFrame(diag_rows)
agg_df_out = pd.DataFrame(agg_diag_rows)

if not diag_df_out.empty:
    diag_df_out.to_csv(OUT_DIAG_CSV, index=False)
if not agg_df_out.empty:
    agg_df_out.to_csv(os.path.join(DIAG_DIR, "aggregated_residuals_diagnostics.csv"), index=False)

print("Saved per-borough PNGs to:", OUT_BOROUGH_DIR)
print("Saved aggregated PNGs to:", OUT_AGG_DIR)
print("Saved diagnostics CSV to:", OUT_DIAG_CSV)
