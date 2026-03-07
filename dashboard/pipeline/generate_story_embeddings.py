#!/usr/bin/env python3
"""
Generate embeddings for source stories at the SENTENCE level using Ollama's embeddinggemma model.

This script reads story_data.json, splits each story's 'content' into sentences,
generates an embedding for each sentence, and saves the results to
source_stories_embeddings.json with a structure that groups sentences by article.
"""

import json
import urllib.request
import urllib.error
import re
import sys
from pathlib import Path


def get_embedding(text: str, model: str = "embeddinggemma:latest") -> list:
    """
    Get an embedding for the given text using Ollama's embedding API.

    Args:
        text: The text to embed
        model: The Ollama model to use for embeddings

    Returns:
        A list of floats representing the embedding vector
    """
    url = "http://localhost:11434/api/embed"
    data = json.dumps({
        "model": model,
        "input": text
    }).encode('utf-8')

    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'}
    )

    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))

    return result["embeddings"][0]


def split_into_sentences(text: str) -> list:
    """
    Split text into sentences using regex.
    Handles common abbreviations and edge cases.

    Args:
        text: The text to split

    Returns:
        List of sentence strings
    """
    if not text or not text.strip():
        return []

    # Clean up the text - replace multiple newlines/spaces with single space
    text = re.sub(r'\s+', ' ', text).strip()

    # Pattern to split on sentence boundaries
    # Matches periods, question marks, exclamation marks followed by space
    # Handles common abbreviations like Mr., Mrs., Dr., etc.
    # Also handles abbreviations like U.S., Ph.D., etc.

    # First, protect common abbreviations
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

    # Also protect decimal numbers (e.g., 3.5, $10.99)
    protected_text = re.sub(r'(\d)\.(\d)', r'\1<<DOT>>\2', protected_text)

    # Split on sentence-ending punctuation followed by space and capital letter or end
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z"\']|$)', protected_text)

    # Restore the protected periods
    sentences = [s.replace('<<DOT>>', '.').strip() for s in sentences]

    # Filter out empty sentences and very short ones (likely noise)
    sentences = [s for s in sentences if s and len(s) > 10]

    return sentences


def main():
    # Define file paths
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent

    input_file = project_dir / "story_data.json"
    output_file = script_dir / "source_stories_embeddings.json"

    print(f"Reading stories from: {input_file}")

    # Load source stories
    with open(input_file, "r", encoding="utf-8") as f:
        stories = json.load(f)

    print(f"Loaded {len(stories)} stories")
    print("Splitting content into sentences and generating embeddings...")
    print()

    # Process each story
    granular_data = []
    total_sentences = 0
    processed_sentences = 0

    # First pass: count total sentences
    for story in stories:
        content = story.get("content", "")
        sentences = split_into_sentences(content)
        total_sentences += len(sentences)

    print(f"Total sentences to process: {total_sentences}")
    print()

    # Second pass: generate embeddings
    for story_idx, story in enumerate(stories, 1):
        content = story.get("content", "")
        sentences = split_into_sentences(content)

        article_entry = {
            "article_id": story.get("article_id", ""),
            "title": story.get("title", ""),
            "date": story.get("date", ""),
            "author": story.get("author", ""),
            "sentences": []
        }

        for sent_idx, sentence in enumerate(sentences):
            processed_sentences += 1

            # Show progress
            preview = sentence[:40].replace('\n', ' ')
            progress = f"[{processed_sentences}/{total_sentences}]"
            sys.stdout.write(f"\r{progress} Article {story_idx}/{len(stories)}: {preview}..." + " " * 20)
            sys.stdout.flush()

            try:
                embedding = get_embedding(sentence)
                article_entry["sentences"].append({
                    "text": sentence,
                    "embedding": embedding,
                    "index": sent_idx
                })
            except Exception as e:
                print(f"\nError generating embedding: {e}")
                article_entry["sentences"].append({
                    "text": sentence,
                    "embedding": None,
                    "index": sent_idx
                })

        granular_data.append(article_entry)

    print(f"\n\nSaving embeddings to: {output_file}")

    # Save the results
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(granular_data, f, indent=2, ensure_ascii=False)

    # Count successful embeddings
    successful = sum(
        1 for article in granular_data
        for sent in article.get("sentences", [])
        if sent.get("embedding") is not None
    )

    print(f"\nDone!")
    print(f"Processed {len(stories)} articles")
    print(f"Generated {successful}/{total_sentences} sentence embeddings")
    print(f"Output saved to: {output_file}")


if __name__ == "__main__":
    main()
