# USED IN DISSERTATION
# THIS FILE ITERATES THROUGH EACH FILE IN THE HEADLINE DATASET FOLDER AND AGGREGATES THEM PER CRIME TYPE
# FOR HEADLINES THAT MENTION MULTIPLE CRIMES, THEY ARE MAPPED TO THE CRIME TYPE THAT IS MOST OBVIOUSLY MENTIONED IN THE HEADLINE
    # FOR EXAMPLE: HEADLINES THAT MENTION A KNIFE OR STABBING WILL BE PUT UNDER "KNIFE CRIME" INSTEAD OF "VIOLENCE AGAINS THE PERSON"

# This script iterates every cleaned monthly headline CSV in a folder and processes them in parallel.
# For each file it removes rows where crime_types is "UNKNOWN", fixes mojibake in headlines,
# normalizes headlines for grouping, and maps multi‑label crime_types to a single deterministic
# primary_crime using keyword detection, a priority list, and a first‑listed fallback.
# Exact duplicates are deduplicated (preferring URL + source, otherwise normalized headline + source),
# while preserving legitimate multi‑source duplicates. The cleaned rows are concatenated across files,
# then aggregated to produce a compact monthly summary that, for each month and primary crime, reports:
# average tone, total headline publishes, number of unique headlines duplicated across sources,
# and total duplicate publishes beyond the first. The script writes the final summary CSV to the
# configured output path.

import os
import re
import unicodedata
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from config import CRIME_HEADLINES as KEYWORD_MAP
# -------------------------
# User paths
# -------------------------
headline_folder = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\GDELT_pipeline\data\combined_datasets\Updated Monthly Filtered Datasets\CLEANED FILTERED datasets"
output_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Data_Visuals\Scrollytelling_draft\data"
os.makedirs(output_path, exist_ok=True)
output_file = os.path.join(output_path, "crime_headlines_monthly_aggregation.csv")

# Precompile regex patterns for speed (case-insensitive)
_COMPILED_CRIME_PATTERNS = {}
# -------------------------
# Priority list and keyword map 
# -------------------------
# priority list is based on the most occurences of each singular crime type ordered from:
    #Least mentioned in headlines --> most mentioned in headlines
PRIORITY = [
    "PUBLIC ORDER OFFENCES",
    "MISCELLANEOUS CRIMES AGAINST SOCIETY",
    "DOMESTIC ABUSE",
    "POSSESSION OF WEAPONS",
    "VEHICLE OFFENCES",
    "HATE CRIME",
    "FRAUD AND FORGERY",
    "THEFT",
    "SEXUAL OFFENCES",
    "LETHAL BARREL DISCHARGE",
    "BURGLARY",
    "ROBBERY",
    "DRUG OFFENCES",
    "ARSON AND CRIMINAL DAMAGE",
    "GUN CRIME",
    "KNIFE CRIME",
    "VIOLENCE AGAINST THE PERSON",
]


# PRIORITY = [
#     "FRAUD AND FORGERY",
#     "POSSESSION OF WEAPONS",
#     "DRUG OFFENCES",
#     "GUN CRIME",
#     "KNIFE CRIME",
#     "LETHAL BARREL DISCHARGE",
#     "SEXUAL OFFENCES",
#     "ROBBERY",
#     "VIOLENCE AGAINST THE PERSON",
#     "HATE CRIME",
#     "ARSON AND CRIMINAL DAMAGE",
#     "BURGLARY",
#     "MISCELLANEOUS CRIMES AGAINST SOCIETY",
#     "PUBLIC ORDER OFFENCES",
#     "DOMESTIC ABUSE",
#     "THEFT",
#     "VEHICLE OFFENCES",
# ]


# -------------------------
# Helpers
# -------------------------

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


for crime_label, patterns in KEYWORD_MAP.items():
    compiled = []
    for p in patterns:
        try:
            compiled.append(re.compile(p, flags=re.IGNORECASE))
        except re.error:
            # if a pattern fails to compile, escape it as a literal fallback
            compiled.append(re.compile(re.escape(p), flags=re.IGNORECASE))
    _COMPILED_CRIME_PATTERNS[crime_label] = compiled


def _count_matches(headline: str, patterns) -> int:
    """Return total number of non-overlapping matches for given compiled patterns."""
    if not headline:
        return 0
    total = 0
    for pat in patterns:
        # use finditer to count occurrences robustly
        try:
            total += sum(1 for _ in pat.finditer(headline))
        except Exception:
            continue
    return total

def _earliest_match_pos(headline: str, patterns):
    """
    Return the earliest match start index for any pattern, or None if no match.
    Uses finditer to get positions.
    """
    earliest = None
    for pat in patterns:
        try:
            for m in pat.finditer(headline):
                if m is None:
                    continue
                pos = m.start()
                if earliest is None or pos < earliest:
                    earliest = pos
        except Exception:
            continue
    return earliest

def pick_primary_by_counts_then_first_token(crime_types_str: str, headline: str) -> str:
    
    # Determine primary crime for a row that lists multiple crime types:
    #   1) Count keyword matches in the headline for each candidate crime token.
    #   2) If one crime has strictly highest count, choose it.
    #   3) If tie on counts, choose the crime whose keyword appears earliest in the headline.
    #   4) If no matches or an unresolved tie, return "UNKNOWN".
    
    if not isinstance(crime_types_str, str) or not crime_types_str.strip():
        return "UNKNOWN"

    # Normalize tokens from the crime_types field (split on commas)
    tokens = [t.strip() for t in re.split(r'\s*,\s*', crime_types_str) if t.strip()]
    if not tokens:
        return "UNKNOWN"

    # Map tokens to available KEYWORD_MAP keys (case-insensitive match)
    token_to_label = {}
    for tok in tokens:
        matched_label = None
        for label in _COMPILED_CRIME_PATTERNS.keys():
            if label.strip().upper() == tok.strip().upper():
                matched_label = label
                break
        # if token not in KEYWORD_MAP, keep token as label (no patterns -> zero matches)
        token_to_label[tok] = matched_label if matched_label is not None else tok

    # Count matches for each candidate and record earliest positions
    counts = {}
    positions = {}
    for tok, label in token_to_label.items():
        patterns = _COMPILED_CRIME_PATTERNS.get(label, []) if label in _COMPILED_CRIME_PATTERNS else []
        counts[label] = _count_matches(headline, patterns)
        positions[label] = _earliest_match_pos(headline, patterns)

    # 1) If any positive counts, pick highest
    max_count = max(counts.values()) if counts else 0
    if max_count > 0:
        candidates = [lab for lab, c in counts.items() if c == max_count]
        if len(candidates) == 1:
            return candidates[0]
        # 2) Tie: choose earliest match position among candidates
        best = None
        best_pos = None
        for lab in candidates:
            pos = positions.get(lab)
            if pos is None:
                continue
            if best_pos is None or pos < best_pos:
                best = lab
                best_pos = pos
        if best is not None:
            return best

        # If still tied (no positions), return UNKNOWN
        return "UNKNOWN"

    # No keyword matches at all: return UNKNOWN
    return "UNKNOWN"



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
    
    # after df["headline"] = df["headline"].apply(fix_mojibake) and df["headline_norm"] created
    df["primary_crime"] = df.apply(
        lambda r: pick_primary_by_counts_then_first_token(r["crime_types"], r["headline"]),
        axis=1
    )

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