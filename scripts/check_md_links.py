#!/usr/bin/env python3
"""
Check for broken links in Markdown files
Reports file links that don't exist
"""

import re
from pathlib import Path
from typing import List, Tuple, Dict

def extract_links_from_md(md_path: Path) -> List[Tuple[int, str]]:
    """Extract all file links from a Markdown file"""
    links = []
    with open(md_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            # Find markdown links: [text](link)
            md_link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            for match in re.finditer(md_link_pattern, line):
                link = match.group(2)
                # Skip URLs (http, https, mailto)
                if not link.startswith(('http://', 'https://', 'mailto:', '#')):
                    links.append((line_num, link))
    return links

def check_link_exists(base_path: Path, link: str) -> bool:
    """Check if a link target exists"""
    # Handle anchors
    if '#' in link:
        link = link.split('#')[0]
    
    if not link:
        return True  # Pure anchor link
    
    # Try relative to base path
    target = base_path.parent / link
    if target.exists():
        return True
    
    # Try relative to project root
    project_root = base_path
    while project_root.parent != project_root:
        if (project_root / '.git').exists():
            break
        project_root = project_root.parent
    
    target = project_root / link
    return target.exists()

def check_md_files(root_dir: Path) -> Dict[str, List[Tuple[int, str]]]:
    """Check all MD files for broken links"""
    broken_links = {}
    
    # Find all MD files
    md_files = list(root_dir.glob('*.md')) + list(root_dir.glob('**/*.md'))
    
    for md_file in md_files:
        if '.git' in str(md_file):
            continue
        
        links = extract_links_from_md(md_file)
        broken = []
        
        for line_num, link in links:
            if not check_link_exists(md_file, link):
                broken.append((line_num, link))
        
        if broken:
            broken_links[str(md_file.relative_to(root_dir))] = broken
    
    return broken_links

def main():
    project_root = Path('/Users/ma3u/projects/sozialgesetze/Sozialrecht_RAG')
    
    print("=== Checking Markdown Files for Broken Links ===\n")
    
    broken_links = check_md_files(project_root)
    
    if not broken_links:
        print("✅ No broken links found!")
        return
    
    print(f"❌ Found broken links in {len(broken_links)} file(s):\n")
    
    for file_path, links in broken_links.items():
        print(f"\n📄 {file_path}")
        print("─" * 60)
        for line_num, link in links:
            print(f"  Line {line_num}: {link}")
    
    print(f"\n\nTotal files with broken links: {len(broken_links)}")
    print(f"Total broken links: {sum(len(links) for links in broken_links.values())}")

if __name__ == '__main__':
    main()
