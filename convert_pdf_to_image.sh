#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "Usage: $0 <original_pdf> <output_directory>"
    exit 1
fi

original_pdf=$1
output_directory=$2

python pdf2png.py --pdf "$original_pdf" --output_path "$output_directory"

# Check if the shell script execution was successful
if [ "$?" -ne 0 ]; then
    echo "[$0] Error: Failed to converting the $original_pdf file into images."
    exit 1
else
    echo "[$0] Successfully converted the $original_pdf file into images."
fi