import os
import requests
import pandas as pd
from bs4 import SoupStrainer
from selectolax.parser import HTMLParser
from urllib.parse import urlparse
import re
from config import ACRONYMS, STOPWORDS

import unicodedata
#from run_batch import run_batch_step2
from config import OUTPUT_DIR#, CACHE_FILTERED
#from concurrent.futures import ProcessPoolExecutor, as_completed
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import threading
from tqdm import tqdm


#from config import CACHE_FILTERED
# Adjust these paths to match your pipeline
CACHE_FILTERED_DIR = "cache_filtered"
CACHE_ENRICHED_DIR = "cache_enriched"


os.makedirs(CACHE_ENRICHED_DIR, exist_ok=True)



conn = sqlite3.connect("headline_cache.db", check_same_thread=False)
cursor = conn.cursor()
# Create table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS cache (
    url TEXT PRIMARY KEY,
    headline TEXT
)
""")
conn.commit()

# Lock for thread safety
cache_lock = threading.Lock()


session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"
})

#HEADLINE_CACHE = shelve.open("headline_cache.db", writeback=True)

STRAINER = SoupStrainer(["meta", "title"])


def normalize_word(w: str) -> str:
    w_lower = w.lower().strip()

    # Preserve acronyms in uppercase
    if w_lower in ACRONYMS:
        return w_lower.upper()

    # Preserve numbers and mixed alphanumerics
    if any(ch.isdigit() for ch in w_lower):
        return w_lower

    # Otherwise return lowercase word
    return w_lower


#NOTE: This function is redefined every time enrich_filtered_parquet runs.
            #It should be defined once at module level for performance
def extract_and_clean(url): #Calls the headline extractor.
    headline = extract_headline(url)
    if not isinstance(headline, str): #-If the result isn’t a string, returns it unchanged.
        return headline
        #Otherwise normalizes Unicode to NFC.
    headline = unicodedata.normalize("NFC", headline)
    return headline

def extract_headline_from_url(url: str) -> str | None:
    try:
        path = urlparse(url).path.strip("/")
        parts = path.split("/")

        slug = parts[-1]

        # Daily Mail pattern: /article-####/<slug>.html
        if len(parts) >= 2 and parts[-2].startswith("article-"):
            slug = parts[-1]

        # Remove .html or similar
        slug = re.sub(r"\.html?$", "", slug)

        # Remove Reuters-style IDs: -idUKXXXX
        slug = re.sub(r"-id[A-Za-z0-9]+$", "", slug)

        # Remove long numeric IDs (but keep meaningful numbers)
        slug = re.sub(r"-(\d{6,})$", "", slug)

        # Split on hyphens
        words = slug.split("-")

        cleaned = []
        for w in words:
            # Keep letters, digits, hyphens inside numbers
            w = re.sub(r"[^\w\d-]", "", w).strip()
            if w:
                cleaned.append(normalize_word(w))

        if not cleaned:
            return None

        return " ".join(cleaned)

    except Exception:
        return None

def get_cached_headline(url: str):
    with cache_lock:
        cursor.execute("SELECT headline FROM cache WHERE url = ?", (url,))
        row = cursor.fetchone()
        return row[0] if row else None


def set_cached_headline(url: str, headline: str | None):
    with cache_lock:
        cursor.execute(
            "INSERT OR REPLACE INTO cache (url, headline) VALUES (?, ?)",
            (url, headline)
        )
        conn.commit()

def extract_headline(url: str) -> str | None:
    """
    Fetch a webpage and extract its headline using common metadata fields.
    Returns None if the headline cannot be extracted.
    """
    cached = get_cached_headline(url)
    # if cached is not None:
    #     return cached
    if cached not in (None, "__MISSED HEADLINE__", ""):
        return cached
    #--------USING HEADLINE CACHE----------------
    # -------------------------------
    # 2. Validate URL
    # -------------------------------
    if not isinstance(url, str) or not url.startswith("http"):
        return None

    # -------------------------------
    # 3. Download page
    # -------------------------------
    try:
        response = session.get(url, timeout=4)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or response.encoding or "utf-8"
        html = response.text
    except Exception:
        # Fallback: try to recover headline from URL slug
        slug_headline = extract_headline_from_url(url)
        if slug_headline:
            set_cached_headline(url, slug_headline)
            return slug_headline
        return None

    tree = HTMLParser(html)

    # 1. OpenGraph title
    og = tree.css_first('meta[property="og:title"]')
    if og and og.attributes.get("content"):
        headline = og.attributes["content"].strip()
        set_cached_headline(url, headline)
        return headline

    # 2. Twitter title

    tw = tree.css_first('meta[name="twitter:title"]')
    if tw and tw.attributes.get("content"):
        headline = tw.attributes["content"].strip()
        set_cached_headline(url, headline)
        return headline

    # 3. <title> fallback
    #GRABS HTML <title>
    title = tree.css_first("title")
    if title and title.text():
        headline = title.text().strip()
        set_cached_headline(url, headline)
        return headline



    set_cached_headline(url, "__MISSED HEADLINE__")  # 5. Cache the miss
    return None



#------------------------------------------------------------------------------------------------------
#------ MAIN RUN BATCH FUNCTION THAT STARTS CREATION OF "HEADLINE" COLUMN------------------------------
#------------------------------------------------------------------------------------------------------
def parallel_headline_extraction(filtered_df, max_workers):
    if filtered_df.empty:
        return filtered_df

    urls = filtered_df["V1DOCUMENTIDENTIFIER"].tolist()

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        headlines = list(
            tqdm(
                ex.map(extract_and_clean, urls),
                total=len(urls),
                desc="⚡ Fetching headlines",
                unit="url"
            )
        )

    filtered_df = filtered_df.copy()
    filtered_df["headline"] = headlines
    return filtered_df


#NEW FIX FOR DUPLICATE HEADLINE EXTRACTION
def extract_article_id(url: str) -> str | None:
    """
    Extracts the numeric article ID from a URL.
    Example: '.../11879917.display/' → '11879917'
    """
    # if not isinstance(url, str):
    #     return None
    # match = re.search(r"/(\d{6,})[./]", url)
    # return match.group(1) if match else None

    if not isinstance(url, str):
        return None

    # Unified pattern: digits after "/" and before "." or "/"
    match = re.search(r"/(\d{6,})(?=[./])", url)
    return match.group(1) if match else None

def is_same_article(row, other_row):
    """
    Returns True if two rows represent the same article:
    Same source + same article ID.
    """
    id1 = extract_article_id(row["V1DOCUMENTIDENTIFIER"])
    id2 = extract_article_id(other_row["V1DOCUMENTIDENTIFIER"])

    same_source = row["V2SOURCECOMMONNAME"] == other_row["V2SOURCECOMMONNAME"]
    same_id = (id1 is not None and id1 == id2)

    return same_source and same_id

def correct_false_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fix duplicate flags by ensuring that:
    If rows share the same source + article ID but have different headlines,
    they are NOT duplicates.
    """
    df = df.copy()

    # Precompute article_id
    df["article_id"] = df["V1DOCUMENTIDENTIFIER"].apply(extract_article_id)

    corrected = df["headline_is_duplicate"].copy()

    # Group by source + article_id
    grouped = df.groupby(["V2SOURCECOMMONNAME", "article_id"])

    for (_, article_id), group in grouped:
        # Skip groups with no valid article_id
        if article_id is None:
            continue

        # If same article has multiple different headlines → not duplicates
        if group["headline"].nunique() > 1:
            corrected.loc[group.index] = False
    df["headline_is_duplicate"] = corrected
    df = df.drop(columns=["article_id"])
    return df


def enrich_filtered_csv(input_csv_path: str, output_csv_path: str):
    
    """
    Standalone function.
    Takes a filtered CSV file and writes a new CSV with an added 'headline' column.
    """

    print(f"Loading filtered CSV: {input_csv_path}")
    df = pd.read_csv(input_csv_path) #gets csv from combined csv folder

    if "V1DOCUMENTIDENTIFIER" not in df.columns:
        raise ValueError("CSV is missing the 'V1URV1DOCUMENTIDENTIFIER' column required for headline extraction.")
        
    #FIX THIS BEFORE RUNNING cache_key = 
    print(f"Extracting headlines for {len(df)} rows...")
    df["headline"] = df["V1DOCUMENTIDENTIFIER"].apply(extract_headline)

    #---------rearrange headlines----------------
    first_cols = ["date", "tone", "daily_avg_tone","crime_mentions","headline","V1DOCUMENTIDENTIFIER", "V2ENHANCEDTHEMES","V2SOURCECOMMONNAME"]
    other_cols = [c for c in df.columns if c not in first_cols]
    df = df[first_cols + other_cols]

    # --------- Build output filename ---------
    # Extract date range from the input filename
    filename = os.path.basename(input_csv_path)
    name_without_ext = os.path.splitext(filename)[0]

    output_filename = f"{name_without_ext}_ENRICHED.csv"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    print(f"Saving enriched CSV to: {output_path}")
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print("✔ CSV successfully enriched with headlines.")
   
    return output_path


# def extract_headlines_chunk(df_chunk):
#     df_chunk = df_chunk.copy()
#     headlines = []
#     for url in df_chunk["V1DOCUMENTIDENTIFIER"]:
#         try:
#             headline = extract_and_clean(url)   # YOUR HTML SCRAPER
#         except Exception:
#             headline = None
#         headlines.append(headline)

#     df_chunk = df_chunk.copy()
#     df_chunk["headline"] = headlines
#     return df_chunk


# def enrich_filtered_parquet(df):
#      #Prints how many rows will be processed.
#     headlines = [] #Prepares a list to store extracted headlines.

    
#     for i, url in enumerate(df["V1DOCUMENTIDENTIFIER"]): #Loops through every row's URL and extracts headlines
#         headlines.append(extract_and_clean(url))
#         #Appends the result to the list created earlier
#         #calls the extract_and_clean function which then calls the extract_headline
#         if (i + 1) % 500 == 0:
#             print(f"  → Processed {i + 1:,} / {len(df):,} rows")# Prints progress every 500 rows
    
    

#     print("✔ DataFrame successfully enriched with headlines.")
#     df["headline"] = headlines #Adds the new column to the DataFrame
  
#     return df


# def enrich_month_with_headlines(year: int, month: int):
#     from run_batch import run_batch_step2
#     """
#     Load a monthly crime-filtered parquet, extract headlines for each URL,
#     and save an enriched parquet with a new 'headline' column.
#     """

#     month_key = f"{year}{month:02d}"
#     input_path = os.path.join(CACHE_FILTERED_DIR, f"{month_key}.parquet")

#     if not os.path.exists(input_path):
#         print(f"No filtered parquet found for {month_key}")
#         return

#     print(f"Loading filtered parquet for {month_key}...")
#     df = pd.read_parquet(input_path)

#     if "V1DOCUMENTIDENTIFIER" not in df.columns:
#         print("Error: V1DOCUMENTIDENTIFIER column missing from filtered dataset")
#         return

#     print(f"Extracting headlines for {len(df)} URLs...")

#     headlines = []
#     for i, url in enumerate(df["V1DOCUMENTIDENTIFIER"]):
#         headline = extract_headline(url)
#         headlines.append(headline)

#         # Light rate limiting to avoid hammering servers
#         time.sleep(0.2)

#         if i % 100 == 0:
#             print(f"Processed {i} URLs...")

#     df["headline"] = headlines

#     output_path = os.path.join(CACHE_ENRICHED_DIR, f"{month_key}_enriched.parquet")
#     df.to_parquet(output_path, index=False)
#     #run_batch_step2(df)
#     print(f"✔ Saved enriched parquet: {output_path}")

import atexit

def _close_cache():
    try:
        conn.close()
    except:
        pass

atexit.register(_close_cache)



if __name__ == "__main__":
    #import sys

    # if len(sys.argv) != 3:
    #     print("Usage: py headline_enricher.py YEAR MONTH")
    #     sys.exit(1)

    # year = int(sys.argv[1])
    # month = int(sys.argv[2])
    input_csv = r"data\combined_datasets\London_Crime_Combined_2026-02-28_to_2026-03-01.csv"
    output_csv =r"data\combined_datasets\London_Crime_Combined_2026-02-28_to_2026-03-01_enriched.csv" 
    enrich_filtered_csv(input_csv, output_csv)

    #enrich_month_with_headlines(year, month)