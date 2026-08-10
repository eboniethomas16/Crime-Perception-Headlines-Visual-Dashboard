# USED IN DISSERTATION TO CONVERT RAW CSV/XLSX FILES TO PARQUET FOR FASTER PROCESSING
# THESE PARQUETS ARE LATER USED IN THE Crime_data_cleaner to properly process datasets
import pandas as pd
from pathlib import Path
import pandas as pd
import datetime

RAW_FOLDER = Path(
    r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\MOPAC Data Cleaner\MOPAC Monthly Crime Data"
)

RAW_PARQUET_FOLDER = RAW_FOLDER / "raw_parquet"
RAW_PARQUET_FOLDER.mkdir(exist_ok=True)

def excel_serial_to_date(x):
    try:
        x = int(x)
        if x > 40000:  # Excel serial threshold
            return datetime.date(1899, 12, 30) + datetime.timedelta(days=x)
        return pd.NaT
    except:
        return pd.NaT
    
def convert_raw_to_parquet():
    all_files = [f for f in RAW_FOLDER.iterdir() if f.suffix.lower() in [".csv", ".xlsx", ".xls"]]

    if not all_files:
        raise RuntimeError("No raw CSV/XLSX files found in folder.")

    for file in all_files:
        out_path = RAW_PARQUET_FOLDER / (file.stem + ".parquet")

        if out_path.exists():
            print(f"Skipping (already exists): {out_path.name}")
            continue

        print(f"Converting to Parquet: {file.name}")

        if file.suffix.lower() == ".csv":
            df = pd.read_csv(file, encoding="utf-8-sig", low_memory=False)
        else:
            df = pd.read_excel(file)

        # ⭐ Normalize date columns BEFORE writing parquet
        for col in df.columns:
            if "date" in col.lower():
                # Convert Excel serials first
                df[col] = df[col].apply(excel_serial_to_date)

                # Then convert everything to datetime
                df[col] = pd.to_datetime(df[col], errors="coerce")

        df.to_parquet(out_path, index=False)
        print(f"  -> Saved: {out_path.name}")

    


if __name__ == "__main__":
    convert_raw_to_parquet()
    print("Finished converting all raw files to Parquet.")
