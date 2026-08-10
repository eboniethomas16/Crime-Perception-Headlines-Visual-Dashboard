import pandas as pd
import os
#from collections import Counter
from datetime import datetime
#import numpy as np
from config import CRIME_THEMES, UK_SITES, CACHE_FILTERED, CACHE_PARSED_DIR, GREATER_LONDON_LOC, CRIME_HEADLINES

### Imports the CRIME_THEMES list from your config.py file.
### CRIME_THEMES is A list of theme keywords I defined in config, e.g.
### ["CRIME", "VIOLENCE", "POLICE", "SECURITY", "TERROR"] ###

#filters.py is the gatekeeper:
#- It takes the full GDELT GKG dataset.
#- It keeps only the rows that are about crime, violence, policing, security, or terrorism.
#- Everything else is discarded before you compute tone, aggregate, or visualise.
#outputs a focused subset of GDELT that aligns with crime and policing perception (or whatever parameters i want)


#filter_crime function will return only the rows in df that are related to crime/policing in LONDON
#the "|" is an "OR". 
    # ex. CRIME_THEMES = ["CRIME", "VIOLENCE", "POLICE"]
    # pattern = "CRIME|VIOLENCE|POLICE"
#It lets you search for any of the themes in a single .str.contains() call.

os.makedirs(CACHE_FILTERED, exist_ok=True)

import re

# TAKES A HEADLINE STRING AND RETURNS A LIST OF CRIME TYPES FOUND
def classify_crime_types(headline: str) -> list:
    if not isinstance(headline, str): # RETURNS UNKNOWN IF HEADLINE NOT A CRIME
        return ["UNKNOWN"]
    text = headline.lower()
    matched = []
    for crime_type, patterns in CRIME_HEADLINES.items():
        for pattern in patterns:
            if re.search(pattern, text):
                matched.append(crime_type)
                break  # avoid duplicates within same category
    return matched if matched else ["UNKNOWN"]


def parse_filtered_filename(fname):    
    # Extracts start_date and end_date from filenames like:
    # 2026-03-01_to_2026-03-08_17-59-09.parquet
    # 2026-02-01_to_2026-03-08_18-10-01.parquet
        
    if not fname.lower().endswith(".parquet"):
        return None, None

    base = fname[:-8]  # strip ".parquet"

    try:
        start_str, end_str = base.split("_to_")
        start_dt = datetime.strptime(start_str, "%Y-%m-%d")
        end_dt = datetime.strptime(end_str, "%Y-%m-%d_%H-%M-%S")
        return start_dt, end_dt
    except Exception:
        return None, None

def run_crime_filter_logic(df, start_date, end_date):
    print("FILLING COLUMNS WITH SAFETY QUOTES " " ")
    for col in [
        "V2ENHANCEDTHEMES", 
         "V1LOCATIONS", "V2ENHANCEDLOCATIONS",
         "V2SOURCECOMMONNAME"]:
        df[col] = df[col].fillna("").str.upper()
    print("✅ FINISHED FILLING COLUMNS WITH SAFETY QUOTES " " ")

    # Ensure date column is datetime
    df["date"] = pd.to_datetime(df["date"])

    # Apply date range filter FIRST
    df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
    print(f"FILTERING DOWN {len(df)} ROWS")
    #------------FILTERS------------------

    # ---------------------------------------------------------
    # 1. Website filtering (vectorised)
    # ---------------------------------------------------------
    # Normalize domain
    # Exact match filter
    # Convert to Python-backed strings to avoid ArrowMemoryError
    df["V2SOURCECOMMONNAME"] = df["V2SOURCECOMMONNAME"].astype("string[python]")
    
    df = df[df["V2SOURCECOMMONNAME"]
            .str
            .upper().isin(UK_SITES)]
    print("✅ WEBSITES FILTERED")

    # ---------------------------------------------------------
    # 2. London detection (checks if any London locations EXIST in GDELT row)
    # ---------------------------------------------------------
    # pattern = "|".join(GREATER_LONDON_LOC)
    # greater_london_mask = (
    # df["V1LOCATIONS"].str.contains(pattern, case=False, regex=True) |
    # df["V2ENHANCEDLOCATIONS"].str.contains(pattern, case=False, regex=True)
    # )
    # df = df[greater_london_mask]
    # print("✅ LONDON ARTICLES FILTERED")
    # ---------------------------------------------------------
    # 3. Crime theme detection (vectorised)
    # ---------------------------------------------------------
 
    crime_pattern = "|".join(
    rf"(?:^|;){theme}(?:,|$)" for theme in CRIME_THEMES
    )

    crime_mask = df["V2ENHANCEDTHEMES"].str.contains(
        crime_pattern,
        case=False,
        regex=True,
        na=False
    )
    df = df[crime_mask]
    print("✅ CRIME THEMES FILTERED")


    # ---------------------------------------------------------
    # 4. London mentions ≥ 2 (fast vectorised counting)
    # ---------------------------------------------------------
    # Make an uppercase lookup set once
    # df["london_mentions"] = sum(
    # df["V2ENHANCEDLOCATIONS"].str.count(gl)
    # for gl in GREATER_LONDON_LOC
    # )
    # london_count_mask = df["london_mentions"] >= 2
    df["london_mentions"] = sum(
    df["V2ENHANCEDLOCATIONS"].str.count(rf"\b{gl}\b")
    for gl in GREATER_LONDON_LOC
)
    london_count_mask = df["london_mentions"] >= 2
    
    print("✅ LONDON MENTIONS ≥ 2 FILTERED")
    # ---------------------------------------------------------
    # 5. Crime mentions ≥ 2 (vectorised)
    # ---------------------------------------------------------
    df["crime_mentions"] = sum(
    df["V2ENHANCEDTHEMES"].str.count(crime)
    for crime in CRIME_THEMES)
    crime_mentions_mask = df["crime_mentions"] >= 2
    print("✅ CRIME MENTIONS ≥ 2 FILTERED")


    # ---------------------------------------------------------
    # 8. Combine all filters
    # ---------------------------------------------------------
    print("COMBINING ALL FILTERS")
    final_mask = (
        london_count_mask &
        crime_mentions_mask
        #df["london_top2"]
    )
    filtered = df[final_mask].copy()
    print(f"✅ FILTERS COMBINED AND {len(filtered)} ROWS APPLIED TO NEW DATAFRAME")
 

    return filtered




# - df = combined_raw
# - start_date = datetime
# - end_date = datetime
# - cache_key = something like "2026-03-06_to_2026-03-08"
#def filter_crime(df, timestamp): #df is a pandas DataFrame containing GDELT GKG data (already parsed)
def filter_crime(df, start_date, end_date, cache_key):
    cached_files = [
        f for f in os.listdir(CACHE_FILTERED)
        if f.endswith(".parquet")
    ] #if a file is a .parquet file, then add it to the list for checking


    overlapping_dfs = []
    covered_ranges = []
    for fname in cached_files:
        cached_start, cached_end = parse_filtered_filename(fname)
        if cached_start is None:
            continue

        # Check overlap
        if cached_end >= start_date and cached_start <= end_date:
            print(f"✔ Overlapping cached file found: {fname}")

            df_cached = pd.read_parquet(os.path.join(CACHE_FILTERED, fname))

            # Slice to requested range
            mask = (df_cached["date"] >= start_date) & (df_cached["date"] <= end_date)
            df_slice = df_cached.loc[mask]

            if not df_slice.empty:
                overlapping_dfs.append(df_slice)
                covered_ranges.append((cached_start, cached_end))

    # -----------------------------------------
    # 2. Determine if entire range is covered
        #returns the combined data. else it continues to find the parsed data elsewhere
    # -----------------------------------------
    if covered_ranges:
        min_cached = min(r[0] for r in covered_ranges)
        max_cached = max(r[1] for r in covered_ranges)

        if min_cached <= start_date and max_cached >= end_date:
            print("✔ Entire range already cached — combining cached slices only")
            combined_cached = pd.concat(overlapping_dfs, ignore_index=True)
            combined_cached = combined_cached.drop_duplicates() #removes duplicate rows

            return combined_cached

    # -----------------------------------------
    # 3. CALL THE MAIN FILTER LOGIC FUNCTION
    # -----------------------------------------

    # THIS CALLS THE MAIN FILTER FUNCTION (LENGTHY)
    df_filtered = run_crime_filter_logic(df, start_date, end_date)
    print("🔍 FILTERING FINISHED. COMBINING EXISTING CACHE AND NEWLY FILTERED")
    # -----------------------------------------
    # 4. Combine cached + newly filtered
    # -----------------------------------------
    all_parts = overlapping_dfs + [df_filtered]
    combined = pd.concat(all_parts, ignore_index=True)
    combined = combined.drop_duplicates(subset=["GKGRECORDID"])

    # -----------------------------------------
    # 5. Save new combined + FILTERED parquet
    # -----------------------------------------
    print(f"saving new combined filtered parquet")
    filtered_path = os.path.join(
        CACHE_FILTERED,
        f"{cache_key}.parquet"
    )
    combined.to_parquet(filtered_path, index=False)
    print(f"✔ Saved combined filtered parquet: {filtered_path}")

    return combined

def filter_parsed_cache_monthly():
    """
    Load parsed parquet files in monthly batches,
    filter them using filter_crime(),
    and save monthly filtered outputs.
    """

    # 1. List all parsed parquet files
    files = sorted(
        f for f in os.listdir(CACHE_PARSED_DIR)
        if f.endswith(".parquet")
    )

    # 2. Group by YYYYMM
    monthly_groups = {}
    for fname in files:
        ts = fname.replace(".parquet", "")
        month_key = ts[:6]  # YYYYMM
        monthly_groups.setdefault(month_key, []).append(fname)

    print(f"Found {len(monthly_groups)} monthly groups")

    # 3. Process each month
    for month_key, fnames in monthly_groups.items():
        print(f"\n=== Processing month {month_key} ({len(fnames)} files) ===")

        dfs = []
        timestamps = []

        # Load all files for this month
        for fname in fnames:
            path = os.path.join(CACHE_PARSED_DIR, fname)
            df = pd.read_parquet(path)
            dfs.append(df)
            timestamps.append(fname.replace(".parquet", ""))

        # Combine month
        combined_raw = pd.concat(dfs, ignore_index=True)

        # Determine start/end timestamps for the month
        start_ts = min(timestamps)
        end_ts   = max(timestamps)

        start_date = pd.to_datetime(start_ts, format="%Y%m%d%H%M%S")
        end_date   = pd.to_datetime(end_ts, format="%Y%m%d%H%M%S")

        # Use month_key as cache_key
        cache_key = month_key

        # Filter using your existing function
        filtered = filter_crime(combined_raw, start_date, end_date, cache_key)

        # Save filtered monthly parquet
        out_path = os.path.join(CACHE_FILTERED, f"{month_key}.parquet")
        filtered.to_parquet(out_path, index=False)

        print(f"✔ Saved filtered month: {out_path}")



#---------------ONLY USED WHEN RUNNING FILTERS.PY ON ITS OWN---------------------------------
def filter_month(year: int, month: int):
    """
    Filter parsed parquet files for a specific year and month.
    """

    # Format YYYYMM
    month_key = f"{year}{month:02d}"

    # List all parsed parquet files for that month
    files = sorted(
        f for f in os.listdir(CACHE_PARSED_DIR)
        if f.startswith(month_key) and f.endswith(".parquet")
    )

    if not files:
        print(f"No parsed files found for {month_key}")
        return

    print(f"Filtering {len(files)} files for {month_key}")

    dfs = []
    timestamps = []

    for fname in files:
        ts = fname.replace(".parquet", "")
        timestamps.append(ts)

        path = os.path.join(CACHE_PARSED_DIR, fname)

        df = pd.read_parquet(path)
        dfs.append(df)

    # Combine month
    combined_raw = pd.concat(dfs, ignore_index=True)

    # Determine start/end timestamps
    start_ts = min(timestamps)
    end_ts   = max(timestamps)

    start_date = pd.to_datetime(start_ts, format="%Y%m%d%H%M%S")
    end_date   = pd.to_datetime(end_ts, format="%Y%m%d%H%M%S")

    # cache_key is the month
    cache_key = month_key

    # Filter using your existing function
    combined_df = filter_crime(combined_raw, start_date, end_date, cache_key)

    # Save filtered monthly parquet
    out_path = os.path.join(CACHE_FILTERED_DIR, f"{month_key}.parquet")
    combined_df.to_parquet(out_path, index=False)

    print(f"✔ Saved filtered month as parquet: {out_path}")

#-------EVERYTHING BELOW IS FROM THE LAST PART OF RUN_BATCH.PY------------
    if combined_df.empty:
        print("No London crime rows in entire range.")
        return


    #removes the london_top2 column if exists
    if "london_top2" in combined_df.columns:
        print("removed london_top2")
        combined_df = combined_df.drop(columns=["london_top2"])

    #EXTRACT TONE AND DATE   
    combined_df = extract_tone_and_date(combined_df)


    # Compute daily average tone
    daily_avg = (
        combined_df.groupby(combined_df["date"].dt.date)["tone"]
        .mean()
        .reset_index()
        .rename(columns={"tone": "daily_avg_tone", "date": "date_only"})
    )

    combined_df["date_only"] = combined_df["date"].dt.date
    combined_df = combined_df.merge(daily_avg, on="date_only", how="left")
    combined_df.drop(columns=["date_only"], inplace=True)
    
    #DROP UNUSED COLUMNS
    cols_to_drop = [
    "V2.1TRANSLATIONINFO",
    "V2.1COUNTS",
    "V2SOURCECOLLECTIONID",
    "V2EXTRASXML",
    "V2.1QUOTATIONS",
    "V2ENHANCEDPERSONS",
    "V2.1SOCIALVIDEOEMBEDS",
    "V2.1ALLNAMES",
    "V2.1AMOUNTS",
    "V2.1SOCIALIMAGEEMBEDS",
    "V2.1RELATEDIMAGES",
    "V1COUNTS",
    "V2GCAM",
    "V2.1SHARINGIMAGE",
    "V2.1ENHANCEDDATES",
    "V1PERSONS",
    "V2.1DATE",
    "V2SOURCECOLLECTIONIDENTIFIER"
    ]
    combined_df = combined_df.drop(columns=[c for c in cols_to_drop if c in combined_df.columns], errors="ignore")

    # Reorder columns: date, tone, daily_avg_tone first
    first_cols = ["date", "tone", "daily_avg_tone","crime_mentions","V2ENHANCEDTHEMES","V2SOURCECOMMONNAME","V1DOCUMENTIDENTIFIER"]
    other_cols = [c for c in combined_df.columns if c not in first_cols]
    combined_df = combined_df[first_cols + other_cols]
    print("FINISHED REORDERING COLUMNS")
    def safe_save(base_path):
        """
        Returns a unique file path by appending (1), (2), ... if needed.
        """
        if not os.path.exists(base_path):
            return base_path

        root, ext = os.path.splitext(base_path)
        counter = 1

        while True:
            new_path = f"{root} ({counter}){ext}"
            if not os.path.exists(new_path):
                return new_path
            counter += 1
    
    if end is None:
        end = datetime.now().strftime("%Y%m%d%H%M%S")

    # Save final combined_df CSV
    filename = f"London_Crime_combined_df_{start}_to_{end}.csv"
    out_path = os.path.join(OUTPUT_DIR, filename)
    output_path = safe_save(out_path)
    combined_df.to_csv(output_path, index=False)


    print(f"\n✔ combined_df CSV saved to: {out_path}")

    


if __name__ == "__main__":
    import sys

   # if len(sys.argv) != 3:
   #     print("Usage: py filters.py YEAR MONTH")
    #    sys.exit(1)
   
    year = 2025
    month = 2
    #call filter_month function by this:
    # py filters.py 2025 4
    # which calls april, 2025
    filter_month(year, month)

