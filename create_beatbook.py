#!/usr/bin/env python3
"""Create a strictly chronological beat book from stories_entities_3.json."""

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


def parse_date(date_str):
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def format_list(items, limit):
    if not items:
        return "None"
    return ", ".join(items[:limit])


def summarize_counter(items, limit):
    counter = Counter(items)
    return [name for name, _ in counter.most_common(limit)]


def format_story_entry(story, list_limit):
    date_obj = parse_date(story.get("date", ""))
    date_label = date_obj.isoformat() if date_obj else "Unknown date"
    title = story.get("title", "Untitled")
    topic = story.get("llm_classification", {}).get("topic")

    places = summarize_counter(story.get("places", []), list_limit)
    organizations = summarize_counter(story.get("organizations", []), list_limit)
    people = summarize_counter(story.get("people", []), list_limit)

    lines = [f"- {date_label} — {title}\n"]
    if topic:
        lines.append(f"  - Topic: {topic}\n")
    if places:
        lines.append(f"  - Places: {format_list(places, list_limit)}\n")
    if organizations:
        lines.append(f"  - Organizations: {format_list(organizations, list_limit)}\n")
    if people:
        lines.append(f"  - People: {format_list(people, list_limit)}\n")
    return "".join(lines)


def build_chronological_sections(stories, list_limit):
    by_month = defaultdict(list)

    for story in stories:
        date_obj = parse_date(story.get("date", ""))
        if not date_obj:
            key = (9999, 12)
        else:
            key = (date_obj.year, date_obj.month)
        by_month[key].append(story)

    sections = []
    for (year, month) in sorted(by_month.keys()):
        month_stories = sorted(
            by_month[(year, month)],
            key=lambda s: parse_date(s.get("date", "")) or datetime.max.date(),
        )
        if year == 9999:
            month_label = "Unknown dates"
        else:
            month_label = datetime(year, month, 1).strftime("%B %Y")
        sections.append(f"## {month_label}\n\n")
        for story in month_stories:
            sections.append(format_story_entry(story, list_limit))
        sections.append("\n")

    return "".join(sections)


def main():
    parser = argparse.ArgumentParser(
        description="Create a strictly chronological beat book from stories_entities_3.json"
    )
    parser.add_argument(
        "--input",
        default="stories_entities_3.json",
        help="Input JSON file (default: stories_entities_3.json)",
    )
    parser.add_argument(
        "--output",
        default="beatbook_chronological.md",
        help="Output markdown file (default: beatbook_chronological.md)",
    )
    parser.add_argument(
        "--list-limit",
        type=int,
        default=3,
        help="Max items per metadata list (default: 3)",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {args.input}")

    with input_path.open("r", encoding="utf-8") as f:
        stories = json.load(f)

    stories.sort(key=lambda s: parse_date(s.get("date", "")) or datetime.max.date())

    date_values = [parse_date(s.get("date", "")) for s in stories if s.get("date")]
    date_range = (min(date_values).isoformat(), max(date_values).isoformat()) if date_values else ("Unknown", "Unknown")

    output = [
        "# Beat Book: Public Safety (Chronological)\n\n",
        f"Stories: {len(stories)}\n\n",
        f"Date range: {date_range[0]} to {date_range[1]}\n\n",
        "## Timeline\n\n",
        build_chronological_sections(stories, args.list_limit),
    ]

    output_path = Path(args.output)
    if output_path.exists():
        stem = output_path.stem
        suffix = output_path.suffix or ".md"
        version = 2
        while True:
            candidate = output_path.with_name(f"{stem}_v{version}{suffix}")
            if not candidate.exists():
                output_path = candidate
                break
            version += 1

    output_path.write_text("".join(output), encoding="utf-8")
    print(f"Chronological beat book saved to {output_path}")


if __name__ == "__main__":
    main()
