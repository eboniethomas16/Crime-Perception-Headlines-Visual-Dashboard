# USED IN DISSERTATION TO CLEAN MPS CRIME DATASETS
# =============================================================================
# MOPAC Monthly Crime Data Cleaner
# =============================================================================
#
# PURPOSE
#   Cleans and standardises raw MOPAC (Mayor's Office for Policing And Crime)
#   monthly crime data exports for Greater London, which arrive as parquet
#   files with inconsistent schemas across three source datasets:
#     - KnifeCrimeData
#     - TNO (Total Notifiable Offences)
#     - OtherCrimeData
#
# INPUT
#   RAW_PARQUET_FOLDER  - folder of raw *.parquet files, one per data export,
#                          with varying column names/date formats per source
#
# PIPELINE (per file, in clean_file):
#   1. normalise_schema()              - maps messy raw column names to a
#                                         standard schema (date, area_type,
#                                         area_name, crime_type, crime_subtype,
#                                         measure, count, financial_year,
#                                         refresh_date)
#   2. normalise_dates()               - builds a usable 'date' column, either
#                                         from an existing date field or
#                                         derived from 'financial_year'
#   3. normalise_measures()            - maps measure labels (count/value/
#                                         statistics/outcomes/etc.) to
#                                         'offences' or 'positive outcomes';
#                                         drops anything else
#   4. normalise_refresh_date()        - parses/creates 'refresh_date' and
#                                         flags whether a row has one
#   5. normalise_specific_area_names() - standardises borough names, strips
#                                         out non-borough areas (e.g. Aviation
#                                         Security, Unknown, Non Met Police
#                                         Force)
#   6. normalise_crime_type()          - lowercases/cleans crime_type text,
#                                         fixes typos, reclassifies "lethal
#                                         barrel discharge" subtypes, drops
#                                         unwanted categories
#   7. normalise_crime_subtype()       - cleans crime_subtype text and remaps
#                                         many historical/inconsistent labels
#                                         to current naming conventions (e.g.
#                                         burglary types)
#   8. normalise_gun_crime()           - reconciles gun crime type/subtype
#                                         pairs that have been labelled
#                                         inconsistently
#   9. drop_crime_subtypes()           - removes specific noisy/duplicate
#                                         subtypes (e.g. TNO figures
#                                         duplicated in OtherCrimeData)
#  10. Area/area_type filtering        - drops rows with no area_name and
#                                         rows for "Safer Neighbourhood Teams"
#  11. category_status flag            - tags each (crime_type, crime_subtype)
#                                         pair as "Current Data" (in
#                                         VALID_2026, the current MOPAC
#                                         classification) or "Legacy Data"
#  12. pivot_and_melt()                - pivots to wide format to compute
#                                         'outcome rate' (positive outcomes /
#                                         offences), then melts back to long
#                                         format (date, area, crime, measure,
#                                         count)
#  13. crime_type is upper-cased for the final output
#
# PARALLEL PROCESSING
#   clean_all_parquets() / process_one() - runs clean_file() over every raw
#   parquet file using a multiprocessing Pool, writing one cleaned parquet
#   per input file to CLEAN_PARQUET_FOLDER
#
# POST-PROCESSING (after all files are cleaned)
#   load_all_mopac_datasets()  - loads and concatenates all cleaned parquet
#                                 files into a single pandas DataFrame
#   dedupe_by_refresh_date()   - for duplicate (date, area, crime_type,
#                                 crime_subtype, measure) rows across sources,
#                                 keeps the one with the most recent
#                                 refresh_date (rows with no refresh_date lose)
#   fix_miscellaneous()        - drops "miscellaneous" crime_type rows from
#                                 Aug 2020 onward (superseded), and renames
#                                 earlier ones to "MISCELLANEOUS CRIMES
#                                 AGAINST SOCIETY"
#
# OUTPUT
#   A single combined CSV: MPS_Crime_Data.csv, containing deduplicated,
#   schema-normalised monthly crime figures across all boroughs/areas, with
#   'offences', 'positive outcomes' and 'outcome rate' as measures.
# =============================================================================
import pandas as pd
from pathlib import Path
import polars as pl
from multiprocessing import Pool
import datetime

RAW_PARQUET_FOLDER = Path(r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\MOPAC Data Cleaner\MOPAC Monthly Crime Data\raw_parquet")
CLEAN_PARQUET_FOLDER = Path(
    r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\MOPAC Data Cleaner\MOPAC Monthly Crime Data\clean_parquet"
)
CLEAN_PARQUET_FOLDER.mkdir(exist_ok=True)


MEASURE_MAP = {
    "statistics": "offences",
    "count": "offences",
    "value": "offences",
    "offence count": "offences",
    "outcomes": "positive outcomes",
}

SCHEMA_MAP = {
    "date": [
        "Month_Year",
        "month_year",
        "month_year ",
        "month",
        "date"
    ],
    "area_type": [
        "area type",
        "area_type"
    ],
    "area_name": [
        "area name",
        "area_name"
    ],
    "crime_type": [
        "crime type",
        "offence group",
        "majortext",
        "crime_type"
    ],
    "crime_subtype": [
        "crime subtype",
        "offence subgroup",
        "minortext",
        "crime_subtype"
    ],
    "measure": [
        "measure"
    ],
    "count": [
        "count",
        "value",
        "statistics",
        "offence count"
    ],
    "financial_year": [
        "financial year",
        "fy_fyindex",
        "financial_year"
    ],
    "refresh_date": [
        "refresh date",
        "refresh_date",
        "Refresh Date"
    ]
}
    

AREA_NAME_MAP = {
    "barking & dagenham": "Barking and Dagenham",
    "barking and dagenham": "Barking and Dagenham",
    "hammersmith & fulham": "Hammersmith and Fulham",
    "hammersmith and fulham": "Hammersmith and Fulham",
    "kensington & chelsea": "Kensington and Chelsea",
    "kensington and chelsea": "Kensington and Chelsea",
}

VALID_2026 = {
    ("arson and criminal damage", "arson"),
    ("arson and criminal damage", "criminal damage"),

    ("burglary", "burglary - business and community"),
    ("burglary", "residential - home"),
    ("burglary", "residential - outbuilding"),
    ("burglary", "residential - general"),

    ("domestic abuse", "domestic abuse"),
    ("domestic abuse", "domestic abuse violence with injury"),

    ("drug offences", "possession of drugs"),
    ("drug offences", "trafficking of drugs"),

    ("fraud and forgery", "fraud and forgery"),

    ("gun crime", "gun crime"),
    ("gun crime", "gun crime personal robbery"),

    ("hate crime", "antisemitic"),
    ("hate crime", "disability crime"),
    ("hate crime", "faith crime"),
    ("hate crime", "hate crime"),
    ("hate crime", "homophobic crime"),
    ("hate crime", "islamophobic crime"),
    ("hate crime", "racist and religious crime"),
    ("hate crime", "racist crime"),
    ("hate crime", "transphobic crime"),

    ("knife crime", "knife crime"),
    ("knife crime", "knife crime with injury"),
    ("knife crime", "knife crime with injury (personal robbery)"),
    ("knife crime", "knife injury victims (1-24)"),
    ("knife crime", "knife injury victims (non da 1-24)"),

    ("lethal barrel discharge", "lethal barrel discharge"),

    ("miscellaneous", "robbery mobile phone"),
    ("miscellaneous", "theft person - mobile phone"),
    ("miscellaneous", "tno non victim based"),
    ("miscellaneous", "tno victim based"),

    ("miscellaneous crimes against society", "misc crimes against society"),

    ("possession of weapons", "possession of weapons"),

    ("public order offences", "other offences against the state, or public order"),
    ("public order offences", "public fear alarm or distress"),
    ("public order offences", "race or religious agg public fear"),
    ("public order offences", "violent disorder"),

    ("robbery", "robbery of business property"),
    ("robbery", "robbery of personal property"),

    ("sexual offences", "other sexual offences"),
    ("sexual offences", "rape"),

    ("theft", "bicycle theft"),
    ("theft", "other theft"),
    ("theft", "shoplifting"),
    ("theft", "theft from the person"),

    ("vehicle offences", "aggravated vehicle taking"),
    ("vehicle offences", "interfering with a motor vehicle"),
    ("vehicle offences", "theft from a vehicle"),
    ("vehicle offences", "theft or unauth taking of a motor veh"),

    ("violence against the person", "death serious injury illegal driving"),
    ("violence against the person", "stalking and harassment"),
    ("violence against the person", "violence with injury"),
    ("violence against the person", "violence without injury"),
    ("violence against the person", "homicide"),
}
def detect_dataset_type(path: str) -> str:
    name = Path(path).name.lower()

    if "knifecrimedata" in name:
        return "KnifeCrimeData"
    if "tnocrimedata" in name:
        return "TNO"
    if "othercrimedata" in name:
        return "OtherCrimeData"

    # fallback for unexpected files
    return "Unknown"


def fix_miscellaneous(df: pd.DataFrame) -> pd.DataFrame:
    cutoff = pd.Timestamp("2020-08-01")

    # Remove miscellaneous ON/AFTER August 2020
    mask_remove = (df["crime_type"].str.lower() == "miscellaneous") & (pd.to_datetime(df["date"]) >= cutoff)
    df = df[~mask_remove]

    # Retroactively rename prev miscellaneous to "miscellaneous crimes against society"
    mask_rename = df["crime_type"].str.lower() == "miscellaneous"
    df.loc[mask_rename, "crime_type"] = "miscellaneous crimes against society"
    # Uppercase the renamed category ONLY
    df.loc[df["crime_type"] == "miscellaneous crimes against society", "crime_type"] = \
    df.loc[df["crime_type"] == "miscellaneous crimes against society", "crime_type"].str.upper()

    return df


def dedupe_by_refresh_date(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure datetime types (coerce invalid to NaT)
    df["refresh_date"] = pd.to_datetime(df["refresh_date"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Sort so that:
    # 1. rows WITH refresh_date come before rows WITHOUT
    # 2. newer refresh_date comes before older
    # 3. grouping keys remain stable
    df = df.sort_values(
        by=[
            "date",
            "area_name",
            "crime_type",
            "crime_subtype",
            "measure",
            "refresh_date"
        ],
        ascending=[True, True, True, True, True, False]
    )
    # Drop duplicates keeping the first (the best row after sorting)
    df = df.drop_duplicates(
        subset=["date", "area_name", "crime_type", "crime_subtype", "measure"],
        keep="first"
    )
    df["date"] = df["date"].dt.strftime("%m/%d/%Y")
    df = fix_miscellaneous(df)
    return df

# ---------------------------------------------------------
# 1. Schema normalisation
# ---------------------------------------------------------
def normalise_schema(df: pl.DataFrame) -> pl.DataFrame:
    rename_map = {}
    lower_cols = {c.lower(): c for c in df.columns}

    for target, candidates in SCHEMA_MAP.items():
        for c in candidates:
            c_lower = c.lower()
            if c_lower in lower_cols:
                rename_map[lower_cols[c_lower]] = target
                break

    return df.rename(rename_map)


# ---------------------------------------------------------
# 2. Date normalisation
# ---------------------------------------------------------
def normalise_dates(df: pl.DataFrame) -> pl.DataFrame:

    # Case 1: date exists
    if "date" in df.columns:

        # If it's already a datetime column → just truncate to month
        if df.schema["date"] == pl.Date or df.schema["date"] == pl.Datetime:
            return df.with_columns(
                pl.col("date").dt.truncate("1mo")
            )

        # Otherwise treat it as a string
        # NOTE: had to comment these rows out since they were causing major issues.
        return df.with_columns(
            pl.col("date")
        )

    # Case 2: financial_year exists
    if "financial_year" in df.columns:
        return df.with_columns(
            pl.col("financial_year")
            .cast(pl.Utf8, strict = False)
            .str.extract(r"(20\d{2})")
            .str.concat("-04-01")
            .str.strptime(pl.Date, strict=False)
            .alias("date")
        )

    # Case 3: no usable date column
    print(f"SKIPPED (no date column): {df.columns}")
    return pl.DataFrame()

def normalise_crime_type(df: pl.DataFrame) -> pl.DataFrame:
    # If column missing, return unchanged
    if "crime_type" not in df.columns:
        return df

    # 1. Clean and normalise crime_type
    df = df.with_columns(
        pl.col("crime_type")
        .cast(pl.Utf8)                           # ensure string dtype
        .fill_null("")                           # avoid null issues
        .str.to_lowercase()                      # lowercase everything
        .str.replace(r"\s+", " ", literal=False) # collapse multiple spaces
        .str.replace(" - ", " - ")               # normalise spaced hyphens
        .str.replace("-", "-")                   # fallback hyphen fix
        .str.strip_chars()                       # trim whitespace
        .replace({
            "miscalleneous": "miscellaneous",
            "miscalleneous ": "miscellaneous"
        })
        .alias("crime_type")
    )

    # 2. CONNECT update:
    #    If subtype contains lethal barrel discharge → change crime_type to lethal barrel discharge
    if "crime_subtype" in df.columns:
        df = df.with_columns(
            pl.when(
                pl.col("crime_subtype")
                  .cast(pl.Utf8)
                  .fill_null("")
                  .str.to_lowercase()
                  .str.contains("lethal barrel discharge")
            )
            .then(pl.lit("lethal barrel discharge"))
            .otherwise(pl.col("crime_type"))
            .alias("crime_type")
        )
        
    # 3. Remove unwanted crime types
    UNWANTED_TYPES = [
        "historical fraud and forgery",
        "non-notifiable",
        "other accepted crime"
        # "miscellaneous"
    ]

    df = df.filter(~pl.col("crime_type").is_in(UNWANTED_TYPES))

    return df





def normalise_crime_subtype(df: pl.DataFrame) -> pl.DataFrame:

    # STEP 1 — Base cleaning (string ops only)
    cleaned = df.with_columns([
        pl.col("crime_subtype")
            .cast(pl.Utf8)
            .fill_null("")
            .str.to_lowercase()
            .str.replace(r"\s+", " ", literal=False)
            .str.replace(" - ", " - ")
            .str.replace("-", "-")
            .str.strip_chars()
            .str.replace("anti-semitic", "antisemitic")
            .str.replace("transgender crime", "transphobic crime")
            .str.replace("lethal barrel discharge", "lethal barrel discharge")
            .str.replace("racially or religiously aggravated public fear, al",
                         "race or religious agg public fear")
            .str.replace("other offences public order",
                         "other offences against the state, or public order")
            .str.replace("theft from person", "theft from the person")
            .str.replace("burglary business and community",
                         "burglary - business and community")
            .str.replace("theft from a motor vehicle", "theft from a vehicle")
            .str.replace("drug trafficking", "trafficking of drugs")
            .str.replace("theft or taking of a motor vehicle",
                         "theft or unauth taking of a motor veh")
            .str.replace("domestic burglary", "burglary - residential")
            .alias("crime_subtype")
    ])

    # STEP 2 — burglary normalisation (top‑level conditional)
    cleaned = cleaned.with_columns([
        pl.when(pl.col("crime_subtype").str.contains("burglary - residential", literal=False))
            .then(pl.lit("Residential - General"))
        .when(pl.col("crime_subtype").str.contains("res burglary of a home", literal=False))
            .then(pl.lit("Residential - Home"))
        .when(pl.col("crime_subtype").str.contains("res burglary of unconnected building", literal=False))
            .then(pl.lit("Residential - Outbuilding"))
        .otherwise(pl.col("crime_subtype"))
        .alias("crime_subtype")
    ])

    return cleaned

#     )


def normalise_gun_crime(df: pl.DataFrame) -> pl.DataFrame:
    # If required columns missing, return unchanged
    if "crime_type" not in df.columns or "crime_subtype" not in df.columns:
        return df

    # Normalise formatting of both columns
    df = df.with_columns([
        pl.col("crime_type")
            .cast(pl.Utf8)
            .str.to_lowercase()
            .str.strip_chars()
            .str.replace(r"\s+", " ", literal=False)
            .alias("crime_type"),

        pl.col("crime_subtype")
            .cast(pl.Utf8)
            .str.to_lowercase()
            .str.strip_chars()
            .str.replace(r"\s+", " ", literal=False)
            .alias("crime_subtype"),
    ])

    # Normalise crime_type values
    df = df.with_columns(
        pl.when(
            (pl.col("crime_type") == pl.lit("gun crime personal robbery")) |
            (
                (pl.col("crime_type") == pl.lit("gun crime")) &
                (pl.col("crime_subtype") == pl.lit("personal robbery"))
            )
        )
        .then(pl.lit("gun crime"))
        .otherwise(pl.col("crime_type"))
        .alias("crime_type")
    )

    # Normalise crime_subtype values
    df = df.with_columns(
        pl.when(
            (pl.col("crime_type") == pl.lit("gun crime")) &
            (pl.col("crime_subtype").is_in([
                "personal robbery",
                "gun crime personal robbery"
            ]))
        )
        .then(pl.lit("gun crime personal robbery"))
        .otherwise(pl.col("crime_subtype"))
        .alias("crime_subtype")
    )

    return df

# ADD ABILITY to REMOVE THE FOLLOWING:
# Aviation Security(So18)
# Unknown
# Other / Nk
# Aviation Security (So18) (Legacy Only)
# N/K (Legacy Only)
def normalise_specific_area_names(df: pl.DataFrame) -> pl.DataFrame:
    if "area_name" not in df.columns:
        return df

    #Clean names
    df = df.with_columns(
        pl.col("area_name")
        .cast(pl.Utf8)
        .str.to_lowercase()
        .replace(AREA_NAME_MAP)
        .str.to_titlecase()
        .alias("area_name")
    )

    # remove unwanted area names
    # only want focus on BOROUGHS
    UNWANTED_AREAS = {
        "Aviation Security(So18)",
        "Aviation Security (So18) (Legacy Only)",
        "Unknown",
        "Other / Nk",
        "N/K (Legacy Only)",
        "Non Met Police Force"
    }

    df = df.filter(~pl.col("area_name").is_in(UNWANTED_AREAS))
    df = df.with_columns(
    pl.col("area_name")
    .str.replace(" And ", " and ")
    .str.replace(" Upon ", " upon ")
    )

    return df


def drop_crime_subtypes(df: pl.DataFrame) -> pl.DataFrame:
    return df.filter(
        pl.col("crime_subtype") != "domestic abuse incidents",
        pl.col("crime_subtype") != "tno non victim based", #TNO data from "OtherCrime" is duplicated from what's recorded in TNO datasets.
        pl.col("crime_subtype") != "tno victim based" 
    )




# ---------------------------------------------------------
# 3. Measure normalisation
# ---------------------------------------------------------
def normalise_measures(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df.with_columns(pl.col("measure").str.to_lowercase())
          .with_columns(pl.col("measure").replace_strict(MEASURE_MAP, default=pl.col("measure")))
          .filter(pl.col("measure").is_in(["offences", "positive outcomes"]))
    )
# ---------------------------------------------------------
# 4. normalise refresh_date column
# ---------------------------------------------------------
def normalise_refresh_date(df: pl.DataFrame) -> pl.DataFrame:
    # 1. Find any refresh-like column (case-insensitive)
    refresh_candidates = [c for c in df.columns if "refresh" in c.lower()]

    # 2. If no refresh column exists → create null metadata
    if not refresh_candidates:
        return df.with_columns([
            pl.lit(None).cast(pl.Date).alias("refresh_date"),
            pl.lit("NO REFRESH DATE").alias("refresh_status")
        ])

    col = refresh_candidates[0]

    # 3. If already a Date or Datetime → keep it exactly like old behaviour
    if df.schema[col] in (pl.Date, pl.Datetime):
        return df.with_columns([
            pl.col(col).cast(pl.Date).alias("refresh_date"),
            pl.lit("HAS REFRESH DATE").alias("refresh_status")
        ])

    # 4. Otherwise parse it safely (old behaviour)
    df = df.with_columns(
        pl.col(col)
        .cast(pl.Utf8, strict=False)          # convert anything to string or null
        .str.strptime(pl.Date, strict=False)  # parse flexibly, never errors
        .alias("refresh_date")
    )

    # 5. Assign refresh_status exactly like old behaviour
    df = df.with_columns(
        pl.when(pl.col("refresh_date").is_not_null())
        .then("HAS REFRESH DATE")
        .otherwise("NO REFRESH DATE")
        .alias("refresh_status")
    )

    return df


# ---------------------------------------------------------
# 4. Pivot + melt
# ---------------------------------------------------------
def pivot_and_melt(df: pl.DataFrame) -> pl.DataFrame:
    wide = df.pivot(
        index=["date", "area_type", "area_name", "crime_type", 
               "crime_subtype", "refresh_date",
               "dataset_source", "category_status"],
        columns="measure",
        values="count",
        aggregate_function="sum"
    )
    if "offences" not in wide.columns:
        wide = wide.with_columns(pl.lit(0).alias("offences"))
    if "positive outcomes" not in wide.columns:
        wide = wide.with_columns(pl.lit(0).alias("positive outcomes"))
    wide = wide.with_columns(
        (pl.col("positive outcomes") / 
         pl.col("offences")).fill_null(0).alias("outcome rate")
    )
    return wide.melt(
        id_vars=["date", "area_type", "area_name", "crime_type", 
                 "crime_subtype", "refresh_date","dataset_source", 
                 "category_status"],
        value_vars=["offences", "positive outcomes", "outcome rate"],
        variable_name="measure",
        value_name="count"
    )

def pivot_and_melt(df: pl.DataFrame) -> pl.DataFrame:
    # Pivot the input DataFrame from long to wide format so that each 'measure'
    # becomes its own column (e.g., 'offences', 'positive outcomes').
    # The pivot groups by the specified index columns and sums 'count' per measure.
    wide = df.pivot(
        index=["date", "area_type", "area_name", "crime_type", 
               "crime_subtype", "refresh_date","dataset_source", 
               "category_status"],
        columns="measure",
        values="count",
        aggregate_function="sum"
    )

    # Ensure the expected numeric columns exist after pivoting.
    # If 'offences' is missing (no rows for that measure), create it with zeros.
    if "offences" not in wide.columns:
        wide = wide.with_columns(pl.lit(0).alias("offences"))
    # If 'positive outcomes' is missing, create it with zeros.
    if "positive outcomes" not in wide.columns:
        wide = wide.with_columns(pl.lit(0).alias("positive outcomes"))

    # Compute an 'outcome rate' as positive outcomes divided by offences.
    # Fill nulls with 0 to avoid propagation of missing values.
    wide = wide.with_columns(
        (pl.col("positive outcomes") / pl.col("offences")).fill_null(0).alias("outcome rate")
    )

    # Convert the wide table back to long format (melt) so that downstream
    # consumers receive a consistent (date, area, crime, measure, count) schema.
    # The id_vars are the grouping columns; value_vars are the measures to unpivot.
    return wide.melt(
        id_vars=["date", "area_type", "area_name", "crime_type", "crime_subtype", "refresh_date","dataset_source", "category_status"],
        value_vars=["offences", "positive outcomes", "outcome rate"],
        variable_name="measure",
        value_name="count"
    )


# ---------------------------------------------------------
# 5. Clean a single file
# ---------------------------------------------------------
def clean_file(path: str) -> pl.DataFrame:
    # DEBUG: catch bad date rows before normalisation

    df = pl.read_parquet(path)
    # print(path.name)
    df = normalise_schema(df)
    if path.stem == "M1045_MonthlyCrimeDashboard_KnifeCrimeData (9)":
        print("STOP")

    df = normalise_dates(df)
    df = normalise_measures(df)
    df = normalise_refresh_date(df)   # <-- ADD THIS LINE

    # Add dataset source column
    dataset_type = detect_dataset_type(path)
    df = df.with_columns(
        pl.lit(dataset_type).alias("dataset_source")
    )
    
    # Normalise area names
    df = normalise_specific_area_names(df)
    df = normalise_crime_type(df)
    df = normalise_crime_subtype(df)
    df = normalise_gun_crime(df)
    df = drop_crime_subtypes(df)
    #df.filter(pl.col("crime_subtype").str.contains("lethal"))


    df = df.filter(pl.col("area_name").is_not_null())
    df = df.filter(pl.col("area_type").str.to_lowercase() != "safer neighbourhood teams")

    # NOW apply the category-status flag
    df = df.with_columns([
        pl.when(
            pl.struct(["crime_type", "crime_subtype"])
            .map_elements(lambda s: (s["crime_type"], s["crime_subtype"]) in VALID_2026)
        )
        .then(pl.lit("Current Data"))
        .otherwise(pl.lit("Legacy Data"))
        .alias("category_status")
    ])

    df = pivot_and_melt(df)

    # Uppercase crime_type AFTER pivot
    df = df.with_columns(
        pl.col("crime_type").str.to_uppercase()
    )

    return df


# ---------------------------------------------------------
# 6. Parallel cleaning
# ---------------------------------------------------------
def process_one(path):
    try:
        df = clean_file(path)
        out = CLEAN_PARQUET_FOLDER / Path(path).name
        df.write_parquet(out)
        return f"OK: {Path(path).name}"
    except Exception as e:
        return f"FAIL: {Path(path).name}\n→ ERROR: {e}"

def clean_all_parquets():
    files = list(RAW_PARQUET_FOLDER.glob("*.parquet"))
    with Pool() as p:
        for f in p.imap_unordered(process_one, files):
            print("Cleaned:", f)

# ---------------------------------------------------------
# 7. Load all cleaned datasets (Pandas)
# ---------------------------------------------------------
def load_all_mopac_datasets():
    files = list(CLEAN_PARQUET_FOLDER.glob("*.parquet"))
    dfs = [pd.read_parquet(f) for f in files]
    return pd.concat(dfs, ignore_index=True)

# ---------------------------------------------------------
# 8. Main
# ---------------------------------------------------------
if __name__ == "__main__":
    print("Cleaning all raw Parquets...")
    clean_all_parquets()

    print("Loading all cleaned datasets...")
    all_mopac = load_all_mopac_datasets()

    print("Applying refresh-aware deduplication...")
    all_mopac = dedupe_by_refresh_date(all_mopac)

    output_path = Path(
    r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\MOPAC Data Cleaner\MOPAC Monthly Crime Data\MPS_Crime_Data.csv"
    )

    all_mopac.to_csv(output_path, index=False, encoding="utf8")
    print(f"Saved combined refresh-aware CSV to:\n{output_path}")








