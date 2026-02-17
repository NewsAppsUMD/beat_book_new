#!/usr/bin/env python3
"""Create a chronological beat book from stories_entities_3.json."""

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import re


def parse_date(date_str):
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def normalize_author(author):
    if not author:
        return []
    # Remove emails and trim whitespace
    cleaned = re.sub(r"\b\S+@\S+\b", "", author).strip()
    # Split on common separators
    parts = re.split(r";| and |,", cleaned)
    return [p.strip() for p in parts if p.strip()]


def get_topic(story):
    return story.get("llm_classification", {}).get("topic")


def summarize_counter(counter, top_n):
    return counter.most_common(top_n)


def render_list(items, label):
    if not items:
        return f"- {label}: None\n"
    formatted = ", ".join(f"{name} ({count})" for name, count in items)
    return f"- {label}: {formatted}\n"


def build_chronology(stories, top_n):
    by_month = defaultdict(list)
    by_year = defaultdict(list)

    for story in stories:
        date_obj = parse_date(story.get("date", ""))
        if not date_obj:
            continue
        key_month = (date_obj.year, date_obj.month)
        by_month[key_month].append(story)
        by_year[date_obj.year].append(story)

    sections = []
    for (year, month) in sorted(by_month.keys()):
        month_stories = by_month[(year, month)]
        topics = Counter(filter(None, (get_topic(s) for s in month_stories)))
        places = Counter(p for s in month_stories for p in s.get("places", []))
        orgs = Counter(o for s in month_stories for o in s.get("organizations", []))
        people = Counter(p for s in month_stories for p in s.get("people", []))
        authors = Counter(a for s in month_stories for a in normalize_author(s.get("author", "")))

        month_label = datetime(year, month, 1).strftime("%B %Y")
        section = [f"## {month_label}\n"]
        section.append(render_list(summarize_counter(topics, top_n), "Top topics"))
        section.append(render_list(summarize_counter(places, top_n), "Top places"))
        section.append(render_list(summarize_counter(orgs, top_n), "Top organizations"))
        section.append(render_list(summarize_counter(people, top_n), "Top people"))
        section.append(render_list(summarize_counter(authors, top_n), "Top bylines"))

        # Highlight a few story titles to show coverage flavor
        sample_titles = [s.get("title", "Untitled") for s in month_stories[:3]]
        if sample_titles:
            section.append("- Sample stories:\n")
            for title in sample_titles:
                section.append(f"  - {title}\n")

        sections.append("".join(section))

    return "\n".join(sections), by_year


def build_location_trends(by_year, top_n):
    lines = ["## Location Focus Over Time\n"]
    for year in sorted(by_year.keys()):
        places = Counter(p for s in by_year[year] for p in s.get("places", []))
        lines.append(f"- {year}: ")
        top_places = summarize_counter(places, top_n)
        if top_places:
            lines.append(", ".join(f"{name} ({count})" for name, count in top_places))
        else:
            lines.append("None")
        lines.append("\n")
    return "".join(lines)


def build_newsroom_trends(by_year, top_n):
    lines = ["## Newsroom and Bylines Over Time\n"]
    prev_authors = set()
    for year in sorted(by_year.keys()):
        authors = Counter(a for s in by_year[year] for a in normalize_author(s.get("author", "")))
        top_authors = summarize_counter(authors, top_n)
        current_authors = set(a for a, _ in authors.most_common())
        new_authors = sorted(current_authors - prev_authors)
        lines.append(f"- {year}: ")
        if top_authors:
            lines.append(", ".join(f"{name} ({count})" for name, count in top_authors))
        else:
            lines.append("None")
        if new_authors:
            lines.append(f" | New bylines: {', '.join(new_authors[:top_n])}")
        lines.append("\n")
        prev_authors = current_authors
    return "".join(lines)


def build_topic_trends(by_year, top_n):
    lines = ["## Topic Trends Over Time\n"]
    for year in sorted(by_year.keys()):
        topics = Counter(filter(None, (get_topic(s) for s in by_year[year])))
        top_topics = summarize_counter(topics, top_n)
        lines.append(f"- {year}: ")
        if top_topics:
            lines.append(", ".join(f"{name} ({count})" for name, count in top_topics))
        else:
            lines.append("None")
        lines.append("\n")
    return "".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Create a chronological beat book from stories_entities_3.json"
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
        "--top-n",
        type=int,
        default=5,
        help="How many top items to show per section (default: 5)",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {args.input}")

    with input_path.open("r", encoding="utf-8") as f:
        stories = json.load(f)

    # Sort stories by date for chronological context
    stories.sort(key=lambda s: parse_date(s.get("date", "")) or datetime.min.date())

    chronology, by_year = build_chronology(stories, args.top_n)
    topic_trends = build_topic_trends(by_year, args.top_n)
    location_trends = build_location_trends(by_year, args.top_n)
    newsroom_trends = build_newsroom_trends(by_year, args.top_n)

    output = [
        "# Beat Book (Chronological)\n\n",
        "This beat book summarizes coverage over time based on story metadata.\n\n",
        topic_trends,
        "\n",
        location_trends,
        "\n",
        newsroom_trends,
        "\n",
        "# Monthly Coverage Timeline\n\n",
        chronology,
    ]

    output_path = Path(args.output)
    output_path.write_text("".join(output), encoding="utf-8")

    print(f"Beat book saved to {output_path}")


if __name__ == "__main__":
    main()
