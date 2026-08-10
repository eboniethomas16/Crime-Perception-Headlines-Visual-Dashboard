import pandas as pd

#the "extract_tone(df)" function prepares the GDELT data for aggregation by extracting two key fields:
#- tone (sentiment)
    #the average “tone” of the document as a whole. The score ranges from -100 (extremely negative) to +100 (extremely positive). Common
    #values range between -10 and +10, with 0 indicating neutra

 #strips the V1TONE value into a list by the ",". we just need the first element hence [0]
#also converts it from a string into a numeric float
def extract_tone(df):
    # Tone from V2TONE
    if "V1.5TONE" in df.columns:
        df["tone"] = (
            df["V1.5TONE"]
            .str.split(",", expand=True)[0]
            .apply(pd.to_numeric, errors="coerce")
        )
    else:
        df["tone"] = None
    return df


#"aggregate_daily(df)" function takes the processed DataFrame and produces a daily sentiment time series.
# def aggregate_daily(df):
#     daily = (df.groupby(df["date"].dt.date)["tone"].mean().reset_index().rename(columns={"date": "Date", "tone": "Tone"})
#               )
#     return daily

    #df["date"].dt.date - Extracts the date only (no time) from the datetime.
    #df.groupby(... ) - Groups all rows by their date. All GDELT entries from the same day are grouped together.
    #["tone"].mean() - Computes the average tone for each day. 
    #.reset_index() - Converts the grouped result back into a clean DataFrame.


#final output looks something like:
    #  Date         tone
    #2025-02-14     1.23
    #2025‑02‑15    -0.45