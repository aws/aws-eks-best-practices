import os
import re

def convert_syntax(content):
    # Define the mapping (case-insensitive keys)
    mapping = {
        'attention': 'IMPORTANT',
        'info': 'NOTE',
        'note': 'NOTE',
        'tip': 'NOTE',
        'caution': 'WARNING',
        'warning': 'WARNING',
        'important': 'IMPORTANT',
        'Info': 'INFO',
        'Attention': 'IMPORTANT',
        'Tip': 'NOTE'
    }
    
    # Regular expression to match the markdown syntax (case-insensitive)
    pattern = r'!!! (attention|info|note|tip|caution|warning|important|Info|Attention|Tip)\s+(.*?)(?=\n\n|\Z)'
    
    def replacement(match):
        type_ = match.group(1)
        text = match.group(2)
        
        # Remove any leading/trailing whitespace and newlines
        text = text.strip()
        
        # Replace newlines within the text with spaces
        text = re.sub(r'\s*\n\s*', ' ', text)
        
        # Use the mapping, defaulting to uppercase of the original if not found
        adoc_type = mapping.get(type_, type_.upper())
        
        return f"[{adoc_type}]\n====\n{text}\n===="
    
    # Perform the replacement
    converted_content = re.sub(pattern, replacement, content, flags=re.DOTALL|re.IGNORECASE)
    
    return converted_content

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()
    
    converted_content = convert_syntax(content)
    
    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(converted_content)
    
    print(f"Processed: {filepath}")

def process_directory(directory):
    # Process files in the current directory
    for filename in os.listdir(directory):
        if filename.endswith('.adoc'):
            filepath = os.path.join(directory, filename)
            process_file(filepath)
    
    # Process files in immediate subdirectories
    for item in os.listdir(directory):
        subdir = os.path.join(directory, item)
        if os.path.isdir(subdir):
            for filename in os.listdir(subdir):
                if filename.endswith('.adoc'):
                    filepath = os.path.join(subdir, filename)
                    process_file(filepath)

# Usage
current_directory = os.getcwd()  # Get the current working directory
process_directory(current_directory)