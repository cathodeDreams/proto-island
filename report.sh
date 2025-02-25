#!/bin/bash

# Create a timestamp for the report
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
OUTPUT_FILE="docs/poetry_environment_report.txt"

# Create the report file with a header
echo "===================================" > $OUTPUT_FILE
echo "POETRY ENVIRONMENT REPORT" >> $OUTPUT_FILE
echo "Generated: $TIMESTAMP" >> $OUTPUT_FILE
echo "===================================" >> $OUTPUT_FILE

# Run poetry commands and append their output to the single report file
echo -e "\n\n=== DEPENDENCIES (poetry lock & install) ===\n" >> $OUTPUT_FILE
poetry lock
poetry install

echo -e "\n\n=== INSTALLED PACKAGES (poetry show) ===\n" >> $OUTPUT_FILE
poetry show >> $OUTPUT_FILE

echo -e "\n\n=== ENVIRONMENT INFORMATION (poetry env info) ===\n" >> $OUTPUT_FILE
poetry env info >> $OUTPUT_FILE

echo -e "\n\n=== TEST RESULTS (poetry run pytest) ===\n" >> $OUTPUT_FILE
poetry run pytest >> $OUTPUT_FILE 2>&1

echo -e "\n\n=== PROJECT DIRECTORY STRUCTURE ===\n" >> $OUTPUT_FILE
tree --gitignore >> $OUTPUT_FILE

echo -e "\n\nReport generated successfully: $OUTPUT_FILE"
