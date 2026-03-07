#!/usr/bin/env python3
"""
Script to identify stories with high local government relevance scores
from topic-classified story files.

Analyzes llm_classification metadata to find stories where Local Government
scored > 0.75 as a candidate topic.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path("data")
OUTPUT_FILE = "high_local_gov_stories.json"
LOCAL_GOV_THRESHOLD = 0.75

# Topic files to analyze (excluding local_government_stories.json which is already classified)
TOPIC_FILES = [
    'agriculture_stories.json',
    'aquaculture_stories.json', 
    'arts_culture.json',
    'business_economy_stories.json',
    'education_stories.json',
    'environment_stories.json',
    'health_stories.json',
    'public_notices.json',
    'public_safety_stories.json',
    'race_diversity_stories.json'
]

def get_local_gov_score(story):
    """Extract local government score from llm_classification candidates."""
    if 'llm_classification' not in story:
        return 0.0
    
    classification = story['llm_classification']
    if not isinstance(classification, dict):
        return 0.0
    
    candidates = classification.get('candidates', [])
    if not isinstance(candidates, list):
        return 0.0
    
    # Find Local Government in candidates
    for candidate in candidates:
        if isinstance(candidate, dict) and candidate.get('topic') == 'Local Government':
            return candidate.get('score', 0.0)
    
    return 0.0

def analyze_files():
    """Analyze all topic files and extract stories with high local gov scores."""
    
    high_local_gov_stories = []
    stats = defaultdict(int)
    
    print("=" * 80)
    print("ANALYZING TOPIC FILES FOR LOCAL GOVERNMENT RELEVANCE")
    print("=" * 80)
    print(f"Threshold: Local Government score > {LOCAL_GOV_THRESHOLD}")
    print()
    
    for filename in TOPIC_FILES:
        filepath = DATA_DIR / filename
        
        if not filepath.exists():
            print(f"⚠️  {filename}: File not found")
            continue
        
        with open(filepath, 'r') as f:
            stories = json.load(f)
        
        topic_name = filename.replace('_stories.json', '').replace('.json', '')
        found_count = 0
        
        for story in stories:
            stats['total_analyzed'] += 1
            local_gov_score = get_local_gov_score(story)
            
            if local_gov_score > LOCAL_GOV_THRESHOLD:
                # Add source information
                story_with_source = story.copy()
                story_with_source['source_file'] = filename
                story_with_source['source_topic'] = topic_name
                story_with_source['local_gov_score'] = local_gov_score
                
                high_local_gov_stories.append(story_with_source)
                found_count += 1
                stats['total_found'] += 1
        
        if found_count > 0:
            print(f"✓ {filename:35s}: {found_count:3d} stories (out of {len(stories):4d})")
        else:
            print(f"  {filename:35s}: {found_count:3d} stories (out of {len(stories):4d})")
    
    # Sort by local_gov_score (highest first)
    high_local_gov_stories.sort(key=lambda x: x['local_gov_score'], reverse=True)
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total stories analyzed: {stats['total_analyzed']}")
    print(f"Stories with local_gov_score > {LOCAL_GOV_THRESHOLD}: {stats['total_found']}")
    print(f"Percentage: {stats['total_found']/stats['total_analyzed']*100:.1f}%")
    print()
    
    # Save results
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(high_local_gov_stories, f, indent=2)
    
    print(f"💾 Saved {len(high_local_gov_stories)} stories to: {OUTPUT_FILE}")
    print()
    
    # Show top 10 by score
    if high_local_gov_stories:
        print("TOP 10 STORIES BY LOCAL GOVERNMENT SCORE:")
        print("-" * 80)
        for i, story in enumerate(high_local_gov_stories[:10], 1):
            score = story['local_gov_score']
            source = story['source_topic']
            title = story['title'][:60]
            print(f"{i:2d}. [{score:.2f}] [{source:20s}] {title}")
    
    return high_local_gov_stories, stats

def main():
    high_local_gov_stories, stats = analyze_files()
    
    if stats['total_found'] > 0:
        print()
        print("✅ Analysis complete!")
    else:
        print()
        print("⚠️  No stories found above threshold.")

if __name__ == "__main__":
    main()
