import os
import sys
import pandas as pd
from datetime import datetime
from daterange import generate_GDELT_timestamps
from config import OUTPUT_DIR, CRIME_HEADLINES
from parser import parallel_parse_all
from filters import filter_crime, classify_crime_types
from extract_tone import extract_tone
from config import CACHE_PARSED_DIR, CACHE_FILTERED
from headline_extractor import parallel_headline_extraction, correct_false_duplicates
import time
from parquet_csv_conversion import parquet_df_to_csv_auto

# # ============================
# # Terminal Log Capture
# # ============================

# LOG_FILE = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\GDELT_pipeline\data\Headline Log History.txt"


# class TeeLogger:
#     def __init__(self, logfile):
#         self.terminal = sys.stdout
#         # "a" = append so logs accumulate across runs
#         self.log = open(logfile, "a", encoding="utf-8")

#         # Add a timestamp header for each pipeline run
#         self.log.write("\n\n" + "="*80 + "\n")
#         self.log.write(f"Pipeline run started at: {datetime.now()}\n")
#         self.log.write("="*80 + "\n\n")

#     def write(self, message):
#         self.terminal.write(message)
#         self.log.write(message)

#     def flush(self):
#         self.terminal.flush()
#         self.log.flush()

# # Redirect stdout and stderr
# sys.stdout = TeeLogger(LOG_FILE)
# sys.stderr = TeeLogger(LOG_FILE)

# print(f"📄 Terminal output is being logged to:\n{LOG_FILE}\n")


def run_year(year: int, reextract_only=False):#Downloads+filters+extracts headlines+creates Csv file for every month of the year
    
    for month in range(1, 13):
        
        start, end = get_month_range(year, month)
        print(f"\n===== Running month {year}-{month:02d} ({start} to {end}) =====")
        if month_already_processed(start, end):
            print(f"✔ Month already processed. Skipping {start} → {end}")
            continue 
        # if month < 10:
        #     continue
        total_month_start = time.perf_counter()           
        run_batch(start=start, end=end,reextract_only=reextract_only)
        total_month_end = time.perf_counter()
        duration_minutes = (total_month_end- total_month_start) / 60
        print(f"⏱ Month {year}-{month:02d} took {duration_minutes:.2f} minutes")


def get_month_range(year: int, month: int): #grabs the start and end day of any given month/year
    start = pd.Timestamp(year, month, 1)
    end = start + pd.offsets.MonthEnd(1)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

def month_already_processed(start: str, end: str) -> bool: #Boolean check if monthly csv has already been created in folder.
    filename = f"London_Crime_combined_df_{start}_to_{end}.csv"
    return os.path.exists(os.path.join(OUTPUT_DIR, filename))


#-----------STEP 2 OF THE RUN_Batch--------------
#----THIS REORDERS THE COLUMNS-------
#----THIS SAVES THE final_df parquet AS A CSV FILE-------
def run_batch_step2(final_df, start, end, total_start):#requires a filtered/enriched parquet
    if "headline" in final_df.columns:#checks if headline extraction has happened. else it starts that process
        print("")
    else:
        final_df = parallel_headline_extraction(final_df, max_workers=20)

    # First-pass duplicate detection
    final_df["headline_is_duplicate"] = final_df["headline"].duplicated(keep=False) #prints true or false if a headline is duplicate from another source

    # Correct false duplicates using article ID + source
    final_df = correct_false_duplicates(final_df)
        
    #-------------------EXTRACT TONE AND DATE-------------------------------   
    final_df = extract_tone(final_df)
    # Compute daily average tone
    daily_avg = (
        final_df.groupby(final_df["date"].dt.date)["tone"]
        .mean()
        .reset_index()
        .rename(columns={"tone": "daily_avg_tone", "date": "date_only"})
    )
    
    final_df["date_only"] = final_df["date"].dt.date
    final_df = final_df.merge(daily_avg, on="date_only", how="left") #populates the daily average tone column
    final_df.drop(columns=["date_only"], inplace=True) #drops the date_only col. not needed anymore   
    
    #-----------------------------------------------------------------------------------------
    #FILTERS THROUGH THE HEADLINES AND ASSIGNS A "CRIME_TYPE" BASED ON THE WORDS IN THE HEADLINE
    #ADDITONALLY ASSIGNS A "SEVERITY" BASED ON THE AMOUNT OF CRIME WORDS IN THE HEADLINE
    #CRIME TYPE AND SEVERITY SCORES ARE ASSIGNED IN CONFIG.PY
    if "crime_types" in final_df.columns:
        print("")
    else:
        final_df["headline"] = final_df["headline"].fillna("")

        final_df["crime_types"] = final_df["headline"].apply(classify_crime_types)
        #df = df.explode('crime_types') #<--Dupicates each crime type into a separate row
        CRIME_KEYWORDS = sorted({kw.lower() for kws in CRIME_HEADLINES.values() for kw in kws}
        )

        final_df["crime_keyword_count"] = sum(
        final_df["headline"].str.lower().str.count(kw)
        for kw in CRIME_KEYWORDS
        )
        final_df["crime_types"] = final_df["crime_types"].apply(
        lambda lst: ", ".join(lst) if isinstance(lst, list) else ""
        )  

    #---------REORDER COLUMNS (PUT MOST IMPORTANT ONES FIRST)--------------------------------------
    first_cols = ["date", "tone", "daily_avg_tone","london_mentions","crime_mentions","crime_keyword_count",
                  "crime_types","headline","headline_is_duplicate",
                  "V1DOCUMENTIDENTIFIER", "V2ENHANCEDTHEMES",
                  "V2SOURCECOMMONNAME"]
    
    other_cols = [c for c in final_df.columns if c not in first_cols]
    final_df = final_df[first_cols + other_cols]
   #--------------------------------------------------------------------------------
    #########################FINAL SAVE#######################
    #Saves the parquet as a csv
    parquet_df_to_csv_auto(final_df, start, end)
    
    
    print(f"\n✔ combined_df CSV saved for:{start} to {end}")
    

#--------------------------------------------------------------------------------
#-----------STEP 1 OF THE RUN_Batch----------------------------------------------
#--------------------------------------------------------------------------------
def run_batch(start, end, reextract_only=False):
    print("STARTING EXTRACTION PROCESS!")
    if end is None:       
        end_date = datetime.today()
    else:
        end_date = datetime.strptime(end, "%Y-%m-%d")
        end_date = end_date.replace(hour=23, minute=59, second=59)

    start_date = datetime.strptime(start, "%Y-%m-%d")

    all_df = []
    start_ts_str = start_date.strftime("%Y%m%d%H%M%S")
    end_ts_str   = end_date.strftime("%Y%m%d%H%M%S")
    existing_ts = set()

    # ============================================================
    # OPTIONAL MODE: Re-extract headlines ONLY (skip download/parse)
    # ============================================================

    if reextract_only:
        print("\n=== RE-EXTRACT HEADLINES MODE ENABLED ===")
        print("Checking for existing monthly filtered parquet...\n")

        # Build expected filename for this month
        month_start = start_date.strftime("%Y-%m-%d")
        month_end   = end_date.strftime("%Y-%m-%d")
        fname = f"{month_start}_to_{month_end}_23-59-59.parquet"
        fpath = os.path.join(CACHE_FILTERED, fname)

        if not os.path.exists(fpath):
            raise FileNotFoundError(
                f"Missing filtered parquet for {month_start} → {month_end}: {fname}"
            )

        print(f"✔ Found filtered parquet: {fname}")
        combined_df = pd.read_parquet(fpath)
        print(f"Loaded {len(combined_df)} rows from filtered cache.")

        # Run updated headline extraction logic
        print("\nStarting headline re-extraction with updated config...")
        headline_updated_df = parallel_headline_extraction(combined_df, max_workers=36)
        total_start = time.perf_counter()

        # # Save output
        # out_path = os.path.join(
        #     OUTPUT_DIR,
        #     f"reextracted_{month_start}_to_{month_end}.parquet"
        # )
        # headline_updated_df.to_parquet(out_path, index=False)
        # print(f"\n✔ Saved re-extracted headlines to {out_path}")

        return run_batch_step2(headline_updated_df, start, end, total_start)


     # 1. Load all peviously cached parsed parquet files in range
    
    for fname in sorted(os.listdir(CACHE_PARSED_DIR)):
        
        if not fname.endswith(".parquet"):
            continue
        ts_str = fname.replace(".parquet", "")

        # Skip files before range
        if ts_str < start_ts_str:
            continue

        # Stop scanning once we pass the end of the range
        if ts_str > end_ts_str:
            break
        
        # Track that this timestamp exists in cache
        existing_ts.add(ts_str)
        path = os.path.join(CACHE_PARSED_DIR, fname)
        try:
            df = pd.read_parquet(path)
            df["date"] = datetime.strptime(ts_str, "%Y%m%d%H%M%S")
            all_df.append(df)

        except Exception as e:
            print(f"❌ Failed to read parquet {fname}: {e}")
            # Optional: remove corrupted file so future runs don't choke
            # os.remove(path)
            continue

        # df = pd.read_parquet(os.path.join(CACHE_PARSED_DIR, fname))
        # df["date"] = datetime.strptime(ts_str, "%Y%m%d%H%M%S")
        # #print(f"FOUND EXISTING CACHE FILE FOR {ts_str}")
        # all_df.append(df)
       
    print("FINISHED loading all previously cached parsed parquet files in range")

    # === Determine which timestamps are missing ===
    # Generate all expected timestamps (15‑minute intervals)
    expected_ts = [
    ts for ts in generate_GDELT_timestamps(start_date, end_date)
    ]
    # Missing = expected - existing
    missing_ts = [ts for ts in expected_ts if ts not in existing_ts]
    parse_start = time.perf_counter()
    if missing_ts:
        print(f"\n{len(missing_ts)} Missing timestamps. Downloading and Parsing Now.")
        parquet_paths = parallel_parse_all(missing_ts, max_download_threads=32, max_parse_procs=5)
        new_dfs = [pd.read_parquet(p) for p in parquet_paths] 
        for df in new_dfs:
            df["date"] = pd.to_datetime(
                df["GKGRECORDID"].str[:14],
                format="%Y%m%d%H%M%S"
            )

        all_df.extend(new_dfs)
    else:
        print("✔ No missing timestamps. Skipping parsing stage.")

    parse_end = time.perf_counter()
    print(f"\n⏱ Total PARSER runtime: {parse_end - parse_start:.2f} seconds")

    
    print("Downloaded + parse any missing timestamps within the range")
    print("Now combining all parsed parquets into a pandas DataFrame")
    combined_raw = pd.concat(all_df, ignore_index=True) #combines ALL PARSED PARQUET into a pandas DataFrame
    print("combined raw dataframe is this long: ", len(combined_raw))
    print(f"\n FINISHED COMBINING PARSED TIMESTAMPS \n")

    cache_key = f"{start}_to_{end_date.strftime('%Y-%m-%d_%H-%M-%S')}"
  
#-----------PARQUET IS FILTERED HERE ---------------------------
#------FUNCTION RETURNS A FILTERED PARQUET FILE (combined_df)----------
    print(f"\n NOW FILTERING LARGE PARQUET!")
    filter_start = time.perf_counter()
    combined_df= filter_crime(combined_raw, start_date, end_date, cache_key)
    filter_end = time.perf_counter()
    print(f"\n⏱ Total FILTER runtime: {filter_end - filter_start:.2f} seconds")

    if combined_df.empty:
        print("No London crime rows in entire range.")
        return

    #DROP UNUSED COLUMNS if not dropped already
    #COLUMNS ORIGINALLY DROPPED IN parser.py BUT THIS IS A DOUBLE CHECK
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


    ###########-----HEADLINE EXTRACTION------########################
    #--------parse through the website link column to create HEADLINE column-------------------
    print(f"Extracting headlines for {len(combined_df)} rows...")
    total_start = time.perf_counter()
    final_df = parallel_headline_extraction(combined_df, max_workers=36)
    total_end = time.perf_counter()
    print(f"\n⏱ Total HEADLINE EXTRACTION runtime: {total_end - total_start:.2f} seconds")
    #-------CALLS PART 2 OF RUN_BATCH THAT CONVERTS THE PARQUET TO A .CSV ------------------------
    # -------ALSO SAVES THE FINAL DATASET TO THE COMBINED FOLDER -----------------------
    run_batch_step2(final_df, start, end, total_start)


if __name__ == "__main__":
    total_pipeline_start = time.perf_counter()#start timer before the run_batch starts  
    
    #use this and comment the 6 lines below if you just want to run one year
    # year=2017o
    # run_year(year)

    #use this and comment the two lines above if you want to run multiple years:
    start_year = 2023
    end_year = 2027
    final_month = 12  # 3 == March 2026
    for year in range(start_year, end_year):
        print(f"\n▶ Processing full year: {year}")
        run_year(year)  


    total_pipeline_end = time.perf_counter() #end timer when whole year is processed
    print(
    f"\n⏱ Total pipeline runtime for {year}: "
    f"{total_pipeline_end - total_pipeline_start:.2f} seconds"
    )
    
