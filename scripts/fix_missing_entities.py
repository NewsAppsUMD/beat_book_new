#!/usr/bin/env python3
"""
Script to manually process the 48 stories that failed entity extraction.
Uses more robust JSON parsing and error handling.
"""

import json
import subprocess
import sys
import re
from pathlib import Path

INPUT_FILE = "stories_missing_entities.json"
OUTPUT_FILE = "stories_missing_entities_fixed.json"
LLM_MODEL = "groq/meta-llama/llama-4-maverick-17b-128e-instruct"

def extract_json_from_text(text):
    """
    More robust JSON extraction that handles various edge cases.
    """
    # Try to find JSON object boundaries more carefully
    # Look for the first { and the last } that creates valid JSON
    
    # Remove any leading/trailing whitespace
    text = text.strip()
    
    # Find all potential JSON objects
    start_positions = [i for i, char in enumerate(text) if char == '{']
    end_positions = [i for i, char in enumerate(text) if char == '}']
    
    if not start_positions or not end_positions:
        return None
    
    # Try different combinations, starting with the most likely (first { to last })
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

def call_llm(prompt, story_json):
    """Call LLM with improved error handling."""
    full_prompt = f"{prompt}\n\nStory to process:\n{json.dumps(story_json, indent=2)}"
    
    try:
        result = subprocess.run(
            ["uv", "run", "llm", "-m", LLM_MODEL],
            input=full_prompt.encode(),
            capture_output=True,
            check=True,
            timeout=120
        )
        
        response_text = result.stdout.decode()
        
        # Try robust JSON extraction
        parsed = extract_json_from_text(response_text)
        
        if parsed:
            return parsed
        else:
            print(f"❌ Could not extract valid JSON from response", file=sys.stderr)
            print(f"Response preview: {response_text[:500]}", file=sys.stderr)
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"❌ LLM call failed: {e.stderr.decode()}", file=sys.stderr)
        return None
    except subprocess.TimeoutExpired:
        print(f"❌ LLM call timed out (120s)", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return None

def main():
    if not Path(INPUT_FILE).exists():
        print(f"❌ Input file {INPUT_FILE} not found.", file=sys.stderr)
        sys.exit(1)
    
    # Load stories
    with open(INPUT_FILE, "r") as f:
        stories = json.load(f)
    
    print(f"📚 Loaded {len(stories)} stories to process\n")
    
    # Check if we have partial progress
    if Path(OUTPUT_FILE).exists():
        with open(OUTPUT_FILE, "r") as f:
            fixed_stories = json.load(f)
        print(f"📂 Found existing output with {len(fixed_stories)} processed stories")
        print(f"📍 Resuming from story {len(fixed_stories) + 1}\n")
    else:
        fixed_stories = []
    
    prompt = """
You are an expert news data annotator specializing in LOCAL GOVERNMENT stories. Analyze the story and return a JSON object with ALL the original story fields plus these NEW fields.

CRITICAL: ALL entities must be EXPLICITLY local government-related. This is a local government beat book.

NEW FIELDS TO ADD:
- content_type: single best from: ["News", "Calendars", "Obituaries", "Legal Notices", "Opinion", "Miscellaneous"]
- regions: array of general regions (Maryland, Virginia, D.C., or other country/state/region; 'U.S.' for national)
- municipalities: array of Maryland municipalities mentioned or central to story
- counties: array of Maryland counties where those municipalities are located. ALWAYS include "County" in the name (e.g., "Talbot County", "Caroline County", not just "Talbot" or "Caroline")
- key_people: array of ALL public officials, politicians, elected officials, city/town/county managers, council members, commissioners, planners, department heads, appointed officials, candidates for office, etc. Format MUST be: "Name — Title, Organization/Body" (use em dash —, not hyphen). Examples: "Tom Carroll — City Manager, City of Cambridge", "Theresa Stafford — Planning and Zoning Commissioner, Cambridge Planning and Zoning Commission". STANDARDIZE all names (consistent capitalization), titles, and organizations.
- key_events: array of LOCAL GOVERNMENT-RELATED events. ONLY include: named, recurring or significant government events. Examples: "Cambridge Planning and Zoning Commission Meeting", "City Council Public Hearing", "County Budget Hearing". DO NOT include: generic ceremonies or general community events unless they are official government meetings/hearings/events.
- key_initiatives: array of SPECIFIC NAMED local government initiatives/ordinances/resolutions/policies with proper names. Examples: "YMCA Institutional Overlay District", "Ordinance 799". DO NOT include: general concepts.
- key_establishments: array of LOCAL GOVERNMENT-RELATED establishments in Maryland. ONLY include: Maryland town/city halls, county offices, planning offices, public works facilities, government buildings, courthouses, municipal offices that are central to the story. Examples: "Cambridge City Hall", "Talbot County Council Chambers". DO NOT include: out-of-state buildings or private businesses.
- key_organizations: array of LOCAL GOVERNMENT-RELATED organizations AND government bodies. ONLY include: city councils, town councils, county councils, planning commissions, zoning boards, county/city/town government bodies, departments. Examples: "Cambridge City Council", "Cambridge Planning and Zoning Commission", "Dorchester County Council". Avoid duplicates.

RULES:
- Use title case when original is capitalized
- NEVER include 'Star-Democrat', 'Chesapeake Publishing Group', or 'Adams Publishing/APGMedia'
- Leave arrays empty [] if no local government-related items exist
- State legislature = 'Maryland General Assembly'
- When in doubt, EXCLUDE - only include if it's clearly local government-related
- For key_people, be INCLUSIVE - extract all public officials
- Return ONLY valid JSON with all original fields plus new fields
- DO NOT include any text before or after the JSON
- DO NOT include explanations or notes outside the JSON"""
    
    # Process remaining stories
    start_idx = len(fixed_stories)
    for i, story in enumerate(stories[start_idx:], start=start_idx + 1):
        print(f"\n{'='*80}")
        print(f"Processing {i}/{len(stories)}: {story.get('title', 'NO TITLE')[:60]}")
        print(f"Date: {story.get('date', 'NO DATE')}")
        print(f"{'='*80}")
        
        result = call_llm(prompt, story)
        
        if result:
            # Verify the result has the new fields
            new_fields = ['content_type', 'regions', 'municipalities', 'counties', 
                         'key_people', 'key_events', 'key_establishments', 
                         'key_organizations', 'key_initiatives']
            
            missing_fields = [f for f in new_fields if f not in result]
            
            if missing_fields:
                print(f"⚠️  Result missing fields: {missing_fields}")
                print(f"⚠️  Keeping original story without new fields")
                fixed_stories.append(story)
            else:
                print(f"✅ Success! Added new fields:")
                print(f"   - People: {len(result.get('key_people', []))}")
                print(f"   - Events: {len(result.get('key_events', []))}")
                print(f"   - Establishments: {len(result.get('key_establishments', []))}")
                print(f"   - Organizations: {len(result.get('key_organizations', []))}")
                print(f"   - Initiatives: {len(result.get('key_initiatives', []))}")
                fixed_stories.append(result)
        else:
            print(f"❌ Failed - keeping original story")
            fixed_stories.append(story)
        
        # Save progress after each story
        with open(OUTPUT_FILE, "w") as f:
            json.dump(fixed_stories, f, indent=2)
        print(f"💾 Progress saved ({len(fixed_stories)}/{len(stories)})")
    
    print(f"\n{'='*80}")
    print(f"✨ COMPLETE!")
    print(f"{'='*80}")
    print(f"Processed: {len(fixed_stories)} stories")
    print(f"Output: {OUTPUT_FILE}")
    
    # Count successful extractions
    successful = sum(1 for s in fixed_stories if 'key_people' in s)
    print(f"Successful entity extractions: {successful}/{len(stories)}")
    print(f"Failed: {len(stories) - successful}")

if __name__ == "__main__":
    main()
