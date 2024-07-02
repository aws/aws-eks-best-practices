import subprocess
import re
import os
import time
import shutil
import signal
import sys
from dataclasses import dataclass
from typing import List, Tuple

# File to test
TEST_FILE = 'multiaccount.adoc'

@dataclass
class Section:
    level: int
    title: str
    content: str
    start_line: int
    end_line: int

# Global flag to indicate if the script should exit
should_exit = False

def signal_handler(sig, frame):
    global should_exit
    print("\nInterrupt received. Cleaning up and exiting...")
    should_exit = True

signal.signal(signal.SIGINT, signal_handler)

def safe_file_operations(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"An error occurred: {e}")
            restore_original_file()
            sys.exit(1)
    return wrapper

@safe_file_operations
def run_build(content: str, test_description: str, header: str) -> bool:
    if should_exit:
        restore_original_file()
        sys.exit(0)
    
    print(f"\nTesting: {test_description}")
    print("Building... (this may take about 30 seconds)")
    start_time = time.time()
    
    with open(TEST_FILE, 'w') as f:
        f.write(header + content)
    
    try:
        result = subprocess.run(["eda", "build", "brazil-build", "release", "-Dtype=html"], capture_output=True, text=True)
        end_time = time.time()
        success = result.returncode == 0
        print(f"Build {'succeeded' if success else 'failed'} in {end_time - start_time:.2f} seconds")
        return success
    except subprocess.CalledProcessError as e:
        print(f"Build process error: {e}")
        return False

@safe_file_operations
def parse_sections(content: str) -> List[Section]:
    print("\nParsing AsciiDoc sections...")
    lines = content.split('\n')
    sections = []
    current_section = None
    for i, line in enumerate(lines):
        match = re.match(r'^(=+)\s+(.+)$', line)
        if match:
            if current_section:
                current_section.end_line = i - 1
                sections.append(current_section)
            level = len(match.group(1))
            title = match.group(2)
            current_section = Section(level, title, '', i, -1)
        elif current_section:
            current_section.content += line + '\n'
    if current_section:
        current_section.end_line = len(lines) - 1
        sections.append(current_section)
    print(f"Found {len(sections)} sections")
    return sections

@safe_file_operations
def bisect_problematic_sections(sections: List[Section], header: str) -> List[Section]:
    print("\nStarting bisection search for problematic sections...")
    all_content = '\n'.join(section.content for section in sections)
    
    if run_build(all_content, "Full document", header):
        print("Full document builds successfully. No problematic sections identified.")
        return []
    
    def bisect_recursive(start: int, end: int) -> List[Section]:
        if should_exit:
            restore_original_file()
            sys.exit(0)
        
        if start == end:
            return [sections[start]]
        
        mid = (start + end) // 2
        first_half = '\n'.join(section.content for section in sections[start:mid+1])
        second_half = '\n'.join(section.content for section in sections[mid+1:end+1])
        
        problematic_sections = []
        
        if not run_build(first_half, f"First half (sections {start+1}-{mid+1})", header):
            problematic_sections.extend(bisect_recursive(start, mid))
        
        if not run_build(second_half, f"Second half (sections {mid+2}-{end+1})", header):
            problematic_sections.extend(bisect_recursive(mid+1, end))
        
        return problematic_sections
    
    return bisect_recursive(0, len(sections) - 1)

def suggest_fixes(section: Section) -> List[str]:
    print(f"\nAnalyzing section: {section.title}")
    suggestions = []
    
    if re.search(r'\[.*\]', section.content) and not re.search(r'\[.*\]\n', section.content):
        suggestions.append("Ensure all attribute lists are on their own line")
    
    if re.search(r'[^=]=+[^=]', section.content):
        suggestions.append("Check for misplaced section headers or formatting issues with '=' characters")
    
    if re.search(r'[^`]`[^`]+`[^`]', section.content):
        suggestions.append("Ensure all inline code blocks use matching backticks")
    
    if re.search(r'\{[^}]+\}', section.content):
        suggestions.append("Check for unclosed or mismatched curly braces in attribute references")
    
    print(f"Found {len(suggestions)} potential issues")
    return suggestions

def restore_original_file():
    if os.path.exists(f'{TEST_FILE}.backup'):
        shutil.copy2(f'{TEST_FILE}.backup', TEST_FILE)
        print(f"Original '{TEST_FILE}' file has been restored.")

def print_sections_preview(sections: List[Section]):
    print("\nSections preview:")
    for i, section in enumerate(sections):
        first_line = section.content.split('\n')[0].strip()
        print(f"Section {i+1}: {section.title}")
        print(f"  First line: {first_line[:60]}{'...' if len(first_line) > 60 else ''}")
        print(f"  Lines: {section.start_line + 11}-{section.end_line + 11}")
        print()

@safe_file_operations
def main():
    print(f"Starting AsciiDoc debugging process for file: {TEST_FILE}")
    
    # Backup the original file
    if not os.path.exists(f'{TEST_FILE}.backup'):
        shutil.copy2(TEST_FILE, f'{TEST_FILE}.backup')
    
    with open(TEST_FILE, 'r') as f:
        content = f.read()
    
    # Separate the header (first 10 lines) from the rest of the content
    lines = content.split('\n')
    header = '\n'.join(lines[:10]) + '\n'
    main_content = '\n'.join(lines[10:])
    
    sections = parse_sections(main_content)
    print_sections_preview(sections)
    
    input("Press Enter to start the bisection search...")
    
    problematic_sections = bisect_problematic_sections(sections, header)
    
    if problematic_sections:
        print("\nResults:")
        print("The following sections may be causing issues:")
        for section in problematic_sections:
            print(f"\nSection: {section.title} (lines {section.start_line + 11}-{section.end_line + 11})")
            print("First few lines of the section:")
            print('\n'.join(section.content.split('\n')[:5]))
            print("...")
            
            suggestions = suggest_fixes(section)
            if suggestions:
                print("Suggestions for fixing this section:")
                for suggestion in suggestions:
                    print(f"- {suggestion}")
    else:
        print("\nNo specific problematic sections identified. The issue may be more complex or involve interactions between multiple sections.")
    
    restore_original_file()
    print("\nDebugging process completed.")

if __name__ == "__main__":
    main()