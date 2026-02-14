#!/usr/bin/env python3
"""
Extract individuals, events, and places from news stories.
Highlights prominently featured entities across the story collection.
"""

import json
import llm
import sys
from pathlib import Path
from collections import Counter, defaultdict

def get_model(model_name=None):
    """Get the LLM model to use."""
    if model_name:
        return llm.get_model(model_name)
    return llm.get_model()

def extract_entities_from_batch(stories, batch_num, model):
    """Extract individuals, events, and places from a batch of stories."""
    prompt = f"""Extract the following from these {len(stories)} news stories:

1. **INDIVIDUALS AND TITLES**: Every person mentioned with their full title/role
   - Format: "Name (Title/Role)"
   - Include all mentions: officials, victims, witnesses, experts, etc.
   
2. **EVENTS AND ORGANIZATIONAL ACTS**: Specific incidents, activities, decisions
   - Criminal incidents (arrests, charges, investigations)
   - Government actions (ordinances, meetings, decisions)
   - Emergency responses (fires, accidents, rescues)
   - Public meetings and hearings
   - Organizational decisions and announcements
   
3. **PLACES**: All geographic locations mentioned
   - Specific addresses and intersections
   - Neighborhoods and communities
   - Buildings and facilities
   - County/regional locations

For each category, note which story (by title) it appears in.

Stories:
{json.dumps([{'title': s['title'], 'date': s.get('date', ''), 'content': s['content']} for s in stories], indent=2)}

Return a structured JSON response:
{{
  "individuals": [
    {{"name": "Person Name", "title": "Their Title/Role", "story_titles": ["Story 1", "Story 2"]}}
  ],
  "events": [
    {{"event": "Description of event", "type": "criminal/government/emergency/meeting/other", "story_titles": ["Story 1"]}}
  ],
  "places": [
    {{"location": "Place Name", "type": "address/neighborhood/building/region", "story_titles": ["Story 1", "Story 2"]}}
  ]
}}"""
    
    print(f"Extracting entities from batch {batch_num}...", file=sys.stderr)
    response = model.prompt(prompt)
    
    # Try to extract JSON from response
    response_text = response.text()
    
    # First, try to parse directly
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from markdown code blocks
    import re
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try to find JSON object in the text
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    print(f"Warning: Could not parse JSON from batch {batch_num}", file=sys.stderr)
    if len(response_text) < 500:
        print(f"Response was: {response_text[:500]}", file=sys.stderr)
    return {"individuals": [], "events": [], "places": []}

def consolidate_entities(batch_results):
    """Consolidate entities from all batches and count frequencies."""
    # Track all mentions
    individuals_dict = defaultdict(lambda: {"titles": set(), "stories": set()})
    events_dict = defaultdict(lambda: {"types": set(), "stories": set()})
    places_dict = defaultdict(lambda: {"types": set(), "stories": set()})
    
    # Process all batches
    for batch in batch_results:
        # Individuals
        for person in batch.get("individuals", []):
            name = person.get("name", "").strip()
            if name:
                individuals_dict[name]["titles"].add(person.get("title", ""))
                individuals_dict[name]["stories"].update(person.get("story_titles", []))
        
        # Events
        for event in batch.get("events", []):
            event_desc = event.get("event", "").strip()
            if event_desc:
                events_dict[event_desc]["types"].add(event.get("type", ""))
                events_dict[event_desc]["stories"].update(event.get("story_titles", []))
        
        # Places
        for place in batch.get("places", []):
            location = place.get("location", "").strip()
            if location:
                places_dict[location]["types"].add(place.get("type", ""))
                places_dict[location]["stories"].update(place.get("story_titles", []))
    
    # Convert to sorted lists with frequency
    individuals = [
        {
            "name": name,
            "titles": list(data["titles"]),
            "story_count": len(data["stories"]),
            "stories": list(data["stories"])
        }
        for name, data in individuals_dict.items()
    ]
    individuals.sort(key=lambda x: x["story_count"], reverse=True)
    
    events = [
        {
            "event": event,
            "types": list(data["types"]),
            "story_count": len(data["stories"]),
            "stories": list(data["stories"])
        }
        for event, data in events_dict.items()
    ]
    events.sort(key=lambda x: x["story_count"], reverse=True)
    
    places = [
        {
            "location": location,
            "types": list(data["types"]),
            "story_count": len(data["stories"]),
            "stories": list(data["stories"])
        }
        for location, data in places_dict.items()
    ]
    places.sort(key=lambda x: x["story_count"], reverse=True)
    
    return {
        "individuals": individuals,
        "events": events,
        "places": places
    }

def generate_report(consolidated, total_stories, threshold_percent=5):
    """Generate a markdown report highlighting prominent entities."""
    # Calculate threshold for "prominent" (appears in X% of stories)
    prominence_threshold = max(2, int(total_stories * (threshold_percent / 100)))
    
    report = f"""# Entity Extraction Report

**Total Stories Analyzed:** {total_stories}
**Prominence Threshold:** Appears in at least {prominence_threshold} stories ({threshold_percent}% of total)

---

## INDIVIDUALS AND TITLES

### Prominently Featured Individuals
*These individuals appear in {prominence_threshold} or more stories*

"""
    
    # Prominently featured individuals
    prominent_individuals = [p for p in consolidated["individuals"] if p["story_count"] >= prominence_threshold]
    
    if prominent_individuals:
        for person in prominent_individuals:
            titles_str = " / ".join(person["titles"]) if person["titles"] else "No title specified"
            report += f"### **{person['name']}** ({person['story_count']} stories)\n"
            report += f"**Title(s):** {titles_str}\n\n"
    else:
        report += "*No individuals meet the prominence threshold*\n\n"
    
    # All other individuals
    other_individuals = [p for p in consolidated["individuals"] if p["story_count"] < prominence_threshold]
    
    if other_individuals:
        report += f"\n### Other Individuals ({len(other_individuals)} total)\n\n"
        for person in other_individuals[:50]:  # Limit to first 50
            titles_str = " / ".join(person["titles"]) if person["titles"] else "No title specified"
            report += f"- **{person['name']}** ({person['story_count']} stories) - {titles_str}\n"
        
        if len(other_individuals) > 50:
            report += f"\n*...and {len(other_individuals) - 50} more individuals*\n"
    
    # Events section
    report += "\n\n---\n\n## EVENTS AND ORGANIZATIONAL ACTS\n\n"
    report += "### Prominent Events\n"
    report += f"*Events appearing in {prominence_threshold} or more stories*\n\n"
    
    prominent_events = [e for e in consolidated["events"] if e["story_count"] >= prominence_threshold]
    
    if prominent_events:
        for event in prominent_events:
            types_str = ", ".join(event["types"]) if event["types"] else "general"
            report += f"### {event['event']} ({event['story_count']} stories)\n"
            report += f"**Type:** {types_str}\n\n"
    else:
        report += "*No events meet the prominence threshold*\n\n"
    
    # All other events
    other_events = [e for e in consolidated["events"] if e["story_count"] < prominence_threshold]
    
    if other_events:
        report += f"\n### Other Events ({len(other_events)} total)\n\n"
        # Group by type
        events_by_type = defaultdict(list)
        for event in other_events:
            event_type = event["types"][0] if event["types"] else "other"
            events_by_type[event_type].append(event)
        
        for event_type, events in sorted(events_by_type.items()):
            report += f"\n#### {event_type.title()} Events\n"
            for event in events[:20]:  # Limit per type
                report += f"- {event['event']} ({event['story_count']} stories)\n"
            if len(events) > 20:
                report += f"*...and {len(events) - 20} more {event_type} events*\n"
    
    # Places section
    report += "\n\n---\n\n## PLACES\n\n"
    report += "### Prominently Featured Locations\n"
    report += f"*Locations appearing in {prominence_threshold} or more stories*\n\n"
    
    prominent_places = [p for p in consolidated["places"] if p["story_count"] >= prominence_threshold]
    
    if prominent_places:
        for place in prominent_places:
            types_str = ", ".join(place["types"]) if place["types"] else "general"
            report += f"### **{place['location']}** ({place['story_count']} stories)\n"
            report += f"**Type:** {types_str}\n\n"
    else:
        report += "*No locations meet the prominence threshold*\n\n"
    
    # All other places
    other_places = [p for p in consolidated["places"] if p["story_count"] < prominence_threshold]
    
    if other_places:
        report += f"\n### Other Locations ({len(other_places)} total)\n\n"
        # Group by type
        places_by_type = defaultdict(list)
        for place in other_places:
            place_type = place["types"][0] if place["types"] else "other"
            places_by_type[place_type].append(place)
        
        for place_type, places in sorted(places_by_type.items()):
            report += f"\n#### {place_type.title()} Locations\n"
            for place in places[:30]:  # Limit per type
                report += f"- {place['location']} ({place['story_count']} stories)\n"
            if len(places) > 30:
                report += f"*...and {len(places) - 30} more {place_type} locations*\n"
    
    return report

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Extract individuals, events, and places from news stories'
    )
    parser.add_argument('input_file', help='Path to JSON file with news stories')
    parser.add_argument('-o', '--output',
                       help='Output file for the entity report (default: entity_report.md)')
    parser.add_argument('-j', '--json-output',
                       help='Also save structured JSON output to this file')
    parser.add_argument('-b', '--batch-size', type=int, default=20,
                       help='Number of stories per batch (default: 20)')
    parser.add_argument('-m', '--model', 
                       help='LLM model to use (default: llm default model)')
    parser.add_argument('-t', '--threshold', type=int, default=5,
                       help='Prominence threshold as percentage (default: 5%%)')
    parser.add_argument('--debug', action='store_true',
                       help='Save intermediate batch outputs for debugging')
    
    args = parser.parse_args()
    
    # Load stories
    print(f"Loading stories from {args.input_file}...", file=sys.stderr)
    with open(args.input_file, 'r') as f:
        data = json.load(f)
    
    # Handle different JSON structures
    if isinstance(data, list):
        stories = data
    elif isinstance(data, dict) and 'stories' in data:
        stories = data['stories']
    elif isinstance(data, dict) and 'articles' in data:
        stories = data['articles']
    else:
        print("Error: JSON structure not recognized. Expected a list or dict with 'stories' or 'articles' key.", 
              file=sys.stderr)
        sys.exit(1)
    
    print(f"Loaded {len(stories)} stories", file=sys.stderr)
    
    # Set default output file if not specified
    if not args.output:
        input_path = Path(args.input_file)
        args.output = str(input_path.parent / 'entity_report.md')
    
    # Get model
    model = get_model(args.model)
    print(f"Using model: {model.model_id}", file=sys.stderr)
    
    # Extract entities from batches
    batch_results = []
    num_batches = (len(stories) + args.batch_size - 1) // args.batch_size
    
    for i in range(0, len(stories), args.batch_size):
        batch = stories[i:i+args.batch_size]
        batch_num = i // args.batch_size + 1
        entities = extract_entities_from_batch(batch, batch_num, model)
        batch_results.append(entities)
        
        # Debug: save each batch result
        if args.debug:
            debug_file = f"debug_entities_batch_{batch_num:03d}.json"
            with open(debug_file, 'w') as f:
                json.dump(entities, f, indent=2)
    
    # Consolidate all entities
    print("Consolidating entities across all batches...", file=sys.stderr)
    consolidated = consolidate_entities(batch_results)
    
    print(f"\nExtraction Summary:", file=sys.stderr)
    print(f"  Individuals: {len(consolidated['individuals'])}", file=sys.stderr)
    print(f"  Events: {len(consolidated['events'])}", file=sys.stderr)
    print(f"  Places: {len(consolidated['places'])}", file=sys.stderr)
    
    # Save JSON output if requested
    if args.json_output:
        with open(args.json_output, 'w') as f:
            json.dump(consolidated, f, indent=2)
        print(f"Structured data saved to {args.json_output}", file=sys.stderr)
    
    # Generate and save report
    print("Generating report...", file=sys.stderr)
    report = generate_report(consolidated, len(stories), args.threshold)
    
    with open(args.output, 'w') as f:
        f.write(report)
    
    print(f"\n✓ Entity report saved to {args.output}", file=sys.stderr)
    print(f"  Analyzed {len(stories)} stories in {num_batches} batches", file=sys.stderr)
    print(f"  Prominence threshold: {args.threshold}% ({max(2, int(len(stories) * (args.threshold / 100)))} stories)", file=sys.stderr)

if __name__ == '__main__':
    main()
