import pandas as pd
import itertools
import networkx as nx
import os
import glob

# 1. Paths
input_folder = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\GDELT_pipeline\data\combined_datasets\Updated Monthly Filtered Datasets\CLEANED Combined Datasets"
output_folder = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\GDELT_pipeline\Duplicate Headline Network Graphs"

os.makedirs(output_folder, exist_ok=True)

# 2. Loop through all CSV files
csv_files = glob.glob(os.path.join(input_folder, "*.csv"))

for file_path in csv_files:
    print(f"Processing: {file_path}")

    # Extract month label from filename
    file_name = os.path.basename(file_path)
    month_label = file_name.replace(".csv", "")

    # 3. Load data
    df = pd.read_csv(file_path, low_memory=False)

    # 4. Apply filters
    df = df[df['headline_is_duplicate'] == True]
    df = df[df['crime_type'] != 'UNKNOWN']

    # Skip empty files after filtering
    if df.empty:
        print(f"Skipping {file_name}: no duplicate headlines after filtering.")
        continue

    # 5. Create duplicate group ID
    df['duplicate_group_id'] = df.groupby('headline').ngroup()

    # 6. Build undirected edges
    edges = []
    for group_id, g in df.groupby('duplicate_group_id'):
        sources = g['V2SOURCECOMMONNAME'].unique()
        for a, b in itertools.combinations(sorted(sources), 2):
            edges.append((a, b))

    # 7. Aggregate weights
    edge_df = pd.DataFrame(edges, columns=['source_a', 'source_b'])
    edge_df = edge_df.value_counts().reset_index(name='weight')

    # 8. Build undirected graph
    G = nx.Graph()
    for _, row in edge_df.iterrows():
        G.add_edge(row['source_a'], row['source_b'], weight=row['weight'])

    # 9. Save outputs
    edges_out = os.path.join(output_folder, f"undirected_duplication_edges_{month_label}.csv")
    nodes_out = os.path.join(output_folder, f"undirected_duplication_nodes_{month_label}.csv")

    edge_df.to_csv(edges_out, index=False)
    pd.DataFrame({'id': list(G.nodes())}).to_csv(nodes_out, index=False)

    print(f"Saved: {edges_out}")
    print(f"Saved: {nodes_out}")

print("All files processed.")
