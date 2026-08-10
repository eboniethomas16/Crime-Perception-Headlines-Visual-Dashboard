import os
import zipfile
import pandas as pd
from config import CACHE_PARSED_DIR, GDELT_BASE
import pyarrow.csv as pv
import io
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
import requests
from tqdm import tqdm
import pyarrow.parquet as pq


 
#this file takes a raw GDELT 2.0 ZIP file, extracts the CSV within it,
#assignes the correct column names,
#and saves a clean, readable CSV for downstream processing.
#ZIP → CSV → DataFrame → Cleaned CSV

GDELT_COLUMNS = [
    "GKGRECORDID",             
    "V2.1DATE",                
    "V2SOURCECOLLECTIONID",   
    "V2SOURCECOMMONNAME",      
    "V1DOCUMENTIDENTIFIER",    
    "V1COUNTS",                
    "V2.1COUNTS",
    "V1THEMES",                
    "V2ENHANCEDTHEMES",
    "V1LOCATIONS",
    "V2ENHANCEDLOCATIONS",
    "V1PERSONS",               
    "V2ENHANCEDPERSONS",
    "V1ORGANIZATIONS",         
    "V2ENHANCEDORGANIZATIONS",
    "V1.5TONE",                
    "V2.1ENHANCEDDATES",
    "V2GCAM",
    "V2.1SHARINGIMAGE",
    "V2.1RELATEDIMAGES",
    "V2.1SOCIALIMAGEEMBEDS",
    "V2.1SOCIALVIDEOEMBEDS",
    "V2.1QUOTATIONS",
    "V2.1ALLNAMES",
    "V2.1AMOUNTS",
    "V2.1TRANSLATIONINFO",
    "V2EXTRASXML"
]

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

EXPECTED_COLS = len(GDELT_COLUMNS)
os.makedirs(CACHE_PARSED_DIR, exist_ok=True)

# ---------------------------------------------------------
# 1. THREAD-BASED DOWNLOAD FUNCTION
# ---------------------------------------------------------
def download_timestamp(ts):
    session = requests.Session()
    url = f"{GDELT_BASE}{ts}.gkg.csv.zip"

    try:
        r = session.get(url, timeout=10)
        r.raise_for_status()
    except Exception as e:
        # print(f"✖ Download failed for {ts}: {e}")
        return None

    return (ts, r.content)   # ← return timestamp + raw ZIP bytes


# ---------------------------------------------------------
# 2. PROCESS-BASED PARSE FUNCTION
# ---------------------------------------------------------
def parse_timestamp(download_result):
    if download_result is None:
        return None

    ts, zip_bytes = download_result

    return parse_GDELT_stream(zip_bytes, ts, CACHE_PARSED_DIR)




def parallel_parse_all(missing_ts, max_download_threads, max_parse_procs):
    # -------------------------
    # 1. DOWNLOAD WITH THREADS
    # -------------------------
    zip_paths = []
    with ThreadPoolExecutor(max_workers=max_download_threads) as ex:
        download_futures = {ex.submit(download_timestamp, ts): ts for ts in missing_ts}       

        for future in tqdm(as_completed(download_futures), total=len(download_futures),                           
                           desc="📥 Downloading GDELT ZIPs",
                           unit="file",
                           dynamic_ncols=True):
            result = future.result()
            if result:
                zip_paths.append(result)
    # -------------------------
    # 2. PARSE WITH PROCESSES
    # -------------------------
    parquet_paths = []
    with ProcessPoolExecutor(max_workers=max_parse_procs) as ex:
        parse_futures = {ex.submit(parse_timestamp, zp): zp for zp in zip_paths}

        parquet_paths = []
        for future in tqdm(as_completed(parse_futures), total=len(parse_futures),
                           desc="Parsing GDELT Streams",
                           unit="file",
                           dynamic_ncols=True):
            try:
                result = future.result()   # <-- this is where worker exceptions surface
                if result:
                    parquet_paths.append(result)
            except Exception as e:
                ts = parse_futures[future]
                print(f"❌ Parse failed for {ts}")
                # optionally log traceback:
                # import traceback; traceback.print_exc()
                continue
            
    return parquet_paths


def parse_GDELT_stream(zip_bytes,timestamp, Output_directory):
        """
    Replacement for parse_GDELT_file(zip_path).
    Takes ZIP bytes in memory and returns a parsed pandas DataFrame.
    """  
        parsed_path = os.path.join(Output_directory, f"{timestamp}.parquet")
        try:
            # Open ZIP from bytes
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
                csv_name = z.namelist()[0]  # GKG ZIP always contains one CSV

                with z.open(csv_name) as f:
                    table = pv.read_csv(
                        f,
                        parse_options=pv.ParseOptions(delimiter="\t"),
                        convert_options=pv.ConvertOptions(strings_can_be_null=True)
                    )
                    df = table.to_pandas()

        except Exception as e:
            # print("✖ Parse failed:", e)
            return None

        # Validate column count
        if df.shape[1] < EXPECTED_COLS:
            print(f"✖ Unexpected column count: {df.shape[1]} (expected ≥ {EXPECTED_COLS})")
            return None

        # Assign minimal schema
        df = df.iloc[:, :EXPECTED_COLS]
        df.columns = GDELT_COLUMNS

        # ---------DROP UNWANTED COLUMNS --------------
        df = df.drop(columns=cols_to_drop, errors="ignore")

        # ---------- SAVE PARSED PARQUET FILE ---------------------------
        df.to_parquet(parsed_path, index=False)
        #print(f"✔ Saved parsed parquet: {parsed_path}")

        return parsed_path #returns parsed_path. parquet can be combined later


# CHECKS IF A PARQUET IN FOLDER IS CORRUPTED
def is_parquet_corrupted(path):
    # A. Size check
    if os.path.getsize(path) < 1000:   # tiny parquet = corrupted
        return True

    # B. Magic bytes check
    with open(path, "rb") as f:
        start = f.read(4)
        f.seek(-4, os.SEEK_END)
        end = f.read(4)

    if start != b"PAR1" or end != b"PAR1":
        return True

    # C. Safe read check
    try:
        pq.read_table(path)
        return False
    except Exception:
        return True

# DELETES ANY CORRUPTED PARQUET FILES IN FOLDER  
def clean_corrupted_parquets(directory):
    removed = []

    for fname in os.listdir(directory):
        if not fname.endswith(".parquet"):
            continue

        path = os.path.join(directory, fname)

        if is_parquet_corrupted(path):
            print(f"🗑️ Removing corrupted parquet: {fname}")
            os.remove(path)
            removed.append(fname)

    return removed


