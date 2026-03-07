#!/usr/bin/env python3
"""
Identify top recurring issues from standardized beat book stories based on recency and significance.

This script analyzes beatbook_standardized_stories.json to identify the most important
recurring issues, weighing recent developments more heavily.
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

INPUT_FILE = "beatbook_standardized_stories.json"
OUTPUT_FILE = "top_recurring_issues.json"
LLM_MODEL = "groq/meta-llama/llama-4-maverick-17b-128e-instruct"

ISSUE_IDENTIFICATION_PROMPT = """You are analyzing local government stories from five Maryland counties (Talbot, Kent, Dorchester, Caroline, Queen Anne's) to identify TOP RECURRING ISSUES for a beat book.

A "top issue" for a beat book should be:
- A topic that appears in MULTIPLE stories (not one-time events)
- Something with ONGOING developments or unresolved questions
- Recent activity (stories from 2024-2025 weighted more heavily)
- Significant impact on multiple jurisdictions or stakeholders
- Provides important context for future reporting

CONTEXT: It is now late November 2025. Recent stories (2024-2025) are more relevant than older ones.

Below are stories tagged as "{tag}" - analyze them to identify the top 3-5 recurring issues within this category.

{stories}

For each issue you identify, provide:
1. **Issue name** (concise, descriptive)
2. **Story count** (how many stories relate to this issue)
3. **Date range** (earliest to most recent story)
4. **Primary counties** (which jurisdictions are involved)
5. **Significance** (why this matters for a beat book - 1-2 sentences)
6. **Recent developments** (what's happened in 2024-2025)
7. **Story indices** (which story numbers in the list relate to this issue)

Respond with ONLY a JSON array:
[
  {{
    "issue_name": "Descriptive Issue Name",
    "story_count": number,
    "date_range": "YYYY-MM-DD to YYYY-MM-DD",
    "primary_counties": ["County1", "County2"],
    "significance": "Why this matters for beat book",
    "recent_developments": "What's happened recently",
    "story_indices": [0, 3, 5]
  }}
]

Your JSON array response:
"""


def load_stories(input_path: Path) -> list:
    """Load stories from JSON file."""
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_story_for_analysis(story: dict, index: int) -> str:
    """Format a story for LLM analysis."""
    title = story.get('title', 'Untitled')
    date = story.get('date', 'Unknown')
    counties = ', '.join(story.get('counties', []))
    
    # Get summary from refinement evaluation if available
    refinement = story.get('refinement_evaluation', {})
    reason = refinement.get('reason', '')
    
    return f"""Story {index}:
Title: {title}
Date: {date}
Counties: {counties}
Why relevant: {reason}

"""


def analyze_tag_for_issues(tag: str, stories: list) -> list:
    """Use LLM to identify top recurring issues within a tag."""
    
    # Sort stories by date (newest first)
    dated_stories = []
    for story in stories:
        try:
            date_obj = datetime.strptime(story.get('date', '2000-01-01'), '%Y-%m-%d')
            dated_stories.append((date_obj, story))
        except:
            dated_stories.append((datetime(2000, 1, 1), story))
    
    dated_stories.sort(reverse=True, key=lambda x: x[0])
    sorted_stories = [s for _, s in dated_stories]
    
    # Limit to recent stories (last 50 or all if fewer)
    analysis_stories = sorted_stories[:50]
    
    # Format stories for prompt
    stories_text = ""
    for i, story in enumerate(analysis_stories):
        stories_text += format_story_for_analysis(story, i)
    
    prompt = ISSUE_IDENTIFICATION_PROMPT.format(tag=tag, stories=stories_text)
    
    # Call LLM
    try:
        result = subprocess.run(
            ['llm', '-m', LLM_MODEL],
            input=prompt,
            capture_output=True,
            text=True,
            check=True
        )
        
        response_text = result.stdout.strip()
        
        # Extract JSON
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0].strip()
        
        issues = json.loads(response_text)
        
        if not isinstance(issues, list):
            raise ValueError("Response is not a list")
        
        # Add the tag to each issue
        for issue in issues:
            issue['tag'] = tag
            # Add full story references
            story_refs = []
            for idx in issue.get('story_indices', []):
                if idx < len(analysis_stories):
                    story_refs.append({
                        'title': analysis_stories[idx].get('title'),
                        'date': analysis_stories[idx].get('date'),
                        'counties': analysis_stories[idx].get('counties', [])
                    })
            issue['story_references'] = story_refs
        
        return issues
        
    except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError) as e:
        print(f"  ⚠️  Analysis failed for {tag}: {e}", file=sys.stderr)
        return []


def main():
    input_path = Path(INPUT_FILE)
    output_path = Path(OUTPUT_FILE)
    
    print(f"Loading stories from {input_path}...")
    all_stories = load_stories(input_path)
    print(f"Loaded {len(all_stories)} stories")
    
    # Group by tag
    by_tag = defaultdict(list)
    for story in all_stories:
        tag = story.get('beatbook_tag', 'Untagged')
        by_tag[tag].append(story)
    
    print(f"\nFound {len(by_tag)} tags")
    print(f"Tags: {', '.join(sorted(by_tag.keys(), key=lambda x: -len(by_tag[x])))}")
    
    all_issues = []
    
    print("\n" + "="*80)
    print("ANALYZING TAGS FOR RECURRING ISSUES")
    print("="*80)
    
    # Process each tag
    for tag_num, (tag, stories) in enumerate(sorted(by_tag.items(), key=lambda x: -len(x[1])), 1):
        print(f"\n[{tag_num}/{len(by_tag)}] Analyzing: {tag} ({len(stories)} stories)")
        
        issues = analyze_tag_for_issues(tag, stories)
        
        if issues:
            print(f"  ✅ Found {len(issues)} recurring issues:")
            for issue in issues:
                print(f"     • {issue['issue_name']} ({issue['story_count']} stories)")
            all_issues.extend(issues)
        else:
            print(f"  ⚠️  No issues identified")
    
    # Sort all issues by story count and recency
    all_issues.sort(key=lambda x: (x['story_count'], x['date_range'].split(' to ')[-1]), reverse=True)
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total recurring issues identified: {len(all_issues)}")
    print("\nTop 10 issues by story count:")
    for i, issue in enumerate(all_issues[:10], 1):
        print(f"  {i}. {issue['issue_name']} - {issue['story_count']} stories ({issue['tag']})")
    
    print(f"\nSaving {len(all_issues)} issues to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_issues, f, indent=2, ensure_ascii=False)
    
    print("✅ Done!")


if __name__ == '__main__':
    main()
