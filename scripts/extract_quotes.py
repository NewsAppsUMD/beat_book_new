import json
import re
from collections import defaultdict

def get_context_around_position(text, start_pos, end_pos, context_sentences=2):
    """Get surrounding context for a quote"""
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Find which sentence contains our quote
    current_pos = 0
    quote_sentence_idx = -1
    
    for i, sentence in enumerate(sentences):
        sentence_end = current_pos + len(sentence)
        if current_pos <= start_pos <= sentence_end:
            quote_sentence_idx = i
            break
        current_pos = sentence_end + 1
    
    if quote_sentence_idx == -1:
        return ""
    
    # Get context sentences before and after
    start_idx = max(0, quote_sentence_idx - context_sentences)
    end_idx = min(len(sentences), quote_sentence_idx + context_sentences + 1)
    
    context = ' '.join(sentences[start_idx:end_idx])
    return context.strip()

def extract_quotes_from_text(text, person_name):
    """Extract all quotes and paraphrases attributed to a specific person from text"""
    quotes = []
    
    # Clean up the name for matching (remove title, just get name parts)
    name_parts = person_name.split('\u2014')[0].strip().split()
    last_name = name_parts[-1]
    full_name = person_name.split('\u2014')[0].strip()
    
    # Direct quote patterns
    quote_patterns = [
        # Direct quotes with said/says
        (rf'(["\u201c])([^"\u201d]+)["\u201d],?\s*(?:said|says|told|added|noted|explained|emphasized|asked|pointed out)\s+{re.escape(last_name)}', 'direct'),
        (rf'{re.escape(last_name)}\s+(?:said|says|told|added|noted|explained|emphasized|asked|pointed out)[^"\u201c]*(["\u201c])([^"\u201d]+)["\u201d]', 'direct'),
        (rf'(["\u201c])([^"\u201d]+)["\u201d],?\s*(?:said|says|told|added|noted|explained|emphasized|asked|pointed out)\s+{re.escape(full_name)}', 'direct'),
        (rf'{re.escape(full_name)}\s+(?:said|says|told|added|noted|explained|emphasized|asked|pointed out)[^"\u201c]*(["\u201c])([^"\u201d]+)["\u201d]', 'direct'),
    ]
    
    # Paraphrase patterns (no quotes, but attribution)
    paraphrase_patterns = [
        (rf'{re.escape(last_name)}\s+(?:said|explained|noted|emphasized|pointed out|argued|believes|thinks|wants|hopes|stressed)\s+(?:that\s+)?([^.!?]+[.!?])', 'paraphrase'),
        (rf'{re.escape(full_name)}\s+(?:said|explained|noted|emphasized|pointed out|argued|believes|thinks|wants|hopes|stressed)\s+(?:that\s+)?([^.!?]+[.!?])', 'paraphrase'),
        (rf'(?:According to|Per)\s+{re.escape(last_name)},?\s+([^.!?]+[.!?])', 'paraphrase'),
        (rf'(?:According to|Per)\s+{re.escape(full_name)},?\s+([^.!?]+[.!?])', 'paraphrase'),
    ]
    
    all_patterns = quote_patterns + paraphrase_patterns
    
    for pattern, quote_type in all_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            # Get the quote/paraphrase text (it's in group 2 for quotes, group 1 for paraphrases)
            if quote_type == 'direct':
                quote_text = match.group(2).strip()
            else:
                quote_text = match.group(1).strip()
            
            if quote_text and len(quote_text) > 10:  # Ignore very short quotes
                # Get surrounding context
                context = get_context_around_position(text, match.start(), match.end(), context_sentences=1)
                
                quotes.append({
                    'text': quote_text,
                    'type': quote_type,
                    'context': context
                })
    
    return quotes

def categorize_education_story(story):
    """Categorize education story into subtopics based on content"""
    title = story.get('title', '').lower()
    content = story.get('content', '').lower()
    combined = title + ' ' + content
    
    # Define topic keywords
    topics = {
        'School Board & Governance': ['board', 'superintendent', 'board meeting', 'board member', 'policy', 'vote', 'resolution'],
        'Student Achievement & Testing': ['test', 'score', 'achievement', 'assessment', 'graduation', 'performance', 'proficiency', 'grade'],
        'Budget & Funding': ['budget', 'funding', 'million', 'dollar', 'finance', 'revenue', 'expenditure', 'cost'],
        'Staff & Employment': ['teacher', 'staff', 'hire', 'hiring', 'employee', 'salary', 'contract', 'union'],
        'Facilities & Infrastructure': ['building', 'construction', 'facility', 'renovation', 'school building', 'campus', 'maintenance'],
        'Student Programs & Services': ['program', 'service', 'special education', 'athletics', 'sports', 'activity', 'club'],
        'Safety & Security': ['safety', 'security', 'lockdown', 'incident', 'threat', 'police'],
        'Enrollment & Demographics': ['enrollment', 'student', 'population', 'demographic', 'attendance'],
        'Community Relations': ['parent', 'community', 'public', 'family', 'partnership'],
    }
    
    # Count keyword matches
    topic_scores = {}
    for topic, keywords in topics.items():
        score = sum(1 for keyword in keywords if keyword in combined)
        if score > 0:
            topic_scores[topic] = score
    
    # Return topic with highest score, or 'General Education' if no match
    if topic_scores:
        return max(topic_scores.items(), key=lambda x: x[1])[0]
    return 'General Education'

def extract_all_quotes(stories_file, output_file):
    """Extract quotes from all key people and organize by topic"""
    
    print(f"Loading stories from {stories_file}...")
    with open(stories_file, 'r') as f:
        stories = json.load(f)
    
    # Organize quotes by topic and person
    quotes_by_topic = defaultdict(lambda: defaultdict(list))
    
    total_stories = len(stories)
    stories_with_quotes = 0
    total_quotes_found = 0
    
    for i, story in enumerate(stories, 1):
        if i % 50 == 0:
            print(f"Processing story {i}/{total_stories}...")
        
        # Categorize into education subtopic
        topic = categorize_education_story(story)
        
        content = story.get('content', '')
        key_people = story.get('key_people', [])
        
        if not key_people:
            continue
        
        story_had_quotes = False
        
        for person in key_people:
            # Extract quotes for this person
            quote_objects = extract_quotes_from_text(content, person)
            
            if quote_objects:
                story_had_quotes = True
                total_quotes_found += len(quote_objects)
                
                # Store each quote with metadata
                for quote_obj in quote_objects:
                    quotes_by_topic[topic][person].append({
                        'quote': quote_obj['text'],
                        'type': quote_obj['type'],  # 'direct' or 'paraphrase'
                        'context': quote_obj['context'],
                        'story_title': story.get('title'),
                        'story_date': story.get('date'),
                        'story_author': story.get('author'),
                        'counties': story.get('counties', []),
                        'municipalities': story.get('municipalities', [])
                    })
        
        if story_had_quotes:
            stories_with_quotes += 1
    
    # Convert to regular dict for JSON serialization
    output_data = {
        'metadata': {
            'total_stories': total_stories,
            'stories_with_quotes': stories_with_quotes,
            'total_quotes_extracted': total_quotes_found,
            'topics_covered': len(quotes_by_topic),
            'total_speakers': sum(len(people) for people in quotes_by_topic.values())
        },
        'quotes_by_topic': {}
    }
    
    for topic in sorted(quotes_by_topic.keys()):
        output_data['quotes_by_topic'][topic] = {}
        
        for person in sorted(quotes_by_topic[topic].keys()):
            quotes_list = quotes_by_topic[topic][person]
            
            output_data['quotes_by_topic'][topic][person] = {
                'full_name_and_title': person,
                'quote_count': len(quotes_list),
                'quotes': quotes_list
            }
    
    # Save to file
    print(f"\nSaving quotes to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    # Print summary
    print("\n" + "="*80)
    print("EXTRACTION COMPLETE")
    print("="*80)
    print(f"Total stories processed: {total_stories}")
    print(f"Stories with quotes found: {stories_with_quotes}")
    print(f"Total quotes extracted: {total_quotes_found}")
    print(f"Topics covered: {len(quotes_by_topic)}")
    print(f"Unique speakers: {output_data['metadata']['total_speakers']}")
    print("\nQuotes by topic:")
    for topic, people in output_data['quotes_by_topic'].items():
        quote_count = sum(p['quote_count'] for p in people.values())
        print(f"  {topic}: {quote_count} quotes from {len(people)} speakers")
    print(f"\n✓ Saved to {output_file}")

if __name__ == "__main__":
    stories_file = "../refined_beatbook_stories.json"
    output_file = "../master_quotes.json"
    
    extract_all_quotes(stories_file, output_file)
