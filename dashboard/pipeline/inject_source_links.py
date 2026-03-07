#!/usr/bin/env python3
"""
Inject source links directly into index.html.

Reads source_links_mapping.json and wraps matching text in index.html
with <span class="sourced-content" data-article-id="..."> tags.

Uses direct string replacement on the raw HTML (not BS4 DOM walking)
so that sentences spanning across inline tags like <strong> are matched
correctly.
"""

import json
import re
import html as html_module
from pathlib import Path


def escape_for_regex(text):
    """Escape text for use in a regex pattern."""
    return re.escape(text)


def build_flexible_pattern(sentence):
    """
    Build a regex that matches the sentence text even if it's interrupted
    by inline HTML tags like <strong>, <em>, <br>, etc.

    For each character in the sentence, allow optional HTML tags between chars.
    To keep it fast, we only insert the optional tag pattern at word boundaries
    and around punctuation.
    """
    # Split sentence into words
    words = sentence.split()
    if not words:
        return None

    # Between each word, allow optional HTML tags and whitespace
    tag_pattern = r'(?:<[^>]+>|\s)*'

    escaped_words = []
    for word in words:
        # Escape the word for regex, but allow tags inside the word
        # at positions where tags commonly appear (around <strong>, etc.)
        escaped_words.append(re.escape(word))

    # Join words with flexible whitespace/tag pattern
    pattern = tag_pattern.join(escaped_words)

    return pattern


def main():
    project_dir = Path(__file__).parent.parent
    html_file = project_dir / "index.html"
    mapping_file = project_dir / "source_links_mapping.json"

    print(f"Reading mapping from: {mapping_file}")
    with open(mapping_file, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    # Only apply first-in-run links
    links = [m for m in mapping if m.get("is_first_in_run")]
    print(f"Links to inject: {len(links)}")

    print(f"Reading HTML from: {html_file}")
    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()

    # First, strip any existing sourced-content spans (idempotent re-runs)
    # Replace <span class="sourced-content" data-article-id="...">...</span> with just the inner content
    html_content = re.sub(
        r'<span class="sourced-content" data-article-id="[^"]*">([^<]*(?:<(?!/span>)[^<]*)*)</span>',
        r'\1',
        html_content
    )
    print("Stripped existing source links")

    applied = 0
    for link_info in links:
        full_sentence = link_info["full_sentence"]
        article_id = link_info["article_id"]
        if not full_sentence or len(full_sentence) < 10:
            continue

        pattern = build_flexible_pattern(full_sentence)
        if not pattern:
            continue

        # Find the match in the HTML
        match = re.search(pattern, html_content)
        if not match:
            continue

        matched_text = match.group(0)

        # Don't wrap if already inside a sourced-content span
        if 'sourced-content' in matched_text:
            continue

        # Build the replacement
        replacement = f'<span class="sourced-content" data-article-id="{article_id}">{matched_text}</span>'

        # Replace only the first occurrence
        html_content = html_content[:match.start()] + replacement + html_content[match.end():]
        applied += 1

    print(f"Injected {applied} source links into HTML")

    # Write back
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Updated: {html_file}")


if __name__ == "__main__":
    main()
