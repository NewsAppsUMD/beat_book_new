import json
import sys
import subprocess
from pathlib import Path
from time import perf_counter

INPUT_FILE = "data/local_government_stories.json"
OUTPUT_FILE = "data/local_government_stories_top_issues.json"
PROGRESS_FILE = "data/top_issues_progress.json"
SCORE_THRESHOLD = 0.7
LLM_MODEL = "groq/meta-llama/llama-4-maverick-17b-128e-instruct"
BATCH_SIZE = 20

# Top 10 issues from 2025 analysis
TOP_ISSUES = [
    "Town/City Council decisions and meetings",
    "Budget and Finance matters (budgets, funding, taxes, bonds)",
    "Ordinances and Regulations (local laws, policies)",
    "Elections and Political Candidates",
    "Community Engagement and public input",
    "Development and Housing projects",
    "Planning and Zoning Board decisions",
    "State/Local Relations (state legislation affecting local areas)",
    "County Government decisions",
    "Infrastructure (roads, bridges, water, sewer, utilities)"
]

def call_llm_batch(prompts):
    """Call LLM to analyze multiple stories at once."""
    # Combine prompts into a single batch prompt
    batch_prompt = "Analyze each story below and answer YES or NO for each.\n\n"
    for idx, prompt in enumerate(prompts, 1):
        batch_prompt += f"STORY {idx}:\n{prompt}\n\n"
    
    batch_prompt += f"\nProvide {len(prompts)} answers in order, each on its own line, starting with 'STORY X: YES' or 'STORY X: NO'."
    
    try:
        result = subprocess.run(
            ["llm", "-m", LLM_MODEL],
            input=batch_prompt.encode(),
            capture_output=True,
            check=True,
            timeout=60
        )
        
        response_text = result.stdout.decode().strip().lower()
        
        # Parse responses
        answers = []
        lines = response_text.split('\n')
        for line in lines:
            if 'yes' in line[:50]:
                answers.append(True)
            elif 'no' in line[:50]:
                answers.append(False)
        
        # If we didn't get enough answers, pad with True (include by default)
        while len(answers) < len(prompts):
            answers.append(True)
            
        return answers[:len(prompts)]
            
    except Exception as e:
        print(f"❌ Batch LLM call failed: {e}", file=sys.stderr)
        # Default to including all on error
        return [True] * len(prompts)

def check_top_issues_relevance_batch(stories):
    """
    Use LLM to check if stories relate to the top 10 issues of 2025.
    Returns list of True/False for each story.
    """
    prompts = []
    for story in stories:
        title = story.get("title", "")
        year = story.get("year", 0)
        llm_class = story.get("llm_classification", {})
        explanation = llm_class.get("explanation", "")
        
        # Create context about the story's timeframe
        timeframe_note = ""
        if year < 2025:
            timeframe_note = f"\n\nNOTE: This story is from {year} (BEFORE 2025). Only include it if it relates to ongoing events or provides important historical context for 2025 issues."
        
        prompt = f"""You are filtering local government stories for a beat book. Only keep stories related to these TOP 10 ISSUES:

1. Town/City Council decisions and meetings
2. Budget and Finance matters (budgets, funding, taxes, bonds)
3. Ordinances and Regulations (local laws, policies)
4. Elections and Political Candidates
5. Community Engagement and public input
6. Development and Housing projects
7. Planning and Zoning Board decisions
8. State/Local Relations (state legislation affecting local areas)
9. County Government decisions
10. Infrastructure (roads, bridges, water, sewer, utilities)

Title: {title}
Year: {year}
Explanation: {explanation}{timeframe_note}

Does this story clearly relate to one or more of the top 10 issues above? Answer ONLY "YES" (keep it) or "NO" (exclude it)."""
        
        prompts.append(prompt)
    
    return call_llm_batch(prompts)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Filter stories by top 10 issues of 2025.')
    parser.add_argument('--limit', type=int, help='Limit number of stories to process (for testing)')
    parser.add_argument('--skip-llm', action='store_true', help='Skip LLM analysis, just do score filter')
    args = parser.parse_args()
    
    if not Path(INPUT_FILE).exists():
        print(f"Input file {INPUT_FILE} not found.", file=sys.stderr)
        sys.exit(1)
    
    with open(INPUT_FILE, "r") as f:
        stories = json.load(f)
    
    if args.limit:
        stories = stories[:args.limit]
        print(f"⚠️  Limited to {args.limit} stories for testing")
    
    print(f"📊 Starting with {len(stories)} stories")
    
    # First filter: score threshold
    filtered_stories = []
    score_rejected = 0
    
    for story in stories:
        llm_class = story.get("llm_classification", {})
        
        # Check if this is a Local Government story
        if llm_class.get("topic") == "Local Government":
            score = llm_class.get("score", 0)
            
            if score >= SCORE_THRESHOLD:
                filtered_stories.append(story)
            else:
                score_rejected += 1
        else:
            # Not even classified as Local Government
            score_rejected += 1
    
    print(f"❌ Rejected {score_rejected} stories with score < {SCORE_THRESHOLD} or wrong topic")
    print(f"✅ Kept {len(filtered_stories)} stories after score filter")
    
    # Show breakdown by year
    from collections import Counter
    year_counts = Counter(s.get("year") for s in filtered_stories if s.get("year"))
    print(f"\n📅 Stories by year after score filter:")
    for year in sorted(year_counts.keys()):
        print(f"   {year}: {year_counts[year]} stories")
    
    if args.skip_llm:
        print(f"⚠️  Skipping LLM analysis (--skip-llm flag)")
        final_stories = filtered_stories
    else:
        # Second filter: LLM-based top issues relevance (in batches)
        print(f"\n🤖 Starting LLM analysis for top 10 issues (batch size: {BATCH_SIZE})...")
        print(f"\nTop 10 Issues:")
        for i, issue in enumerate(TOP_ISSUES, 1):
            print(f"   {i}. {issue}")
        print()
        
        # Load progress if it exists
        progress_data = {}
        start_idx = 0
        if Path(PROGRESS_FILE).exists():
            with open(PROGRESS_FILE, "r") as f:
                progress_data = json.load(f)
                final_stories = progress_data.get("filtered_stories", [])
                start_idx = progress_data.get("last_processed_index", 0)
                if start_idx > 0:
                    print(f"📂 Resuming from story {start_idx + 1}")
        else:
            final_stories = []
        
        relevance_rejected = 0
        start_time = perf_counter()
        
        try:
            # Process in batches
            for batch_start in range(start_idx, len(filtered_stories), BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE, len(filtered_stories))
                batch = filtered_stories[batch_start:batch_end]
                
                print(f"  Processing batch [{batch_start + 1}-{batch_end}/{len(filtered_stories)}]...", flush=True)
                
                # Get batch results
                results = check_top_issues_relevance_batch(batch)
                
                # Process results
                for idx, (story, keep) in enumerate(zip(batch, results)):
                    title = story.get("title", "")[:60]
                    year = story.get("year", "")
                    actual_idx = batch_start + idx
                    status = "✓ INCLUDE" if keep else "✗ EXCLUDE"
                    print(f"    [{actual_idx + 1}] ({year}) {title}... {status}")
                    
                    if keep:
                        final_stories.append(story)
                    else:
                        relevance_rejected += 1
                
                # Save progress after each batch
                with open(PROGRESS_FILE, "w") as f:
                    json.dump({
                        "last_processed_index": batch_end,
                        "filtered_stories": final_stories,
                        "relevance_rejected": relevance_rejected
                    }, f, indent=2)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user. Progress saved.")
            with open(PROGRESS_FILE, "w") as f:
                json.dump({
                    "last_processed_index": batch_start,
                    "filtered_stories": final_stories,
                    "relevance_rejected": relevance_rejected
                }, f, indent=2)
            print(f"💾 Progress saved to {PROGRESS_FILE}")
            print(f"   Processed {batch_start}/{len(filtered_stories)} stories")
            print(f"   Run again to resume from where you left off")
            sys.exit(0)
        
        elapsed = perf_counter() - start_time
        avg_per_story = elapsed / len(filtered_stories) if len(filtered_stories) > 0 else 0
        print(f"\n⏱️  LLM analysis took {elapsed:.1f}s ({avg_per_story:.2f}s per story)")
        print(f"❌ Rejected {relevance_rejected} stories not related to top 10 issues")
        print(f"✅ Final count: {len(final_stories)} stories")
        
        # Show final breakdown by year
        year_counts_final = Counter(s.get("year") for s in final_stories if s.get("year"))
        print(f"\n📅 Final stories by year:")
        for year in sorted(year_counts_final.keys()):
            print(f"   {year}: {year_counts_final[year]} stories")
        
        # Remove progress file after successful completion
        if Path(PROGRESS_FILE).exists():
            Path(PROGRESS_FILE).unlink()
            print(f"🗑️  Removed progress file")
    
    # Save filtered stories
    with open(OUTPUT_FILE, "w") as f:
        json.dump(final_stories, f, indent=2)
    
    print(f"\n💾 Saved filtered stories to {OUTPUT_FILE}")
    
    # Print summary stats
    print(f"\n📈 Summary:")
    print(f"  Original: {len(stories)}")
    print(f"  After score filter: {len(filtered_stories)} ({len(filtered_stories)/len(stories)*100:.1f}%)")
    if not args.skip_llm:
        print(f"  After top issues filter: {len(final_stories)} ({len(final_stories)/len(stories)*100:.1f}%)")
    print(f"  Total rejected: {len(stories) - len(final_stories)} ({(len(stories) - len(final_stories))/len(stories)*100:.1f}%)")

if __name__ == "__main__":
    main()
