#!/usr/bin/env python3
"""
Standardize ALL metadata across stories in beatbook_refined_stories.json.

This script ensures complete consistency:
- Organization names: "Town of X" vs "X", "X Commissioners" vs "Commissioners of X"
- Event names: standardized meeting formats
- Title formats: consistent organization references
- People entries: same person with same role uses identical format
"""

import json
import re
from pathlib import Path
from collections import defaultdict, Counter

INPUT_FILE = "beatbook_refined_stories.json"
OUTPUT_FILE = "beatbook_standardized_stories.json"

# Master canonical forms for common entities
CANONICAL_ORGANIZATIONS = {
    # Towns - use "Town of X" format
    'town of easton': 'Town of Easton',
    'easton': 'Town of Easton',
    'town of federalsburg': 'Town of Federalsburg',
    'federalsburg': 'Town of Federalsburg',
    'town of greensboro': 'Town of Greensboro',
    'greensboro': 'Town of Greensboro',
    'town of ridgely': 'Town of Ridgely',
    'ridgely': 'Town of Ridgely',
    'town of denton': 'Town of Denton',
    'denton': 'Town of Denton',
    'town of queenstown': 'Town of Queenstown',
    'queenstown': 'Town of Queenstown',
    'town of trappe': 'Town of Trappe',
    'trappe': 'Town of Trappe',
    'town of st. michaels': 'Town of St. Michaels',
    'st. michaels': 'Town of St. Michaels',
    'town of oxford': 'Town of Oxford',
    'oxford': 'Town of Oxford',
    'city of cambridge': 'City of Cambridge',
    'cambridge': 'City of Cambridge',
    
    # Commissioners - use "[Place] Town Commissioners" or "[Place] County Commissioners"
    'commissioners of easton': 'Easton Town Council',
    'easton town council': 'Easton Town Council',
    'easton commissioners': 'Easton Town Council',
    
    'commissioners of federalsburg': 'Federalsburg Town Council',
    'federalsburg town council': 'Federalsburg Town Council',
    'federalsburg commissioners': 'Federalsburg Town Council',
    
    'commissioners of greensboro': 'Greensboro Town Council',
    'greensboro town council': 'Greensboro Town Council',
    'greensboro commissioners': 'Greensboro Town Council',
    
    'commissioners of ridgely': 'Ridgely Town Commissioners',
    'ridgely town commissioners': 'Ridgely Town Commissioners',
    'ridgely commissioners': 'Ridgely Town Commissioners',
    
    'commissioners of denton': 'Denton Town Commissioners',
    'denton town commissioners': 'Denton Town Commissioners',
    'denton commissioners': 'Denton Town Commissioners',
    
    'commissioners of queenstown': 'Queenstown Town Commissioners',
    'queenstown town commissioners': 'Queenstown Town Commissioners',
    'queenstown commissioners': 'Queenstown Town Commissioners',
    
    'commissioners of trappe': 'Trappe Town Commissioners',
    'trappe town commissioners': 'Trappe Town Commissioners',
    'trappe commissioners': 'Trappe Town Commissioners',
    
    'commissioners of st. michaels': 'St. Michaels Town Commissioners',
    'st. michaels town commissioners': 'St. Michaels Town Commissioners',
    'st. michaels commissioners': 'St. Michaels Town Commissioners',
    
    'commissioners of oxford': 'Oxford Town Commissioners',
    'oxford town commissioners': 'Oxford Town Commissioners',
    'oxford commissioners': 'Oxford Town Commissioners',
    
    'cambridge city council': 'Cambridge City Council',
    'city council of cambridge': 'Cambridge City Council',
    'cambridge council': 'Cambridge City Council',
    
    # County Commissioners
    'talbot county commissioners': 'Talbot County Council',
    'talbot county council': 'Talbot County Council',
    'commissioners of talbot county': 'Talbot County Council',
    
    'caroline county commissioners': 'Caroline County Commissioners',
    'commissioners of caroline county': 'Caroline County Commissioners',
    
    'dorchester county commissioners': 'Dorchester County Council',
    'dorchester county council': 'Dorchester County Council',
    'commissioners of dorchester county': 'Dorchester County Council',
    
    'kent county commissioners': 'Kent County Commissioners',
    'commissioners of kent county': 'Kent County Commissioners',
    
    "queen anne's county commissioners": "Queen Anne's County Commissioners",
    "commissioners of queen anne's county": "Queen Anne's County Commissioners",
    
    # Sheriff's Offices
    'caroline county sheriff\'s office': 'Caroline County Sheriff\'s Office',
    'caroline county sheriff office': 'Caroline County Sheriff\'s Office',
    'sheriff\'s office': 'Caroline County Sheriff\'s Office',
    
    # Police Departments
    'easton police department': 'Easton Police Department',
    'ridgely police department': 'Ridgely Police Department',
    'federalsburg police department': 'Federalsburg Police Department',
    'st. michaels police department': 'St. Michaels Police Department',
    
    # State Agencies
    'maryland office of the state prosecutor': 'Maryland Office of the State Prosecutor',
    'office of the state prosecutor': 'Maryland Office of the State Prosecutor',
    'state prosecutor': 'Maryland Office of the State Prosecutor',
    
    'maryland state police': 'Maryland State Police',
    'state police': 'Maryland State Police',
    
    'maryland department of human services': 'Maryland Department of Human Services',
    'department of human services': 'Maryland Department of Human Services',
}

# Event name standardization
CANONICAL_EVENTS = {
    # Meeting formats: "[Organization] Meeting"
    'easton town council meeting': 'Easton Town Council Meeting',
    'federalsburg town council meeting': 'Federalsburg Town Council Meeting',
    'greensboro town council meeting': 'Greensboro Town Council Meeting',
    'ridgely town commissioners meeting': 'Ridgely Town Commissioners Meeting',
    'denton town commissioners meeting': 'Denton Town Commissioners Meeting',
    'queenstown town commissioners meeting': 'Queenstown Town Commissioners Meeting',
    'trappe town commissioners meeting': 'Trappe Town Commissioners Meeting',
    'st. michaels town commissioners meeting': 'St. Michaels Town Commissioners Meeting',
    'oxford town commissioners meeting': 'Oxford Town Commissioners Meeting',
    'cambridge city council meeting': 'Cambridge City Council Meeting',
    
    'talbot county council meeting': 'Talbot County Council Meeting',
    'caroline county commissioners meeting': 'Caroline County Commissioners Meeting',
    'dorchester county council meeting': 'Dorchester County Council Meeting',
    'kent county commissioners meeting': 'Kent County Commissioners Meeting',
    "queen anne's county commissioners meeting": "Queen Anne's County Commissioners Meeting",
    
    # Close/Closed session
    'closed session meeting': 'Closed Session Meeting',
    'close session meeting': 'Closed Session Meeting',
}


def normalize_for_lookup(text: str) -> str:
    """Normalize text for dictionary lookup."""
    return text.lower().strip()


def standardize_organization(org: str) -> str:
    """Standardize an organization name."""
    normalized = normalize_for_lookup(org)
    return CANONICAL_ORGANIZATIONS.get(normalized, org.strip())


def standardize_event(event: str) -> str:
    """Standardize an event name."""
    normalized = normalize_for_lookup(event)
    return CANONICAL_EVENTS.get(normalized, event.strip())


def standardize_person_title(title: str) -> str:
    """Standardize the organization part of a person's title."""
    if not title:
        return title
    
    # Check if title contains organization name
    for org_lower, canonical in CANONICAL_ORGANIZATIONS.items():
        # Case insensitive search and replace
        pattern = re.compile(re.escape(org_lower), re.IGNORECASE)
        if pattern.search(title.lower()):
            # Replace with canonical form
            title = pattern.sub(canonical, title, count=1)
            break
    
    return title.strip()


def extract_name_and_title(full_entry: str) -> tuple:
    """Extract name and title from 'Name — Title, Organization' format."""
    if ' — ' in full_entry:
        parts = full_entry.split(' — ', 1)
        name = parts[0].strip()
        title = parts[1].strip() if len(parts) > 1 else ""
        return name, title
    return full_entry.strip(), ""


def build_person_canonical_map(stories: list) -> dict:
    """Build mapping for people entries, grouping by name and standardizing titles."""
    # Collect all person entries with counts
    people_entries = defaultdict(Counter)
    
    for story in stories:
        for person_entry in story.get('key_people', []):
            name, title = extract_name_and_title(person_entry)
            # Standardize the organization part of the title
            standardized_title = standardize_person_title(title)
            standardized_entry = f"{name} — {standardized_title}" if standardized_title else name
            
            # Group by name (to find same person with different roles)
            people_entries[name.lower().strip()][standardized_entry] += 1
    
    # Build mapping from all variations to standardized forms
    mapping = {}
    for name_key, entry_counts in people_entries.items():
        # For each unique standardized entry for this person, map all variations to it
        for standardized_entry in entry_counts:
            # Map this standardized form to itself
            mapping[standardized_entry] = standardized_entry
            
            # Also map any non-standardized variations
            name, _ = extract_name_and_title(standardized_entry)
            # Find all original entries with this name in the stories
            for story in stories:
                for original_entry in story.get('key_people', []):
                    orig_name, _ = extract_name_and_title(original_entry)
                    if orig_name.lower().strip() == name_key:
                        mapping[original_entry] = standardized_entry
    
    return mapping


def apply_standardization(stories: list, people_mapping: dict) -> list:
    """Apply standardized mappings to all stories."""
    
    standardized = []
    
    for story in stories:
        # Standardize people using the mapping
        if 'key_people' in story:
            story['key_people'] = [
                people_mapping.get(person, person)
                for person in story['key_people']
            ]
            # Remove duplicates while preserving order
            seen = set()
            story['key_people'] = [
                p for p in story['key_people']
                if not (p in seen or seen.add(p))
            ]
        
        # Standardize organizations using canonical dictionary
        if 'key_organizations' in story:
            story['key_organizations'] = [
                standardize_organization(org)
                for org in story['key_organizations']
            ]
            # Remove duplicates
            seen = set()
            story['key_organizations'] = [
                o for o in story['key_organizations']
                if not (o in seen or seen.add(o))
            ]
        
        # Standardize initiatives (keep as-is but dedupe)
        if 'key_initiatives' in story:
            seen = set()
            deduped = []
            for init in story['key_initiatives']:
                init_clean = init.strip()
                if init_clean not in seen:
                    seen.add(init_clean)
                    deduped.append(init_clean)
            story['key_initiatives'] = deduped
        
        # Standardize events using canonical dictionary
        if 'key_events' in story:
            story['key_events'] = [
                standardize_event(event)
                for event in story['key_events']
            ]
            # Remove duplicates
            seen = set()
            story['key_events'] = [
                e for e in story['key_events']
                if not (e in seen or seen.add(e))
            ]
        
        # Standardize key_establishments (if present)
        if 'key_establishments' in story:
            story['key_establishments'] = [
                standardize_organization(est)
                for est in story['key_establishments']
            ]
            seen = set()
            story['key_establishments'] = [
                e for e in story['key_establishments']
                if not (e in seen or seen.add(e))
            ]
        
        standardized.append(story)
    
    return standardized


def print_statistics(people_mapping: dict, stories: list):
    """Print statistics about standardization."""
    print("\nSTANDARDIZATION STATISTICS")
    print("="*80)
    
    # Count unique entities after standardization
    unique_people = set(people_mapping.values())
    
    # Count unique organizations and events from canonical lists
    unique_orgs_from_data = set()
    unique_events_from_data = set()
    unique_inits_from_data = set()
    
    for story in stories:
        for org in story.get('key_organizations', []):
            unique_orgs_from_data.add(standardize_organization(org))
        for event in story.get('key_events', []):
            unique_events_from_data.add(standardize_event(event))
        for init in story.get('key_initiatives', []):
            unique_inits_from_data.add(init.strip())
    
    print(f"People: {len(unique_people)} unique person entries (name + role combinations)")
    print(f"Organizations: {len(unique_orgs_from_data)} unique organizations")
    print(f"Events: {len(unique_events_from_data)} unique events")
    print(f"Initiatives: {len(unique_inits_from_data)} unique initiatives")
    
    # Show examples of standardization
    print("\nEXAMPLES OF STANDARDIZATION:")
    
    # People examples
    print("\nPeople (showing standardized entries):")
    people_by_name = defaultdict(list)
    for entry in unique_people:
        name, _ = extract_name_and_title(entry)
        people_by_name[name].append(entry)
    
    count = 0
    for name, entries in sorted(people_by_name.items()):
        if count >= 10:
            break
        if len(entries) == 1:
            print(f"  {entries[0]}")
        else:
            print(f"  {name} (multiple roles):")
            for entry in sorted(entries)[:3]:
                print(f"    - {entry}")
        count += 1
    
    # Organizations examples
    print("\nOrganizations (canonical forms):")
    for i, org in enumerate(sorted(unique_orgs_from_data)[:15]):
        print(f"  {org}")
    
    # Events examples  
    print("\nEvents (canonical forms):")
    for i, event in enumerate(sorted(unique_events_from_data)[:15]):
        print(f"  {event}")


def main():
    input_path = Path(INPUT_FILE)
    output_path = Path(OUTPUT_FILE)
    
    print(f"Loading stories from {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        stories = json.load(f)
    print(f"Loaded {len(stories)} stories")
    
    print("\nBuilding person mappings with standardized titles...")
    people_mapping = build_person_canonical_map(stories)
    
    print(f"\nApplying standardization to {len(stories)} stories...")
    print("  - Standardizing people entries")
    print("  - Standardizing organizations (Town of X, X Town Commissioners, etc.)")
    print("  - Standardizing events (X Meeting format)")
    print("  - Deduplicating all metadata")
    
    standardized_stories = apply_standardization(stories, people_mapping)
    
    print_statistics(people_mapping, standardized_stories)
    
    print(f"\nSaving standardized stories to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(standardized_stories, f, indent=2, ensure_ascii=False)
    
    print("✅ Done!")


if __name__ == '__main__':
    main()
