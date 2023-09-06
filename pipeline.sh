#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "Usage: $0 <input_tex> [<debug_flag>]"
    exit 1
fi

# Assign the command line arguments to variables
input_tex=$1
debug_flag=$3

# Get the directory of the input_tex file
input_directory=$(dirname "$input_tex")

# Get the filename of the input_tex file without extension
filename_with_extension=$(basename -- "$input_tex")
input_filename="${filename_with_extension%.*}"

# store the result
mkdir -p $input_directory/output
if [ "$?" -ne 0 ]; then
    echo "Error: Failed to create the output directory"
    exit 1
fi

# name of output tex file wthout extension
output_filename="${input_filename}_rendered"

# Run the Python script to render the .tex file
if [ -z "$debug_flag" ]; then
    python run_rendering.py --input_tex_file "$input_tex" --output_tex_file "$input_directory/$output_filename"
else
    python run_rendering.py --input_tex_file "$input_tex" --output_tex_file "$input_directory/$output_filename" "$debug_flag"
fi

# Check if the Python script execution was successful
if [ "$?" -ne 0 ]; then
    echo "Error: Failed to render the .tex file."
    exit 1
else
    echo "Successfully rendered the .tex file."
fi

############# compile the original .tex file into a PDF###########################
# Run the shell script to compile the original .tex file into a PDF
bash compile_latex.sh "$input_directory" "$input_filename"

# Check if the shell script execution was successful
if [ "$?" -ne 0 ]; then
    echo "Error: Failed to compile the original .tex file into a PDF."
    exit 1
else
    echo "Successfully compiled the original .tex file into a PDF."
fi

# copy the original PDF file to the output directory
mkdir -p "output/original"
original_pdf="$input_directory/output/original/$input_filename.pdf"
cp "$input_directory/$input_filename.pdf" "$original_pdf"

############# compile the rendered .tex file into a PDF###########################
# Run the shell script to compile the output .tex file into a PDF
bash compile_latex.sh "$input_directory" "$output_filename"

# Check if the shell script execution was successful
if [ "$?" -ne 0 ]; then
    echo "Failed to compile the output .tex file into a PDF."
    exit 1
else
    echo "Successfully compiled the output .tex file into a PDF."
fi

mkdir -p "output/rendered/"
rendered_pdf="$input_directory/output/rendered/$output_filename.pdf"
mv "$input_directory/$output_filename.pdf" "$rendered_pdf"

############# convert the original PDF into images ################
python pdf2jpg.py --pdf "$original_pdf" --output_path "$input_directory/output/original"

# Check if the shell script execution was successful
if [ "$?" -ne 0 ]; then
    echo "Error: Failed to converting the input .pdf file into images."
    exit 1
else
    echo "Successfully converted the input .pdf file into images."
fi

############# convert the rendered PDF into images ################
python pdf2jpg.py --pdf "$rendered_pdf" --output_path "$input_directory/output/rendered"

# Check if the shell script execution was successful
if [ "$?" -ne 0 ]; then
    echo "Error: Failed to converting the output .pdf file into images."
    exit 1
else
    echo "Successfully converted the output .pdf file into images."
fi

############## generate the bounding box with original and rendered PDF ##########
python generate_bb.py --path "$input_directory/output" --file_name "$input_filename"

# Check if the shell script execution was successful
if [ "$?" -ne 0 ]; then
    echo "Error: Failed to generate the bounding box."
    exit 1
else
    echo "Successfully generated the bounding box."
fi

echo "Script completed successfully."