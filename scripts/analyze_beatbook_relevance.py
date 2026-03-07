import json
from collections import Counter

def analyze_beatbook_relevance(input_file):
    """Analyze which quotes are relevant for ongoing beatbook vs one-time mentions"""
    
    print(f"Loading {input_file}...")
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Criteria for beatbook relevance:
    # HIGH: Multiple quotes, ongoing position (superintendent, board member, principal, director)
    # MEDIUM: Single quote but important position, or multiple quotes but less central role
    # LOW: One-time speaker, ceremonial mention, or quote about past event
    
    high_relevance = []
    medium_relevance = []
    low_relevance = []
    
    # Key positions for beatbook
    high_value_titles = ['superintendent', 'principal', 'board president', 'board member', 
                         'board chair', 'director', 'assistant superintendent']
    medium_value_titles = ['coordinator', 'teacher', 'specialist', 'supervisor', 
                          'delegate', 'senator', 'commissioner', 'council']
    
    for person, person_data in data['by_person'].items():
        title_lower = person.lower()
        quote_count = person_data['summary']['total_quotes']
        topics = person_data['summary']['topics_covered']
        
        # High relevance: Key position OR multiple substantive quotes
        is_key_position = any(title in title_lower for title in high_value_titles)
        has_multiple_quotes = quote_count >= 3
        covers_multiple_topics = len(topics) >= 2
        
        if is_key_position and has_multiple_quotes:
            high_relevance.append({
                'person': person,
                'quotes': quote_count,
                'topics': len(topics),
                'reason': 'Key position + multiple quotes'
            })
        elif is_key_position:
            high_relevance.append({
                'person': person,
                'quotes': quote_count,
                'topics': len(topics),
                'reason': 'Key position'
            })
        elif has_multiple_quotes and covers_multiple_topics:
            medium_relevance.append({
                'person': person,
                'quotes': quote_count,
                'topics': len(topics),
                'reason': 'Multiple quotes across topics'
            })
        elif any(title in title_lower for title in medium_value_titles):
            if quote_count >= 2:
                medium_relevance.append({
                    'person': person,
                    'quotes': quote_count,
                    'topics': len(topics),
                    'reason': 'Secondary position with quotes'
                })
            else:
                low_relevance.append({
                    'person': person,
                    'quotes': quote_count,
                    'topics': len(topics),
                    'reason': 'Secondary position, single quote'
                })
        else:
            low_relevance.append({
                'person': person,
                'quotes': quote_count,
                'topics': len(topics),
                'reason': 'One-time or unclear role'
            })
    
    # Calculate quote totals
    high_quotes = sum(data['by_person'][p['person']]['summary']['total_quotes'] for p in high_relevance)
    medium_quotes = sum(data['by_person'][p['person']]['summary']['total_quotes'] for p in medium_relevance)
    low_quotes = sum(data['by_person'][p['person']]['summary']['total_quotes'] for p in low_relevance)
    
    total_quotes = data['metadata']['filtered_total_quotes']
    
    # Print analysis
    print("\n" + "="*80)
    print("BEATBOOK RELEVANCE ANALYSIS")
    print("="*80)
    print()
    
    print("HIGH RELEVANCE (Key institutional sources - essential for beatbook)")
    print(f"  People: {len(high_relevance)}")
    print(f"  Quotes: {high_quotes} ({high_quotes/total_quotes*100:.1f}%)")
    print()
    
    print("MEDIUM RELEVANCE (Useful context but not core sources)")
    print(f"  People: {len(medium_relevance)}")
    print(f"  Quotes: {medium_quotes} ({medium_quotes/total_quotes*100:.1f}%)")
    print()
    
    print("LOW RELEVANCE (One-time mentions, less useful for beatbook)")
    print(f"  People: {len(low_relevance)}")
    print(f"  Quotes: {low_quotes} ({low_quotes/total_quotes*100:.1f}%)")
    print()
    
    print("="*80)
    print("HIGH RELEVANCE PEOPLE (Core beatbook sources)")
    print("="*80)
    for item in sorted(high_relevance, key=lambda x: x['quotes'], reverse=True)[:20]:
        print(f"{item['person']}")
        print(f"  {item['quotes']} quotes across {item['topics']} topics - {item['reason']}")
        print()
    
    if high_relevance:
        print("="*80)
        print(f"RECOMMENDATION: Focus beatbook on {len(high_relevance)} high-relevance people")
        print(f"These {len(high_relevance)} people account for {high_quotes} quotes ({high_quotes/total_quotes*100:.1f}%)")
        print("="*80)
    
    # Topic analysis for high-relevance people
    print("\n" + "="*80)
    print("WHAT HIGH-RELEVANCE PEOPLE TALK ABOUT")
    print("="*80)
    
    high_people_names = [p['person'] for p in high_relevance]
    topic_counter = Counter()
    
    for topic, quotes in data['by_topic'].items():
        count = sum(1 for q in quotes if q['person'] in high_people_names)
        if count > 0:
            topic_counter[topic] = count
    
    for topic, count in topic_counter.most_common():
        print(f"{topic}: {count} quotes")
    
    # Show some low relevance examples
    print("\n" + "="*80)
    print("LOW RELEVANCE EXAMPLES (Can probably exclude)")
    print("="*80)
    for item in sorted(low_relevance, key=lambda x: x['quotes'], reverse=True)[:10]:
        print(f"{item['person']}")
        print(f"  {item['quotes']} quotes - {item['reason']}")
        print()

if __name__ == '__main__':
    analyze_beatbook_relevance('../master_quotes_for_llm.json')
