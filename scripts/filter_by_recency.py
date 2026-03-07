#!/usr/bin/env python3
"""
Filter stories by relevance to a 2025 beat book based on recency and issue importance.

This script analyzes stories_grouped_by_issue.json and uses an LLM to determine which
issues and stories are most relevant for a beat book created in late 2025, considering:
- Story dates (prioritize recent stories, especially 2025)
- Number of stories per issue
- Ongoing relevance vs. old resolved issues
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Configuration
INPUT_FILE = "stories_grouped_by_issue.json"
OUTPUT_FILE = "beatbook_filtered_stories.json"
LLM_MODEL = "groq/meta-llama/llama-4-maverick-17b-128e-instruct"

FILTER_PROMPT = """You are helping create a LOCAL GOVERNMENT BEAT BOOK for a reporter starting in LATE 2025.

A beat book should contain CURRENT, ONGOING issues that help a reporter understand the landscape they're covering NOW. It should NOT include old, resolved issues from 2023-2024 unless they have clear ongoing relevance in 2025.

Below is information about a specific issue/topic:

ISSUE: {issue_name}
TOTAL STORIES: {total_stories}
DATE RANGE: {date_range}
STORY DATES BREAKDOWN:
  2023: {count_2023} stories
  2024: {count_2024} stories  
  2025: {count_2025} stories

COUNTIES COVERED: {counties_list}

SAMPLE RECENT STORY TITLES (up to 5 most recent):
{recent_titles}

EVALUATION CRITERIA:
1. **Recency**: Issues with stories primarily from 2023 should be EXCLUDED unless they clearly remain relevant in 2025
2. **Ongoing Nature**: Is this an ongoing issue/debate or a resolved historical event?
3. **2025 Relevance**: Does this issue have clear connection to current (2025) reporting needs?
4. **Story Count in 2025**: Issues with multiple 2025 stories suggest ongoing relevance

INCLUDE if:
- Issue has substantial 2025 coverage (3+ stories in 2025)
- OR issue is clearly ongoing with recent (2024-2025) activity
- OR older issue that remains unresolved and relevant (e.g., major infrastructure projects)

EXCLUDE if:
- Stories are primarily from 2023 with no 2024-2025 follow-up
- Issue appears to be resolved or historical
- Old election coverage (2023/2024 elections are over)
- One-time events from 2023-2024 with no ongoing impact

Respond with a JSON object:
{{
  "include": true or false,
  "reasoning": "Brief explanation of decision focusing on recency and ongoing relevance",
  "confidence": 0.0-1.0
}}

Your response (JSON only):"""


def load_grouped_stories(input_path: Path) -> dict:
    """Load grouped stories from JSON file."""
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_filtered_stories(filtered: dict, output_path: Path):
    """Save filtered stories to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(filtered, f, indent=2, ensure_ascii=False)


def analyze_issue_dates(issue_data: dict) -> dict:
    """Analyze date distribution for an issue."""
    all_stories = []
    
    for county, stories in issue_data.get('counties', {}).items():
        all_stories.extend(stories)
    
    dates = []
    count_by_year = defaultdict(int)
    
    for story in all_stories:
        date_str = story.get('date', '')
        if date_str:
            try:
                year = int(date_str.split('-')[0])
                dates.append(year)
                count_by_year[year] += 1
            except (ValueError, IndexError):
                pass
    
    if dates:
        date_range = f"{min(dates)}-{max(dates)}"
    else:
        date_range = "Unknown"
    
    return {
        'date_range': date_range,
        'count_2023': count_by_year.get(2023, 0),
        'count_2024': count_by_year.get(2024, 0),
        'count_2025': count_by_year.get(2025, 0),
        'all_stories': all_stories
    }


def get_recent_titles(stories: list, count: int = 5) -> list:
    """Get titles of most recent stories."""
    # Sort by date descending
    sorted_stories = sorted(
        stories,
        key=lambda x: x.get('date', '0000-00-00'),
        reverse=True
    )
    
    titles = []
    for story in sorted_stories[:count]:
        date = story.get('date', 'Unknown')
        title = story.get('title', 'Untitled')
        titles.append(f"[{date}] {title}")
    
    return titles


def evaluate_issue(issue_name: str, issue_data: dict) -> dict:
    """Use LLM to evaluate if an issue should be included in beat book."""
    
    # Analyze dates
    date_analysis = analyze_issue_dates(issue_data)
    
    # Get recent titles
    recent_titles = get_recent_titles(date_analysis['all_stories'])
    
    # Get counties list
    counties_list = ', '.join(issue_data.get('counties', {}).keys())
    
    # Create prompt
    prompt = FILTER_PROMPT.format(
        issue_name=issue_name,
        total_stories=issue_data.get('total_stories', 0),
        date_range=date_analysis['date_range'],
        count_2023=date_analysis['count_2023'],
        count_2024=date_analysis['count_2024'],
        count_2025=date_analysis['count_2025'],
        counties_list=counties_list,
        recent_titles='\n'.join(recent_titles)
    )
    
    # Call LLM
    try:
        result = subprocess.run(
            ['llm', '-m', LLM_MODEL],
            input=prompt,
            capture_output=True,
            text=True,
            check=True,
            timeout=60
        )
        
        response_text = result.stdout.strip()
        
        # Try to extract JSON if wrapped in markdown
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0].strip()
        
        evaluation = json.loads(response_text)
        return evaluation
        
    except (subprocess.CalledProcessError, json.JSONDecodeError, subprocess.TimeoutExpired) as e:
        print(f"  ⚠️  Evaluation failed: {e}")
        return {"include": False, "reasoning": "Error in evaluation", "confidence": 0.0}


def main():
    """Main execution function."""
    
    input_path = Path(INPUT_FILE)
    output_path = Path(OUTPUT_FILE)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1
    
    print(f"Loading grouped stories from {input_path}...")
    grouped_stories = load_grouped_stories(input_path)
    print(f"Loaded {len(grouped_stories)} issues")
    
    print("\n" + "="*80)
    print("EVALUATING ISSUES FOR 2025 BEAT BOOK RELEVANCE")
    print("="*80)
    
    filtered_stories = {}
    included_count = 0
    excluded_count = 0
    
    # Sort by total story count for processing
    sorted_issues = sorted(
        grouped_stories.items(),
        key=lambda x: x[1].get('total_stories', 0),
        reverse=True
    )
    
    for issue_name, issue_data in sorted_issues:
        total = issue_data.get('total_stories', 0)
        
        print(f"\n[{included_count + excluded_count + 1}/{len(sorted_issues)}] Evaluating: {issue_name}")
        print(f"  Total stories: {total}")
        
        # Evaluate with LLM
        evaluation = evaluate_issue(issue_name, issue_data)
        
        include = evaluation.get('include', False)
        reasoning = evaluation.get('reasoning', 'No reasoning provided')
        confidence = evaluation.get('confidence', 0.0)
        
        if include:
            print(f"  ✅ INCLUDE (confidence: {confidence:.2f})")
            print(f"     {reasoning}")
            filtered_stories[issue_name] = issue_data
            included_count += 1
        else:
            print(f"  ❌ EXCLUDE (confidence: {confidence:.2f})")
            print(f"     {reasoning}")
            excluded_count += 1
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total issues evaluated: {len(sorted_issues)}")
    print(f"Issues included: {included_count}")
    print(f"Issues excluded: {excluded_count}")
    
    # Count total stories
    total_stories = sum(data.get('total_stories', 0) for data in filtered_stories.values())
    print(f"Total stories in filtered beat book: {total_stories}")
    
    # Save filtered results
    print(f"\nSaving filtered stories to {output_path}...")
    save_filtered_stories(filtered_stories, output_path)
    print("✅ Done!")
    
    return 0


if __name__ == '__main__':
    exit(main())
