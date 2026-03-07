#!/usr/bin/env python3
"""
Refine beat book stories by analyzing each tag group and filtering for ongoing relevance.

This script takes beatbook_tagged_stories.json and has the LLM carefully analyze
stories within each tag to determine which are still relevant for a beat book in late 2025.
"""

import json
import subprocess
import sys
from pathlib import Path
from time import perf_counter
from collections import defaultdict

# Configuration
INPUT_FILE = "beatbook_tagged_stories.json"
OUTPUT_FILE = "beatbook_refined_stories.json"
LLM_MODEL = "groq/meta-llama/llama-4-maverick-17b-128e-instruct"

REFINEMENT_PROMPT = """You are refining stories for a LOCAL GOVERNMENT BEAT BOOK in LATE 2025 covering five Maryland counties: Talbot, Kent, Dorchester, Caroline, and Queen Anne's.

A beat book is a reference tool for reporters. It should contain stories that:
- Provide background on ONGOING issues and controversies
- Introduce key decision-makers and their stances
- Explain policies that are still relevant
- Document important precedents and context
- Help understand current political dynamics

CONTEXT: It is now late November 2025. Consider story dates when evaluating relevance.

EXCLUDE stories that are:
- One-time events with no lasting impact (routine meetings, single appointments)
- Stories older than 2 years UNLESS they involve ongoing controversies or foundational policies
- Routine administrative actions without policy significance
- Stories primarily about individuals rather than issues/policies
- Purely procedural votes without substantive policy content

INCLUDE stories that:
- Document ongoing controversies or initiatives (even if older)
- Establish important context for current issues
- Introduce key officials and their policy positions
- Explain regulations, zoning, or policies still in effect
- Show patterns of governance (voting blocks, recurring conflicts)
- Provide precedents for understanding current decisions

Below are stories all tagged as "{tag}". Evaluate each story for beat book relevance in late 2025.

{stories}

Respond with ONLY a JSON array. Each evaluation must have EXACTLY these fields:
{{
  "story_index": number (0-based index in the list),
  "relevant": true or false,
  "reason": "brief explanation why included or excluded"
}}

Your JSON array response:
"""


def load_stories(input_path: Path) -> list:
    """Load stories from JSON file."""
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_stories(stories: list, output_path: Path):
    """Save stories to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stories, f, indent=2, ensure_ascii=False)


def group_by_tag(stories: list) -> dict:
    """Group stories by their beatbook_tag."""
    by_tag = defaultdict(list)
    for story in stories:
        tag = story.get('beatbook_tag', 'Untagged')
        by_tag[tag].append(story)
    return dict(by_tag)


def format_story_for_evaluation(story: dict, index: int) -> str:
    """Format a story for LLM evaluation."""
    title = story.get('title', 'Untitled')
    date = story.get('date', 'Unknown')
    counties = ', '.join(story.get('counties', []))
    content = story.get('content', '')[:800]  # Limit content length
    
    return f"""Story {index}:
Title: {title}
Date: {date}
Counties: {counties}
Content: {content}...

"""


def evaluate_tag_batch(tag: str, stories: list, batch_start: int, batch_size: int) -> list:
    """Evaluate a batch of stories within a tag for relevance."""
    batch = stories[batch_start:batch_start + batch_size]
    
    # Format stories for prompt
    stories_text = ""
    for i, story in enumerate(batch):
        stories_text += format_story_for_evaluation(story, i)
    
    prompt = REFINEMENT_PROMPT.format(tag=tag, stories=stories_text)
    
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
        
        evaluations = json.loads(response_text)
        
        if not isinstance(evaluations, list):
            raise ValueError("Response is not a list")
        
        return evaluations
        
    except (subprocess.CalledProcessError, json.JSONDecodeError, ValueError) as e:
        print(f"  ⚠️  Batch evaluation failed: {e}", file=sys.stderr)
        # Default to keeping all on error
        return [{"story_index": i, "relevant": True, "reason": "error - keeping"} for i in range(len(batch))]


def main():
    """Main execution function."""
    import argparse
    parser = argparse.ArgumentParser(description='Refine beatbook stories for late 2025 relevance')
    parser.add_argument('--tag', help='Process only this tag')
    parser.add_argument('--batch-size', type=int, default=8, help='Stories per batch (default: 8)')
    args = parser.parse_args()
    
    input_path = Path(INPUT_FILE)
    output_path = Path(OUTPUT_FILE)
    
    print(f"Loading stories from {input_path}...")
    all_stories = load_stories(input_path)
    print(f"Loaded {len(all_stories)} stories")
    
    # Group by tag
    by_tag = group_by_tag(all_stories)
    print(f"\nFound {len(by_tag)} tags")
    
    # Filter to specific tag if requested
    if args.tag:
        if args.tag not in by_tag:
            print(f"Error: Tag '{args.tag}' not found")
            sys.exit(1)
        by_tag = {args.tag: by_tag[args.tag]}
        print(f"Processing only tag: {args.tag}")
    
    refined_stories = []
    stats = {
        'total': len(all_stories),
        'kept': 0,
        'removed': 0,
        'errors': 0
    }
    
    start_time = perf_counter()
    
    # Process each tag
    for tag_num, (tag, stories) in enumerate(sorted(by_tag.items(), key=lambda x: -len(x[1])), 1):
        print(f"\n{'='*80}")
        print(f"TAG {tag_num}/{len(by_tag)}: {tag}")
        print(f"{'='*80}")
        print(f"{len(stories)} stories to evaluate")
        print()
        
        tag_start_time = perf_counter()
        kept_count = 0
        removed_count = 0
        
        # Process in batches
        BATCH_SIZE = args.batch_size
        total_batches = (len(stories) + BATCH_SIZE - 1) // BATCH_SIZE
        
        for batch_start in range(0, len(stories), BATCH_SIZE):
            batch = stories[batch_start:batch_start + BATCH_SIZE]
            batch_num = (batch_start // BATCH_SIZE) + 1
            
            print(f"  Batch {batch_num}/{total_batches} (stories {batch_start+1}-{batch_start+len(batch)})...")
            
            evaluations = evaluate_tag_batch(tag, stories, batch_start, BATCH_SIZE)
            
            # Process evaluations
            for eval_data in evaluations:
                idx = eval_data.get('story_index', 0)
                if idx >= len(batch):
                    continue
                    
                story = batch[idx]
                relevant = eval_data.get('relevant', True)
                reason = eval_data.get('reason', '')
                
                story['refinement_evaluation'] = {
                    'relevant': relevant,
                    'reason': reason,
                    'evaluated_date': '2025-11-29'
                }
                
                if relevant:
                    refined_stories.append(story)
                    kept_count += 1
                    stats['kept'] += 1
                    title = story.get('title', 'Untitled')[:60]
                    print(f"    ✅ {title}")
                else:
                    removed_count += 1
                    stats['removed'] += 1
                    title = story.get('title', 'Untitled')[:60]
                    print(f"    ❌ {title} - {reason[:40]}")
        
        tag_time = perf_counter() - tag_start_time
        print(f"\n  Tag summary: Kept {kept_count}, Removed {removed_count} ({tag_time:.1f}s)")
        
        # Save progress after each tag
        print(f"  💾 Saving progress ({len(refined_stories)} stories)...")
        save_stories(refined_stories, output_path)
    
    total_time = perf_counter() - start_time
    
    # Final summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"Total stories processed: {stats['total']}")
    print(f"Stories kept: {stats['kept']} ({stats['kept']/stats['total']*100:.1f}%)")
    print(f"Stories removed: {stats['removed']} ({stats['removed']/stats['total']*100:.1f}%)")
    print(f"Total time: {total_time:.1f}s ({total_time/stats['total']:.1f}s per story)")
    
    print(f"\n✅ Saved {len(refined_stories)} refined stories to {output_path}")


if __name__ == '__main__':
    main()
