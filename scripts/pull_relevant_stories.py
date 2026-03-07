#!/usr/bin/env python3
"""
Filter local government stories for beat book relevance.

This script uses an LLM to evaluate each story in local_government_stories_with_entities_v2_cleaned_final.json
and determines whether it would be relevant for a local government beat book covering
Talbot County, Kent County, Dorchester County, Caroline County, and Queen Anne's County.
"""

import json
import subprocess
import sys
from pathlib import Path
from time import perf_counter

# Configuration
INPUT_FILE = "local_government_all_stories_combined.json"
OUTPUT_FILE = "selected_local_government_stories.json"
EXCLUDED_FILE = "excluded_local_government_stories.json"
COUNTY_ISSUES_FILE = "county_top_issues.json"
LLM_MODEL = "groq/meta-llama/llama-4-maverick-17b-128e-instruct"

# Target counties for the beat book
TARGET_COUNTIES = [
    "Talbot County",
    "Kent County",
    "Dorchester County",
    "Caroline County",
    "Queen Anne's County"
]

RELEVANCE_PROMPT = """You are helping to create a beat book for a reporter covering the local government beat across five Maryland counties: Talbot County, Kent County, Dorchester County, Caroline County, and Queen Anne's County.

Based on comprehensive analysis of local news, the TOP ISSUES in each county are:

{county_issues}

EVALUATION TASK:
For EACH story, determine if it relates to ANY of the top issues listed above. If it does, identify which specific issue(s) it relates to.

BEAT BOOK FOCUS - INCLUDE STORIES ABOUT:

LOCAL GOVERNMENT MEETINGS & ACTIONS:
- Town/city council meetings, votes, appointments, controversies
- County commissioner meetings, decisions, discussions
- Planning and zoning commission meetings and decisions
- Board of education meetings and decisions
- Any other local government board or commission meetings

GOVERNMENT LEADERSHIP & PERSONNEL:
- Mayor, city manager, county administrator actions or changes
- Department head appointments, resignations, or controversies
- Elected official actions, statements, or controversies
- Government staff changes affecting operations

LEGISLATION, POLICY & REGULATIONS:
- Local ordinances, resolutions, laws proposed or passed
- Zoning changes, comprehensive plans, land use decisions
- Environmental regulations and policies
- Business regulations and licensing
- State or federal legislation affecting the five counties

BUDGETS & FUNDING:
- Local government budgets, tax rates, fiscal decisions
- Grant funding received by counties or municipalities (INCLUDE ALL)
- State or federal funding for local projects
- Bond issues, debt, financial planning
- Budget cuts or expansions

ELECTIONS & REPRESENTATION:
- Local elections, candidates, results
- Voter registration, polling places
- Redistricting, ward changes
- Referendums, ballot questions

SCHOOLS & EDUCATION (LOCAL GOVERNMENT ANGLE):
- School board decisions and funding
- School construction, facilities, capital projects
- School budget votes and tax implications
- School-related referendums

INFRASTRUCTURE & DEVELOPMENT:
- Roads, bridges, transportation projects
- Water, sewer, utilities infrastructure
- Broadband, telecommunications infrastructure
- DATA CENTER projects (ALWAYS INCLUDE)
- Major development projects requiring government approval
- Housing developments, affordable housing initiatives

ECONOMIC DEVELOPMENT:
- Business attraction and retention programs
- Economic development authority actions
- Tax incentives, enterprise zones
- Downtown revitalization, Main Street programs

PUBLIC SERVICES & FACILITIES:
- Parks, recreation facilities, libraries
- Public safety facilities (fire, police, EMS)
- Government buildings, courthouses
- Waste management, recycling programs

LAND USE & ENVIRONMENT:
- Annexations, municipal boundaries
- Critical area regulations
- Historic preservation decisions
- Environmental permits and reviews
- Waterfront access, marina issues

ACCOUNTABILITY & TRANSPARENCY:
- Ethics investigations, violations
- Open meetings law, public records disputes
- Government audits, investigations
- Lawsuits involving local government
- Regional cooperation or conflicts

Respond with a JSON object containing:
- "relevant": true if the story relates to ANY of the top issues above, false otherwise
- "key_topic": the title of the top issue this story relates to (from the list above), or null if not relevant
- "confidence": a number from 0.0 to 1.0

Examples:
{{"relevant": true, "key_topic": "Affordable Housing Initiatives", "confidence": 0.95}}
{{"relevant": true, "key_topic": "Cannabis Regulation and Zoning", "confidence": 0.88}}
{{"relevant": false, "key_topic": null, "confidence": 0.75}}

Your response (JSON only):"""


def load_stories(input_path: Path) -> list:
    """Load stories from JSON file."""
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_county_issues(issues_path: Path) -> str:
    """Load county issues and format them for the prompt."""
    with open(issues_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    issues_text = []
    for county, county_data in data.get('counties', {}).items():
        issues_text.append(f"\n{county.upper()}:")
        for issue in county_data.get('top_issues', []):
            rank = issue.get('rank', '?')
            title = issue.get('title', 'Unknown')
            description = issue.get('description', '')
            issues_text.append(f"  {rank}. {title}: {description}")
    
    return '\n'.join(issues_text)


def save_stories(stories: list, output_path: Path):
    """Save stories to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stories, f, indent=2, ensure_ascii=False)


def get_local_gov_score(story: dict) -> float:
    """Extract local government topic score from story classification."""
    classification = story.get('llm_classification', {})
    
    # Check primary topic
    if classification.get('topic') == 'Local Government':
        return classification.get('score', 0.0)
    
    # Check candidates
    candidates = classification.get('candidates', [])
    for candidate in candidates:
        if candidate.get('topic') == 'Local Government':
            return candidate.get('score', 0.0)
    
    return 0.0


def format_story_for_batch(story: dict, index: int) -> str:
    """Format a single story's metadata for batch evaluation."""
    title = story.get('title', 'Untitled')
    date = story.get('date', 'Unknown')
    content_type = story.get('content_type', 'Unknown')
    local_gov_score = get_local_gov_score(story)
    
    # Get topics
    classification = story.get('llm_classification', {})
    topics = []
    if classification.get('topic'):
        topics.append(f"{classification['topic']} ({classification.get('score', 0.0):.2f})")
    for candidate in classification.get('candidates', [])[:3]:
        if candidate.get('topic') != classification.get('topic'):
            topics.append(f"{candidate['topic']} ({candidate.get('score', 0.0):.2f})")
    
    counties = story.get('counties', [])
    key_people = story.get('key_people', [])[:3]
    key_organizations = story.get('key_organizations', [])[:3]
    key_initiatives = story.get('key_initiatives', [])[:3]
    
    return f"""
Story {index}:
- Title: {title}
- Date: {date}
- Content Type: {content_type}
- Local Government Score: {local_gov_score:.2f}
- Topics: {', '.join(topics) if topics else 'None'}
- Counties: {', '.join(counties) if counties else 'None'}
- Key People: {', '.join(key_people) if key_people else 'None'}
- Key Organizations: {', '.join(key_organizations) if key_organizations else 'None'}
- Key Initiatives: {', '.join(key_initiatives) if key_initiatives else 'None'}
"""


def evaluate_stories_batch(stories: list, county_issues_text: str) -> list:
    """Evaluate a batch of stories at once using LLM."""
    
    batch_prompt = RELEVANCE_PROMPT.format(county_issues=county_issues_text) + "\n\n"
    batch_prompt += "Evaluate the following stories. Respond with a JSON array containing one evaluation object for each story (in order), with these fields:\n"
    batch_prompt += '- "relevant": true/false (true if relates to ANY top issue)\n'
    batch_prompt += '- "key_topic": the exact title of the top issue from the list above, or null if not relevant\n'
    batch_prompt += '- "confidence": 0.0-1.0\n\n'
    
    for i, story in enumerate(stories, 1):
        batch_prompt += format_story_for_batch(story, i)
    
    batch_prompt += '\nYour response (JSON array only, no explanations):\n'
    
    # Call LLM
    try:
        result = subprocess.run(
            ['llm', '-m', LLM_MODEL],
            input=batch_prompt,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse JSON response
        response_text = result.stdout.strip()
        
        # Try to extract JSON if wrapped in markdown
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0].strip()
        
        evaluations = json.loads(response_text)
        
        # Ensure it's a list and has the right length
        if not isinstance(evaluations, list):
            raise ValueError("Response is not a list")
        if len(evaluations) != len(stories):
            raise ValueError(f"Expected {len(stories)} evaluations, got {len(evaluations)}")
        
        return evaluations
        
    except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError) as e:
        print(f"  ⚠️  Batch evaluation failed: {e}", file=sys.stderr)
        # Return all False as fallback
        return [{"relevant": False, "confidence": 0.0, "error": True} for _ in stories]


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Filter local government stories for beat book relevance')
    parser.add_argument('--limit', type=int, help='Limit number of stories to process')
    parser.add_argument('--skip', type=int, default=0, help='Skip first N stories')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without saving')
    args = parser.parse_args()
    
    input_path = Path(INPUT_FILE)
    output_path = Path(OUTPUT_FILE)
    issues_path = Path(COUNTY_ISSUES_FILE)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    if not issues_path.exists():
        print(f"Error: County issues file not found: {issues_path}", file=sys.stderr)
        print(f"Run analyze_county_issues.py first to generate this file.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loading county issues from {issues_path}...")
    county_issues_text = load_county_issues(issues_path)
    print(f"Loaded top issues for all counties")
    
    print(f"\nLoading stories from {input_path}...")
    stories = load_stories(input_path)
    print(f"Loaded {len(stories)} stories")
    
    # Reverse stories to process newest first
    stories = list(reversed(stories))
    print(f"Reversed stories to process newest first")
    
    # Apply skip and limit
    if args.skip > 0:
        stories = stories[args.skip:]
        print(f"Skipped first {args.skip} stories, {len(stories)} remaining")
    
    if args.limit:
        stories = stories[:args.limit]
        print(f"Limited to {len(stories)} stories")
    
    relevant_stories = []
    excluded_stories = []
    excluded_by_reason = {}
    stats = {
        'total': len(stories),
        'relevant': 0,
        'not_relevant': 0,
        'errors': 0,
        'non_news': 0
    }
    
    # Filter to only News stories upfront
    news_stories = [s for s in stories if s.get('content_type') == 'News']
    stats['non_news'] = len(stories) - len(news_stories)
    
    print(f"\nFiltered to {len(news_stories)} News stories (skipped {stats['non_news']} non-news)")
    print("Processing in batches of 10...")
    start_time = perf_counter()
    
    BATCH_SIZE = 10
    processed = 0
    
    for batch_start in range(0, len(news_stories), BATCH_SIZE):
        batch = news_stories[batch_start:batch_start + BATCH_SIZE]
        batch_num = (batch_start // BATCH_SIZE) + 1
        total_batches = (len(news_stories) + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"\n{'='*80}")
        print(f"Batch {batch_num}/{total_batches} (stories {batch_start+1}-{batch_start+len(batch)})")
        print(f"{'='*80}")
        
        batch_start_time = perf_counter()
        evaluations = evaluate_stories_batch(batch, county_issues_text)
        batch_time = perf_counter() - batch_start_time
        
        # Process results
        for story, evaluation in zip(batch, evaluations):
            processed += 1
            title = story.get('title', 'Untitled')
            
            # Add evaluation to story
            story['beatbook_evaluation'] = evaluation
            
            # Add key_topic field directly to story
            key_topic = evaluation.get('key_topic')
            if key_topic:
                story['key_topic'] = key_topic
            
            if evaluation.get('error'):
                print(f"  [{processed}] ⚠️  {title[:70]}")
                stats['errors'] += 1
                excluded_stories.append(story)
            elif evaluation.get('relevant'):
                topic_display = f" [{key_topic}]" if key_topic else ""
                print(f"  [{processed}] ✅ {title[:70]}{topic_display} (conf: {evaluation.get('confidence', 0):.2f})")
                relevant_stories.append(story)
                stats['relevant'] += 1
            else:
                print(f"  [{processed}] ❌ {title[:70]}")
                stats['not_relevant'] += 1
                excluded_stories.append(story)
        
        print(f"\nBatch completed in {batch_time:.1f}s ({batch_time/len(batch):.1f}s per story)")
        print(f"Running total: {stats['relevant']} relevant, {stats['not_relevant']} not relevant, {stats['errors']} errors")
        
        # Save every 10 relevant stories (check after each batch)
        if not args.dry_run and stats['relevant'] > 0 and stats['relevant'] % 10 <= len(batch):
            print(f"💾 Saving progress ({stats['relevant']} relevant stories so far)...")
            save_stories(relevant_stories, output_path)
    
    total_time = perf_counter() - start_time
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total stories processed: {stats['total']}")
    print(f"Non-news stories skipped: {stats['non_news']}")
    print(f"Relevant stories: {stats['relevant']}")
    print(f"Not relevant stories: {stats['not_relevant']}")
    print(f"Errors: {stats['errors']}")
    print(f"Total time: {total_time:.1f}s ({total_time/stats['total']:.1f}s per story)")
    
    # Print topic breakdown
    topic_counts = {}
    for story in relevant_stories:
        topic = story.get('key_topic', 'Unknown')
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
    
    if topic_counts:
        print("\nTOP ISSUES COVERAGE:")
        for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
            print(f"  {topic}: {count} stories")
    
    if args.dry_run:
        print("\n🔍 DRY RUN - No files saved")
    else:
        print(f"\nSaving {len(relevant_stories)} relevant stories to {output_path}...")
        save_stories(relevant_stories, output_path)
        
        # Save excluded stories
        excluded_path = Path(EXCLUDED_FILE)
        print(f"Saving {len(excluded_stories)} excluded stories to {excluded_path}...")
        save_stories(excluded_stories, excluded_path)
        print("✅ Done!")


if __name__ == '__main__':
    main()
