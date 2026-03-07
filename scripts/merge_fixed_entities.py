#!/usr/bin/env python3
"""
Script to merge fixed entity data back into the main local government stories file.
Reads stories_missing_entities_fixed.json and updates matching stories in
local_government_stories_with_entities_v2_cleaned.json based on article_id.
"""

import json
from pathlib import Path

def load_json(filepath):
    """Load JSON file and return data."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath, data):
    """Save data to JSON file with proper formatting."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def merge_entities():
    """Merge fixed entity data into main stories file."""
    
    # File paths
    fixed_file = Path('stories_missing_entities_fixed.json')
    main_file = Path('local_government_stories_with_entities_v2_cleaned.json')
    output_file = Path('local_government_stories_with_entities_v2_cleaned_merged.json')
    
    print(f"Loading fixed entities from {fixed_file}...")
    fixed_stories = load_json(fixed_file)
    
    print(f"Loading main stories file from {main_file}...")
    main_stories = load_json(main_file)
    
    # Create a lookup dictionary by article_id for fixed stories
    fixed_by_id = {story['article_id']: story for story in fixed_stories}
    
    print(f"\nFound {len(fixed_stories)} stories with fixed entities")
    print(f"Found {len(main_stories)} total stories in main file")
    
    # Track updates
    updated_count = 0
    entity_fields = [
        'content_type',
        'regions',
        'municipalities',
        'counties',
        'key_people',
        'key_events',
        'key_initiatives',
        'key_establishments',
        'key_organizations'
    ]
    
    # Update main stories with fixed entity data
    for story in main_stories:
        article_id = story.get('article_id')
        
        if article_id in fixed_by_id:
            fixed_story = fixed_by_id[article_id]
            
            # Copy all entity fields from fixed story
            for field in entity_fields:
                if field in fixed_story:
                    story[field] = fixed_story[field]
            
            updated_count += 1
            print(f"Updated story: {story.get('title', 'Unknown')[:60]}...")
    
    print(f"\n✓ Updated {updated_count} stories with fixed entity data")
    
    # Save merged data
    print(f"\nSaving merged data to {output_file}...")
    save_json(output_file, main_stories)
    
    print(f"✓ Successfully saved {len(main_stories)} stories to {output_file}")
    print("\nMerge complete!")

if __name__ == '__main__':
    merge_entities()
