import json
from collections import defaultdict

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

def analyze_quotes(quotes_file):
    """Analyze the relevance of quoted people"""
    
    with open(quotes_file, 'r') as f:
        data = json.load(f)
    
    # Statistics
    stats = {
        'highly_relevant': {'people': [], 'quote_count': 0, 'direct_quotes': 0, 'paraphrases': 0},
        'moderately_relevant': {'people': [], 'quote_count': 0, 'direct_quotes': 0, 'paraphrases': 0},
        'not_relevant': {'people': [], 'quote_count': 0, 'direct_quotes': 0, 'paraphrases': 0},
        'unknown': {'people': [], 'quote_count': 0, 'direct_quotes': 0, 'paraphrases': 0}
    }
    
    # Track by topic
    topic_stats = defaultdict(lambda: {
        'highly_relevant': 0,
        'moderately_relevant': 0,
        'not_relevant': 0,
        'unknown': 0
    })
    
    # Analyze each person
    for topic, people in data['quotes_by_topic'].items():
        for person, person_data in people.items():
            category = categorize_person(person)
            quote_count = len(person_data['quotes'])
            
            # Count direct vs paraphrase
            direct_count = sum(1 for q in person_data['quotes'] if q['type'] == 'direct')
            paraphrase_count = sum(1 for q in person_data['quotes'] if q['type'] == 'paraphrase')
            
            stats[category]['people'].append({
                'name': person,
                'topic': topic,
                'quotes': quote_count,
                'direct': direct_count,
                'paraphrases': paraphrase_count
            })
            stats[category]['quote_count'] += quote_count
            stats[category]['direct_quotes'] += direct_count
            stats[category]['paraphrases'] += paraphrase_count
            
            topic_stats[topic][category] += quote_count
    
    # Print summary
    print("="*80)
    print("QUOTE RELEVANCE ANALYSIS")
    print("="*80)
    print()
    
    total_quotes = data['metadata']['total_quotes_extracted']
    
    for category in ['highly_relevant', 'moderately_relevant', 'not_relevant', 'unknown']:
        people_count = len(stats[category]['people'])
        quote_count = stats[category]['quote_count']
        direct = stats[category]['direct_quotes']
        paraphrases = stats[category]['paraphrases']
        percentage = (quote_count / total_quotes * 100) if total_quotes > 0 else 0
        
        label = category.replace('_', ' ').title()
        print(f"{label}:")
        print(f"  People: {people_count}")
        print(f"  Total Quotes: {quote_count} ({percentage:.1f}%)")
        print(f"  Direct Quotes: {direct}")
        print(f"  Paraphrases: {paraphrases}")
        print()
    
    # Show top quoted people in each category
    print("="*80)
    print("TOP 10 HIGHLY RELEVANT PEOPLE")
    print("="*80)
    highly_relevant_sorted = sorted(stats['highly_relevant']['people'], 
                                    key=lambda x: x['quotes'], reverse=True)[:10]
    for i, person in enumerate(highly_relevant_sorted, 1):
        print(f"{i}. {person['name']}")
        print(f"   {person['quotes']} quotes ({person['direct']} direct, {person['paraphrases']} paraphrases)")
        print(f"   Topic: {person['topic']}")
        print()
    
    print("="*80)
    print("TOP 10 NOT RELEVANT PEOPLE (TO REVIEW)")
    print("="*80)
    not_relevant_sorted = sorted(stats['not_relevant']['people'], 
                                 key=lambda x: x['quotes'], reverse=True)[:10]
    for i, person in enumerate(not_relevant_sorted, 1):
        print(f"{i}. {person['name']}")
        print(f"   {person['quotes']} quotes ({person['direct']} direct, {person['paraphrases']} paraphrases)")
        print(f"   Topic: {person['topic']}")
        print()
    
    # Topic breakdown
    print("="*80)
    print("RELEVANCE BY TOPIC")
    print("="*80)
    for topic in sorted(topic_stats.keys()):
        print(f"\n{topic}:")
        total_topic = sum(topic_stats[topic].values())
        for category in ['highly_relevant', 'moderately_relevant', 'not_relevant', 'unknown']:
            count = topic_stats[topic][category]
            pct = (count / total_topic * 100) if total_topic > 0 else 0
            label = category.replace('_', ' ').title()
            print(f"  {label}: {count} quotes ({pct:.1f}%)")

if __name__ == '__main__':
    analyze_quotes('../master_quotes.json')
