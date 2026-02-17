#!/usr/bin/env python3
"""
Generate a thematic narrative beat book from stories_entities_3.json.
Uses LLM to synthesize story summaries and entities into a free-form narrative,
organized by themes and patterns rather than geography.
"""

import argparse
import json
import subprocess
from pathlib import Path
from collections import Counter
from datetime import datetime


def parse_date(date_str):
    """Parse various date formats."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def extract_themes(stories):
    """Extract key themes, entities, and patterns from stories."""
    topics = Counter()
    people = Counter()
    orgs = Counter()
    all_summaries = []
    date_range = []
    
    for story in stories:
        # Extract topic
        topic = story.get("llm_classification", {}).get("topic")
        if topic:
            topics[topic] += 1
        
        # Extract people, orgs
        for person in story.get("people", []):
            people[person] += 1
        for org in story.get("organizations", []):
            orgs[org] += 1
        
        # Collect summaries for content analysis
        summary = story.get("content", "")
        if summary:
            all_summaries.append({
                "title": story.get("title", "Untitled"),
                "summary": summary,
                "date": story.get("date", ""),
                "people": story.get("people", []),
                "orgs": story.get("organizations", []),
            })
        
        # Track date range
        date_obj = parse_date(story.get("date", ""))
        if date_obj:
            date_range.append(date_obj)
    
    return {
        "topics": topics.most_common(10),
        "key_people": people.most_common(15),
        "key_orgs": orgs.most_common(10),
        "summaries": all_summaries,
        "date_range": (min(date_range), max(date_range)) if date_range else (None, None),
        "total_stories": len(stories),
    }


def call_llm(prompt, model):
    """Call LLM via CLI and return response."""
    try:
        result = subprocess.run(
            ["llm", "prompt", prompt, "-m", model],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"LLM error: {result.stderr}")
            return None
    except Exception as e:
        print(f"Failed to call LLM: {e}")
        return None


def generate_narrative_section(section_title, summaries, key_patterns, model):
    """Generate a narrative section for a group of stories."""
    summaries_text = "\n\n".join([
        f"**{s['title']}** ({s['date']}): {s['summary']}"
        for s in summaries[:10]  # Limit to avoid token limits
    ])
    
    prompt = f"""You are writing a thematic analysis of public safety news coverage. 

Write a compelling 2-3 paragraph narrative about "{section_title}" based on these news stories.

KEY PATTERNS IN THIS THEME:
{key_patterns}

STORY SUMMARIES:
{summaries_text}

Create a flowing narrative that:
- Identifies the key issues and tensions within this theme
- References actual stories and specific details from the summaries
- Shows what patterns emerge and why they matter
- Connects individual stories into a larger pattern
- Explains why a reporter should care about this theme

Do not use bullet points. Write in natural prose. Be specific and grounded in the stories provided."""
    
    return call_llm(prompt, model)


def generate_beatbook(input_file, output_file, model):
    """Generate the complete thematic narrative beatbook."""
    input_path = Path(input_file)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_file}")
    
    with input_path.open("r", encoding="utf-8") as f:
        stories = json.load(f)
    
    print(f"Loaded {len(stories)} stories from {input_file}")
    
    # Extract themes and metadata
    themes = extract_themes(stories)
    
    print(f"Identified themes: {[t[0] for t in themes['topics']]}")
    print(f"Key people: {[p[0] for p in themes['key_people'][:5]]}")
    print(f"Key organizations: {[o[0] for o in themes['key_orgs']]}")
    
    # Build narrative sections for each theme
    output_sections = [
        "# Beat Book: Public Safety (Thematic Narrative)\n\n",
        "This beat book synthesizes coverage patterns without geographic focus, "
        "looking instead at themes, issues, and stories that define the beat.\n\n",
        "---\n\n",
    ]
    
    # Generate introduction using LLM
    print("\nGenerating introduction...")
    intro_prompt = f"""Write a compelling introduction to a public safety beat book based on {themes['total_stories']} news stories.

KEY THEMES: {', '.join([t[0] for t in themes['topics']])}
KEY PEOPLE: {', '.join([p[0] for p in themes['key_people'][:10]])}
KEY ORGANIZATIONS: {', '.join([o[0] for o in themes['key_orgs']])}
DATE RANGE: {themes['date_range'][0]} to {themes['date_range'][1]}

This introduction should explain what public safety reporting looks like in this community—what issues recur, 
who the key players are, and what patterns a new reporter should watch for.

Write 2-3 paragraphs of compelling, specific prose. Reference the themes and key players identified above.
Do not include a heading."""
    
    intro = call_llm(intro_prompt, model)
    if intro:
        output_sections.append(f"## Introduction\n\n{intro}\n\n")
    
    output_sections.append("---\n\n")
    
    # Generate narrative for each theme
    for theme_name, theme_count in themes["topics"]:
        if theme_count < 2:
            continue
        
        print(f"\nGenerating narrative for theme: {theme_name}")
        
        # Filter stories for this theme
        themed_stories = [
            s for s in themes["summaries"]
            if any(s["summary"] and theme_name.lower() in s["summary"].lower() for _ in [1])
            or any(theme_name.lower() in s.get("title", "").lower() for _ in [1])
        ]
        
        if not themed_stories:
            # If no exact match, just use sample
            themed_stories = themes["summaries"][:min(5, len(themes["summaries"]))]
        
        # Create key patterns text
        key_patterns = f"This theme appears in {theme_count} stories. "
        if themed_stories:
            people_in_theme = Counter()
            for story in themed_stories:
                people_in_theme.update(story.get("people", []))
            if people_in_theme:
                top_people = [p[0] for p in people_in_theme.most_common(3)]
                key_patterns += f"Key figures: {', '.join(top_people)}. "
        
        # Generate narrative
        narrative = generate_narrative_section(theme_name, themed_stories, key_patterns, model)
        if narrative:
            output_sections.append(f"## {theme_name}\n\n{narrative}\n\n")
    
    # Generate synthesis/conclusion
    print("\nGenerating synthesis...")
    synthesis_prompt = f"""Write a compelling concluding section that ties together the themes in this public safety beat book.

THEMES COVERED: {', '.join([t[0] for t in themes['topics']])}
TIME PERIOD: {themes['date_range'][0]} to {themes['date_range'][1]}
TOTAL STORIES ANALYZED: {themes['total_stories']}

The conclusion should:
- Identify the connective tissue between themes (What do these patterns reveal?)
- Suggest implications for ongoing coverage (What should a reporter keep watching?)
- Acknowledge complexity and ongoing tensions
- Be forward-looking without being predictive

Write 2-3 paragraphs of reflective prose. Do not include a heading."""
    
    synthesis = call_llm(synthesis_prompt, model)
    if synthesis:
        output_sections.append("## Themes and Implications\n\n")
        output_sections.append(synthesis)
        output_sections.append("\n\n")
    
    # Write output
    output_path = Path(output_file)
    output_path.write_text("".join(output_sections), encoding="utf-8")
    print(f"\nThematic narrative beat book saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a thematic narrative beat book from stories_entities_3.json"
    )
    parser.add_argument(
        "--input",
        default="stories_entities_3.json",
        help="Input JSON file (default: stories_entities_3.json)",
    )
    parser.add_argument(
        "--output",
        default="beatbook_thematic_narrative.md",
        help="Output markdown file (default: beatbook_thematic_narrative.md)",
    )
    parser.add_argument(
        "--model",
        default="groq/meta-llama/llama-4-maverick-17b-128e-instruct",
        help="LLM model to use (default: groq/meta-llama/llama-4-maverick-17b-128e-instruct)",
    )
    
    args = parser.parse_args()
    generate_beatbook(args.input, args.output, args.model)


if __name__ == "__main__":
    main()
