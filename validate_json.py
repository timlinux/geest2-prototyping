#!/usr/bin/env python
import json
import jsonschema
from jsonschema import validate

# Function to load JSON from a file
def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Function to validate a JSON document against a schema
def validate_json(json_data, json_schema):
    try:
        # Perform validation
        validate(instance=json_data, schema=json_schema)
        print("Validation successful: The JSON document is valid.")
    except jsonschema.exceptions.ValidationError as err:
        print("Validation error: The JSON document is invalid.")
        print(f"Error details: {err.message}")

# Main function
def main():
    # File paths for schema and data
    schema_file = 'schema.json'
    json_file = 'model.json'

    # Load the JSON schema and JSON data
    json_schema = load_json(schema_file)
    json_data = load_json(json_file)

    # Validate the JSON data against the schema
    validate_json(json_data, json_schema)

# Run the main function
if __name__ == "__main__":
    main()

