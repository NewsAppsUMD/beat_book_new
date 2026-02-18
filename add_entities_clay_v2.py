import json
import subprocess
import time
import argparse
import sys
from pathlib import Path
from datetime import datetime
import re
import random

def derive_season(date_str):
    """Derive season from date string (YYYY-MM-DD format)."""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        month = date_obj.month
        
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:  # 9, 10, 11
            return "fall"
    except:
        return None

def is_weekend(date_str):
    """Determine if date falls on weekend (Saturday=5, Sunday=6)."""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.weekday() in [5, 6]
    except:
        return None

def extract_entities(story_title, story_content, model):
    """Use LLM to extract named entities and comprehensive metadata from public safety news stories."""
    
    prompt = f"""
Extract ALL named entities and detailed metadata from PUBLIC SAFETY news stories and return them in JSON format.

CONTEXT: This story is from the Public Safety beat covering law enforcement, fire departments, emergency services, courts, crime, accidents, and public safety-related news.

Extract the following entities and metadata:

**NAMED ENTITIES:**

- people: Array of IMPORTANT people mentioned in the story. Include their name and title/role/description when available:
  * Law enforcement officers: Include rank and agency (e.g., "Chief John Smith, Easton Police Department")
  * Fire and EMS personnel: Include rank and department
  * Court officials: Include role and jurisdiction
  * Suspects/defendants: Include name and any details stated (e.g., "James Wilson, 35, of Easton")
  * Victims: Include if named
  * Public officials: Include title and organization
  Format: "First Last, Title/Role" or "First Last, age, description" as appropriate

- places: Array of geographic locations mentioned within Maryland Eastern Shore:
  * Cities/Towns: Include state (e.g., "Easton, Maryland")
  * Counties: Use format "Talbot County, Maryland"
  * Specific locations: Roads, buildings, facilities (e.g., "Route 50", "Easton Police Department")

- organizations: Array of RELEVANT organizations, institutions, and agencies mentioned:
  * Law enforcement agencies (e.g., "Easton Police Department", "Maryland State Police")
  * Fire departments and EMS
  * Courts and legal institutions
  * Government agencies
  Use full official names when possible

**CONTENT CLASSIFICATION:**

- primary_theme: The main topic/category of the story. Choose ONE from:
  * "traffic accidents"
  * "violent crime"
  * "fire/rescue"
  * "emergency services"
  * "court proceedings"
  * "law enforcement operations"
  * "public safety policy"
  * "community safety"
  * "weather emergencies"
  * If none fit, return "Other" and include a brief descriptive label

- secondary_themes: List of additional themes (articles often cover multiple issues). Use any relevant from above list.

- incident_type: More specific description of incident (e.g., "pedestrian fatality", "armed robbery", "house fire", "DUI checkpoint", "missing person", "drug arrest", etc.)

- severity_level: Based on injuries, damage, response. Choose ONE: "minor", "moderate", "major"

**GEOGRAPHIC INFORMATION:**

- location: Specific neighborhood/district where incident occurred (if mentioned)
- location_type: Type of location. Choose ONE: "residential", "commercial", "highway", "rural road", "park", "school zone", "government building", "waterfront", "other", or null if not specified

**CONTEXTUAL DETAILS:**

- time_of_incident: If time is mentioned in story, extract it (e.g., "morning", "early morning", "afternoon"). Use null if not mentioned.
- weather_conditions: If weather is relevant/mentioned (e.g., "rainy", "snowy", "foggy", "clear"). Use null if not mentioned.
- response_agencies: List of agencies that responded. Choose from: "police", "fire", "EMS", "state police", "coast guard", "multiple", or create list like ["police", "fire"]
- outcome: Current status. Choose ONE: "arrest made", "under investigation", "resolved", "ongoing", "charges filed", "no charges", or describe briefly

IMPORTANT RULES:
- Do NOT include news organizations, reporters, photographers, or byline names
- Be thorough and specific
- Use null for fields where information is not available or not mentioned
- For arrays, use [] if no information found

Example output:
{{
  "people": ["Chief Chris Thomas, St. Michaels Volunteer Fire Department", "Officer John Doe, Easton Police"],
  "places": ["St. Michaels, Maryland", "Talbot County, Maryland", "Route 50"],
  "organizations": ["St. Michaels Volunteer Fire Department", "Easton Police Department", "Maryland State Police"],
  "primary_theme": "fire/rescue",
  "secondary_themes": ["emergency services"],
  "incident_type": "structure fire",
  "severity_level": "major",
  "location": "downtown St. Michaels",
  "location_type": "commercial",
  "time_of_incident": "2:30 a.m.",
  "weather_conditions": "foggy",
  "response_agencies": ["fire", "EMS"],
  "outcome": "resolved"
}}

Story Title: {story_title}
Story Content: {story_content}

Return only valid JSON with all the fields above. Use null or [] as appropriate for missing information:
"""
    
    try:
        result = subprocess.run([
            'llm', '-m', model, prompt
        ], capture_output=True, text=True, timeout=90)
        
        if result.returncode == 0:
            response_text = result.stdout.strip()
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('\n', 1)[1]
                response_text = response_text.rsplit('\n', 1)[0]
            
            metadata = json.loads(response_text)
            return metadata
        else:
            stderr_msg = result.stderr[:200] if result.stderr else "No error message"
            return {"error": "LLM failed", "stderr": stderr_msg, "returncode": result.returncode}
    except subprocess.TimeoutExpired:
        return {"error": "LLM request timed out after 90 seconds"}
    except json.JSONDecodeError as e:
        return {"error": f"JSON parsing failed: {str(e)}", "response": result.stdout[:200] if 'result' in locals() else "No response"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def summarize_story_with_quotes(story_title, story_content, model):
    """Use LLM to summarize the story while retaining ALL direct quotes."""
    
    prompt = f"""
Summarize this PUBLIC SAFETY news story in a concise way (2-5 paragraphs) while RETAINING ALL DIRECT QUOTES from the original story.

CRITICAL REQUIREMENTS:
1. Include EVERY direct quote from the original story - do not paraphrase or omit any quotes
2. Keep quotes in their original context
3. Preserve the speaker attribution for each quote
4. Maintain the factual accuracy of all details
5. Keep the summary focused on the key facts: who, what, when, where, why, how
6. Organize information chronologically if appropriate
7. Include relevant names, locations, and organizations
8. Retain specific numbers, dates, and times mentioned

Do NOT include any meta-commentary like "this article discusses" - just provide the summary with integrated quotes.

Story Title: {story_title}
Story Content: {story_content}

Provide the summary as plain text (not JSON):
"""
    
    try:
        result = subprocess.run([
            'llm', '-m', model, prompt
        ], capture_output=True, text=True, timeout=90)
        
        if result.returncode == 0:
            summary = result.stdout.strip()
            # Clean up any markdown if present
            if summary.startswith('```'):
                summary = summary.split('\n', 1)[1]
                summary = summary.rsplit('\n', 1)[0]
            return summary
        else:
            return f"[Summary Error: {result.stderr[:100] if result.stderr else 'Unknown error'}]"
    except subprocess.TimeoutExpired:
        return "[Summary Error: Request timed out]"
    except Exception as e:
        return f"[Summary Error: {str(e)}]"

def main():
    parser = argparse.ArgumentParser(description='Extract comprehensive thematic entities and summaries from public safety stories for temporal/thematic analysis')
    parser.add_argument('--model', required=True, help='LLM model to use (e.g., groq/llama-3.3-70b-versatile)')
    parser.add_argument('--input', default='public_safety_stories.json', help='Input JSON file with stories (default: public_safety_stories.json)')
    parser.add_argument('--output', default='thematic_entities_stories.json', help='Output JSON file (default: thematic_entities_stories.json)')
    parser.add_argument('--limit', type=int, help='Limit the number of stories to process (useful for testing)')
    parser.add_argument('--skip-summary', action='store_true', help='Skip summarization step (only extract entities)')
    
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    args = parser.parse_args()
    
    # Load public safety stories
    try:
        with open(args.input) as f:
            all_stories = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find input file '{args.input}'")
        return
    
    # Filter out unwanted story types
    stories = []
    filtered_out = []
    
    for story in all_stories:
        title = story.get('title', '')
        content = story.get('content', '')
        
        # Skip non-news content
        skip_patterns = ['TODAY IN HISTORY', 'RELIGION CALENDAR', 'MID-SHORE CALENDAR', 'OBITUARY']
        if any(pattern in title.upper() for pattern in skip_patterns):
            filtered_out.append(f"{title} (filtered)")
            continue
        
        if 'Section: Calendar' in content or 'Section: Columns' in content or 'Section: Letters' in content:
            filtered_out.append(f"{title} (Calendar/Columns/Letters)")
            continue
        
        stories.append(story)
    
    print(f"\n{'='*60}")
    print(f"THEMATIC ENTITY EXTRACTION")
    print(f"{'='*60}")
    print(f"Loaded {len(all_stories)} stories from {args.input}")
    print(f"Filtered out {len(filtered_out)} non-news stories")
    print(f"Remaining stories after filtering: {len(stories)}")
    
    # Randomly sample 300 stories by default
    sample_size = min(300, len(stories))
    if sample_size < len(stories) and not args.limit:
        print(f"Randomly sampling {sample_size} stories from {len(stories)} available")
        random.seed(42)  # Set seed for reproducibility
        stories = random.sample(stories, sample_size)
    else:
        print(f"Using all {len(stories)} stories (less than 300 available)")
    
    # Apply limit if specified (for testing)
    if args.limit and args.limit < len(stories):
        print(f"Limiting to first {args.limit} stories (--limit)")
        stories = stories[:args.limit]
    
    print(f"Will process {len(stories)} stories")
    print(f"Model: {args.model}")
    print(f"Output: {args.output}")
    print(f"{'='*60}\n")
    
    output_filename = args.output
    
    # Initialize or load existing results
    if Path(output_filename).exists():
        print(f"Found existing output file, loading previous results...")
        with open(output_filename) as f:
            enhanced_stories = json.load(f)
        print(f"Loaded {len(enhanced_stories)} previously processed stories\n")
    else:
        enhanced_stories = []
        print(f"Starting fresh with new output file\n")
    
    # Process each story
    errors = []
    starting_count = len(enhanced_stories)
    summary_success_count = 0
    
    for i, story in enumerate(stories):
        # Skip if already processed
        if i < starting_count:
            continue
        
        print(f"\n[{i+1}/{len(stories)}] Processing: {story.get('title', 'Untitled')[:70]}...")
        
        story_content = story.get('content', '')
        story_title = story.get('title', '')
        story_date = story.get('date', '')
        
        if not story_content:
            print(f"  ⚠️  Warning: No content found, skipping")
            continue
        
        # Step 1: Extract entities FIRST (as requested)
        print(f"  → Extracting entities...")
        entities = extract_entities(story_title, story_content, args.model)
        
        # Step 2: Summarize story with quotes (unless skipped)
        summary = None
        if not args.skip_summary:
            print(f"  → Summarizing story (retaining quotes)...")
            # Wait before making second LLM call to avoid rate limits
            time.sleep(3)
            summary = summarize_story_with_quotes(story_title, story_content, args.model)
        
        # Build enhanced story
        enhanced_story = story.copy()
        
        # Add temporal metadata (derived from date)
        enhanced_story['year'] = story.get('year')  # Use existing year if available
        if not enhanced_story['year'] and story_date:
            try:
                enhanced_story['year'] = int(story_date.split('-')[0])
            except:
                enhanced_story['year'] = None
        
        enhanced_story['season'] = derive_season(story_date) if story_date else None
        enhanced_story['is_weekend'] = is_weekend(story_date) if story_date else None
        
        # Add entity extraction results
        if isinstance(entities, dict) and 'error' not in entities:
            # Named entities
            enhanced_story['people'] = entities.get('people', [])
            enhanced_story['places'] = entities.get('places', [])
            enhanced_story['organizations'] = entities.get('organizations', [])
            
            # Content classification
            enhanced_story['primary_theme'] = entities.get('primary_theme')
            enhanced_story['secondary_themes'] = entities.get('secondary_themes', [])
            enhanced_story['incident_type'] = entities.get('incident_type')
            enhanced_story['severity_level'] = entities.get('severity_level')
            
            # Geographic information
            enhanced_story['location'] = entities.get('location')
            enhanced_story['location_type'] = entities.get('location_type')
            
            # Contextual details
            enhanced_story['time_of_incident'] = entities.get('time_of_incident')
            enhanced_story['weather_conditions'] = entities.get('weather_conditions')
            enhanced_story['response_agencies'] = entities.get('response_agencies', [])
            enhanced_story['outcome'] = entities.get('outcome')
            
            print(f"  ✓ Entities: {len(enhanced_story['people'])} people, {len(enhanced_story['places'])} places, {len(enhanced_story['organizations'])} orgs")
            print(f"    Theme: {enhanced_story.get('primary_theme')} | Type: {enhanced_story.get('incident_type')} | Severity: {enhanced_story.get('severity_level')}")
        else:
            # Handle errors (including unexpected response formats)
            if isinstance(entities, dict):
                error_msg = entities.get('error', 'Unknown error')
            else:
                error_msg = f"Unexpected response format: {type(entities).__name__}"
            
            enhanced_story['people'] = []
            enhanced_story['places'] = []
            enhanced_story['organizations'] = []
            enhanced_story['primary_theme'] = None
            enhanced_story['secondary_themes'] = []
            enhanced_story['incident_type'] = None
            enhanced_story['severity_level'] = None
            enhanced_story['location'] = None
            enhanced_story['location_type'] = None
            enhanced_story['time_of_incident'] = None
            enhanced_story['weather_conditions'] = None
            enhanced_story['response_agencies'] = []
            enhanced_story['outcome'] = None
            enhanced_story['entity_extraction_error'] = error_msg
            
            errors.append(f"Story {i+1}: {error_msg[:80]}")
            print(f"  ✗ Entity extraction error: {error_msg[:60]}")
        
        # Replace content with summary
        if summary and not summary.startswith('[Summary Error'):
            enhanced_story['content'] = summary
            summary_success_count += 1
            print(f"  ✓ Summary generated ({len(summary)} chars, original was {len(story_content)} chars)")
        elif summary:
            # If summary failed, keep original content but note the error
            enhanced_story['entity_extraction_error'] = enhanced_story.get('entity_extraction_error', '') + f" | Summary error: {summary}"
            print(f"  ✗ Summary error: {summary[:60]}")
        
        enhanced_stories.append(enhanced_story)
        
        # Incremental save after each story
        with open(output_filename, 'w') as f:
            json.dump(enhanced_stories, f, indent=2)
        
        # Rate limiting - increased delay to respect API limits (2 LLM calls per story)
        time.sleep(4)
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"Total stories in input: {len(all_stories)}")
    print(f"Filtered out: {len(filtered_out)}")
    processed_this_run = len(enhanced_stories) - starting_count
    print(f"Processed in this run: {processed_this_run}")
    print(f"Total stories in output: {len(enhanced_stories)}")
    
    # Count successful operations
    successful_entities = sum(1 for s in enhanced_stories if 'entity_extraction_error' not in s)
    print(f"\n✓ Successfully extracted entities: {successful_entities}/{len(enhanced_stories)}")
    if not args.skip_summary:
        print(f"✓ Summaries generated in this run: {summary_success_count}/{processed_this_run}")
    
    # Thematic breakdown
    print(f"\nTHEMATIC BREAKDOWN:")
    themes = {}
    for story in enhanced_stories:
        theme = story.get('primary_theme', 'unknown')
        themes[theme] = themes.get(theme, 0) + 1
    for theme, count in sorted(themes.items(), key=lambda x: x[1], reverse=True):
        print(f"  {theme}: {count}")
    
    # Seasonal breakdown
    print(f"\nSEASONAL BREAKDOWN:")
    seasons = {}
    for story in enhanced_stories:
        season = story.get('season', 'unknown')
        seasons[season] = seasons.get(season, 0) + 1
    for season in ['winter', 'spring', 'summer', 'fall', 'unknown']:
        if season in seasons:
            print(f"  {season}: {seasons[season]}")
    
    print(f"\nOutput saved to: {output_filename}")
    print(f"(File saved incrementally after each story)")
    
    if errors:
        print(f"\n⚠️  {len(errors)} errors occurred:")
        for error in errors[:5]:
            print(f"  - {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more")
    
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
