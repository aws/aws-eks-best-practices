#!/bin/bash

# Function to convert string to lowercase and replace spaces with hyphens
format_string() {
    echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g'
}

# Loop through all .adoc files in the current directory
for file in *.adoc; do
    # Skip index.adoc
    if [ "$file" != "index.adoc" ]; then
        echo "Processing $file"
        
        # Get the title from the first line of the file
        title=$(head -n 1 "$file" | sed 's/^= //')
        
        # Format the title for use inside square brackets
        formatted_title=$(format_string "$title")
        
        # Create the new header (using a heredoc to preserve formatting)
        read -r -d '' new_header << EOM
//!!NODE_ROOT <section>
[."topic"]
[[${formatted_title},${formatted_title}.title]]
= ${title}
:info_doctype: section
:info_title: ${title}
:info_abstract: ${title}
:info_titleabbrev: ${title}
:imagesdir: images/
EOM

        # Replace the first line with the new header
        awk -v header="$new_header" 'NR==1 {print header; next} 1' "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"
    fi
done

echo "Processing complete."