import pandas as pd
import numpy as np
import itertools
import os
import matplotlib.pyplot as plt
from mpl_chord_diagram import chord_diagram   # LOCAL renderer from GitHub repo

# ---------------------------------------------------------
# 1. File paths
# ---------------------------------------------------------
input_csv = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\GDELT_pipeline\data\combined_datasets\Updated Monthly Filtered Datasets\CLEANED Combined Datasets\London_Crime_combined_df_2020-04-01_to_2020-04-30_CLEANED.csv"

output_folder = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\GDELT_pipeline\Chord Diagram Output"
output_png = os.path.join(output_folder, "crime_type_chord_diagram.png")

os.makedirs(output_folder, exist_ok=True)

# ---------------------------------------------------------
# 2. Load dataset
# ---------------------------------------------------------
df = pd.read_csv(input_csv, low_memory=False)

if "crime_types" not in df.columns:
    raise ValueError("Column 'crime_types' not found in CSV")

df["crime_types"] = df["crime_types"].fillna("").astype(str).str.strip()

# Keep only rows with multiple crime types
df_multi = df[df["crime_types"].str.contains(",")].copy()

# Split into lists
df_multi["crime_list"] = df_multi["crime_types"].str.split(",")
df_multi["crime_list"] = df_multi["crime_list"].apply(lambda lst: [x.strip() for x in lst])

# ---------------------------------------------------------
# 3. Build co-occurrence pairs
# ---------------------------------------------------------
pair_counts = {}

for lst in df_multi["crime_list"]:
    for a, b in itertools.combinations(sorted(set(lst)), 2):
        pair_counts[(a, b)] = pair_counts.get((a, b), 0) + 1

# ---------------------------------------------------------
# 4. Build list of unique crime types
# ---------------------------------------------------------
crime_types = sorted({c for pair in pair_counts.keys() for c in pair})
index_map = {c: i for i, c in enumerate(crime_types)}

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
# 6. Render chord diagram locally (NO API)
# ---------------------------------------------------------
plt.figure(figsize=(12, 12))

chord_diagram(
    matrix,
    names=crime_types,
    sort="size",          # optional: sort arcs by total weight
    cmap="tab20",         # colour palette
    chordwidth=0.7,       # thickness of ribbons
    pad=2,                # spacing between arcs
    gap=0.03,              # gap between ribbons
    fontsize = 5,
    rotate_names = 90
)

plt.title("Crime Type Co-Occurrence Chord Diagram (April 2020)", fontsize=16)
plt.tight_layout()

# ---------------------------------------------------------
# 7. Save output locally
# ---------------------------------------------------------
plt.savefig(output_png, dpi=300)
plt.close()

print(f"Chord diagram saved to:\n{output_png}")
