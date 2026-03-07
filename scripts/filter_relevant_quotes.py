import json

# Define relevant titles/roles
HIGHLY_RELEVANT = [
    'superintendent', 'principal', 'board member', 'board president', 'board chair',
    'school board', 'director', 'teacher', 'assistant superintendent', 'ceo',
    'president', 'vice president', 'secretary', 'treasurer'
]

MODERATELY_RELEVANT = [
    'coordinator', 'specialist', 'manager', 'supervisor', 'staff', 'employee',
    'parent', 'student', 'delegate', 'senator', 'commissioner', 'council',
    'mayor', 'official'
]

NOT_RELEVANT = [
    'architect', 'contractor', 'consultant', 'vendor', 'project manager',
    'engineer', 'designer', 'attorney', 'lawyer'
]

def categorize_person(full_name_and_title):
    """Categorize a person by their title/role"""
    title_lower = full_name_and_title.lower()
    
    for keyword in HIGHLY_RELEVANT:
        if keyword in title_lower:
            return 'highly_relevant'
    
    for keyword in MODERATELY_RELEVANT:
        if keyword in title_lower:
            return 'moderately_relevant'
    
    for keyword in NOT_RELEVANT:
        if keyword in title_lower:
            return 'not_relevant'
    
    # If no title info, check if there's a dash (indicating a title was provided)
    if '—' not in full_name_and_title:
        return 'unknown'
    
    return 'unknown'

def filter_quotes(input_file, output_file):
    """Filter quotes to only include highly and moderately relevant people"""
    
    print(f"Loading quotes from {input_file}...")
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Create new structure
    filtered_data = {
        'metadata': {
            'total_stories': data['metadata']['total_stories'],
            'stories_with_quotes': data['metadata']['stories_with_quotes'],
            'original_total_quotes': data['metadata']['total_quotes_extracted'],
            'filtered_total_quotes': 0,
            'topics_covered': 0,
            'total_speakers': 0
        },
        'quotes_by_topic': {}
    }
    
    total_quotes = 0
    total_speakers = 0
    
    # Filter each topic
    for topic, people in data['quotes_by_topic'].items():
        filtered_people = {}
        
        for person, person_data in people.items():
            category = categorize_person(person)
            
            # Only keep highly and moderately relevant
            if category in ['highly_relevant', 'moderately_relevant']:
                filtered_people[person] = person_data
                total_quotes += len(person_data['quotes'])
                total_speakers += 1
        
        # Only add topic if it has people
        if filtered_people:
            filtered_data['quotes_by_topic'][topic] = filtered_people
    
    # Update metadata
    filtered_data['metadata']['filtered_total_quotes'] = total_quotes
    filtered_data['metadata']['total_speakers'] = total_speakers
    filtered_data['metadata']['topics_covered'] = len(filtered_data['quotes_by_topic'])
    
    # Save filtered data
    print(f"\nSaving filtered quotes to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(filtered_data, f, indent=2)
    
    # Print summary
    print("\n" + "="*80)
    print("FILTERING COMPLETE")
    print("="*80)
    print(f"Original quotes: {data['metadata']['total_quotes_extracted']}")
    print(f"Filtered quotes: {total_quotes}")
    print(f"Removed: {data['metadata']['total_quotes_extracted'] - total_quotes}")
    print(f"Retention rate: {(total_quotes / data['metadata']['total_quotes_extracted'] * 100):.1f}%")
    print()
    print(f"Original speakers: {data['metadata']['total_speakers']}")
    print(f"Filtered speakers: {total_speakers}")
    print(f"Removed: {data['metadata']['total_speakers'] - total_speakers}")
    print()
    print(f"Topics covered: {len(filtered_data['quotes_by_topic'])}")
    print()
    
    # Print by topic
    print("Quotes by topic:")
    for topic in sorted(filtered_data['quotes_by_topic'].keys()):
        topic_quotes = sum(len(p['quotes']) for p in filtered_data['quotes_by_topic'][topic].values())
        topic_speakers = len(filtered_data['quotes_by_topic'][topic])
        print(f"  {topic}: {topic_quotes} quotes from {topic_speakers} speakers")
    
    print(f"\n✓ Saved to {output_file}")

if __name__ == '__main__':
    filter_quotes('../master_quotes.json', '../master_quotes_filtered.json')
