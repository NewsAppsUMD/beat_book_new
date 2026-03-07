#!/usr/bin/env python3
"""
Manually analyze Kent County issues with more explicit JSON-only prompt.
"""

import json
import subprocess
from datetime import datetime

def call_llm(prompt: str) -> str:
    """Call LLM via llm CLI tool."""
    result = subprocess.run(
        ['llm', '-m', 'groq/meta-llama/llama-4-maverick-17b-128e-instruct', prompt],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()

def main():
    # Load Kent County stories
    with open('stories_by_county/kent_county.json') as f:
        stories = json.load(f)
    
    print(f"Loaded {len(stories)} Kent County stories")
    
    # Sort by date
    dated_stories = []
    for story in stories:
        date_str = story.get('date', '')
        if date_str:
            try:
                date_obj = datetime.fromisoformat(date_str)
                dated_stories.append((date_obj, story))
            except:
                pass
    
    dated_stories.sort(reverse=True, key=lambda x: x[0])
    sorted_stories = [s[1] for s in dated_stories]
    
    # Format stories
    stories_text = "\n\n".join([
        f"[{idx}] {story.get('title', 'NO TITLE')} ({story.get('date', 'NO DATE')}) - {story.get('beatbook_tag', 'NO TAG')}\n    {story.get('refinement_evaluation', {}).get('why_included', 'N/A')}"
        for idx, story in enumerate(sorted_stories)
    ])
    
    prompt = f"""Analyze these {len(sorted_stories)} stories from Kent County, Maryland (late November 2025).

{stories_text}

Identify the TOP 3 recurring issues. Respond ONLY with a JSON array - NO explanatory text before or after:

[
  {{
    "issue_name": "Issue Name",
    "story_count": number,
    "date_range": "YYYY-MM-DD to YYYY-MM-DD",
    "significance": "Why this matters",
    "recent_developments": "What happened in 2024-2025",
    "story_indices": [0, 1, 2]
  }}
]

JSON ONLY - NO OTHER TEXT:"""
    
    print("Calling LLM...")
    response = call_llm(prompt)
    
    print("\nRaw response:")
    print(response)
    print("\n" + "=" * 80)
    
    # Try to parse
    response_text = response.strip()
    
    # Find JSON array
    start = response_text.find('[')
    if start != -1:
        end = response_text.rfind(']')
        if end != -1:
            response_text = response_text[start:end+1]
    
    print("\nParsing JSON...")
    issues = json.loads(response_text)
    
    # Add story references
    for issue in issues:
        story_indices = issue.get('story_indices', [])
        story_refs = []
        for idx in story_indices:
            if idx < len(sorted_stories):
                story = sorted_stories[idx]
                story_refs.append({
                    'title': story.get('title', ''),
                    'date': story.get('date', ''),
                    'url': story.get('url', ''),
                    'beatbook_tag': story.get('beatbook_tag', '')
                })
        issue['story_references'] = story_refs
    
    print(f"\n✅ Found {len(issues)} issues:")
    for issue in issues:
        print(f"  • {issue['issue_name']} ({issue['story_count']} stories)")
    
    # Update the main file
    with open('top_issues_by_county.json') as f:
        all_issues = json.load(f)
    
    all_issues['Kent County'] = issues
    
    with open('top_issues_by_county.json', 'w') as f:
        json.dump(all_issues, f, indent=2)
    
    print("\n✅ Updated top_issues_by_county.json with Kent County issues")

if __name__ == "__main__":
    main()
