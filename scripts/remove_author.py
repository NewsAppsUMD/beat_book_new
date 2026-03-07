import json

def remove_story_author(input_file, output_file):
    """Remove story_author field from all quotes"""
    
    print(f"Loading {input_file}...")
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Remove story_author from by_person
    for person in data['by_person'].values():
        for quote in person['quotes']:
            if 'story_author' in quote:
                del quote['story_author']
    
    # Remove story_author from by_county
    for county_quotes in data['by_county'].values():
        for quote in county_quotes:
            if 'story_author' in quote:
                del quote['story_author']
    
    # Remove story_author from by_topic
    for topic_quotes in data['by_topic'].values():
        for quote in topic_quotes:
            if 'story_author' in quote:
                del quote['story_author']
    
    # Remove story_author from by_date
    for date_quotes in data['by_date'].values():
        for quote in date_quotes:
            if 'story_author' in quote:
                del quote['story_author']
    
    print(f"Saving to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✓ Removed story_author field from all quotes")

if __name__ == '__main__':
    remove_story_author('../master_quotes_for_llm.json', '../master_quotes_for_llm.json')
