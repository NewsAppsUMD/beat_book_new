#!/usr/bin/env python3
"""
Evaluate stories for beat book relevance and assign general tags.

This script reads local_government_all_stories_combined.json and uses an LLM to:
1. Determine if each story is relevant for a beat book
2. If relevant, assign a general tag for organization
"""

import json
import subprocess
import sys
from pathlib import Path
from time import perf_counter

# Configuration
INPUT_FILE = "local_government_all_stories_combined.json"
OUTPUT_FILE = "beatbook_tagged_stories.json"
LLM_MODEL = "groq/meta-llama/llama-4-maverick-17b-128e-instruct"

# General tags for organization
TAGS = [
    "Governance & Leadership",
    "Budget & Finance",
    "Development & Zoning",
    "Infrastructure",
    "Public Safety",
    "Environment",
    "Elections & Accountability",
    "Education",
    "Economic Development",
    "Community Services"
]

EVALUATION_PROMPT = """You are evaluating stories for a LOCAL GOVERNMENT BEAT BOOK covering five Maryland counties: Talbot, Kent, Dorchester, Caroline, and Queen Anne's.

A beat book should contain stories that help a reporter understand KEY ISSUES, DECISION-MAKERS, and POLICIES in their coverage area.

GENERAL TAGS (choose ONE):
- **Governance & Leadership**: Council/commission meetings, appointments, official actions, personnel changes
- **Budget & Finance**: Budgets, taxes, funding, fiscal decisions, grants
- **Development & Zoning**: Land use, zoning, development projects, housing, comprehensive plans
- **Infrastructure**: Roads, bridges, water/sewer, utilities, public facilities, transportation
- **Public Safety**: Police, fire, emergency services, law enforcement policies
- **Environment**: Environmental regulations, conservation, flooding, climate, waterfront
- **Elections & Accountability**: Elections, transparency, ethics, investigations, open meetings
- **Education**: School boards, education funding, school facilities
- **Economic Development**: Business attraction, tourism, economic initiatives, downtown revitalization
- **Community Services**: Parks, recreation, libraries, social programs

INCLUDE stories about:
- Local government meetings, votes, and decisions
- Policy changes and regulations
- Major projects and initiatives
- Budget and funding decisions
- Leadership changes and controversies
- Land use and development
- Public services and infrastructure
- Elections and government accountability

EXCLUDE stories that are:
- Pure opinion/editorial without reporting government action
- Routine announcements with no policy impact
- Stories ONLY about other jurisdictions (not the 5 counties)
- Individual citizen complaints without government response
- One-time events with no ongoing policy relevance

Story to evaluate:
Title: {title}
Date: {date}
Counties: {counties}
Content Type: {content_type}
Content: {content}

Respond with JSON:
{{
  "relevant": true or false,
  "tag": "Tag name from list above" or null if not relevant,
  "confidence": 0.0-1.0
}}

Your response (JSON only):"""


def load_stories(input_path: Path) -> list:
    """Load stories from JSON file."""
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_stories(stories: list, output_path: Path):
    """Save stories to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stories, f, indent=2, ensure_ascii=False)


def evaluate_stories_batch(stories: list) -> list:
    """Evaluate a batch of stories at once using LLM."""
    
    batch_prompt = EVALUATION_PROMPT.split("Story to evaluate:")[0]
    batch_prompt += "\n\nEvaluate the following stories. Respond with a JSON array containing one evaluation for each story (in order):\n\n"
    
    for i, story in enumerate(stories, 1):
        title = story.get('title', 'Untitled')
        date = story.get('date', 'Unknown')
        counties = ', '.join(story.get('counties', []))
        content_type = story.get('content_type', 'Unknown')
        content = story.get('content', '')[:1500]  # Limit to first 1500 chars
        
        batch_prompt += f"""Story {i}:
Title: {title}
Date: {date}
Counties: {counties}
Content Type: {content_type}
Content: {content}

"""
    
    batch_prompt += '''
Respond with ONLY a JSON array. Each evaluation must have EXACTLY these fields:
{
  "relevant": true or false,
  "tag": "exact tag name from list" or null,
  "confidence": number between 0.0 and 1.0
}

Example response format:
[
  {"relevant": true, "tag": "Governance & Leadership", "confidence": 0.9},
  {"relevant": false, "tag": null, "confidence": 0.0}
]

Your JSON array response:
'''
    
    # Call LLM
    try:
        result = subprocess.run(
            ['llm', '-m', LLM_MODEL],
            input=batch_prompt,
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
        
        evaluations = json.loads(response_text)
        
        if not isinstance(evaluations, list):
            raise ValueError("Response is not a list")
        if len(evaluations) != len(stories):
            raise ValueError(f"Expected {len(stories)} evaluations, got {len(evaluations)}")
        
        return evaluations
        
    except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError) as e:
        print(f"  ⚠️  Batch evaluation failed: {e}", file=sys.stderr)
        return [{"relevant": False, "tag": None, "confidence": 0.0, "error": True} for _ in stories]


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Tag stories for beat book')
    parser.add_argument('--limit', type=int, help='Limit number of stories to process')
    parser.add_argument('--skip', type=int, default=0, help='Skip first N stories')
    args = parser.parse_args()
    
    input_path = Path(INPUT_FILE)
    output_path = Path(OUTPUT_FILE)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loading stories from {input_path}...")
    stories = load_stories(input_path)
    print(f"Loaded {len(stories)} stories")
    
    # Reverse to process newest first
    stories = list(reversed(stories))
    print(f"Reversed to process newest first")
    
    # Apply skip and limit
    if args.skip > 0:
        stories = stories[args.skip:]
        print(f"Skipped first {args.skip} stories")
    
    if args.limit:
        stories = stories[:args.limit]
        print(f"Limited to {len(stories)} stories")
    
    # Filter to News stories only
    news_stories = [s for s in stories if s.get('content_type') == 'News']
    print(f"Filtered to {len(news_stories)} News stories")
    
    relevant_stories = []
    tag_counts = {tag: 0 for tag in TAGS}
    stats = {
        'total': len(news_stories),
        'relevant': 0,
        'not_relevant': 0,
        'errors': 0
    }
    
    print("\nProcessing in batches of 10...")
    print("Available tags:", ', '.join(TAGS))
    print()
    start_time = perf_counter()
    
    BATCH_SIZE = 10
    processed = 0
    
    for batch_start in range(0, len(news_stories), BATCH_SIZE):
        batch = news_stories[batch_start:batch_start + BATCH_SIZE]
        batch_num = (batch_start // BATCH_SIZE) + 1
        total_batches = (len(news_stories) + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"{'='*80}")
        print(f"Batch {batch_num}/{total_batches} (stories {batch_start+1}-{batch_start+len(batch)})")
        print(f"{'='*80}")
        
        batch_start_time = perf_counter()
        evaluations = evaluate_stories_batch(batch)
        batch_time = perf_counter() - batch_start_time
        
        for story, evaluation in zip(batch, evaluations):
            processed += 1
            title = story.get('title', 'Untitled')
            
            story['beatbook_evaluation'] = evaluation
            
            if evaluation.get('error'):
                print(f"  [{processed}] ⚠️  {title[:70]}")
                stats['errors'] += 1
            elif evaluation.get('relevant'):
                tag = evaluation.get('tag', 'Untagged')
                conf = evaluation.get('confidence', 0.0)
                print(f"  [{processed}] ✅ [{tag}] {title[:50]} (conf: {conf:.2f})")
                
                story['beatbook_tag'] = tag
                relevant_stories.append(story)
                stats['relevant'] += 1
                if tag in tag_counts:
                    tag_counts[tag] += 1
            else:
                print(f"  [{processed}] ❌ {title[:70]}")
                stats['not_relevant'] += 1
        
        print(f"\nBatch time: {batch_time:.1f}s")
        print(f"Running total: {stats['relevant']} relevant, {stats['not_relevant']} excluded, {stats['errors']} errors")
        
        # Save progress every 10 relevant stories
        if stats['relevant'] > 0 and stats['relevant'] % 10 <= len(batch):
            print(f"💾 Saving progress ({stats['relevant']} stories)...")
            save_stories(relevant_stories, output_path)
    
    total_time = perf_counter() - start_time
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total stories: {stats['total']}")
    print(f"Relevant: {stats['relevant']}")
    print(f"Not relevant: {stats['not_relevant']}")
    print(f"Errors: {stats['errors']}")
    print(f"Time: {total_time:.1f}s ({total_time/stats['total']:.1f}s per story)")
    
    print("\nSTORIES BY TAG:")
    for tag in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True):
        if tag[1] > 0:
            print(f"  {tag[0]}: {tag[1]}")
    
    print(f"\nSaving {len(relevant_stories)} stories to {output_path}...")
    save_stories(relevant_stories, output_path)
    print("✅ Done!")


if __name__ == '__main__':
    main()
