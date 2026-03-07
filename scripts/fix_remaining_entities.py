#!/usr/bin/env python3
"""
Script to extract entities for the 4 remaining stories without entity fields.
Uses llm CLI tool with Groq.
"""

import json
import subprocess
import sys
from pathlib import Path

LLM_MODEL = "groq/meta-llama/llama-4-maverick-17b-128e-instruct"

def load_json(filepath):
    """Load JSON file and return data."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath, data):
    """Save data to JSON file with proper formatting."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def extract_json_from_text(text):
    """Extract JSON from LLM response."""
    text = text.strip()
    
    # Find all potential JSON objects
    start_positions = [i for i, char in enumerate(text) if char == '{']
    end_positions = [i for i, char in enumerate(text) if char == '}']
    
    if not start_positions or not end_positions:
        return None
    
    # Try different combinations
    for start in start_positions:
        for end in reversed(end_positions):
            if end > start:
                try:
                    json_str = text[start:end+1]
                    parsed = json.loads(json_str)
                    return parsed
                except json.JSONDecodeError:
                    continue
    
    return None

def call_llm(story):
    """Call LLM to extract entities."""
    
    prompt = f"""Extract entity information from this news article about local government.

Article Title: {story.get('title', 'Unknown')}
Date: {story.get('date', 'Unknown')}
Content: {story.get('content', '')[:3000]}

Extract the following entities and return ONLY a JSON object with these fields:
- content_type: "News", "Opinion", "Legal Notices", or "Public Notices"
- regions: Array of regions mentioned (e.g., ["Maryland", "Delaware"])
- municipalities: Array of cities/towns (e.g., ["Easton", "Cambridge"])
- counties: Array of counties with "County" in name (e.g., ["Talbot County", "Dorchester County"])
- key_people: Array of people with format "Name — Role, Organization" (e.g., ["John Smith — Mayor, Town of Easton"])
- key_events: Array of significant government events (e.g., ["Town Council Meeting"])
- key_initiatives: Array of programs/ordinances (e.g., ["Comprehensive Plan Update"])
- key_establishments: Array of government buildings (e.g., ["Town Hall"])
- key_organizations: Array of government organizations (e.g., ["Town Council"])

Use empty arrays [] for fields with no relevant data. Return ONLY valid JSON, no explanations."""

    try:
        result = subprocess.run(
            ["uv", "run", "llm", "-m", LLM_MODEL],
            input=prompt.encode(),
            capture_output=True,
            check=True,
            timeout=120
        )
        
        response_text = result.stdout.decode()
        parsed = extract_json_from_text(response_text)
        
        if parsed:
            return parsed
        else:
            print(f"  ❌ Could not extract valid JSON")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"  ❌ LLM call failed: {e.stderr.decode()}")
        return None
    except subprocess.TimeoutExpired:
        print(f"  ❌ LLM call timed out")
        return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

def process_remaining_stories():
    """Find and process stories without entity fields."""
    
    # Load merged file
    merged_file = 'local_government_stories_with_entities_v2_cleaned_merged.json'
    print(f"Loading {merged_file}...")
    stories = load_json(merged_file)
    
    entity_fields = ['content_type', 'regions', 'municipalities', 'counties', 
                     'key_people', 'key_events', 'key_initiatives', 
                     'key_establishments', 'key_organizations']
    
    # Find stories missing all entity fields
    missing_entities = []
    for i, story in enumerate(stories):
        missing = [field for field in entity_fields if field not in story]
        if len(missing) == len(entity_fields):
            missing_entities.append((i, story))
    
    print(f"\nFound {len(missing_entities)} stories missing entity fields\n")
    
    if not missing_entities:
        print("All stories have entity fields!")
        return
    
    # Process each story
    for idx, (story_idx, story) in enumerate(missing_entities):
        print(f"[{idx+1}/{len(missing_entities)}] Processing: {story.get('title', 'Unknown')[:60]}...")
        
        entities = call_llm(story)
        
        if entities:
            # Verify all required fields are present
            missing = [f for f in entity_fields if f not in entities]
            if missing:
                print(f"  ⚠️  Missing fields: {missing}")
                # Add empty arrays for missing fields
                for field in missing:
                    entities[field] = []
            
            # Add entities to story
            for field in entity_fields:
                stories[story_idx][field] = entities.get(field, [])
            print(f"  ✅ Success!")
        else:
            print(f"  ❌ Failed - adding empty entity fields")
            # Add empty entity fields so the story isn't left incomplete
            for field in entity_fields:
                stories[story_idx][field] = []
    
    # Save updated file
    output_file = 'local_government_stories_with_entities_v2_cleaned_final.json'
    print(f"\nSaving updated stories to {output_file}...")
    save_json(output_file, stories)
    
    print(f"\n✨ Complete!")
    print(f"Processed: {len(missing_entities)} stories")
    print(f"Total stories in output: {len(stories)}")
    print(f"Output file: {output_file}")

if __name__ == '__main__':
    process_remaining_stories()
