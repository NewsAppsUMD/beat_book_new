#!/usr/bin/env python3
"""
Extract narrative text from index.html for source-link matching.

Reads the HTML, extracts plain text from narrative containers
(.narrative-box p, .analysis-highlight, .issue-content > p,
 .county-tab-pane, .county-stat-panel p), splits into sentences,
and outputs pipeline/narrative_sentences.json.
"""

import json
import re
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("BeautifulSoup not found. Install with: pip install beautifulsoup4")
    raise SystemExit(1)


def split_into_sentences(text: str) -> list:
    """
    Split text into sentences using regex.
    Handles common abbreviations and edge cases.
    """
    if not text or not text.strip():
        return []

    text = re.sub(r'\s+', ' ', text).strip()

    abbreviations = [
        (r'\bMr\.', 'Mr<<DOT>>'),
        (r'\bMrs\.', 'Mrs<<DOT>>'),
        (r'\bMs\.', 'Ms<<DOT>>'),
        (r'\bDr\.', 'Dr<<DOT>>'),
        (r'\bProf\.', 'Prof<<DOT>>'),
        (r'\bSr\.', 'Sr<<DOT>>'),
        (r'\bJr\.', 'Jr<<DOT>>'),
        (r'\bvs\.', 'vs<<DOT>>'),
        (r'\betc\.', 'etc<<DOT>>'),
        (r'\bInc\.', 'Inc<<DOT>>'),
        (r'\bLtd\.', 'Ltd<<DOT>>'),
        (r'\bCo\.', 'Co<<DOT>>'),
        (r'\bCorp\.', 'Corp<<DOT>>'),
        (r'\bSt\.', 'St<<DOT>>'),
        (r'\bAve\.', 'Ave<<DOT>>'),
        (r'\bBlvd\.', 'Blvd<<DOT>>'),
        (r'\bRd\.', 'Rd<<DOT>>'),
        (r'\bPh\.D\.', 'Ph<<DOT>>D<<DOT>>'),
        (r'\bM\.D\.', 'M<<DOT>>D<<DOT>>'),
        (r'\bB\.A\.', 'B<<DOT>>A<<DOT>>'),
        (r'\bB\.S\.', 'B<<DOT>>S<<DOT>>'),
        (r'\bM\.A\.', 'M<<DOT>>A<<DOT>>'),
        (r'\bM\.S\.', 'M<<DOT>>S<<DOT>>'),
        (r'\bU\.S\.', 'U<<DOT>>S<<DOT>>'),
        (r'\bU\.K\.', 'U<<DOT>>K<<DOT>>'),
        (r'\bD\.C\.', 'D<<DOT>>C<<DOT>>'),
        (r'\ba\.m\.', 'a<<DOT>>m<<DOT>>'),
        (r'\bp\.m\.', 'p<<DOT>>m<<DOT>>'),
        (r'\bNo\.', 'No<<DOT>>'),
        (r'\bVol\.', 'Vol<<DOT>>'),
        (r'\bGen\.', 'Gen<<DOT>>'),
        (r'\bSgt\.', 'Sgt<<DOT>>'),
        (r'\bLt\.', 'Lt<<DOT>>'),
        (r'\bCapt\.', 'Capt<<DOT>>'),
        (r'\bCol\.', 'Col<<DOT>>'),
        (r'\bRev\.', 'Rev<<DOT>>'),
        (r'\bSen\.', 'Sen<<DOT>>'),
        (r'\bRep\.', 'Rep<<DOT>>'),
        (r'\bGov\.', 'Gov<<DOT>>'),
    ]

    protected_text = text
    for pattern, replacement in abbreviations:
        protected_text = re.sub(pattern, replacement, protected_text, flags=re.IGNORECASE)

    protected_text = re.sub(r'(\d)\.(\d)', r'\1<<DOT>>\2', protected_text)

    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z"\']|$)', protected_text)

    sentences = [s.replace('<<DOT>>', '.').strip() for s in sentences]
    sentences = [s for s in sentences if s and len(s) > 10]

    return sentences


def main():
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent

    html_file = project_dir / "index.html"
    output_file = script_dir / "narrative_sentences.json"

    print(f"Reading HTML from: {html_file}")

    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # Selectors for narrative containers that contain prose to match
    selectors = [
        ".narrative-box p",
        ".analysis-highlight",
        ".issue-content > p",
        ".county-tab-pane",
        ".county-stat-panel p",
    ]

    results = []
    paragraphs = {}
    paragraph_index = 0

    for selector in selectors:
        elements = soup.select(selector)
        for el in elements:
            text = el.get_text(separator=" ", strip=True)
            if not text or len(text) < 20:
                continue

            paragraphs[paragraph_index] = text
            sentences = split_into_sentences(text)
            for sentence in sentences:
                results.append({
                    "sentence": sentence,
                    "container_selector": selector,
                    "paragraph_index": paragraph_index,
                })
            paragraph_index += 1

    print(f"Extracted {len(results)} sentences from {paragraph_index} paragraphs")

    output = {
        "sentences": results,
        "paragraphs": paragraphs,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Output saved to: {output_file}")


if __name__ == "__main__":
    main()
