#!/bin/bash

# Function to convert markdown to asciidoc
convert_markdown_to_asciidoc() {
    local file="$1"
    local output_file="${file%.md}.adoc"
    kramdoc "$file" > "$output_file"
    echo "Converted $file to $output_file"
}

# Iterate through each subdirectory of the current directory
for dir in */; do
    # Check if the directory exists
    if [ -d "$dir" ]; then
        # Change to the subdirectory
        cd "$dir"
        
        # Find all .md files in the subdirectory and its subdirectories
        find . -type f -name "*.md" -print0 | while IFS= read -r -d '' file; do
            # Convert markdown to asciidoc
            convert_markdown_to_asciidoc "$file"
        done
        
        # Change back to the parent directory
        cd ..
    fi
done