import subprocess
import re
import os
import time
import shutil
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Section:
    level: int
    title: str
    content: str
    start_line: int
    end_line: int

def run_build(content: str, test_description: str) -> bool:
    print(f"\nTesting: {test_description}")
    print("Building... (this may take about 30 seconds)")
    start_time = time.time()
    
    if not os.path.exists('iam.adoc.backup'):
        shutil.copy2('iam.adoc', 'iam.adoc.backup')
    
    with open('iam.adoc', 'w') as f:
        f.write(content)
    
    try:
        result = subprocess.run(["eda", "build", "brazil-build", "release", "-Dtype=html"], capture_output=True, text=True)
        end_time = time.time()
        success = result.returncode == 0
        print(f"Build {'succeeded' if success else 'failed'} in {end_time - start_time:.2f} seconds")
        return success
    finally:
        shutil.copy2('iam.adoc.backup', 'iam.adoc')

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

def bisect_problematic_sections(sections: List[Section]) -> List[Section]:
    print("\nStarting bisection search for problematic sections...")
    all_content = '\n'.join(section.content for section in sections)
    
    if run_build(all_content, "Full document"):
        print("Full document builds successfully. No problematic sections identified.")
        return []
    
    def bisect_recursive(start: int, end: int) -> List[Section]:
        if start == end:
            return [sections[start]]
        
        mid = (start + end) // 2
        first_half = '\n'.join(section.content for section in sections[start:mid+1])
        second_half = '\n'.join(section.content for section in sections[mid+1:end+1])
        
        problematic_sections = []
        
        if not run_build(first_half, f"First half (sections {start+1}-{mid+1})"):
            problematic_sections.extend(bisect_recursive(start, mid))
        
        if not run_build(second_half, f"Second half (sections {mid+2}-{end+1})"):
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

def main():
    print("Starting AsciiDoc debugging process...")
    with open('iam.adoc', 'r') as f:
        content = f.read()
    
    sections = parse_sections(content)
    problematic_sections = bisect_problematic_sections(sections)
    
    if problematic_sections:
        print("\nResults:")
        print("The following sections may be causing issues:")
        for section in problematic_sections:
            print(f"\nSection: {section.title} (lines {section.start_line + 1}-{section.end_line + 1})")
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
    
    print("\nDebugging process completed.")
    print("Note: The original 'iam.adoc' file has been restored.")

if __name__ == "__main__":
    main()