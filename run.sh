#!/usr/bin/env bash
./generate_model.py
./infer_schema.py
./validate_json.py
./app.py
