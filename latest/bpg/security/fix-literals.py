import re
import shutil

def fix_code_literals(filename):
    # Create a backup of the original file
    shutil.copy2(filename, f"{filename}.backup")
    
    print(f"Processing file: {filename}")
    print("Creating backup...")

    # Read the content of the file
    with open(filename, 'r') as file:
        content = file.read()

    # Use regex to replace `+code literal+` with `code literal`
    pattern = r'`\+(.*?)\+`'
    replaced_content, count = re.subn(pattern, r'`\1`', content)

    # Write the modified content back to the file
    with open(filename, 'w') as file:
        file.write(replaced_content)

    print(f"Replaced {count} instances of `+code literal+` syntax.")
    print(f"Modified file saved as: {filename}")
    print(f"Original file backed up as: {filename}.backup")

if __name__ == "__main__":
    filename = 'iam.adoc'
    fix_code_literals(filename)