#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "Usage: $0 <input_directory> <input_filename_without_extension>"
    exit 1
fi

# Assign the command line arguments to variables
input_directory=$1
input_filename=$2

# generate the bounding box with original and rendered PDF
mkdir -p "$input_directory/result/"
python output_layout_annotation.py --path "$input_directory" --file_name "$input_filename"

# Check if the shell script execution was successful
if [ "$?" -ne 0 ]; then
    echo "[$0] Error: Failed to generate the bounding box."
    exit 1
else
    echo "[$0] Successfully generated the bounding box."
fi