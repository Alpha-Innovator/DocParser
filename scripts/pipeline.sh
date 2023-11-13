#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <input_tex>"
    exit 1
fi

# Assign the command line arguments to variables
script_name=$(basename "$0")
input_tex=$1
input_directory=$(dirname "$input_tex")

# Get the filename of the input_tex file without extension
filename_with_extension=$(basename -- "$input_tex")
input_filename="${filename_with_extension%.*}"
output_filename="paper"

# cp the original .tex file
original_tex="$input_directory/${output_filename}_original.tex"
cp "$input_tex" "$original_tex"
file_name_with_extension=$(basename -- "$original_tex")

# resolve imputs, remove comments, reduce empty lines
clean_tex --input "$input_directory" --output "$input_directory" --tex "$filename_with_extension"
# crop pdf image and convert into png files
process_images --input_tex "$original_tex"

# store the result
output_directory="$input_directory/output"
mkdir -p $output_directory
mkdir -p $output_directory/original
mkdir -p $output_directory/result

# Run the Python script to render the .tex file
run_rendering --input_tex_file "$original_tex"

echo "[$script_name] Successfully rendered the $original_tex."


# compile .tex file into pdf and convert to png files
prefix="${output_filename}_"
tex_files=$(find "$input_directory" -type f -name "${prefix}*.tex")

for file in $tex_files; do
    filename=$(basename "$file")
    echo "[$script_name] Processing $filename"
    bash compile_latex.sh "$input_directory" "${filename%.*}"

    target_dir="${filename#$prefix}"
    target_dir="$output_directory/${target_dir%.*}"
    mkdir -p "$target_dir"
    mv "$input_directory/${filename%.*}.pdf" "$target_dir/${output_filename}.pdf"
    bash convert_pdf_to_image.sh "$target_dir/${output_filename}.pdf" "$target_dir"
done

extract_layout_metadata --log_file "$input_directory/${output_filename}_colored.log"

# generate the bounding box and save the result
bash annotate.sh "$output_directory" "$input_filename"

echo "[$script_name] Script completed successfully, result is stored in $output_directory/result."

echo "[$script_name] Removing rendunded files, this may take a while..."
for file in $tex_files; do
    filename=$(basename "$file")
    target_dir="${filename#$prefix}"
    target_dir="$output_directory/${target_dir%.*}"
    rm -r "$target_dir"
    rm "$file"
done

# Clean up auxiliary files
rm -f $input_directory/*.aux $input_directory/*.bbl $input_directory/*.blg $input_directory/*.log $input_directory/*.out
rm -f $input_directory/*.toc $input_directory/*.dvi $input_directory/*Notes.bib $input_directory/*.brf $input_directory/*.vtc
rm -f $input_directory/*.axp $input_directory/*.loc $input_directory/*.pdfsync $input_directory/*.pag
rm -f $input_directory/*.abs $input_directory/*.spl $input_directory/*.bcf

echo "[$script_name] Total execution time: $SECONDS seconds"