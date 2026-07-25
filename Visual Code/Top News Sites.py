import pandas as pd

# ---------------------------------------------------------
# 1. Load Excel file
# ---------------------------------------------------------
file_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Top News Sites.xlsx"
sheet_name = "Top News Outlets per year"

df = pd.read_excel(file_path, sheet_name=sheet_name)

# ---------------------------------------------------------
# 2. Normalization dictionary
# ---------------------------------------------------------
normalize = {
    "BBC News online": "BBC News Online",
    "BBC News Online": "BBC News Online",
    "The Daily Mail online": "The Daily Mail Online",
    "Mail Online": "The Daily Mail Online",
    "Guardian online": "Guardian Online",
    "Sky News online": "Sky News Online",
    "Yahoo! News": "Yahoo! News",
    "Regional or local newspaper website": "Regional/Local Newspaper",
    "Regional or local newspaper online": "Regional/Local Newspaper",
    "Mirror online": "Mirror Online",
    "Mirror Online": "Mirror Online",
    "Buzzfeed News": "BuzzFeed News",
    "BuzzFeed News": "BuzzFeed News",
    "Independent/i100 online": "Independent/i100 Online",
    "Independent/ i1oo online": "Independent/i100 Online",
    "Sun online": "Sun Online",
    "The Lad Bible": "The Lad Bible",
    "The Lad Bible news": "The Lad Bible",
    "The Times online": "The Times Online",
    "Other commercial radio news online": "Other Commercial Radio News Online",
    "CNN online": "CNN Online",
    "Al Jazeera online": "Al Jazeera Online",
    "Financial Times online": "Financial Times Online",
    "MSN News": "MSN News",
    "Google News": "Google News",
    "Telegraph online": "Telegraph Online",
    "ITV News online": "ITV News Online",
    "Metro online": "Metro Online",
    "GB News online": "GB News Online"
}

# ---------------------------------------------------------
# 3. Domain lookup
# ---------------------------------------------------------
domains = {
    "BBC News Online": "bbc.co.uk",
    "The Daily Mail Online": "dailymail.co.uk",
    "Sky News Online": "news.sky.com",
    "Yahoo! News": "news.yahoo.com",
    "Regional/Local Newspaper": "VARIES_BY_PUBLICATION",
    "Guardian Online": "theguardian.com",
    "Google News": "news.google.com",
    "Huffington Post": "huffpost.com",
    "MSN News": "msn.com",
    "Telegraph Online": "telegraph.co.uk",
    "Sun Online": "thesun.co.uk",
    "Mirror Online": "mirror.co.uk",
    "BuzzFeed News": "buzzfeednews.com",
    "Independent/i100 Online": "independent.co.uk",
    "Metro Online": "metro.co.uk",
    "ITV News Online": "itv.com/news",
    "The Lad Bible": "ladbible.com",
    "The Times Online": "thetimes.co.uk",
    "GB News Online": "gbnews.com",
    "Other Commercial Radio News Online": "VARIES_BY_STATION",
    "Al Jazeera Online": "aljazeera.com",
    "CNN Online": "cnn.com",
    "Financial Times Online": "ft.com"
}

# ---------------------------------------------------------
# 4. Normalize all outlet names
# ---------------------------------------------------------
df = df.applymap(lambda x: normalize.get(x, x) if isinstance(x, str) else x)

# ---------------------------------------------------------
# 5. Compute metrics
# ---------------------------------------------------------
results = []
years = df.columns.tolist()

for outlet in pd.unique(df.values.ravel()):
    if pd.isna(outlet):
        continue

    occ_years = []
    ranks = []

    for year in years:
        print("Analyzing years:", years)
        col = df[year].tolist()
        if outlet in col:
            rank = col.index(outlet) + 1  # rank = row index + 1
            occ_years.append(int(year))
            ranks.append((rank, int(year)))

    if not occ_years:
        continue

    first_appearance = min(occ_years)
    num_occurrences = len(occ_years)
    highest_rank, year_of_highest = min(ranks, key=lambda x: x[0])

    results.append({
        "Outlet": outlet,
        "Domain": domains.get(outlet, "UNKNOWN"),
        "FirstAppearance": first_appearance,
        "NumberOfOccurrences": num_occurrences,
        "HighestRank": highest_rank,
        "YearOfHighestRank": year_of_highest
    })

# ---------------------------------------------------------
# 6. Write results to a NEW sheet in the SAME Excel file
# ---------------------------------------------------------
final_df = pd.DataFrame(results)

with pd.ExcelWriter(file_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
    final_df.to_excel(writer, sheet_name="Top News Outlets Summary", index=False)

print("Summary sheet created successfully.")
