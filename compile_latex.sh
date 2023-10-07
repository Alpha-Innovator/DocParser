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

main_file="${main_file%.*}"

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

# Find the bibliography file with .bib extension
bib_file=$(find . -maxdepth 1 -type f -name "*.bib" | head -n 1)

# Check if a bibliography file is found
if [ -z "$bib_file" ]; then
    echo "No bibliography file (*.bib) found in the folder."
    # Compile the main LaTeX file using pdflatex only
    pdflatex "$main_file.tex"
    pdflatex "$main_file.tex"
else
    # Remove the "./" prefix from the bib_file path
    bib_file=${bib_file#./}

    # Compile the main LaTeX file
    pdflatex "$main_file.tex"

    # Run BibTeX to process the bibliography
    bibtex "$main_file"

    # Compile the main LaTeX file again to update references
    pdflatex "$main_file.tex"

    # Compile the main LaTeX file one more time for proper references
    pdflatex "$main_file.tex"
fi


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