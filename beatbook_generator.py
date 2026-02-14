#!/usr/bin/env python3
"""
Generate a reporter-friendly beat book from news stories with existing metadata.
Uses pre-extracted metadata to create a concise, practical guide.
"""

import json
import llm
import sys
from pathlib import Path
from collections import Counter

def get_model(model_name=None):
    """Get the LLM model to use."""
    if model_name:
        return llm.get_model(model_name)
    return llm.get_model()

def analyze_metadata(stories):
    """Extract key patterns from story metadata."""
    topics = Counter()
    all_people = []
    all_places = []
    all_orgs = []
    dates = []
    
    for story in stories:
        # Track topics
        if 'llm_classification' in story and 'topic' in story['llm_classification']:
            topics[story['llm_classification']['topic']] += 1
        
        # Collect metadata
        if 'people' in story:
            all_people.extend(story['people'])
        if 'places' in story:
            all_places.extend(story['places'])
        if 'organizations' in story:
            all_orgs.extend(story['organizations'])
        if 'date' in story:
            dates.append(story['date'])
    
    # Get most common entities
    people_counter = Counter(all_people)
    places_counter = Counter(all_places)
    orgs_counter = Counter(all_orgs)
    
    return {
        'topics': topics.most_common(),
        'top_people': people_counter.most_common(20),
        'top_places': places_counter.most_common(15),
        'top_orgs': orgs_counter.most_common(15),
        'date_range': (min(dates) if dates else None, max(dates) if dates else None),
        'total_stories': len(stories)
    }

def select_representative_stories(stories, model):
    """Select 4-6 diverse, representative stories for examples."""
    # Sample from stories to avoid overwhelming the model
    sample_size = min(50, len(stories))
    sample_stories = stories[:sample_size]
    
    prompt = f"""From this collection of {len(stories)} stories (showing first {sample_size}), identify 4-6 representative examples that showcase different story types.

Choose stories that demonstrate:
- Breaking news: timely incident coverage
- Feature: longer-form, human interest angle
- Profile: focused on specific people or organizations
- In-depth: investigative or analytical piece

Select stories that show geographic diversity and substantive reporting (not just briefs).

Return a JSON array with story indices (0-based from the sample provided) and brief explanations.

Stories:
{json.dumps([{'idx': i, 'title': s['title'], 'date': s.get('date', ''), 'content': s['content'][:400]} for i, s in enumerate(sample_stories)], indent=2)}

Return format: {{"selections": [{{"idx": 0, "type": "breaking news", "reason": "..."}}]}}"""
    
    print("Selecting representative stories...", file=sys.stderr)
    response = model.prompt(prompt)
    try:
        result = json.loads(response.text())
        return result.get('selections', [])
    except:
        # Fallback: pick first few diverse ones
        return [{'idx': i, 'type': 'example', 'reason': 'Representative story'} for i in range(min(5, len(stories)))]

def identify_followups(stories, model):
    """Identify up to 5 potential follow-up stories."""
    recent_stories = sorted(stories, key=lambda x: x.get('date', ''), reverse=True)[:50]
    
    prompt = f"""From these recent stories, identify up to 5 that suggest potential follow-up angles. Look for:
- Ongoing investigations or pending outcomes
- Unresolved issues or unanswered questions
- Policy changes in progress
- Community concerns that need updates

Remember: This dataset may be outdated, so frame these as "potential" follow-ups that might have been resolved.

Stories:
{json.dumps([{'title': s['title'], 'date': s.get('date', ''), 'content': s['content'][:300]} for s in recent_stories[:30]], indent=2)}

Return JSON: {{"followups": [{{"title": "...", "angle": "...", "why": "..."}}]}}"""
    
    print("Identifying follow-up opportunities...", file=sys.stderr)
    response = model.prompt(prompt)
    try:
        result = json.loads(response.text())
        return result.get('followups', [])[:5]  # Max 5
    except:
        return []

def extract_from_batch(stories, batch_num, model):
    """First pass: extract key information from a batch of stories."""
    prompt = f"""You are analyzing news coverage to help onboard a new reporter. Your focus should be on public safety stories from Talbot County, Maryland. 

From these {len(stories)} news stories, extract:
1. Public safety themes and patterns (law enforcement, fire/EMS, violent crime, property crime, emergency response)
2. Geographic patterns (which communities: Easton, St. Michaels, Oxford, Trappe, rural areas)
3. Key people mentioned (local officials, law enforcement, emergency personnel - with their roles)
4. Important organizations (Talbot County Sheriff's Office, local police departments, fire departments, emergency services)
5. Significant incidents and multi-jurisdiction responses
6. Recurring issues that connect multiple stories

Be concise but capture location-specific details and patterns unique to Talbot County.

Stories:
{json.dumps(stories, indent=2)}

Provide a structured summary:"""
    
    print(f"Processing batch {batch_num}...", file=sys.stderr)
    response = model.prompt(prompt)
    return response.text()

def synthesize_intermediate(summaries, level, model):
    """Synthesize a group of summaries into a higher-level summary."""
    combined = "\n\n---\n\n".join(
        f"SECTION {i+1}:\n{summary}" 
        for i, summary in enumerate(summaries)
    )
    
    prompt = f"""Consolidate these {len(summaries)} coverage summaries into a single comprehensive summary.

Preserve all important:
- People and their roles
- Organizations and institutions
- Major themes and issues
- Significant events and developments
- Ongoing debates and conflicts

Be thorough but concise. This will be combined with other summaries later.

SUMMARIES TO CONSOLIDATE:
{combined}

CONSOLIDATED SUMMARY:"""
    
    print(f"Consolidating level {level} ({len(summaries)} summaries)...", file=sys.stderr)
    response = model.prompt(prompt)
    return response.text()

def generate_beatbook(stories, metadata, model, batch_summaries, topic="this beat", max_summaries_per_level=5):
    """Generate the final beat book with a friendly, reporter-focused tone."""
    
    # Get representative stories
    rep_stories = select_representative_stories(stories, model)
    
    # Get follow-up suggestions
    followups = identify_followups(stories, model)
    
    # Consolidate batch summaries hierarchically if needed
    if len(batch_summaries) <= max_summaries_per_level:
        combined = "\n\n---\n\n".join(
            f"BATCH {i+1}:\n{summary}" 
            for i, summary in enumerate(batch_summaries)
        )
    else:
        # Hierarchical consolidation
        current_level = batch_summaries
        level = 1
        
        while len(current_level) > max_summaries_per_level:
            next_level = []
            for i in range(0, len(current_level), max_summaries_per_level):
                group = current_level[i:i+max_summaries_per_level]
                consolidated = synthesize_intermediate(group, level, model)
                next_level.append(consolidated)
            current_level = next_level
            level += 1
        
        combined = "\n\n---\n\n".join(
            f"SECTION {i+1}:\n{summary}" 
            for i, summary in enumerate(current_level)
        )
    
    prompt = f"""You're helping onboard a new reporter covering public safety in Talbot County, Maryland. Write a practical, business-casual beat book.

DATASET INFO:
- {metadata['total_stories']} stories from Star Democrat
- Date range: {metadata['date_range'][0]} to {metadata['date_range'][1]}
- Top topics: {', '.join([f"{t[0]} ({t[1]})" for t in metadata['topics'][:5]])}

KEY PEOPLE (most frequently mentioned):
{chr(10).join([f"- {p[0]} ({p[1]} mentions)" for p in metadata['top_people'][:15]])}

KEY PLACES:
{chr(10).join([f"- {p[0]} ({p[1]} mentions)" for p in metadata['top_places'][:12]])}

KEY ORGANIZATIONS:
{chr(10).join([f"- {o[0]} ({o[1]} mentions)" for o in metadata['top_orgs'][:12]])}

**TALBOT COUNTY DEMOGRAPHIC CONTEXT:**
Use this demographic information to provide context where relevant:

**Population & Geography:**
- Population: ~37,500 residents (2023 estimate)
- County seat: Easton (population ~16,800)
- Major towns: St. Michaels (~1,000), Oxford (~600), Trappe (~1,200)
- Land area: 269 square miles on Maryland's Eastern Shore
- Mix of urban (Easton), historic waterfront towns, and rural areas

**Demographics:**
- Race/Ethnicity: 78.5% White, 14.5% Black/African American, 4.8% Hispanic/Latino, 2.2% other
- Median age: 48.5 years (significantly older than Maryland average of 39)
- 65 years and older: 24.8%

**Economic Indicators:**
- Median household income: $72,300 (Maryland: $97,300)
- Per capita income: $43,800
- Poverty rate: 9.5%
- Unemployment rate: ~3.5%

**Community Notes:**
- Homeownership rate: 73.8%
- Significant seasonal tourism economy
- Mix of working waterfront, agriculture, and service economy
- Rural geography affecting response times

INSTRUCTIONS:
1. Write a SHORT, friendly introduction (2-3 paragraphs max—no "executive summary" language, just welcome them to the beat)
2. Brief "What You're Covering" section (main themes only)
3. CONCISE "Geographic Notes" section—only truly important patterns. Don't make demographic claims unless clearly supported by the dataset or the demographic context above.
4. "Who's Who" section with key contacts (based on frequency)
5. "Organizations to Know" section
6. Keep it conversational and practical, like briefing a colleague over coffee

Tone: Business-casual, direct, helpful. Not formal or academic.

COVERAGE SUMMARIES:
{combined}

REPORTER'S BEAT BOOK:"""
    
    print("Generating main beat book content...", file=sys.stderr)
    response = model.prompt(prompt)
    beatbook_content = response.text()
    
    # Add story examples section
    examples_section = "\n\n## Story Examples\n\n"
    examples_section += "Here are a few pieces that show the range of coverage on this beat:\n\n"
    
    for sel in rep_stories[:6]:
        story = stories[sel['idx']]
        examples_section += f"### {sel.get('type', 'Example').title()}: \"{story['title']}\"\n"
        examples_section += f"*{story.get('date', 'Date unknown')}*\n\n"
        examples_section += f"**Why it's a good example:** {sel.get('reason', 'Representative of coverage')}\n\n"
    
    # Add follow-ups section
    followups_section = "\n\n## Potential Follow-Ups\n\n"
    followups_section += "*Note: This dataset may be outdated. These angles might have been covered already or circumstances may have changed. Always check for recent updates before pursuing.*\n\n"
    
    if followups:
        for i, fu in enumerate(followups[:5], 1):
            followups_section += f"{i}. **{fu.get('title', 'Untitled')}**\n"
            followups_section += f"   - Angle: {fu.get('angle', 'Follow-up opportunity')}\n"
            followups_section += f"   - Why: {fu.get('why', 'Needs update')}\n\n"
    else:
        followups_section += "No specific follow-ups identified from this dataset.\n"
    
    return beatbook_content + examples_section + followups_section

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate a reporter guide from news stories JSON'
    )
    parser.add_argument('input_file', help='Path to JSON file with news stories')
    parser.add_argument('-o', '--output',
                       help='Output file for the beat book (default: beatbook.md in same directory as input)')
    parser.add_argument('-b', '--batch-size', type=int, default=30,
                       help='Number of stories per batch (default: 30)')
    parser.add_argument('-m', '--model', 
                       help='LLM model to use (default: llm default model)')
    parser.add_argument('-t', '--topic', default='this beat',
                       help='Topic/beat name for the guide')
    parser.add_argument('--summaries-only', action='store_true',
                       help='Save batch summaries without final synthesis')
    parser.add_argument('--debug', action='store_true',
                       help='Save intermediate outputs for debugging')
    
    args = parser.parse_args()
    
    # Load stories
    print(f"Loading stories from {args.input_file}...", file=sys.stderr)
    with open(args.input_file, 'r') as f:
        data = json.load(f)
    
    # Handle different JSON structures
    if isinstance(data, list):
        stories = data
    elif isinstance(data, dict) and 'stories' in data:
        stories = data['stories']
    elif isinstance(data, dict) and 'articles' in data:
        stories = data['articles']
    else:
        print("Error: JSON structure not recognized. Expected a list or dict with 'stories' or 'articles' key.", 
              file=sys.stderr)
        sys.exit(1)
    
    print(f"Loaded {len(stories)} stories", file=sys.stderr)
    
    # Set default output file if not specified
    if not args.output:
        input_path = Path(args.input_file)
        args.output = str(input_path.parent / 'beatbook.md')
    
    # Get model
    model = get_model(args.model)
    print(f"Using model: {model.model_id}", file=sys.stderr)
    
    # Analyze metadata
    print("Analyzing story metadata...", file=sys.stderr)
    metadata = analyze_metadata(stories)
    
    # First pass: extract from batches
    batch_summaries = []
    num_batches = (len(stories) + args.batch_size - 1) // args.batch_size
    
    for i in range(0, len(stories), args.batch_size):
        batch = stories[i:i+args.batch_size]
        batch_num = i // args.batch_size + 1
        summary = extract_from_batch(batch, batch_num, model)
        batch_summaries.append(summary)
        
        # Debug: save each batch summary
        if args.debug:
            debug_file = f"debug_batch_{batch_num:03d}.md"
            with open(debug_file, 'w') as f:
                f.write(summary)
    
    # Debug: check total size of all summaries
    if args.debug:
        total_chars = sum(len(s) for s in batch_summaries)
        total_words = sum(len(s.split()) for s in batch_summaries)
        print(f"\nDEBUG: Total summaries size:", file=sys.stderr)
        print(f"  {total_chars:,} characters", file=sys.stderr)
        print(f"  {total_words:,} words", file=sys.stderr)
        print(f"  ~{total_words * 1.3:.0f} tokens (estimate)", file=sys.stderr)
    
    # Save batch summaries if requested
    if args.summaries_only:
        output_file = args.output.replace('.md', '_summaries.md')
        with open(output_file, 'w') as f:
            for i, summary in enumerate(batch_summaries, 1):
                f.write(f"\n\n## Batch {i}\n\n{summary}\n")
        print(f"Batch summaries saved to {output_file}", file=sys.stderr)
        return
    
    # Second pass: synthesize into guide
    guide = generate_beatbook(stories, metadata, model, batch_summaries, args.topic)
    
    # Save final guide
    with open(args.output, 'w') as f:
        f.write(f"# Beat Book: {args.topic.title()}\n\n")
        f.write(guide)
    
    print(f"\n✓ Beat book saved to {args.output}", file=sys.stderr)
    print(f"  Analyzed {len(stories)} stories in {num_batches} batches", file=sys.stderr)
    print(f"  Date range: {metadata['date_range'][0]} to {metadata['date_range'][1]}", file=sys.stderr)

if __name__ == '__main__':
    main()