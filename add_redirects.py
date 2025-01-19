import os
import re
from pathlib import Path

def process_markdown_file(file_path):
    # Skip Korean translations
    if file_path.suffix == '.ko.md':
        return
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for the specific link format:
    # [AWS EKS Best Practices Guide](url) on the AWS Docs
    link_pattern = r'\[AWS EKS Best Practices Guide\]\((https://docs\.aws\.amazon\.com/[^\)]+)\) on the AWS Docs'
    match = re.search(link_pattern, content)
    
    if not match:
        return
        
    aws_url = match.group(1)
    
    # Check if redirect already exists
    if f'redirect: {aws_url}' in content:
        return
        
    # Add redirect to front matter
    if content.startswith('---\n'):
        # Find the end of front matter
        parts = content.split('---\n', 2)
        if len(parts) >= 2:
            # Add redirect to existing front matter
            front_matter = parts[1].rstrip()
            if front_matter:
                front_matter += '\n'
            front_matter += f'redirect: {aws_url}\n'
            new_content = f'---\n{front_matter}---\n{parts[2]}'
        else:
            # Malformed front matter, add new one
            new_content = f'---\nredirect: {aws_url}\n---\n\n{content[4:]}'
    else:
        # No front matter, add it
        new_content = f'---\nredirect: {aws_url}\n---\n\n{content}'
        
    # Write updated content back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
        print(f'Added redirect to {file_path}')

def main():
    # Start from current directory
    root_dir = Path('.')
    
    # Find all .md files
    for md_file in root_dir.glob('**/*.md'):
        if not md_file.name.endswith('.ko.md'):
            process_markdown_file(md_file)

if __name__ == '__main__':
    main() 