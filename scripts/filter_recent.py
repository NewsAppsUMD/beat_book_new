import json
from datetime import datetime

def filter_recent_quotes(input_file, output_file, start_date='2025-04-01'):
    """Filter quotes to only include those from April 2025 forward"""
    
    print(f"Loading {input_file}...")
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    cutoff_date = start_date
    print(f"Filtering quotes from {cutoff_date} forward...")
    
    # Filter by_person
    filtered_by_person = {}
    for person, person_data in data['by_person'].items():
        filtered_quotes = [q for q in person_data['quotes'] if q['story_date'] >= cutoff_date]
        
        if filtered_quotes:
            # Recalculate summary
            direct_count = sum(1 for q in filtered_quotes if q['quote_type'] == 'direct')
            paraphrase_count = sum(1 for q in filtered_quotes if q['quote_type'] == 'paraphrase')
            
            topics = set(q['topic'] for q in filtered_quotes)
            counties = set()
            for q in filtered_quotes:
                counties.update(q['counties'])
            
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
    
    # Filter by_county
    filtered_by_county = {}
    for county, quotes in data['by_county'].items():
        filtered_quotes = [q for q in quotes if q['story_date'] >= cutoff_date]
        if filtered_quotes:
            filtered_by_county[county] = filtered_quotes
    
    # Filter by_topic
    filtered_by_topic = {}
    for topic, quotes in data['by_topic'].items():
        filtered_quotes = [q for q in quotes if q['story_date'] >= cutoff_date]
        if filtered_quotes:
            filtered_by_topic[topic] = filtered_quotes
    
    # Filter by_date
    filtered_by_date = {
        date: quotes 
        for date, quotes in data['by_date'].items() 
        if date >= cutoff_date
    }
    
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
            'date_filter': f'{cutoff_date} forward',
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
    print("DATE FILTERING COMPLETE")
    print("="*80)
    print(f"Date range: {cutoff_date} forward (April 2025 - present)")
    print(f"Original quotes: {original_quotes}")
    print(f"Filtered quotes: {total_quotes}")
    print(f"Removed: {original_quotes - total_quotes}")
    print(f"Retention rate: {(total_quotes / original_quotes * 100):.1f}%")
    print()
    print(f"Total speakers: {len(filtered_by_person)}")
    print(f"Total counties: {len(filtered_by_county)}")
    print(f"Total topics: {len(filtered_by_topic)}")
    print()
    
    if filtered_by_date:
        print(f"Date range in data: {min(filtered_by_date.keys())} to {max(filtered_by_date.keys())}")
    
    print()
    print("Quotes by topic:")
    for topic in sorted(filtered_by_topic.keys()):
        count = len(filtered_by_topic[topic])
        speakers = len(set(q['person'] for q in filtered_by_topic[topic]))
        print(f"  {topic}: {count} quotes from {speakers} speakers")
    
    print(f"\n✓ Saved to {output_file}")

if __name__ == '__main__':
    filter_recent_quotes('../master_quotes_for_llm.json', '../master_quotes_for_llm.json')
