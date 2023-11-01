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
output_filename="${input_filename}_rendered"

# resolve imputs, remove comments, reduce empty lines
clean_tex --input "$input_directory" --output "$input_directory" --tex "$filename_with_extension"
# crop pdf image and convert into png files
process_images --input_tex "$input_tex"

# store the result
output_directory="$input_directory/output"
mkdir -p $output_directory
if [ "$?" -ne 0 ]; then
    echo "[$script_name] Error: Failed to create the $output_directory directory"
    exit 1
fi

mkdir -p $output_directory/original
if [ "$?" -ne 0 ]; then
    echo "[$script_name] Error: Failed to create the $output_directory/original directory"
    exit 1
fi

mkdir -p $output_directory/result
if [ "$?" -ne 0 ]; then
    echo "[$script_name] Error: Failed to create the $output_directory/result directory"
    exit 1
fi

# Run the Python script to render the .tex file
run_rendering --input_tex_file "$input_tex"

echo "[$script_name] Successfully rendered the $input_tex."

# compile the original .tex file into a PDF and save to images
bash compile_latex.sh "$input_directory" "$input_filename"
mv "$input_directory/$input_filename.pdf" "$output_directory/original/"
bash convert_pdf_to_image.sh "$output_directory/original/$input_filename.pdf" "$output_directory/original"

# compile rendered .tex file, pattern: "*_rendered_*.tex"
rendered_tex_files=$(find "$input_directory" -type f -name "${output_filename}_*.tex")
prefix="${output_filename}_"
for file in $rendered_tex_files; do
    filename=$(basename "$file")
    echo "[$script_name] Processing $filename"
    bash compile_latex.sh "$input_directory" "${filename%.*}"

    target_dir="${filename#$prefix}"
    target_dir="$output_directory/${target_dir%.*}"
    mkdir -p "$target_dir"
    mv "$input_directory/${filename%.*}.pdf" "$target_dir"
    bash convert_pdf_to_image.sh "$target_dir/${filename%.*}.pdf" "$target_dir"
done

# generate the bounding box and save the result
bash annotate.sh "$output_directory" "$input_filename"

echo "[$script_name] Script completed successfully, result is stored in $output_directory/result."

echo "[$script_name] Removing rendunded files, this may take a while..."
for file in $rendered_tex_files; do
filename=$(basename "$file")

target_dir="${filename#$prefix}"
target_dir="$output_directory/${target_dir%.*}"
rm -r "$target_dir"
rm "$file"
done

echo "[$script_name] Total execution time: $SECONDS seconds"