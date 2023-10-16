#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "Usage: $0 <input_pdf> <output_directory>"
    exit 1
fi

input_pdf=$1
output_directory=$2

pdf2png --pdf "$input_pdf" --output_path "$output_directory"

# Check if the shell script execution was successful
if [ "$?" -ne 0 ]; then
    echo "[$0] Error: Failed to converting the $input_pdf file into images."
    exit 1
else
    echo "[$0] Successfully converted the $input_pdf file into images."
fi