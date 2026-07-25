import os
import re
import unicodedata
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# -------------------------
# User paths
# -------------------------
headline_folder = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\GDELT_pipeline\data\combined_datasets\Updated Monthly Filtered Datasets\CLEANED Combined Datasets"
output_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Data_Visuals\Scrollytelling_draft\data"
os.makedirs(output_path, exist_ok=True)
output_file = os.path.join(output_path, "crime_headlines_monthly_aggregation.csv")

# -------------------------
# Priority list and keyword map (same logic as before)
# -------------------------
PRIORITY = [
    "FRAUD AND FORGERY",
    "POSSESSION OF WEAPONS",
    "DRUG OFFENCES",
    "GUN CRIME",
    "KNIFE CRIME",
    "LETHAL BARREL DISCHARGE",
    "SEXUAL OFFENCES",
    "ROBBERY",
    "VIOLENCE AGAINST THE PERSON",
    "HATE CRIME",
    "ARSON AND CRIMINAL DAMAGE",
    "BURGLARY",
    "MISCELLANEOUS CRIMES AGAINST SOCIETY",
    "PUBLIC ORDER OFFENCES",
    "DOMESTIC ABUSE",
    "THEFT",
    "VEHICLE OFFENCES",
]

KEYWORD_MAP = {
    r"\bknife\b|\bstabb(?:ing|ed)?\b|\bbladed\b": "KNIFE CRIME",
    r"\bgun\b|\bshoot(?:ing|er|ings)?\b|\bfirearm\b": "GUN CRIME",
    r"\bvehicle\b|\bcar\b|\bvan\b|\bmotorbike\b|\bdriv(?:ing|er)\b|\bhit[- ]and[- ]run\b": "VEHICLE OFFENCES",
    r"\bfraud\b|\bscam\b|\bforger(?:y|ies)?\b|\bembezzl(?:e|ment)\b": "FRAUD AND FORGERY",
    r"\bdrug\b|\bpossession of drugs\b|\btraffick(?:ing)?\b": "DRUG OFFENCES",
    r"\barson\b|\bcriminal damage\b": "ARSON AND CRIMINAL DAMAGE",
    r"\brobber(?:y|ies)?\b|\brobbed\b": "ROBBERY",
    r"\bburglary\b|\bburglar(?:y|ies)?\b": "BURGLARY",
    r"\btheft\b|\bstolen\b|\bshoplift(?:ing)?\b": "THEFT",
    r"\bsexual\b|\brape\b|\bassault(?: sexual)?\b": "SEXUAL OFFENCES",
    r"\bweapon\b|\bpossession of weapons\b": "POSSESSION OF WEAPONS",
    r"\bhate crime\b|\bracist\b|\bdiscriminat": "HATE CRIME",
    r"\bdomestic\b|\bdomestic abuse\b|\bintimate partner\b": "DOMESTIC ABUSE",
}

# -------------------------
# Helpers
# -------------------------
def normalize_token(tok: str) -> str:
    return tok.strip().upper()

def detect_by_keyword(crime_types_str: str):
    s = (crime_types_str or "").lower()
    for pattern, label in KEYWORD_MAP.items():
        if re.search(pattern, s):
            return label
    return None

def pick_primary(crime_types_str: str) -> str:
    if not isinstance(crime_types_str, str) or not crime_types_str.strip():
        return "UNKNOWN"
    kw = detect_by_keyword(crime_types_str)
    if kw:
        return kw
    tokens = [normalize_token(t) for t in crime_types_str.split(",") if t.strip()]
    for p in PRIORITY:
        if p in tokens:
            return p
    return tokens[0] if tokens else "UNKNOWN"

def to_bool(x):
    if pd.isna(x):
        return False
    if isinstance(x, bool):
        return x
    s = str(x).strip().lower()
    return s in {"true", "t", "1", "yes", "y"}

def fix_mojibake(x):
    if not isinstance(x, str):
        return ""
    s = x
    try:
        repaired = s.encode("latin1", errors="ignore").decode("utf8", errors="ignore")
    except Exception:
        repaired = s
    repaired = unicodedata.normalize("NFKC", repaired)
    repaired = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", repaired)
    repaired = re.sub(r"\s+", " ", repaired).strip()
    return repaired

def headline_normalize_for_grouping(s):
    if not isinstance(s, str) or s.strip() == "":
        return ""
    s = s.lower()
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"http\S+", "", s)
    s = re.sub(r"[^\w\s']", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def format_month_label(dt):
    # returns "M/1/YYYY" (no leading zeros)
    if pd.isna(dt):
        return ""
    m = dt.month
    y = dt.year
    return f"{m}/1/{y}"

# -------------------------
# Worker: process one CSV file (dedupe within file)
# -------------------------
def process_file(fpath):
    try:
        df = pd.read_csv(fpath, low_memory=False)
    except Exception as e:
        print(f"Failed to read {os.path.basename(fpath)}: {e}")
        return None

    required = {"date", "crime_types", "tone", "headline", "headline_is_duplicate", "V2SOURCECOMMONNAME", "V1DOCUMENTIDENTIFIER"}
    if not required.issubset(set(df.columns)):
        missing = required - set(df.columns)
        print(f"Skipping {os.path.basename(fpath)} missing columns {missing}")
        return None

    df["crime_types"] = df["crime_types"].fillna("").astype(str)
    df = df[~df["crime_types"].str.strip().str.upper().eq("UNKNOWN")].copy()
    if df.empty:
        return None

    df["date_parsed"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date_parsed"])
    if df.empty:
        return None

    df["headline"] = df["headline"].apply(fix_mojibake)
    df = df[df["headline"].str.strip() != ""].copy()
    if df.empty:
        return None

    df["headline_is_duplicate"] = df["headline_is_duplicate"].apply(to_bool)
    df["headline_norm"] = df["headline"].apply(headline_normalize_for_grouping)
    df["primary_crime"] = df["crime_types"].apply(pick_primary)
    df = df[df["primary_crime"].str.upper() != "UNKNOWN"].copy()
    if df.empty:
        return None

    df["month_period"] = df["date_parsed"].dt.to_period("M")
    df["month_label"] = df["date_parsed"].apply(format_month_label)

    out = df[[
        "month_period",
        "month_label",
        "primary_crime",
        "crime_types",
        "tone",
        "headline",
        "headline_norm",
        "headline_is_duplicate",
        "V2SOURCECOMMONNAME",
        "V1DOCUMENTIDENTIFIER"
    ]].copy()

    # dedupe within file: prefer URL+source, else headline_norm+source
    out["_has_url"] = out["V1DOCUMENTIDENTIFIER"].astype(str).str.strip().ne("")
    url_rows = out[out["_has_url"]].drop_duplicates(subset=["V1DOCUMENTIDENTIFIER", "V2SOURCECOMMONNAME"])
    no_url_rows = out[~out["_has_url"]].drop_duplicates(subset=["headline_norm", "V2SOURCECOMMONNAME"])
    out_clean = pd.concat([url_rows, no_url_rows], ignore_index=True).drop(columns=["_has_url"])

    return out_clean

# -------------------------
# Main: parallel processing and monthly aggregation
# -------------------------
def main(max_workers=None):
    csv_files = [
        os.path.join(headline_folder, f)
        for f in sorted(os.listdir(headline_folder))
        if f.lower().endswith(".csv")
    ]
    if not csv_files:
        print("No CSV files found.")
        return

    results = []
    max_workers = max_workers or min(32, (os.cpu_count() or 4) * 5)
    print(f"Processing {len(csv_files)} files with {max_workers} threads...")

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(process_file, f): f for f in csv_files}
        for future in as_completed(futures):
            fpath = futures[future]
            try:
                df_out = future.result()
                if df_out is not None and not df_out.empty:
                    results.append(df_out)
                    print(f"Processed {os.path.basename(fpath)} -> {len(df_out)} rows")
                else:
                    print(f"Skipped {os.path.basename(fpath)} (no valid rows)")
            except Exception as e:
                print(f"Worker failed for {os.path.basename(fpath)}: {e}")

    if not results:
        print("No rows collected. No output written.")
        return

    combined = pd.concat(results, ignore_index=True)

    # dedupe across files (same logic)
    combined["_has_url"] = combined["V1DOCUMENTIDENTIFIER"].astype(str).str.strip().ne("")
    url_rows = combined[combined["_has_url"]].drop_duplicates(subset=["V1DOCUMENTIDENTIFIER", "V2SOURCECOMMONNAME"])
    no_url_rows = combined[~combined["_has_url"]].drop_duplicates(subset=["headline_norm", "V2SOURCECOMMONNAME"])
    combined = pd.concat([url_rows, no_url_rows], ignore_index=True).drop(columns=["_has_url"])

    # prepare counts of distinct sources per (month_period, primary_crime, headline_norm)
    source_counts = (
        combined.groupby(["month_period", "primary_crime", "headline_norm"])["V2SOURCECOMMONNAME"]
        .nunique()
        .rename("n_sources")
        .reset_index()
    )

    # duplicate_headline_count: number of unique headline_norms in that month+crime with n_sources > 1
    dup_headline_counts = (
        source_counts[source_counts["n_sources"] > 1]
        .groupby(["month_period", "primary_crime"])["headline_norm"]
        .nunique()
        .rename("duplicate_headline_count")
        .reset_index()
    )

    # total_duplicate_publishes: sum over duplicated headlines of (n_sources - 1)
    dup_publish_excess = (
        source_counts[source_counts["n_sources"] > 1]
        .assign(excess=lambda df: df["n_sources"] - 1)
        .groupby(["month_period", "primary_crime"])["excess"]
        .sum()
        .rename("total_duplicate_publishes")
        .reset_index()
    )

    # total_headline_count: total number of publishes (rows) for month+crime in combined
    total_headlines = (
        combined.groupby(["month_period", "primary_crime"])["headline"]
        .count()
        .rename("total_headline_count")
        .reset_index()
    )

    # avg_tone per month+crime
    tone_agg = (
        combined.groupby(["month_period", "primary_crime"])["tone"]
        .mean()
        .rename("avg_tone")
        .reset_index()
    )

    # merge all metrics
    summary = tone_agg.merge(total_headlines, on=["month_period", "primary_crime"], how="left")
    summary = summary.merge(dup_headline_counts, on=["month_period", "primary_crime"], how="left")
    summary = summary.merge(dup_publish_excess, on=["month_period", "primary_crime"], how="left")

    summary["duplicate_headline_count"] = summary["duplicate_headline_count"].fillna(0).astype(int)
    summary["total_duplicate_publishes"] = summary["total_duplicate_publishes"].fillna(0).astype(int)
    summary["total_headline_count"] = summary["total_headline_count"].fillna(0).astype(int)

    # attach month_label (M/1/YYYY)
    month_labels = combined.groupby("month_period")["month_label"].first().reset_index()
    summary = summary.merge(month_labels, on="month_period", how="left")

    # final columns and formatting
    summary = summary.rename(columns={
        "month_label": "date",
        "primary_crime": "crime_type",
        "tone": "avg_tone"
    })
    final = summary[[
        "date",
        "crime_type",
        "avg_tone",
        "total_headline_count",
        "duplicate_headline_count",
        "total_duplicate_publishes"
    ]].copy()

    # sort and write
    final["date_parsed"] = pd.to_datetime(final["date"], format="%m/%d/%Y", errors="coerce")
    if final["date_parsed"].isna().any():
        final["date_parsed"] = pd.to_datetime(final["date"], errors="coerce")
    final = final.sort_values(["date_parsed", "crime_type"]).drop(columns=["date_parsed"])

    final.to_csv(output_file, index=False)
    print(f"Saved monthly summary to: {output_file}")

if __name__ == "__main__":
    main()