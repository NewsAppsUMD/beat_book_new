#!/usr/bin/env python3
"""Create a narrative chronological beat book from stories_entities_3.json using LLM."""

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import re
import subprocess


def parse_date(date_str):
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def get_topic(story):
    return story.get("llm_classification", {}).get("topic")


def normalize_text(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def first_sentence(text, max_chars=220):
    text = normalize_text(text)
    if not text:
        return ""
    match = re.split(r"(?<=[.!?])\s+", text)
    sentence = match[0] if match else text
    if len(sentence) > max_chars:
        sentence = sentence[: max_chars - 1].rstrip() + "…"
    return sentence


def story_blurb(story, max_chars=220):
    content = story.get("content", "")
    sentence = first_sentence(content, max_chars=max_chars)
    if sentence:
        return sentence
    return story.get("title", "Untitled")


def summarize_counter(items, limit):
    counter = Counter(items)
    return [name for name, _ in counter.most_common(limit)]


def call_llm(prompt, model):
    """Call LLM via CLI and return response."""
    try:
        result = subprocess.run(
            ["llm", "prompt", prompt, "-m", model],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"LLM error: {result.stderr}")
            return None
    except Exception as e:
        print(f"Failed to call LLM: {e}")
        return None


def build_introduction(stories, model):
    """Build an introduction section using LLM."""
    # Extract patterns from the entire dataset
    all_topics = [t for s in stories if (t := get_topic(s))]
    all_places = [p for s in stories for p in s.get("places", [])]
    all_orgs = [o for s in stories for o in s.get("organizations", [])]
    
    top_topics = summarize_counter(all_topics, 5)
    top_places = summarize_counter(all_places, 5)
    top_orgs = summarize_counter(all_orgs, 5)
    
    # Use LLM to generate introduction narrative
    context = f"""
You are writing an introduction to a public safety beat book. 
Here's what to cover:

Primary coverage areas: {', '.join(top_topics)}
Key locations: {', '.join(top_places)}
Main agencies: {', '.join(top_orgs)}

Write a compelling 2-3 paragraph introduction that explains what this beat covers, why it matters, 
and what a new reporter should expect when covering public safety in this area. 
Be conversational and specific to the Eastern Shore.

Do not include a heading—just the narrative text.
"""
    
    intro_text = call_llm(context, model)
    if intro_text:
        return f"## Introduction\n\n{intro_text}\n\n"
    else:
        # Fallback if LLM fails
        lines = []
        lines.append("## Introduction\n\n")
        lines.append("This beat book covers public safety across the Eastern Shore. ")
        if top_topics:
            lines.append(f"The primary focus areas are {', '.join(top_topics)}. ")
        lines.append("Coverage spans patrol operations, emergency response, crime reporting, ")
        lines.append("community safety initiatives, and law-enforcement accountability.\n\n")
        return "".join(lines)


def build_month_narrative(year, month, stories, story_limit):
    month_label = datetime(year, month, 1).strftime("%B %Y")
    places = summarize_counter([p for s in stories for p in s.get("places", [])], 3)

    stories_sorted = sorted(
        stories,
        key=lambda s: parse_date(s.get("date", "")) or datetime.max.date(),
    )
    examples = stories_sorted[:story_limit]

    lines = [f"## {month_label}\n\n"]

    if places:
        lines.append(f"**Locations**: {', '.join(places)}. ")

    if examples:
        if len(examples) == 1:
            story = examples[0]
            lines.append(
                f"**Key story**: \"{story.get('title', 'Untitled')}\" — "
                f"{story_blurb(story)}\n\n"
            )
        else:
            fragments = []
            for story in examples:
                fragments.append(
                    f"\"{story.get('title', 'Untitled')}\" ({story_blurb(story)})"
                )
            lines.append("**Stories**: " + "; ".join(fragments) + ".\n\n")
    else:
        lines.append("\n\n")

    return "".join(lines)


def build_year_narrative(year, stories, story_limit):
    places = summarize_counter([p for s in stories for p in s.get("places", [])], 3)

    stories_sorted = sorted(
        stories,
        key=lambda s: parse_date(s.get("date", "")) or datetime.max.date(),
    )
    examples = []
    if stories_sorted:
        examples.append(stories_sorted[0])
        if len(stories_sorted) > 2:
            examples.append(stories_sorted[len(stories_sorted) // 2])
        if len(stories_sorted) > 1:
            examples.append(stories_sorted[-1])
    examples = examples[:story_limit]

    lines = [f"# {year}\n\n"]
    
    if places:
        lines.append(f"**Recurring locations**: {', '.join(places)}. ")

    if examples:
        fragments = []
        for story in examples:
            fragments.append(
                f"\"{story.get('title', 'Untitled')}\" ({story_blurb(story)})"
            )
        lines.append("**Notable moments**: " + "; ".join(fragments) + ".\n\n")
    else:
        lines.append("\n\n")

    return "".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Create a narrative chronological beat book from stories_entities_3.json using LLM"
    )
    parser.add_argument(
        "--input",
        default="stories_entities_3.json",
        help="Input JSON file (default: stories_entities_3.json)",
    )
    parser.add_argument(
        "--output",
        default="beatbook_narrative_chronological_v3.md",
        help="Output markdown file (default: beatbook_narrative_chronological_v3.md)",
    )
    parser.add_argument(
        "--model",
        default="groq/meta-llama/llama-4-maverick-17b-128e-instruct",
        help="LLM model to use (default: groq/meta-llama/llama-4-maverick-17b-128e-instruct)",
    )
    parser.add_argument(
        "--story-limit",
        type=int,
        default=3,
        help="Max story examples per section (default: 3)",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {args.input}")

    with input_path.open("r", encoding="utf-8") as f:
        stories = json.load(f)

    stories.sort(key=lambda s: parse_date(s.get("date", "")) or datetime.max.date())

    by_year = defaultdict(list)
    by_month = defaultdict(list)
    for story in stories:
        date_obj = parse_date(story.get("date", ""))
        if not date_obj:
            continue
        by_year[date_obj.year].append(story)
        by_month[(date_obj.year, date_obj.month)].append(story)

    output = [
        "# Beat Book: Public Safety (Chronological Narrative)\n\n",
        "This beat book walks through coverage in time order so a new reporter can see how the stories evolve.\n\n",
        "---\n\n",
    ]
    
    # Add introduction section using LLM
    print(f"Generating introduction with {args.model}...")
    output.append(build_introduction(stories, args.model))
    output.append("---\n\n")

    for year in sorted(by_year.keys()):
        output.append(
            build_year_narrative(
                year,
                by_year[year],
                args.story_limit,
            )
        )

        months = sorted([m for m in by_month.keys() if m[0] == year])
        for _, month in months:
            output.append(
                build_month_narrative(
                    year,
                    month,
                    by_month[(year, month)],
                    args.story_limit,
                )
            )

    output_path = Path(args.output)
    output_path.write_text("".join(output), encoding="utf-8")
    print(f"Chronological narrative beat book saved to {output_path}")


if __name__ == "__main__":
    main()
