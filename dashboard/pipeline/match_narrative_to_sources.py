#!/usr/bin/env python3
"""
Match narrative sentences from index.html to source story sentences
using semantic similarity (cosine similarity of embeddings).

Inputs:
  - pipeline/narrative_sentences.json (from extract_html_narrative.py)
  - pipeline/source_stories_embeddings.json (from generate_story_embeddings.py)

Output:
  - source_links_mapping.json (project root, served to browser)

Each narrative sentence is embedded, compared against all source story sentences,
and the best match (above threshold) is recorded. Consecutive sentences matching
the same source are grouped so only the first gets a link.
"""

import json
import math
import sys
import urllib.request
import urllib.error
from pathlib import Path


def get_embedding(text: str, model: str = "embeddinggemma:latest") -> list:
    """
    Get an embedding for the given text using Ollama's embedding API.
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


def cosine_similarity(vec1: list, vec2: list) -> float:
    """
    Calculate cosine similarity between two vectors.
    """
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


def find_best_match(embedding: list, embeddings_data: list) -> dict:
    """
    Find the most similar sentence from the source stories.

    Args:
        embedding: The embedding vector to compare
        embeddings_data: List of articles with sentence embeddings

    Returns:
        Dict with match info including similarity score
    """
    best_match = {
        "article_id": None,
        "sentence_text": None,
        "sentence_index": None,
        "similarity": -1.0,
        "article_title": "",
        "article_date": "",
        "article_author": ""
    }

    for article in embeddings_data:
        article_id = article.get("article_id", "")

        for sentence_data in article.get("sentences", []):
            sent_embedding = sentence_data.get("embedding")
            if sent_embedding is None:
                continue

            similarity = cosine_similarity(embedding, sent_embedding)

            if similarity > best_match["similarity"]:
                best_match = {
                    "article_id": article_id,
                    "sentence_text": sentence_data.get("text", ""),
                    "sentence_index": sentence_data.get("index", 0),
                    "similarity": similarity,
                    "article_title": article.get("title", ""),
                    "article_date": article.get("date", ""),
                    "article_author": article.get("author", "")
                }

    return best_match


def find_best_article_match(embedding, embeddings_data):
    """
    Like find_best_match but returns the best similarity per article
    (not per sentence). Used for paragraph-level matching.
    """
    best = find_best_match(embedding, embeddings_data)
    return best


def compute_article_similarity(para_embedding, article, embeddings_data):
    """
    Compute the best sentence-level similarity between a paragraph embedding
    and a specific article's sentences.
    """
    best_sim = -1.0
    for article_data in embeddings_data:
        if article_data.get("article_id") != article:
            continue
        for sent_data in article_data.get("sentences", []):
            emb = sent_data.get("embedding")
            if emb is None:
                continue
            sim = cosine_similarity(para_embedding, emb)
            if sim > best_sim:
                best_sim = sim
        break
    return best_sim


def main():
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent

    narrative_file = script_dir / "narrative_sentences.json"
    embeddings_file = script_dir / "source_stories_embeddings.json"
    output_file = project_dir / "source_links_mapping.json"

    # Sentence must beat this on its own to even be considered
    SENTENCE_FLOOR = 0.55

    # Combined score threshold: (sentence_sim * 0.6 + paragraph_sim * 0.4)
    COMBINED_THRESHOLD = 0.62

    # Weights
    SENT_WEIGHT = 0.6
    PARA_WEIGHT = 0.4

    # Load narrative data
    print(f"Loading narrative data from: {narrative_file}")
    with open(narrative_file, "r", encoding="utf-8") as f:
        narrative_data = json.load(f)

    narrative_sentences = narrative_data["sentences"]
    paragraph_texts = narrative_data["paragraphs"]
    print(f"Loaded {len(narrative_sentences)} sentences from {len(paragraph_texts)} paragraphs")

    # Load source story embeddings
    print(f"Loading source embeddings from: {embeddings_file}")
    with open(embeddings_file, "r", encoding="utf-8") as f:
        embeddings_data = json.load(f)

    total_source_sents = sum(
        1 for article in embeddings_data
        for sent in article.get("sentences", [])
        if sent.get("embedding") is not None
    )
    print(f"Loaded {len(embeddings_data)} articles with {total_source_sents} embedded sentences")
    print()

    # Load story_data.json to check for CALENDAR articles
    story_data_file = project_dir / "story_data.json"
    with open(story_data_file, "r", encoding="utf-8") as f:
        story_data = json.load(f)
    skip_ids = set()
    education_ids = set()
    news_words = {'board', 'school', 'county', 'budget', 'test', 'scores', 'blueprint',
                  'education', 'superintendent', 'students', 'teachers', 'funding',
                  'state', 'commission', 'meeting', 'report', 'vote', 'election',
                  'audit', 'bill', 'law', 'grant', 'program', 'plan', 'rate',
                  'deficit', 'new', 'update', 'discuss', 'approve', 'announce'}
    for story in story_data:
        aid = story.get("article_id", "")
        title = story.get("title", "")

        # Skip CALENDAR articles
        if "CALENDAR" in title:
            skip_ids.add(aid)

        # Skip person profiles (short title, no news words)
        title_words = title.lower().split()
        if len(title_words) <= 4 and not any(w in news_words for w in title_words):
            skip_ids.add(aid)

        topic = story.get("llm_classification", {}).get("topic", "")
        if topic == "Education":
            education_ids.add(aid)

    print(f"Found {len(skip_ids)} non-news articles to skip (CALENDAR + person profiles)")
    print(f"Found {len(education_ids)} Education articles (only these will be linked)")

    # Step 1: Embed all paragraphs
    print(f"\n--- Embedding {len(paragraph_texts)} paragraphs ---")
    para_embeddings = {}
    for i, (pidx, text) in enumerate(paragraph_texts.items(), 1):
        preview = text[:50].replace('\n', ' ')
        sys.stdout.write(f"\r[{i}/{len(paragraph_texts)}] para: {preview}..." + " " * 20)
        sys.stdout.flush()
        try:
            para_embeddings[pidx] = get_embedding(text[:2000])  # truncate very long paragraphs
        except Exception as e:
            print(f"\nError embedding paragraph {pidx}: {e}")
            para_embeddings[pidx] = None

    # Step 2: Process each sentence
    print(f"\n\n--- Embedding {len(narrative_sentences)} sentences ---")
    results = []
    total = len(narrative_sentences)

    for idx, entry in enumerate(narrative_sentences, 1):
        sentence = entry["sentence"]
        para_idx = str(entry["paragraph_index"])
        preview = sentence[:50].replace('\n', ' ')
        sys.stdout.write(f"\r[{idx}/{total}] {preview}..." + " " * 20)
        sys.stdout.flush()

        try:
            sent_embedding = get_embedding(sentence)
            match = find_best_match(sent_embedding, embeddings_data)

            sent_sim = match["similarity"]
            article_id = match["article_id"]

            # Quick reject: sentence must beat the floor
            if sent_sim < SENTENCE_FLOOR or not article_id or article_id in skip_ids or article_id not in education_ids:
                results.append({
                    "full_sentence": sentence,
                    "article_id": None,
                    "sentence_similarity": round(sent_sim, 4),
                    "paragraph_similarity": 0.0,
                    "combined_score": 0.0,
                    "is_first_in_run": False,
                    "paragraph_index": entry["paragraph_index"],
                })
                continue

            # Compute paragraph similarity to the same article
            para_emb = para_embeddings.get(para_idx)
            if para_emb is not None:
                para_sim = compute_article_similarity(para_emb, article_id, embeddings_data)
            else:
                para_sim = 0.0

            combined = sent_sim * SENT_WEIGHT + para_sim * PARA_WEIGHT

            if combined >= COMBINED_THRESHOLD:
                results.append({
                    "full_sentence": sentence,
                    "article_id": article_id,
                    "sentence_similarity": round(sent_sim, 4),
                    "paragraph_similarity": round(para_sim, 4),
                    "combined_score": round(combined, 4),
                    "is_first_in_run": True,  # updated below
                    "paragraph_index": entry["paragraph_index"],
                })
            else:
                results.append({
                    "full_sentence": sentence,
                    "article_id": None,
                    "sentence_similarity": round(sent_sim, 4),
                    "paragraph_similarity": round(para_sim, 4),
                    "combined_score": round(combined, 4),
                    "is_first_in_run": False,
                    "paragraph_index": entry["paragraph_index"],
                })
        except Exception as e:
            print(f"\nError processing sentence: {e}")
            results.append({
                "full_sentence": sentence,
                "article_id": None,
                "sentence_similarity": 0.0,
                "paragraph_similarity": 0.0,
                "combined_score": 0.0,
                "is_first_in_run": False,
                "paragraph_index": entry["paragraph_index"],
            })

    print(f"\n\nProcessed {total} sentences")

    # Mark "first in run"
    previous_article_id = None
    for entry in results:
        if entry["article_id"] is None:
            previous_article_id = None
            continue
        if entry["article_id"] == previous_article_id:
            entry["is_first_in_run"] = False
        else:
            entry["is_first_in_run"] = True
        previous_article_id = entry["article_id"]

    # Filter to matched only
    matched = [r for r in results if r["article_id"] is not None]

    print(f"\nMatched {len(matched)} sentences (sentence floor >= {SENTENCE_FLOOR}, combined >= {COMBINED_THRESHOLD})")
    first_in_run = sum(1 for r in matched if r["is_first_in_run"])
    print(f"First-in-run links: {first_in_run}")

    # Show score distribution
    if matched:
        scores = sorted([r["combined_score"] for r in matched])
        print(f"Combined score range: {scores[0]:.3f} - {scores[-1]:.3f}")
        for t in [0.55, 0.60, 0.65, 0.70, 0.75]:
            c = sum(1 for s in scores if s >= t)
            print(f"  >= {t:.2f}: {c}")

    # Save results
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(matched, f, indent=2, ensure_ascii=False)

    print(f"\nOutput saved to: {output_file}")


if __name__ == "__main__":
    main()
