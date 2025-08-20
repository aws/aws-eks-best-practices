#!/usr/bin/env python3

import os
import re
import subprocess
import sys

def find_adoc_files():
    """Find all .adoc files in the git repository."""
    try:
        # Use git ls-files to find all .adoc files tracked by git
        result = subprocess.run(
            ["git", "ls-files", "*.adoc"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split('\n')
    except subprocess.CalledProcessError as e:
        print(f"Error finding .adoc files: {e}")
        sys.exit(1)

def convert_links_in_file(file_path):
    """Convert AWS documentation links in the specified file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Regular expression to find links of the form:
        # https://docs.aws.amazon.com/autoscaling/ec2/userguide/AutoScalingGroup.html[Amazon EC2 Auto Scaling groups]
        pattern = r'https://docs\.aws\.amazon\.com/([^[\]]+)\[([^,\]]+)\]'
        
        # Function to replace each match
        def replace_link(match):
            path = match.group(1)
            text = match.group(2)
            return f'link:{path}[{text},type="documentation"]'
        
        # Replace all matches in the content
        new_content = re.sub(pattern, replace_link, content)
        
        # Count the number of replacements
        num_replacements = content.count('https://docs.aws.amazon.com/') - new_content.count('https://docs.aws.amazon.com/')
        
        # Write the modified content back to the file if changes were made
        if num_replacements > 0:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(new_content)
            print(f"Modified {file_path}: {num_replacements} links converted")
            return num_replacements
        else:
            print(f"No links to convert in {file_path}")
            return 0
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0

def main():
    """Main function to find and convert links in all .adoc files."""
    adoc_files = find_adoc_files()
    
    if not adoc_files or adoc_files[0] == '':
        print("No .adoc files found in the repository.")
        return
    
    total_files = len(adoc_files)
    total_links_converted = 0
    files_modified = 0
    
    print(f"Found {total_files} .adoc files to process.")
    
    for file_path in adoc_files:
        links_converted = convert_links_in_file(file_path)
        total_links_converted += links_converted
        if links_converted > 0:
            files_modified += 1
    
    print(f"\nSummary:")
    print(f"- Total .adoc files processed: {total_files}")
    print(f"- Files modified: {files_modified}")
    print(f"- Total links converted: {total_links_converted}")

if __name__ == "__main__":
    main()
