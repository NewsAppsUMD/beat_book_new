import json
from collections import defaultdict

def restructure_for_llm(input_file, output_file):
    """Restructure quotes to be more usable for LLM beatbook generation"""
    
    print(f"Loading quotes from {input_file}...")
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Create multiple organizational structures
    restructured = {
        'metadata': data['metadata'],
        
        # 1. By person (most useful for beatbook - who said what across all topics)
        'by_person': {},
        
        # 2. By county (geographic organization)
        'by_county': {},
        
        # 3. By topic (current structure - keep for reference)
        'by_topic': {},
        
        # 4. Chronological (by date for timeline)
        'by_date': {},
        
        # 5. Person profiles (aggregated stats per person)
        'person_profiles': {}
    }
    
    # Process all quotes
    all_quotes = []
    person_stats = defaultdict(lambda: {
        'full_name_and_title': '',
        'total_quotes': 0,
        'direct_quotes': 0,
        'paraphrases': 0,
        'topics': set(),
        'counties': set(),
        'date_range': {'earliest': None, 'latest': None},
        'quotes': []
    })
    
    for topic, people in data['quotes_by_topic'].items():
        for person, person_data in people.items():
            for quote in person_data['quotes']:
                # Create enriched quote object
                enriched_quote = {
                    'person': person,
                    'quote_text': quote['quote'],
                    'quote_type': quote['type'],
                    'context': quote['context'],
                    'topic': topic,
                    'story_title': quote['story_title'],
                    'story_date': quote['story_date'],
                    'story_author': quote['story_author'],
                    'counties': quote['counties'],
                    'municipalities': quote['municipalities']
                }
                
                all_quotes.append(enriched_quote)
                
                # Update person stats
                person_stats[person]['full_name_and_title'] = person
                person_stats[person]['total_quotes'] += 1
                if quote['type'] == 'direct':
                    person_stats[person]['direct_quotes'] += 1
                else:
                    person_stats[person]['paraphrases'] += 1
                person_stats[person]['topics'].add(topic)
                person_stats[person]['counties'].update(quote['counties'])
                person_stats[person]['quotes'].append(enriched_quote)
                
                # Track date range
                if person_stats[person]['date_range']['earliest'] is None:
                    person_stats[person]['date_range']['earliest'] = quote['story_date']
                    person_stats[person]['date_range']['latest'] = quote['story_date']
                else:
                    if quote['story_date'] < person_stats[person]['date_range']['earliest']:
                        person_stats[person]['date_range']['earliest'] = quote['story_date']
                    if quote['story_date'] > person_stats[person]['date_range']['latest']:
                        person_stats[person]['date_range']['latest'] = quote['story_date']
    
    # 1. BY PERSON - Most useful for beatbook
    print("\nOrganizing by person...")
    for person, stats in person_stats.items():
        restructured['by_person'][person] = {
            'full_name_and_title': stats['full_name_and_title'],
            'summary': {
                'total_quotes': stats['total_quotes'],
                'direct_quotes': stats['direct_quotes'],
                'paraphrases': stats['paraphrases'],
                'topics_covered': sorted(list(stats['topics'])),
                'counties_covered': sorted(list(stats['counties'])),
                'date_range': stats['date_range']
            },
            'quotes': sorted(stats['quotes'], key=lambda x: x['story_date'], reverse=True)
        }
    
    # 2. BY COUNTY
    print("Organizing by county...")
    for quote in all_quotes:
        for county in quote['counties']:
            if county not in restructured['by_county']:
                restructured['by_county'][county] = []
            restructured['by_county'][county].append(quote)
    
    # Sort by date within each county
    for county in restructured['by_county']:
        restructured['by_county'][county] = sorted(
            restructured['by_county'][county], 
            key=lambda x: x['story_date'], 
            reverse=True
        )
    
    # 3. BY TOPIC - Keep original structure but flattened
    print("Organizing by topic...")
    for quote in all_quotes:
        topic = quote['topic']
        if topic not in restructured['by_topic']:
            restructured['by_topic'][topic] = []
        restructured['by_topic'][topic].append(quote)
    
    # 4. BY DATE - Chronological
    print("Organizing by date...")
    for quote in all_quotes:
        date = quote['story_date']
        if date not in restructured['by_date']:
            restructured['by_date'][date] = []
        restructured['by_date'][date].append(quote)
    
    # Sort dates
    restructured['by_date'] = dict(sorted(restructured['by_date'].items(), reverse=True))
    
    # 5. PERSON PROFILES - Summary view
    print("Creating person profiles...")
    for person, stats in person_stats.items():
        # Extract name and title
        name_parts = person.split('—')
        name = name_parts[0].strip() if len(name_parts) > 0 else person
        title = name_parts[1].strip() if len(name_parts) > 1 else 'Unknown'
        
        restructured['person_profiles'][person] = {
            'name': name,
            'title': title,
            'statistics': {
                'total_quotes': stats['total_quotes'],
                'direct_quotes': stats['direct_quotes'],
                'paraphrases': stats['paraphrases'],
                'topics_covered': sorted(list(stats['topics'])),
                'counties_covered': sorted(list(stats['counties'])),
                'date_range': stats['date_range']
            },
            'most_quoted_on': sorted(list(stats['topics']), 
                                     key=lambda t: sum(1 for q in stats['quotes'] if q['topic'] == t),
                                     reverse=True)[0] if stats['topics'] else None
        }
    
    # Save
    print(f"\nSaving restructured data to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(restructured, f, indent=2)
    
    # Print summary
    print("\n" + "="*80)
    print("RESTRUCTURING COMPLETE")
    print("="*80)
    print(f"Total quotes: {len(all_quotes)}")
    print(f"Total people: {len(person_stats)}")
    print(f"Total counties: {len(restructured['by_county'])}")
    print(f"Total topics: {len(restructured['by_topic'])}")
    print(f"Date range: {min(restructured['by_date'].keys())} to {max(restructured['by_date'].keys())}")
    print()
    print("New structure includes:")
    print("  • by_person: All quotes organized by speaker (best for beatbook)")
    print("  • by_county: All quotes organized by county")
    print("  • by_topic: All quotes organized by topic")
    print("  • by_date: All quotes in chronological order")
    print("  • person_profiles: Summary statistics for each person")
    print()
    print(f"✓ Saved to {output_file}")

if __name__ == '__main__':
    restructure_for_llm('../master_quotes_filtered.json', '../master_quotes_for_llm.json')
