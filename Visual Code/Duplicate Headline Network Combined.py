import pandas as pd
import itertools
import networkx as nx
import os
import glob
import matplotlib.pyplot as plt
import community as community_louvain
from pyvis.network import Network
import math
from collections import defaultdict


# ---------------------------------------------------------
# 0. Setup
# ---------------------------------------------------------
import os, glob, itertools, math
import pandas as pd
import networkx as nx
from pyvis.network import Network
from collections import defaultdict
import community.community_louvain as community_louvain

input_folder = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\GDELT_pipeline\data\combined_datasets\Updated Monthly Filtered Datasets\CLEANED Combined Datasets"
output_folder = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Visual Python Code\Duplicate Headline Network Graphs"

edges_out = os.path.join(output_folder, "giant_duplication_network_edges.csv")
nodes_out = os.path.join(output_folder, "giant_duplication_network_nodes.csv")
temporal_edges_out = os.path.join(output_folder, "temporal_duplication_edges.csv")

csv_files = sorted(glob.glob(os.path.join(input_folder, "*CLEANED.csv")))

all_edges = []              # for static giant network
temporal_edges = []         # for monthly time‑slider network

# ---------------------------------------------------------
# 1. Process each monthly file
# ---------------------------------------------------------
print("Building networks from scratch...")

for file_path in csv_files:
    print(f"Processing: {file_path}")

    df = pd.read_csv(file_path, low_memory=False)

    # Filters
    df = df[df['headline_is_duplicate'] == True]
    df = df[df['crime_type'] != 'UNKNOWN']

    if df.empty:
        print("No duplicates after filtering — skipping.")
        continue

    # Clean source names
    df['V2SOURCECOMMONNAME'] = (
        df['V2SOURCECOMMONNAME']
        .str.split('.').str[0]
        .str.upper()
        .str.replace(" ", "")
    )

    # Extract YYYY-MM from date
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['month'] = df['date'].dt.to_period("M").astype(str)

    # Deduplicate (headline, source)
    df = df.drop_duplicates(subset=['headline', 'V2SOURCECOMMONNAME'])

    # Group identical headlines
    df['duplicate_group_id'] = df.groupby('headline').ngroup()

    # Build edges
    for group_id, g in df.groupby('duplicate_group_id'):
        sources = sorted(g['V2SOURCECOMMONNAME'].unique())

        # Skip groups with <2 sources
        if len(sources) < 2:
            continue

        # Month for this headline group
        month = g['month'].iloc[0]

        # Build all pairwise edges
        for a, b in itertools.combinations(sources, 2):

            # Add to static giant network
            all_edges.append((a, b))

            # Add to temporal network
            temporal_edges.append((a, b, month))

# ---------------------------------------------------------
# 2. Build static giant network (aggregated)
# ---------------------------------------------------------
edge_df = pd.DataFrame(all_edges, columns=['source', 'target'])
edge_df = edge_df.value_counts().reset_index(name='weight')

# Build graph
G = nx.Graph()
for _, row in edge_df.iterrows():
    G.add_edge(row['source'], row['target'], weight=row['weight'])

print(f"\nTotal nodes: {G.number_of_nodes()}")
print(f"Total edges: {G.number_of_edges()}")

# Louvain clustering
partition = community_louvain.best_partition(G, weight='weight')
nx.set_node_attributes(G, partition, "cluster")

# Save static outputs
edge_df.to_csv(edges_out, index=False)
pd.DataFrame({
    'node': list(G.nodes()),
    'cluster': [partition[n] for n in G.nodes()]
}).to_csv(nodes_out, index=False)

print(f"\nSaved static edge list to: {edges_out}")
print(f"Saved static node list to: {nodes_out}")

# ---------------------------------------------------------
# 3. Build temporal edge list (for time slider)
# ---------------------------------------------------------
temporal_df = pd.DataFrame(temporal_edges, columns=['source', 'target', 'date'])

# Count edges per month per pair
temporal_df = (
    temporal_df
    .groupby(['source', 'target', 'date'])
    .size()
    .reset_index(name='weight')
)

# Save temporal edges
temporal_df.to_csv(temporal_edges_out, index=False)
print(f"Saved temporal edge list to: {temporal_edges_out}")

# ---------------------------------------------------------
# 4. Build PyVis interactive network (static)
# ---------------------------------------------------------
net = Network(
    height="1200px",
    width="100%",
    bgcolor="#ffffff",
    font_color="black",
    notebook=False
)

net.from_nx(G)

# Style nodes
for n in net.nodes:
    node_id = n['id']
    n['color'] = f"hsl({(partition[node_id] * 40) % 360}, 70%, 50%)"
    deg = G.degree(node_id, weight='weight')
    n['size'] = min(40, deg * 5)
    n['font'] = {'size': 20}

# Style edges
for e in net.edges:
    u = e['from']
    v = e['to']
    w = G[u][v].get('weight', 1)
    e['width'] = 1 + math.log1p(w) * 0.8

# Add cluster groups
for n in net.nodes:
    n['group'] = partition[n['id']]

# Save HTML
output_html = os.path.join(output_folder, "giant_duplication_network_interactive.html")
net.write_html(output_html)

print("Interactive PyVis network saved to:", output_html)
