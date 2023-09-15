#!/bin/bash

# Store the current directory
original_dir=$(pwd)

# Check if the required argument is provided
if [ $# -lt 1 ]; then
    echo "Usage: ./compile.sh <folder> [main_file]"
    exit 1
fi

# Get the command-line arguments
folder="$1"
main_file="$2"

# Change to the folder directory
cd "$folder" || exit 1

# Check if main_file argument is provided
if [ -z "$main_file" ]; then
    # Find all .tex files in the folder
    tex_files=($(find . -maxdepth 1 -type f -name "*.tex"))

    # Check if no .tex file is found
    if [ ${#tex_files[@]} -eq 0 ]; then
        echo "No .tex files found in the folder."
        exit 1
    fi

    # Check if there is only one .tex file
    if [ ${#tex_files[@]} -eq 1 ]; then
        # Extract the filename without extension
        main_file=$(basename "${tex_files[0]}" .tex)
    else
        # Set the default main file as main.tex
        main_file="main"

        # Check if there are multiple .tex files
        if [ ${#tex_files[@]} -gt 1 ]; then
            # Check if main.tex exists
            if [[ " ${tex_files[@]} " =~ " ./main.tex " ]]; then
                main_file="main"
            else
                echo "Multiple .tex files found. Please ensure there is a main.tex file."
                exit 1
            fi
        fi
    fi
fi

$original_dir/tectonic "$main_file.tex"


# Clean up auxiliary files
if [ -f "$main_file.aux" ]; then
    rm "$main_file.aux"
fi

if [ -f "$main_file.bbl" ]; then
    rm "$main_file.bbl"
fi

if [ -f "$main_file.blg" ]; then
    rm "$main_file.blg"
fi

if [ -f "$main_file.log" ]; then
    rm "$main_file.log"
fi

if [ -f "$main_file.out" ]; then
    rm "$main_file.out"
fi

# Change back to the original directory
cd "$original_dir"