#!/usr/bin/env python3
"""
Separate standardized stories into separate JSON files by county.
Stories tagged with multiple counties will appear in each county's file.
"""

import json
from pathlib import Path
from collections import defaultdict

INPUT_FILE = "beatbook_standardized_stories.json"
OUTPUT_DIR = Path("stories_by_county")

# The five counties we're focusing on
TARGET_COUNTIES = [
    "Caroline County",
    "Dorchester County",
    "Kent County",
    "Queen Anne's County",
    "Talbot County"
]

def main():
    print(f"Loading stories from {INPUT_FILE}...")
    with open(INPUT_FILE) as f:
        stories = json.load(f)
    
    print(f"Loaded {len(stories)} stories\n")
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}/\n")
    
    # Group stories by county
    county_stories = defaultdict(list)
    stories_without_counties = []
    
    for story in stories:
        counties = story.get('counties', [])
        
        if not counties:
            stories_without_counties.append(story)
            continue
        
        # Add story to each county it's tagged with
        for county in counties:
            # Normalize county name to match our target counties
            county_normalized = county.strip()
            
            # Check if it matches one of our target counties
            if county_normalized in TARGET_COUNTIES:
                county_stories[county_normalized].append(story)
    
    # Save stories for each county
    print("=" * 80)
    print("SAVING COUNTY FILES")
    print("=" * 80)
    
    for county in TARGET_COUNTIES:
        stories_list = county_stories[county]
        
        if stories_list:
            # Create safe filename
            county_filename = county.lower().replace(' ', '_').replace("'", '')
            output_file = OUTPUT_DIR / f"{county_filename}.json"
            
            with open(output_file, 'w') as f:
                json.dump(stories_list, f, indent=2)
            
            print(f"✅ {county}: {len(stories_list)} stories → {output_file}")
        else:
            print(f"⚠️  {county}: 0 stories (no file created)")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_story_instances = sum(len(stories_list) for stories_list in county_stories.values())
    unique_stories = len(stories)
    
    print(f"Total unique stories: {unique_stories}")
    print(f"Total story instances across counties: {total_story_instances}")
    print(f"Stories without county tags: {len(stories_without_counties)}")
    
    # Count stories that appear in multiple counties
    multi_county_count = 0
    for story in stories:
        counties = story.get('counties', [])
        matching_counties = [c for c in counties if c in TARGET_COUNTIES]
        if len(matching_counties) > 1:
            multi_county_count += 1
    
    print(f"Stories appearing in multiple counties: {multi_county_count}")
    
    print("\nCounty breakdown:")
    for county in TARGET_COUNTIES:
        count = len(county_stories[county])
        pct = (count / unique_stories * 100) if unique_stories > 0 else 0
        print(f"  {county}: {count} stories ({pct:.1f}%)")

if __name__ == "__main__":
    main()
