#!/usr/bin/env bash
./generate_model.py
./infer_schema.py
./validate_json.py
echo "🪛 Running GEEST:"
echo "--------------------------------"
echo "Do you want to enable debug mode?"
choice=$(gum choose "🪲 Yes" "🐞 No" )
case $choice in
	"🪲 Yes") DEBUG_MODE=1 ;;
	"🐞 No") DEBUG_MODE=0 ;;
esac
GEEST_DEBUG=${DEBUG_MODE} ./app.py
