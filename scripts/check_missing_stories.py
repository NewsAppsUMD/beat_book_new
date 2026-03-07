#!/usr/bin/env python3
"""
Check how many stories from county files are not in the issues_with_stories.json file.
"""

import json
from pathlib import Path

ISSUES_FILE = "issues_with_stories.json"
COUNTY_DIR = Path("stories_by_county")

def main():
    # Load issues file and extract all story titles/urls
    print(f"Loading {ISSUES_FILE}...")
    with open(ISSUES_FILE) as f:
        issues = json.load(f)
    
    # Collect all unique stories from issues file
    issue_stories = set()
    for issue in issues:
        for story in issue.get('stories', []):
            # Use title + date as unique identifier
            identifier = (story.get('title', ''), story.get('date', ''))
            issue_stories.add(identifier)
    
    print(f"Found {len(issue_stories)} unique stories in issues file\n")
    
    # Check each county file
    county_files = [
        "caroline_county.json",
        "dorchester_county.json",
        "kent_county.json",
        "queen_annes_county.json",
        "talbot_county.json"
    ]
    
    print("=" * 80)
    print("CHECKING COUNTY FILES")
    print("=" * 80)
    
    total_county_stories = 0
    total_missing = 0
    
    for county_file in county_files:
        file_path = COUNTY_DIR / county_file
        
        if not file_path.exists():
            print(f"⚠️  {county_file} not found")
            continue
        
        with open(file_path) as f:
            county_stories = json.load(f)
        
        # Check which stories are missing from issues file
        missing = []
        for story in county_stories:
            identifier = (story.get('title', ''), story.get('date', ''))
            if identifier not in issue_stories:
                missing.append(story)
        
        total_county_stories += len(county_stories)
        total_missing += len(missing)
        
        county_name = county_file.replace('.json', '').replace('_', ' ').title()
        missing_pct = (len(missing) / len(county_stories) * 100) if county_stories else 0
        
        print(f"\n{county_name}:")
        print(f"  Total stories: {len(county_stories)}")
        print(f"  In issues file: {len(county_stories) - len(missing)}")
        print(f"  NOT in issues file: {len(missing)} ({missing_pct:.1f}%)")
        
        if missing and len(missing) <= 10:
            print(f"  Missing stories:")
            for story in missing[:10]:
                print(f"    - {story.get('title', 'NO TITLE')} ({story.get('date', 'NO DATE')})")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total stories across county files: {total_county_stories}")
    print(f"Stories in issues file: {total_county_stories - total_missing}")
    print(f"Stories NOT in issues file: {total_missing}")
    
    missing_pct = (total_missing / total_county_stories * 100) if total_county_stories > 0 else 0
    print(f"Percentage not in issues: {missing_pct:.1f}%")

if __name__ == "__main__":
    main()
