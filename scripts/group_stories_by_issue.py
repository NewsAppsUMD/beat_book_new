#!/usr/bin/env python3
"""
Group full story content by identified issues.
"""

import json
from pathlib import Path

INPUT_ISSUES = "top_recurring_issues.json"
INPUT_STORIES = "beatbook_standardized_stories.json"
OUTPUT_FILE = "issues_with_stories.json"

def main():
    print(f"Loading issues from {INPUT_ISSUES}...")
    with open(INPUT_ISSUES) as f:
        issues = json.load(f)
    
    print(f"Loading stories from {INPUT_STORIES}...")
    with open(INPUT_STORIES) as f:
        all_stories = json.load(f)
    
    print(f"\nProcessing {len(issues)} issues...")
    
    # Create output structure
    output = []
    
    for issue_idx, issue in enumerate(issues, 1):
        issue_name = issue['issue_name']
        story_count = issue['story_count']
        tag = issue['tag']
        
        print(f"[{issue_idx}/{len(issues)}] {issue_name} ({story_count} stories)")
        
        # Get the full story content for each story index
        story_indices = issue['story_indices']
        
        # Group stories by tag to find them
        stories_by_tag = {}
        for story in all_stories:
            story_tag = story.get('beatbook_tag', '')
            if story_tag not in stories_by_tag:
                stories_by_tag[story_tag] = []
            stories_by_tag[story_tag].append(story)
        
        # Get stories for this issue's tag
        tag_stories = stories_by_tag.get(tag, [])
        
        # Extract the referenced stories
        full_stories = []
        for idx in story_indices:
            if idx < len(tag_stories):
                story = tag_stories[idx].copy()
                full_stories.append(story)
        
        # Create issue entry with full stories
        issue_entry = {
            "issue_name": issue_name,
            "story_count": story_count,
            "date_range": issue['date_range'],
            "primary_counties": issue['primary_counties'],
            "significance": issue['significance'],
            "recent_developments": issue['recent_developments'],
            "tag": tag,
            "stories": full_stories
        }
        
        output.append(issue_entry)
    
    print(f"\nSaving {len(output)} issues with full stories to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    print("✅ Done!")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    total_stories = sum(len(issue['stories']) for issue in output)
    print(f"Total issues: {len(output)}")
    print(f"Total stories extracted: {total_stories}")
    print(f"\nTop 10 issues:")
    for i, issue in enumerate(output[:10], 1):
        print(f"  {i}. {issue['issue_name']} - {len(issue['stories'])} stories ({issue['tag']})")

if __name__ == "__main__":
    main()
