import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import os

# ---------------------------------------------------------
# File paths
# ---------------------------------------------------------
crime_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Data_Visuals\Scrollytelling_draft\data\crime_borough_monthly.csv"
perception_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Data_Visuals\Scrollytelling_draft\data\MOPAC_FULL_LONG_Public_Perception.csv"
output_path = r"C:\Users\einob\OneDrive - King's College London\AA - Individual Project Files\Data_Visuals\Scrollytelling_draft\data"

# ---------------------------------------------------------
# 1. Load datasets
# ---------------------------------------------------------
crime_df = pd.read_csv(crime_path)
perception_df = pd.read_csv(perception_path)

# ---------------------------------------------------------
# 2. Convert dates
# ---------------------------------------------------------
crime_df['date'] = pd.to_datetime(crime_df['date'])
perception_df['date'] = pd.to_datetime(perception_df['date'])

# ---------------------------------------------------------
# 3. Build fiscal quarter → date mapping
# ---------------------------------------------------------
quarter_map = (
    perception_df[['quarter', 'date']]
    .drop_duplicates()
    .sort_values('date')
    .reset_index(drop=True)
)

quarter_map['date_str'] = quarter_map['date'].dt.strftime("%-m/%-d/%Y")

# ---------------------------------------------------------
# 4. Assign fiscal quarter to each crime date
# ---------------------------------------------------------
def assign_fiscal_quarter(crime_date):
    eligible = quarter_map[quarter_map['date'] <= crime_date]
    if len(eligible) == 0:
        return None
    return eligible.iloc[-1]['quarter']

crime_df['quarter'] = crime_df['date'].apply(assign_fiscal_quarter)

crime_df = crime_df.dropna(subset=['quarter'])

# ---------------------------------------------------------
# 5. Aggregate monthly crime → fiscal quarterly crime
# ---------------------------------------------------------
quarterly_crime = (
    crime_df.groupby(['borough', 'quarter'])['crime_count']
    .sum()
    .reset_index()
)

quarterly_crime = quarterly_crime.merge(
    quarter_map[['quarter', 'date_str']],
    on='quarter',
    how='left'
).rename(columns={'date_str': 'date'})

# ---------------------------------------------------------
# 6. Prepare wide-format output tables
# ---------------------------------------------------------
all_metrics = perception_df['metric'].unique()

borough_residuals_wide = quarterly_crime[['borough', 'quarter', 'date']].copy()
aggregated_residuals_wide = (
    quarterly_crime[['quarter', 'date']]
    .drop_duplicates()
    .sort_values('quarter')
    .copy()
)

# ---------------------------------------------------------
# 7. Loop through each perception metric
# ---------------------------------------------------------
for metric in all_metrics:

    metric_df = perception_df[perception_df['metric'] == metric].copy()

    merged = pd.merge(
        quarterly_crime,
        metric_df[['borough', 'quarter', 'metric_value']],
        on=['borough', 'quarter'],
        how='inner'
    )

    metric_residuals = []

    for borough, group in merged.groupby('borough'):
        if len(group) < 3:
            continue

        X = group[['crime_count']].values
        y = group['metric_value'].values

        model = LinearRegression().fit(X, y)
        predicted = model.predict(X)
        resid = y - predicted

        borough_residuals = pd.DataFrame({
            'borough': borough,
            'quarter': group['quarter'],
            'residual': resid
        })

        metric_residuals.append(borough_residuals)

    if len(metric_residuals) == 0:
        print(f"WARNING: No residuals for metric {metric}")
        continue

    metric_residual_df = pd.concat(metric_residuals, ignore_index=True)

    metric_col = metric.replace(" ", "_") + "_residual"

    borough_residuals_wide = borough_residuals_wide.merge(
        metric_residual_df[['borough', 'quarter', 'residual']],
        on=['borough', 'quarter'],
        how='left'
    ).rename(columns={'residual': metric_col})

    agg_residual = (
        metric_residual_df.groupby('quarter')['residual']
        .mean()
        .reset_index()
    )

    aggregated_residuals_wide = aggregated_residuals_wide.merge(
        agg_residual,
        on='quarter',
        how='left'
    ).rename(columns={'residual': metric_col})

# ---------------------------------------------------------
# 8. Save output CSVs
# ---------------------------------------------------------
borough_residuals_wide.to_csv(os.path.join(output_path, "borough_residuals_wide.csv"), index=False)
aggregated_residuals_wide.to_csv(os.path.join(output_path, "aggregated_residuals_wide.csv"), index=False)

print("Residual CSVs created successfully with correct fiscal quarter crime aggregation.")
