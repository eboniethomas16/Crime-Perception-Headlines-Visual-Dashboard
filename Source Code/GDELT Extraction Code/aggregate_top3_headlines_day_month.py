import pandas as pd
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import os

def load_and_parse(path):
    df = pd.read_csv(path)

    # ------------------------------------------------------------
    # SAFETY CHECK: ensure required columns exist BEFORE anything else
    # ------------------------------------------------------------
    required_cols = {"date", "headline"}
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

    return df


if __name__ == "__main__":

    # ------------------------------------------------------------
    # 1. Load all monthly CSVs in parallel
    # ------------------------------------------------------------
    folder = Path(r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\GDELT_pipeline\data\combined_datasets\Updated Monthly Filtered Datasets\CLEANED Combined Datasets")
    files = sorted(folder.glob("*.csv"))

    with ProcessPoolExecutor() as ex:
        dfs = list(ex.map(load_and_parse, files))

    # Remove skipped files
    dfs = [d for d in dfs if d is not None]

    raw = pd.concat(dfs, ignore_index=True)

    # ------------------------------------------------------------
    # 2. Filter duplicates
    # ------------------------------------------------------------
    raw["headline_is_duplicate"] = raw["headline_is_duplicate"].astype(str).str.upper().str.strip()

    filtered = raw[
        (raw["headline_is_duplicate"] == "TRUE") &
        (raw["crime_types"].astype(str).str.upper().str.strip() != "UNKNOWN")
    ]


    # ------------------------------------------------------------
    # 3. Add Day + Month columns
    # ------------------------------------------------------------
    filtered["Day"] = filtered["date"].dt.date
    filtered["Month"] = filtered["date"].dt.to_period("M").dt.to_timestamp()

    # Remove bogus headlines (missing Day)
    filtered = filtered[filtered["Day"].notna()]

    # ------------------------------------------------------------
    # 4. DAILY top-3 headlines
    # ------------------------------------------------------------
    daily_counts = (
        filtered.groupby(["Day", "Month", "headline"])["GKGRECORDID"]
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
    # 5. MONTHLY top-3 headlines
    # ------------------------------------------------------------
    monthly_counts = (
        filtered.groupby(["Month", "headline"])["GKGRECORDID"]
        .nunique()
        .reset_index(name="count")
    )

    monthly_top3 = []
    for month, sub in monthly_counts.groupby("Month"):
        sub_sorted = sub.sort_values("count", ascending=False).head(3)
        sub_sorted["Rank_Month"] = range(1, len(sub_sorted) + 1)
        sub_sorted["Top_Month"] = True
        monthly_top3.append(sub_sorted)

    monthly_top3 = pd.concat(monthly_top3, ignore_index=True)

    # REMOVE bogus monthly headlines
    valid_headlines = filtered["headline"].unique()
    monthly_top3 = monthly_top3[monthly_top3["headline"].isin(valid_headlines)]

    # ------------------------------------------------------------
    # 6. Merge daily + monthly summaries
    # ------------------------------------------------------------
    summary = pd.merge(
    daily_top3,
    monthly_top3,
    on=["headline", "Month"],
    how="outer",
    suffixes=("_day", "_month")
    )

    # ------------------------------------------------------------
    # 6A. Add Headline_Source (one V1DOCUMENTIDENTIFIER per headline)
    # ------------------------------------------------------------
    headline_sources = (
        filtered.groupby("headline")["V1DOCUMENTIDENTIFIER"]
        .agg("first")
        .reset_index()
        .rename(columns={"V1DOCUMENTIDENTIFIER": "Headline_Source"})
    )

    summary = summary.merge(headline_sources, on="headline", how="left")

    # ------------------------------------------------------------
    # 6B. Resolve monthly ties using highest count_day
    # ------------------------------------------------------------
    # Fix 1: fill missing count_day with 0 so sorting works
    summary["count_day"] = summary["count_day"].fillna(0)

    summary = (
        summary.sort_values(["Month", "Rank_Month", "count_day"], ascending=[True, True, False])
        .drop_duplicates(subset=["Month", "Rank_Month"], keep="first")
    )

    # Fix 2: fill Top flags AFTER deduplication
    summary["Top_Day"] = summary["Top_Day"].fillna(False)
    summary["Top_Month"] = summary["Top_Month"].fillna(False)

    # ------------------------------------------------------------
    # 7. Save tiny summary file
    # ------------------------------------------------------------
    summary.to_csv(folder / "headline_daily_monthly_summary.csv", index=False)
    summary.to_json(folder / "headline_daily_monthly_summary.json", orient="records", date_format="iso")

    print("Done. Daily + Monthly summary saved.")
