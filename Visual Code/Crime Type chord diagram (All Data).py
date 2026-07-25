import pandas as pd
import numpy as np
import itertools
import os
import matplotlib.pyplot as plt
from mpl_chord_diagram import chord_diagram   # LOCAL renderer from GitHub repo

# ---------------------------------------------------------
# 1. File paths
# ---------------------------------------------------------
input_folder = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\GDELT_pipeline\data\combined_datasets\Updated Monthly Filtered Datasets\CLEANED Combined Datasets"

output_folder = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\GDELT_pipeline\Chord Diagram Output"
output_png = os.path.join(output_folder, "crime_type_chord_diagram_all_data.png")

os.makedirs(output_folder, exist_ok=True)
# Path to matrix CSV
matrix_csv = os.path.join(output_folder, "crime_type_cooccurrence_matrix.csv")

# If matrix already exists, load it and skip all dataset iteration
# Goes straight to formatting the chord diagram
if os.path.exists(matrix_csv):
    print("Matrix CSV already exists — skipping dataset iteration.")
    matrix_df = pd.read_csv(matrix_csv, index_col=0)
    crime_types = list(matrix_df.index)
    matrix = matrix_df.values
else:
    print("Matrix CSV not found — generating from all datasets...")

    # ---------------------------------------------------------
    # 2. Load ALL CSVs in the folder (if not previously loaded)
    # ---------------------------------------------------------
    all_files = [f for f in os.listdir(input_folder) if f.endswith(".csv")]

    crime_lists = []

    for file in all_files:
        path = os.path.join(input_folder, file)
        df = pd.read_csv(path, low_memory=False)

        if "crime_types" not in df.columns:
            continue

        df["crime_types"] = df["crime_types"].fillna("").astype(str).str.strip()

        # Keep only rows with multiple crime types
        df_multi = df[df["crime_types"].str.contains(",")].copy()

        # Deduplicate on headline (critical!)
        df_multi = df_multi.drop_duplicates(subset=['headline','crime_types'])

        # Split into lists
        df_multi["crime_list"] = df_multi["crime_types"].str.split(",")
        df_multi["crime_list"] = df_multi["crime_list"].apply(lambda lst: [x.strip() for x in lst])

        # Collect lists
        crime_lists.extend(df_multi["crime_list"].tolist())

    # ---------------------------------------------------------
    # 3. Build co-occurrence pairs across ALL files
    # ---------------------------------------------------------
    pair_counts = {}

    for lst in crime_lists:
        for a, b in itertools.combinations(sorted(set(lst)), 2):
            pair_counts[(a, b)] = pair_counts.get((a, b), 0) + 1

    # ---------------------------------------------------------
    # 4. Build list of unique crime types
    # ---------------------------------------------------------
    crime_types = sorted({c for pair in pair_counts.keys() for c in pair})
    index_map = {c: i for i, c in enumerate(crime_types)}

    # ---------------------------------------------------------
    # 4b. Apply minimum frequency threshold
    # ---------------------------------------------------------
    MIN_FREQ = 1   # adjust as needed

    pair_counts = {pair: count for pair, count in pair_counts.items() if count >= MIN_FREQ}

    print(f"Pairs kept after threshold {MIN_FREQ}: {len(pair_counts)}")

    # ---------------------------------------------------------
    # 5. Build co-occurrence matrix
    # ---------------------------------------------------------
    n = len(crime_types)
    matrix = np.zeros((n, n), dtype=int)

    for (a, b), count in pair_counts.items():
        i, j = index_map[a], index_map[b]
        matrix[i, j] = count
        matrix[j, i] = count

    # ---------------------------------------------------------
    # 5b. Export co-occurrence matrix for debugging
    # ---------------------------------------------------------
    matrix_df = pd.DataFrame(matrix, index=crime_types, columns=crime_types)

    matrix_csv = os.path.join(output_folder, "crime_type_cooccurrence_matrix.csv")
    matrix_df.to_csv(matrix_csv, encoding="utf-8-sig")

    print(f"Co-occurrence matrix exported to:\n{matrix_csv}")


# ---------------------------------------------------------
# 6. Render chord diagram
# ---------------------------------------------------------
plt.figure(figsize=(12, 12))

plt.rcParams.update({
    "font.size": 6,
    "axes.titlesize": 10,
})

chord_diagram(
    matrix,
    names=crime_types,
    sort="size",
    cmap="tab20",
    chordwidth=0.7,
    pad=2,
    gap=0.03,
    fontsize=6,
    rotate_names=90
)

plt.suptitle("Crime Type Co-Occurrence Chord Diagram (All Data)", fontsize=7)
plt.subplots_adjust(
    top=0.85,     # lower this to push diagram down
    bottom=0.2,  # raise this to add space below
)
#plt.tight_layout()

# ---------------------------------------------------------
# 7. Save output locally
# ---------------------------------------------------------
plt.savefig(output_png, dpi=300)
plt.close()

print(f"Chord diagram saved to:\n{output_png}")
