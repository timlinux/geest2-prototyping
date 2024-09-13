#!/usr/bin/env python

import pandas as pd
import json
import os

# Load the spreadsheet from the current working directory
spreadsheet_path = 'geest2.ods'  # Ensure this is the correct path to your ODS file

# Load the spreadsheet starting from the relevant row and specifying the columns
df = pd.read_excel(spreadsheet_path, engine='odf', skiprows=3)  # Skipping to the relevant data rows

# Select only the relevant columns
df = df[['DIMENSION', 'FACTOR', 'Layer', 'Source', 'Indicator', 'Status', 'Query', 'Note']]

# Fill NaN values in 'Dimension' and 'Factor' columns to propagate their values downwards for hierarchical grouping
df['DIMENSION'] = df['DIMENSION'].ffill()
df['FACTOR'] = df['FACTOR'].ffill()
# Create a hierarchical JSON structure
result = {"dimensions": []}
dimension_map = {}

for _, row in df.iterrows():
    dimension = row['DIMENSION']
    factor = row['FACTOR']
    layer_data = {
        "layer": row['Layer'],
        "source": row['Source'] if not pd.isna(row['Source']) else "",
        "indicator": row['Indicator'] if not pd.isna(row['Indicator']) else "",
        "status": row['Status'] if not pd.isna(row['Status']) else "",
        "query": row['Query'] if not pd.isna(row['Query']) else "",
        "note": row['Note'] if not pd.isna(row['Note']) else ""
    }

    # If the dimension doesn't exist yet, create it
    if dimension not in dimension_map:
        new_dimension = {
            "name": dimension,
            "factors": []
        }
        result["dimensions"].append(new_dimension)
        dimension_map[dimension] = new_dimension

    # If the factor doesn't exist in the current dimension, add it
    factor_map = {f['name']: f for f in dimension_map[dimension]["factors"]}
    if factor not in factor_map:
        new_factor = {
            "name": factor,
            "layers": []
        }
        dimension_map[dimension]["factors"].append(new_factor)
        factor_map[factor] = new_factor

    # Add layer data to the current factor
    layer_name = row['Layer']
    factor_map[factor]["layers"].append(
        layer_data
    )

# Save the generated JSON data to a file
output_json_path = 'model.json'  # Save the output to data.json in the current directory
with open(output_json_path, 'w') as json_file:
    json.dump(result, json_file, indent=4)

print(f"JSON data has been saved to {output_json_path}")

