#!/usr/bin/env python

import pandas as pd
import json
import os

# Load the spreadsheet from the current working directory
spreadsheet_path = 'geest2.ods'  # Ensure this is the correct path to your ODS file

# Load the spreadsheet starting from the relevant row and specifying the columns
df = pd.read_excel(spreadsheet_path, engine='odf', skiprows=1)  # Skipping to the relevant data rows

# Select only the relevant columns
df = df[['DIMENSION', 'FACTOR', 'Layer', 'Source', 'Indicator', 'Query', 'Text', 'Default Weighting',	'Use Aggregate',	'Default Index Score',	'Index Score',	'Use default Idex Score',	'Rasterise Raster',	'Rasterise Polygon',	'Rasterise Polyline',	'Rasterise Point',	'Default Buffer Distances',	'Use Buffer point',	'Default pixel',	'Use Create Grid',	'Default Mode',	'Default Measurement',	'Default Increments',	'Use Mode of Travel'
]]

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
        'Text': row['Source'] if not pd.isna(row['Source']) else "",
        'Default Weighting': row['Default Weighting'] if not pd.isna(row['Default Weighting']) else "",	
        'Use Aggregate': row['Use Aggregate'] if not pd.isna(row['Use Aggregate']) else "",
        'Default Index Score': row['Default Index Score'] if not pd.isna(row['Default Index Score']) else "",
        'Index Score': row['Index Score'] if not pd.isna(row['Index Score']) else "",
        'Use default Idex Score': row['Use default Idex Score'] if not pd.isna(row['Use default Idex Score']) else "",
        'Rasterise Raster': row['Rasterise Raster'] if not pd.isna(row['Rasterise Raster']) else "",
        'Rasterise Polygon': row['Rasterise Polygon'] if not pd.isna(row['Rasterise Polygon']) else "",
        'Rasterise Polyline': row['Rasterise Polyline'] if not pd.isna(row['Rasterise Polyline']) else "",
        'Rasterise Point': row['Rasterise Point'] if not pd.isna(row['Rasterise Point']) else "",
        'Default Buffer Distances': row['Default Buffer Distances'] if not pd.isna(row['Default Buffer Distances']) else "",
        'Use Buffer point': row['Use Buffer point'] if not pd.isna(row['Use Buffer point']) else "",
        'Default pixel': row['Default pixel'] if not pd.isna(row['Default pixel']) else "",
        'Use Create Grid': row['Use Create Grid'] if not pd.isna(row['Use Create Grid']) else "",
        'Default Mode': row['Default Mode'] if not pd.isna(row['Default Mode']) else "",
        'Default Measurement': row['Default Measurement'] if not pd.isna(row['Default Measurement']) else "",
        'Default Increments': row['Default Increments'] if not pd.isna(row['Default Increments']) else "",
        'Use Mode of Travel': row['Use Mode of Travel'] if not pd.isna(row['Use Mode of Travel']) else "",        
        "source": row['Source'] if not pd.isna(row['Source']) else "",
        "indicator": row['Indicator'] if not pd.isna(row['Indicator']) else "",
        "query": row['Query'] if not pd.isna(row['Query']) else ""
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

