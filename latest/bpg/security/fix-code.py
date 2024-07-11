import re
import sys

def remove_plus_wrapping(file_path):
    with open(file_path, 'r') as file:
        content = file.read()

    # Pattern to match any text wrapped in '+' symbols
    pattern = r'\+([^+\n]+)\+'
    
    # Replace '+text+' with 'text'
    modified_content = re.sub(pattern, r'\1', content)

    with open(file_path, 'w') as file:
        file.write(modified_content)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <path_to_adoc_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    remove_plus_wrapping(file_path)
    print(f"Processed {file_path}. Text wrapped in '+' symbols has been unwrapped.")