#!/usr/bin/env python3
"""
Script to clean and standardize entity metadata in local government stories
for beat book purposes. Removes irrelevant metadata and standardizes formats.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import re

def is_relevant_establishment(establishment: str) -> bool:
    """
    Determine if an establishment is relevant for a beat book.
    Keep: Named places, schools, specific buildings
    Remove: Only truly generic references without proper names
    """
    # Remove if it's just an address number
    if re.match(r'^\d+\s+', establishment):
        return False
    
    establishment_lower = establishment.lower().strip()
    
    # Remove ONLY if it's a standalone generic term with no name
    standalone_generic = [
        'office', 'offices', 'building', 'facility', 'center', 
        'room', 'location', 'site', 'area', 'property', 'department'
    ]
    
    if establishment_lower in standalone_generic:
        return False
    
    # Remove only very generic combinations WITHOUT proper names
    # (e.g., "Town Office" but keep "Oxford Town Office")
    generic_patterns = [
        r'^town office$', r'^city office$', r'^county office$',
        r'^town offices$', r'^city offices$', r'^county offices$',
        r'^council chambers$', r'^commission chambers$',
        r'^public works$', r'^town building$', r'^county building$',
        r'^town hall office$', r'^city hall office$'
    ]
    
    for pattern in generic_patterns:
        if re.match(pattern, establishment_lower):
            return False
    
    # Keep everything else (named places, schools, specific buildings)
    return True

def is_relevant_event(event: str) -> bool:
    """
    Determine if an event is relevant for a beat book.
    Keep: Recurring meetings, important hearings, significant events
    Remove: One-time social events, past-tense completed events
    """
    # Keep meetings and hearings
    relevant_keywords = [
        'meeting', 'hearing', 'session', 'council', 'commission',
        'board', 'workshop', 'budget', 'election'
    ]
    
    event_lower = event.lower()
    return any(keyword in event_lower for keyword in relevant_keywords)

def standardize_person_format(person: str) -> str:
    """
    Standardize person format to: Name — Title, Organization
    """
    # Already in correct format
    if ' — ' in person:
        return person
    
    # Try to parse and standardize
    return person

def clean_key_people(people: List[str]) -> List[str]:
    """Clean and standardize key people entries."""
    cleaned = []
    seen = set()
    
    for person in people:
        # Standardize format
        standardized = standardize_person_format(person)
        
        # Remove duplicates (case-insensitive)
        if standardized.lower() not in seen:
            cleaned.append(standardized)
            seen.add(standardized.lower())
    
    return sorted(cleaned)

def clean_key_events(events: List[str]) -> List[str]:
    """Clean and filter key events."""
    cleaned = []
    seen = set()
    
    for event in events:
        if is_relevant_event(event) and event.lower() not in seen:
            cleaned.append(event)
            seen.add(event.lower())
    
    return sorted(cleaned)

def clean_key_establishments(establishments: List[str]) -> List[str]:
    """Clean and filter key establishments."""
    cleaned = []
    seen = set()
    
    for establishment in establishments:
        if is_relevant_establishment(establishment) and establishment.lower() not in seen:
            cleaned.append(establishment)
            seen.add(establishment.lower())
    
    return sorted(cleaned)

def clean_key_organizations(organizations: List[str]) -> List[str]:
    """Clean and deduplicate organizations, removing only truly generic ones."""
    cleaned = []
    seen = set()
    
    # Remove ONLY standalone generic terms without proper names
    standalone_generic = [
        'county', 'town', 'city', 'state', 'commission', 'council',
        'board', 'department', 'office', 'government', 'administration'
    ]
    
    generic_patterns = [
        r'^county roads$', r'^town roads$', r'^state roads$',
        r'^county office$', r'^town office$', r'^city office$',
        r'^county government$', r'^town government$', r'^city government$'
    ]
    
    for org in organizations:
        if not org:
            continue
            
        org_lower = org.lower().strip()
        
        # Skip if it's just a standalone generic term
        if org_lower in standalone_generic:
            continue
        
        # Skip if it matches a generic pattern
        skip = False
        for pattern in generic_patterns:
            if re.match(pattern, org_lower):
                skip = True
                break
        
        if skip:
            continue
            
        if org_lower not in seen:
            cleaned.append(org)
            seen.add(org_lower)
    
    return sorted(cleaned)

def clean_key_initiatives(initiatives: List[str]) -> List[str]:
    """Clean and deduplicate initiatives."""
    cleaned = []
    seen = set()
    
    for initiative in initiatives:
        if initiative and initiative.lower() not in seen:
            cleaned.append(initiative)
            seen.add(initiative.lower())
    
    return sorted(cleaned)

def clean_story_metadata(story: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and standardize metadata for a single story.
    """
    cleaned_story = story.copy()
    
    # Clean entity fields
    if 'key_people' in cleaned_story:
        cleaned_story['key_people'] = clean_key_people(cleaned_story['key_people'])
    
    if 'key_events' in cleaned_story:
        cleaned_story['key_events'] = clean_key_events(cleaned_story['key_events'])
    
    if 'key_establishments' in cleaned_story:
        cleaned_story['key_establishments'] = clean_key_establishments(cleaned_story['key_establishments'])
    
    if 'key_organizations' in cleaned_story:
        cleaned_story['key_organizations'] = clean_key_organizations(cleaned_story['key_organizations'])
    
    if 'key_initiatives' in cleaned_story:
        cleaned_story['key_initiatives'] = clean_key_initiatives(cleaned_story['key_initiatives'])
    
    return cleaned_story

def main():
    input_file = Path('local_government_secondary_stories_with_entities_v1.json')
    output_file = Path('local_government_secondary_stories_with_entities_v1_cleaned.json')
    
    if not input_file.exists():
        print(f"Error: {input_file} not found")
        sys.exit(1)
    
    print(f"Loading stories from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        stories = json.load(f)
    
    print(f"Loaded {len(stories)} stories")
    print("Cleaning and standardizing metadata...")
    
    # Track statistics
    stats = {
        'total_stories': len(stories),
        'people_removed': 0,
        'events_removed': 0,
        'establishments_removed': 0,
        'organizations_cleaned': 0,
        'initiatives_cleaned': 0
    }
    
    cleaned_stories = []
    for i, story in enumerate(stories):
        if i % 100 == 0:
            print(f"Processing story {i+1}/{len(stories)}...")
        
        # Count before cleaning
        before_people = len(story.get('key_people', []))
        before_events = len(story.get('key_events', []))
        before_establishments = len(story.get('key_establishments', []))
        
        # Clean the story
        cleaned_story = clean_story_metadata(story)
        
        # Count after cleaning
        after_people = len(cleaned_story.get('key_people', []))
        after_events = len(cleaned_story.get('key_events', []))
        after_establishments = len(cleaned_story.get('key_establishments', []))
        
        stats['people_removed'] += (before_people - after_people)
        stats['events_removed'] += (before_events - after_events)
        stats['establishments_removed'] += (before_establishments - after_establishments)
        
        cleaned_stories.append(cleaned_story)
    
    print(f"\nSaving cleaned stories to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_stories, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print("CLEANING SUMMARY")
    print(f"{'='*80}")
    print(f"Total stories processed: {stats['total_stories']}")
    print(f"People entries removed/deduplicated: {stats['people_removed']}")
    print(f"Events filtered out: {stats['events_removed']}")
    print(f"Establishments filtered out: {stats['establishments_removed']}")
    print(f"\nCleaned file saved to: {output_file}")
    print(f"{'='*80}")
    
    # Show some examples of what was removed
    print("\nExamples of cleaned metadata:")
    print("-" * 80)
    
    for i, story in enumerate(cleaned_stories[:3]):
        print(f"\n{i+1}. {story.get('title', 'No title')}")
        print(f"   Date: {story.get('date', 'N/A')}")
        if story.get('key_people'):
            print(f"   Key People: {len(story['key_people'])} entries")
        if story.get('key_events'):
            print(f"   Key Events: {story['key_events']}")
        if story.get('key_establishments'):
            print(f"   Key Establishments: {story['key_establishments']}")

if __name__ == '__main__':
    main()
