import pandas as pd
import itertools
import networkx as nx
import os
import matplotlib.pyplot as plt

# 1. Paths
input_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\GDELT_pipeline\data\combined_datasets\Updated Monthly Filtered Datasets\CLEANED Combined Datasets\London_Crime_combined_df_2020-04-01_to_2020-04-30_CLEANED.csv"
output_dir = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\GDELT_pipeline\Duplicate Headline Network Graphs"

os.makedirs(output_dir, exist_ok=True)

# 2. Load data
df = pd.read_csv(input_path, low_memory=False)

# 3. Apply filters
df = df[df['headline_is_duplicate'] == True]
df = df[df['crime_type'] != 'UNKNOWN']

# 4. Create duplicate group ID (identical headlines grouped)
df['duplicate_group_id'] = df.groupby('headline').ngroup()

# 5. Build directed edge list
edges = []
for group_id, g in df.groupby('duplicate_group_id'):
    sources = g['V2SOURCECOMMONNAME'].unique()
    for a, b in itertools.permutations(sources, 2):
        if a != b:
            edges.append((a, b))

edge_df = pd.DataFrame(edges, columns=['Source', 'Target'])
edge_df = edge_df.value_counts().reset_index(name='weight')

# 6. Build undirected graph
G = nx.Graph()
for _, row in edge_df.iterrows():
    G.add_edge(row['Source'], row['Target'], weight=row['weight'])

# 7. Save outputs
edges_out = os.path.join(output_dir, "headline_duplication_edges.csv")
nodes_out = os.path.join(output_dir, "headline_duplication_nodes.csv")

edge_df.to_csv(edges_out, index=False)
pd.DataFrame({'id': list(G.nodes())}).to_csv(nodes_out, index=False)

plt.figure(figsize=(14, 10))

pos = nx.spring_layout(G, k=0.5, iterations=50)

# draw nodes
nx.draw_networkx_nodes(G, pos, node_size=300, node_color='skyblue')

# draw edges with transparency
nx.draw_networkx_edges(G, pos, alpha=0.4)

# draw labels
nx.draw_networkx_labels(G, pos, font_size=8)

plt.title("Duplicate Headline Network (Directed)")
plt.axis('off')
plt.show()
