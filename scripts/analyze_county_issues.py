#!/usr/bin/env python3
"""
Identify top 3 issues for each county from their specific story files.
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime

COUNTY_DIR = Path("stories_by_county")
OUTPUT_FILE = "top_issues_by_county.json"
LLM_MODEL = "groq/meta-llama/llama-4-maverick-17b-128e-instruct"

COUNTY_ISSUE_PROMPT = """You are analyzing local government stories for {county}.

CONTEXT: It is now late November 2025. You are identifying the TOP 3 most significant recurring issues for this specific county based on:
- Story count (how many stories cover this issue)
- Recency (2024-2025 stories weighted heavily)
- Ongoing developments (not one-time events)
- Impact on the county

Below are {story_count} stories from {county}, sorted by date (newest first):

{stories_text}

TASK: Identify the TOP 3 recurring issues for {county}. Focus on:
- Issues that appear in MULTIPLE stories
- Issues with ONGOING developments or debates
- Issues with significant local impact
- Recent activity (especially 2024-2025)

For each issue, provide:
1. Issue name (concise, descriptive, specific to this county)
2. Story count (how many stories relate to this issue)
3. Date range (earliest to most recent story about this issue)
4. Significance (why this matters for {county})
5. Recent developments (what's happened in 2024-2025)
6. Story indices (array of indices of stories that relate to this issue, from the list above)

Respond with ONLY a JSON array of exactly 3 issues (or fewer if there aren't 3 distinct recurring issues):
[
  {{
    "issue_name": "Specific Issue Name",
    "story_count": number,
    "date_range": "YYYY-MM-DD to YYYY-MM-DD",
    "significance": "Why this matters for {county}",
    "recent_developments": "What's happened recently",
    "story_indices": [0, 3, 5, ...]
  }}
]
"""

def call_llm(prompt: str) -> str:
    """Call LLM via llm CLI tool."""
    result = subprocess.run(
        ['llm', '-m', LLM_MODEL, prompt],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()

def format_story_for_analysis(idx: int, story: dict) -> str:
    """Format a single story for LLM analysis."""
    title = story.get('title', 'NO TITLE')
    date = story.get('date', 'NO DATE')
    tag = story.get('beatbook_tag', 'NO TAG')
    
    # Get refinement evaluation for context
    refinement = story.get('refinement_evaluation', {})
    why_included = refinement.get('why_included', 'N/A')
    
    return f"[{idx}] {title} ({date}) - Tag: {tag}\n    Context: {why_included}"

def analyze_county_issues(county_name: str, stories: list) -> list:
    """Analyze stories for a county and identify top 3 issues."""
    print(f"  Sorting {len(stories)} stories by date...")
    
    # Sort stories by date (newest first)
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
    
    # Limit to 60 most recent stories for analysis
    analysis_stories = sorted_stories[:60] if len(sorted_stories) > 60 else sorted_stories
    
    print(f"  Analyzing {len(analysis_stories)} most recent stories...")
    
    # Format stories for LLM
    stories_text = "\n\n".join([
        format_story_for_analysis(idx, story) 
        for idx, story in enumerate(analysis_stories)
    ])
    
    # Create prompt
    prompt = COUNTY_ISSUE_PROMPT.format(
        county=county_name,
        story_count=len(analysis_stories),
        stories_text=stories_text
    )
    
    # Call LLM with retry logic
    max_retries = 2
    for attempt in range(max_retries):
        try:
            response = call_llm(prompt)
            
            # Parse JSON response
            # Remove markdown code blocks if present
            response_text = response.strip()
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
                if response_text.startswith('json'):
                    response_text = '\n'.join(response_text.split('\n')[1:])
            
            # Try to find JSON array in response
            if not response_text.startswith('['):
                # Look for [ in the response
                start = response_text.find('[')
                if start != -1:
                    end = response_text.rfind(']')
                    if end != -1:
                        response_text = response_text[start:end+1]
            
            issues = json.loads(response_text)
            break  # Success
        except (json.JSONDecodeError, ValueError) as e:
            if attempt < max_retries - 1:
                print(f"  ⚠️  JSON parse error (attempt {attempt + 1}), retrying...")
                continue
            else:
                print(f"  ⚠️  Could not parse JSON after {max_retries} attempts")
                print(f"  Raw response: {response[:200]}...")
                raise
    
    # Add full story references
    for issue in issues:
        story_indices = issue.get('story_indices', [])
        story_refs = []
        for idx in story_indices:
            if idx < len(analysis_stories):
                story = analysis_stories[idx]
                story_refs.append({
                    'title': story.get('title', ''),
                    'date': story.get('date', ''),
                    'url': story.get('url', ''),
                    'beatbook_tag': story.get('beatbook_tag', '')
                })
        issue['story_references'] = story_refs
    
    return issues

def main():
    county_files = {
        "Caroline County": "caroline_county.json",
        "Dorchester County": "dorchester_county.json",
        "Kent County": "kent_county.json",
        "Queen Anne's County": "queen_annes_county.json",
        "Talbot County": "talbot_county.json"
    }
    
    print("=" * 80)
    print("ANALYZING TOP ISSUES BY COUNTY")
    print("=" * 80)
    print()
    
    results = {}
    
    for county_name, filename in county_files.items():
        file_path = COUNTY_DIR / filename
        
        if not file_path.exists():
            print(f"⚠️  {county_name}: File not found - {filename}")
            continue
        
        print(f"[{county_name}]")
        
        # Load stories
        with open(file_path) as f:
            stories = json.load(f)
        
        print(f"  Loaded {len(stories)} stories")
        
        # Analyze issues
        try:
            issues = analyze_county_issues(county_name, stories)
            results[county_name] = issues
            
            print(f"  ✅ Found {len(issues)} top issues:")
            for issue in issues:
                print(f"     • {issue['issue_name']} ({issue['story_count']} stories)")
        except Exception as e:
            print(f"  ❌ Error analyzing {county_name}: {e}")
            results[county_name] = []
        
        print()
    
    # Save results
    print("=" * 80)
    print("SAVING RESULTS")
    print("=" * 80)
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ Saved top issues by county to {OUTPUT_FILE}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    for county_name in county_files.keys():
        issues = results.get(county_name, [])
        print(f"\n{county_name}: {len(issues)} issues")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue['issue_name']} - {issue['story_count']} stories")

if __name__ == "__main__":
    main()
