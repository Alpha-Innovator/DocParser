#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "Usage: $0 <input_tex> [<debug_flag>]"
    exit 1
fi

# Assign the command line arguments to variables
input_tex=$1
debug_flag=$2

# Get the directory of the input_tex file
input_directory=$(dirname "$input_tex")

# Get the filename of the input_tex file without extension
filename_with_extension=$(basename -- "$input_tex")
input_filename="${filename_with_extension%.*}"

# store the result
mkdir -p $input_directory/output
if [ "$?" -ne 0 ]; then
    echo "[$0] Error: Failed to create the output directory"
    exit 1
fi

# name of output tex file wthout extension
output_filename="${input_filename}_rendered"

# Run the Python script to render the .tex file
output_tex="$input_directory/$output_filename.tex"

python run_rendering.py --input_tex_file "$input_tex" --output_tex_file "$output_tex" ${debug_flag:+"$debug_flag"}

# Check if the Python script execution was successful
if [ "$?" -ne 0 ]; then
    echo "[$0] Error: Failed to render the $input_tex."
    exit 1
fi

echo "[$0] Successfully rendered the $input_tex."

############# compile the original .tex file into a PDF###########################
# Run the shell script to compile the original .tex file into a PDF
bash compile_latex.sh "$input_directory" "$input_filename"

# Check if the shell script execution was successful
if [ "$?" -ne 0 ]; then
    echo "[$0] Error: Failed to compile the $input_filename into a PDF."
    exit 1
fi

echo "[$0] Successfully compiled the $input_filename into a PDF."

# copy the original PDF file to the output directory
mkdir -p "$input_directory/output/original"
original_pdf="$input_directory/output/original/$input_filename.pdf"
cp "$input_directory/$input_filename.pdf" "$original_pdf"

############# compile the rendered .tex file into a PDF###########################
# Run the shell script to compile the output .tex file into a PDF
bash compile_latex.sh "$input_directory" "$output_filename"

# Check if the shell script execution was successful
if [ "$?" -ne 0 ]; then
    echo "[$0] Failed to compile the $output_filename into a PDF."
    exit 1
fi

echo "[$0] Successfully compiled the $output_filename into a PDF."

# move the rendered PDF file to the output directory
mkdir -p "$input_directory/output/rendered/"
rendered_pdf="$input_directory/output/rendered/$output_filename.pdf"
mv "$input_directory/$output_filename.pdf" "$rendered_pdf"

############# convert the original PDF into images ################
bash convert_pdf_to_image.sh "$original_pdf" "$input_directory/output/original"

############# convert the rendered PDF into images ################
bash convert_pdf_to_image.sh "$rendered_pdf" "$input_directory/output/rendered"

############## generate the bounding box with original and rendered PDF ##########
bash annotate.sh "$input_directory" "$input_filename"

echo "[$0] Script completed successfully, result is stored in $input_directory/output/result."