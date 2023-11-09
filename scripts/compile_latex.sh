#!/bin/bash

# Check if the required argument is provided
if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "Usage: ./compile.sh <folder> [main_file]"
    exit 1
fi

# Get the command-line arguments
folder="$1"
main_file="$2"

echo "[$0] Compiling $folder/$main_file.tex into a PDF."

main_file="${main_file%.*}" # Remove the ".tex" extension

# Store the current directory and change to the folder directory
original_dir=$(pwd)
cd "$folder"

# Find the bibliography file with .bib extension
bib_file=$(find . -maxdepth 1 -type f -name "*.bib" | head -n 1)

# Check if a bibliography file is found
if [ -z "$bib_file" ]; then
    # Compile the main LaTeX file using pdflatex only
    pdflatex -interaction=nonstopmode "$main_file.tex" > /dev/null
    pdflatex -interaction=nonstopmode  "$main_file.tex" > /dev/null
else
    # Remove the "./" prefix from the bib_file path
    bib_file=${bib_file#./}

    # Compile the main LaTeX file
    pdflatex -interaction=nonstopmode  "$main_file.tex" > /dev/null

    # Run BibTeX to process the bibliography
    bibtex "$main_file" > /dev/null

    # Compile the main LaTeX file again to update references
    pdflatex -interaction=nonstopmode  "$main_file.tex" > /dev/null

    # Compile the main LaTeX file one more time for proper references
    pdflatex -interaction=nonstopmode  "$main_file.tex" > /dev/null
fi


# Change back to the original directory
cd "$original_dir"

# Check if the shell script execution was successful
if [ "$?" -ne 0 ]; then
    echo "[$0] Failed to compile the $main_file into a PDF."
    exit 1
fi

echo "[$0] Successfully compiled the $main_file.tex file into a PDF."