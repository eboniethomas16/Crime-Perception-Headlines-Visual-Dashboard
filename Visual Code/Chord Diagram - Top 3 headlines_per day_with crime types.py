import pandas as pd
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import os

def load_and_parse(path):
    df = pd.read_csv(path)

    # ------------------------------------------------------------
    # SAFETY CHECK: ensure required columns exist BEFORE anything else
    # ------------------------------------------------------------
    required_cols = {"date", "headline", "crime_types"}
    missing = required_cols - set(df.columns)

    if missing:
        print(f"Skipping file missing required columns {missing}: {path}")
        return None

    # ------------------------------------------------------------
    # Fix mojibake SAFELY (headline may contain floats, NaN, None)
    # ------------------------------------------------------------
    def fix_mojibake(x):
        if not isinstance(x, str):
            return ""
        try:
            return x.encode("latin1", errors="ignore").decode("utf8", errors="ignore")
        except:
            return x

    df["headline"] = df["headline"].apply(fix_mojibake)

    # Remove empty headlines
    df = df[df["headline"].str.strip() != ""]

    # ------------------------------------------------------------
    # Parse date AFTER confirming column exists
    # ------------------------------------------------------------
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")

    # Remove rows where date failed to parse
    df = df[df["date"].notna()]

    # ------------------------------------------------------------
    # Clean crime_types
    # ------------------------------------------------------------
    # Clean crime_types
    df["crime_types"] = df["crime_types"].fillna("").astype(str).str.strip()

    # Normalize case
    crime_upper = df["crime_types"].str.upper().str.strip()

    # Keep only rows with MULTIPLE crime types AND not UNKNOWN
    df = df[
        crime_upper.str.contains(",") &
        (crime_upper != "UNKNOWN")
    ].copy()


    return df


if __name__ == "__main__":

    # ------------------------------------------------------------
    # 1. Load all monthly CSVs in parallel
    # ------------------------------------------------------------
    input_folder = Path(
        r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\GDELT_pipeline\data\combined_datasets\Updated Monthly Filtered Datasets\CLEANED Combined Datasets"
    )
    output_folder = Path(
        r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Visual Python Code\Chord Diagram Output"
    )
    output_folder.mkdir(parents=True, exist_ok=True)

    files = sorted(input_folder.glob("*.csv"))

    with ProcessPoolExecutor() as ex:
        dfs = list(ex.map(load_and_parse, files))

    # Remove skipped files
    dfs = [d for d in dfs if d is not None]

    raw = pd.concat(dfs, ignore_index=True)

    # ------------------------------------------------------------
    # 2. Filter duplicates (TRUE only)
    # ------------------------------------------------------------
    raw["headline_is_duplicate"] = raw["headline_is_duplicate"].astype(str).str.upper().str.strip()

    filtered = raw[raw["headline_is_duplicate"] == "TRUE"].copy()

    # ------------------------------------------------------------
    # 3. Add Day column
    # ------------------------------------------------------------
    filtered["Day"] = filtered["date"].dt.date

    # Remove bogus headlines (missing Day)
    filtered = filtered[filtered["Day"].notna()]

    # ------------------------------------------------------------
    # 4. DAILY top-3 headlines (only multi-crime headlines)
    # ------------------------------------------------------------
    daily_counts = (
        filtered.groupby(["Day", "headline", "crime_types"])["GKGRECORDID"]
        .nunique()
        .reset_index(name="count")
    )

    daily_top3 = []
    for day, sub in daily_counts.groupby("Day"):
        sub_sorted = sub.sort_values("count", ascending=False).head(3)
        sub_sorted["Rank_Day"] = range(1, len(sub_sorted) + 1)
        sub_sorted["Top_Day"] = True
        daily_top3.append(sub_sorted)

    daily_top3 = pd.concat(daily_top3, ignore_index=True)

    # ------------------------------------------------------------
    # 5. Add Headline_Source (one V1DOCUMENTIDENTIFIER per headline)
    # ------------------------------------------------------------
    headline_sources = (
        filtered.groupby("headline")["V1DOCUMENTIDENTIFIER"]
        .agg("first")
        .reset_index()
        .rename(columns={"V1DOCUMENTIDENTIFIER": "Headline_Source"})
    )

    daily_top3 = daily_top3.merge(headline_sources, on="headline", how="left")

    # ------------------------------------------------------------
    # 6. Save final DAY-only top-3 file
    # ------------------------------------------------------------
    output_csv = output_folder / "headline_daily_top3_multicrime.csv"
    daily_top3.to_csv(output_csv, index=False, encoding="utf-8-sig")

    print(f"Done. Daily top-3 multi-crime summary saved to:\n{output_csv}")
