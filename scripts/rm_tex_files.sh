#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <directory>"
    exit 1
fi


# Define the directory path
directory=$1

# Use find command to locate .tex files containing '_rendered_' in their filenames
find "$directory" -type f -name "*.tex" -name "*_rendered_*" -print0 |
while IFS= read -r -d '' file; do
    # Delete each matching file
    rm "$file"
done

# Print completion message
echo "Deletion complete."
