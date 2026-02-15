#!/usr/bin/env python3
"""
Get a diverse sample of CPQ models from different series for testing
"""

import mysql.connector

conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='warrantyparts_test'
)

cursor = conn.cursor(dictionary=True)

print("\n" + "="*100)
print("Sample CPQ Models for Testing (one from each series)")
print("="*100)

# Get one model from each series
cursor.execute("""
    SELECT
        m.model_id,
        m.series_id,
        m.description,
        m.length_feet,
        m.seats,
        COUNT(DISTINCT msf.feature_id) as feature_count,
        (SELECT COUNT(*) FROM ModelPricing mp WHERE mp.model_id = m.model_id) as pricing_count
    FROM Models m
    LEFT JOIN ModelStandardFeatures msf ON m.model_id = msf.model_id
    LEFT JOIN Series s ON m.series_id = s.series_id
    WHERE s.parent_series IS NOT NULL  -- CPQ series have parent
    GROUP BY m.model_id, m.series_id, m.description, m.length_feet, m.seats
    HAVING feature_count > 0  -- Must have features
    ORDER BY m.series_id, m.length_feet
""")

models = cursor.fetchall()

# Pick one from each series
series_samples = {}
for model in models:
    series = model['series_id']
    if series not in series_samples:
        series_samples[series] = model

print(f"\nFound {len(series_samples)} different series with CPQ models:\n")
print(f"{'Series':<8} {'Model ID':<12} {'Description':<40} {'Length':>8} {'Seats':>6} {'Features':>10} {'Pricing':>10}")
print("-" * 100)

for series in sorted(series_samples.keys()):
    model = series_samples[series]
    print(f"{model['series_id']:<8} {model['model_id']:<12} {model['description'][:40]:<40} {model['length_feet']:>8}' {model['seats']:>6} {model['feature_count']:>10} {model['pricing_count']:>10}")

# Pick 5 diverse models
selected = []
priority_series = ['Q', 'QX', 'S', 'LX', 'R', 'M']

for series in priority_series:
    if series in series_samples:
        selected.append(series_samples[series])
    if len(selected) >= 5:
        break

# If we need more, add from remaining
if len(selected) < 5:
    for series in sorted(series_samples.keys()):
        if series not in priority_series and len(selected) < 5:
            selected.append(series_samples[series])

print("\n" + "="*100)
print("5 Selected Models for Testing:")
print("="*100)
print(f"{'#':<3} {'Series':<8} {'Model ID':<12} {'Description':<50}")
print("-" * 100)

for i, model in enumerate(selected[:5], 1):
    print(f"{i:<3} {model['series_id']:<8} {model['model_id']:<12} {model['description'][:50]:<50}")

print("\n" + "="*100)

cursor.close()
conn.close()

# Print the model IDs for easy copying
print("\nModel IDs for testing:")
for i, model in enumerate(selected[:5], 1):
    print(f"{i}. {model['model_id']} ({model['series_id']} series)")
print()
