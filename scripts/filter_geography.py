import json

# Our target counties
TARGET_COUNTIES = [
    'Caroline County',
    'Dorchester County', 
    'Kent County',
    'Queen Anne\'s County',
    'Talbot County'
]

# Normalize variations
def normalize_county(county_name):
    """Normalize county name variations"""
    normalized = county_name.strip()
    if not normalized.endswith('County'):
        normalized += ' County'
    return normalized

def filter_by_geography(input_file, output_file):
    """Filter quotes to only include our target counties"""
    
    print(f"Loading {input_file}...")
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    print(f"\nTarget counties: {', '.join(TARGET_COUNTIES)}")
    print("\nFiltering quotes by geography...")
    
    # Normalize target counties
    normalized_targets = [normalize_county(c) for c in TARGET_COUNTIES]
    
    def is_in_target_area(quote):
        """Check if quote is from our target counties"""
        for county in quote.get('counties', []):
            if normalize_county(county) in normalized_targets:
                return True
        return False
    
    # Filter by_person
    filtered_by_person = {}
    for person, person_data in data['by_person'].items():
        filtered_quotes = [q for q in person_data['quotes'] if is_in_target_area(q)]
        
        if filtered_quotes:
            # Recalculate summary
            direct_count = sum(1 for q in filtered_quotes if q['quote_type'] == 'direct')
            paraphrase_count = sum(1 for q in filtered_quotes if q['quote_type'] == 'paraphrase')
            
            topics = set(q['topic'] for q in filtered_quotes)
            counties = set()
            for q in filtered_quotes:
                for c in q['counties']:
                    if normalize_county(c) in normalized_targets:
                        counties.add(c)
            
            dates = [q['story_date'] for q in filtered_quotes]
            
            filtered_by_person[person] = {
                'full_name_and_title': person_data['full_name_and_title'],
                'summary': {
                    'total_quotes': len(filtered_quotes),
                    'direct_quotes': direct_count,
                    'paraphrases': paraphrase_count,
                    'topics_covered': sorted(list(topics)),
                    'counties_covered': sorted(list(counties)),
                    'date_range': {
                        'earliest': min(dates),
                        'latest': max(dates)
                    }
                },
                'quotes': filtered_quotes
            }
    
    # Filter by_county - only include target counties
    filtered_by_county = {}
    for county, quotes in data['by_county'].items():
        if normalize_county(county) in normalized_targets:
            filtered_quotes = [q for q in quotes if is_in_target_area(q)]
            if filtered_quotes:
                filtered_by_county[county] = filtered_quotes
    
    # Filter by_topic
    filtered_by_topic = {}
    for topic, quotes in data['by_topic'].items():
        filtered_quotes = [q for q in quotes if is_in_target_area(q)]
        if filtered_quotes:
            filtered_by_topic[topic] = filtered_quotes
    
    # Filter by_date
    filtered_by_date = {}
    for date, quotes in data['by_date'].items():
        filtered_quotes = [q for q in quotes if is_in_target_area(q)]
        if filtered_quotes:
            filtered_by_date[date] = filtered_quotes
    
    # Filter person_profiles
    filtered_person_profiles = {}
    for person, profile in data['person_profiles'].items():
        if person in filtered_by_person:
            person_data = filtered_by_person[person]
            
            # Find most quoted topic
            topic_counts = {}
            for quote in person_data['quotes']:
                topic = quote['topic']
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
            
            most_quoted_on = max(topic_counts.items(), key=lambda x: x[1])[0] if topic_counts else None
            
            filtered_person_profiles[person] = {
                'name': profile['name'],
                'title': profile['title'],
                'statistics': person_data['summary'],
                'most_quoted_on': most_quoted_on
            }
    
    # Calculate total quotes
    total_quotes = sum(len(p['quotes']) for p in filtered_by_person.values())
    
    # Build new structure
    filtered_data = {
        'metadata': {
            'total_stories': data['metadata']['total_stories'],
            'stories_with_quotes': data['metadata']['stories_with_quotes'],
            'original_total_quotes': data['metadata']['original_total_quotes'],
            'filtered_total_quotes': total_quotes,
            'date_filter': data['metadata'].get('date_filter', 'N/A'),
            'geography_filter': f'{len(TARGET_COUNTIES)} counties: {", ".join(TARGET_COUNTIES)}',
            'topics_covered': len(filtered_by_topic),
            'total_speakers': len(filtered_by_person)
        },
        'by_person': filtered_by_person,
        'by_county': filtered_by_county,
        'by_topic': filtered_by_topic,
        'by_date': filtered_by_date,
        'person_profiles': filtered_person_profiles
    }
    
    print(f"\nSaving to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(filtered_data, f, indent=2)
    
    # Print summary
    original_quotes = data['metadata']['filtered_total_quotes']
    print("\n" + "="*80)
    print("GEOGRAPHY FILTERING COMPLETE")
    print("="*80)
    print(f"Target counties: {len(TARGET_COUNTIES)}")
    for county in TARGET_COUNTIES:
        print(f"  • {county}")
    print()
    print(f"Original quotes: {original_quotes}")
    print(f"Filtered quotes: {total_quotes}")
    print(f"Removed: {original_quotes - total_quotes}")
    print(f"Retention rate: {(total_quotes / original_quotes * 100):.1f}%")
    print()
    print(f"Total speakers: {len(filtered_by_person)}")
    print(f"Total counties represented: {len(filtered_by_county)}")
    print(f"Total topics: {len(filtered_by_topic)}")
    print()
    
    print("Quotes by county:")
    for county in sorted(filtered_by_county.keys()):
        count = len(filtered_by_county[county])
        speakers = len(set(q['person'] for q in filtered_by_county[county]))
        print(f"  {county}: {count} quotes from {speakers} speakers")
    
    print()
    print("Quotes by topic:")
    for topic in sorted(filtered_by_topic.keys()):
        count = len(filtered_by_topic[topic])
        speakers = len(set(q['person'] for q in filtered_by_topic[topic]))
        print(f"  {topic}: {count} quotes from {speakers} speakers")
    
    print(f"\n✓ Saved to {output_file}")

if __name__ == '__main__':
    filter_by_geography('../master_quotes_for_llm.json', '../master_quotes_for_llm.json')
