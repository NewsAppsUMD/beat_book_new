import json
import subprocess
import sys
from pathlib import Path

def get_top_people(quotes_file, min_quotes=5):
    """Get people with at least min_quotes quotes"""
    
    with open(quotes_file, 'r') as f:
        data = json.load(f)
    
    # Get people sorted by quote count
    people = []
    for person, profile in data['person_profiles'].items():
        if profile['statistics']['total_quotes'] >= min_quotes:
            people.append({
                'person': person,
                'name': profile['name'],
                'title': profile['title'],
                'quote_count': profile['statistics']['total_quotes'],
                'direct_quotes': profile['statistics']['direct_quotes'],
                'paraphrases': profile['statistics']['paraphrases'],
                'topics': profile['statistics']['topics_covered'],
                'counties': profile['statistics']['counties_covered'],
                'date_range': profile['statistics']['date_range'],
                'quotes': data['by_person'][person]['quotes']
            })
    
    return sorted(people, key=lambda x: x['quote_count'], reverse=True)

def create_beatbook_summary(person_data):
    """Create a beatbook summary for a person using Groq LLM"""
    
    # Prepare the prompt
    name = person_data['name']
    title = person_data['title']
    quote_count = person_data['quote_count']
    topics = ', '.join(person_data['topics'])
    counties = ', '.join(person_data['counties'])
    
    # Get sample quotes (limit to avoid token limits)
    sample_quotes = person_data['quotes'][:15]  # First 15 quotes
    
    quotes_text = "\n\n".join([
        f"QUOTE #{i+1}\n"
        f"Date: {q['story_date']}\n"
        f"Topic: {q['topic']}\n"
        f"Story: {q['story_title']}\n"
        f"Quote Type: {q['quote_type']}\n"
        f"Quote: \"{q['quote_text']}\"\n"
        f"Context: {q['context']}"
        for i, q in enumerate(sample_quotes)
    ])
    
    prompt = f"""You are creating a beatbook profile for an education reporter covering Maryland's Eastern Shore counties. This profile helps the reporter understand a key source's positions on critical education issues.

SOURCE INFORMATION:
NAME: {name}
TITLE: {title}
COVERAGE PERIOD: {person_data['date_range']['earliest']} to {person_data['date_range']['latest']}
QUOTE COUNT: {quote_count} quotes ({person_data['direct_quotes']} direct, {person_data['paraphrases']} paraphrases)
TOPICS: {topics}
COUNTIES: {counties}

ACTUAL QUOTES WITH FULL CONTEXT FROM COVERAGE:
{quotes_text}

NOTE: Each quote includes the story title and surrounding context. Use these to understand what's actually happening - don't invent details beyond what's in these stories.

Create a 2-3 paragraph beatbook profile focused on KEY EDUCATION ISSUES:

PARAGRAPH 1 - OVERVIEW & ROLE:
- Brief explanation of their role in education decisions
- What authority/influence they have (board votes, budget decisions, policy implementation, etc.)
- Geographic scope of their work

PARAGRAPH 2 - POSITIONS ON KEY ISSUES (use only evidence from quotes above):
Analyze their stances on:
- **Budget/Funding**: Do they support spending increases or restraint? What do they prioritize?
- **Facilities/Construction**: What projects do they support? Any concerns about costs/timing?
- **Staffing**: Positions on teacher pay, hiring, working conditions?
- **Student Issues**: What do they say about achievement, discipline, equity, programs?
- **State vs Local**: How do they view state mandates, Blueprint requirements, local control?

PARAGRAPH 3 - PATTERNS & RELIABILITY:
- How do they vote or make decisions (if applicable)?
- What are their consistent priorities?
- Are they a reliable source for certain topics?
- Any notable advocacy or opposition patterns?

CRITICAL RULES - STICK TO THE FACTS:
1. READ THE STORY TITLES AND CONTEXT CAREFULLY - they tell you what's actually happening
2. USE ONLY information from the quotes, story titles, and context provided above
3. When mentioning a school, building, or project, use the EXACT name from the story title or context
4. DO NOT invent any details not explicitly stated
5. DO NOT combine or conflate different stories/quotes
6. If a story title mentions a specific school/project, you can reference that
7. If insufficient information on a topic, write "The available quotes don't address [topic]"
8. Put actual quotes in quotation marks

EXAMPLES:
If Story Title = "Chapel District Elementary Renovation Design Plans Move to State"
✅ You can say: "involved in the Chapel District Elementary renovation"
✅ You can quote: "noted 'slight hesitations about privacy'"
❌ Don't invent: "East Harbor School" or other schools not in the titles

If quotes don't mention teacher salaries at all:
✅ "The available quotes don't address teacher compensation"
❌ Don't invent: "supports 5% salary increases"

Base everything on the story titles, contexts, and quotes provided. Be factual for a working journalist."""

    try:
        # Call llm with groq model
        result = subprocess.run(
            ['llm', '-m', 'groq/openai/gpt-oss-120b', prompt],
            capture_output=True,
            text=True,
            check=True,
            timeout=120
        )
        
        return result.stdout.strip()
    
    except subprocess.CalledProcessError as e:
        print(f"Error calling LLM: {e}", file=sys.stderr)
        print(f"stderr: {e.stderr}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("Error: 'llm' command not found. Make sure it's installed.", file=sys.stderr)
        return None

def main():
    quotes_file = '../master_quotes_for_llm.json'
    output_file = '../beatbook_profiles.json'
    
    print("Loading quotes data...")
    top_people = get_top_people(quotes_file, min_quotes=5)
    
    print(f"\nFound {len(top_people)} people with 5+ quotes")
    print(f"Generating beatbook profiles using Groq LLM (groq/openai/gpt-oss-120b)...\n")
    
    profiles = []
    
    # Check if we have partial results to resume from
    if Path(output_file).exists():
        print(f"Found existing {output_file}, loading progress...")
        with open(output_file, 'r') as f:
            existing_data = json.load(f)
            profiles = existing_data.get('profiles', [])
        print(f"Resuming from profile {len(profiles) + 1}\n")
    
    for i, person_data in enumerate(top_people, 1):
        name = person_data['name']
        quote_count = person_data['quote_count']
        
        # Skip if already processed
        if any(p['name'] == name for p in profiles):
            print(f"[{i}/{len(top_people)}] Skipping {name} (already processed)")
            continue
        
        print(f"[{i}/{len(top_people)}] Generating profile for {name} ({quote_count} quotes)...")
        
        summary = create_beatbook_summary(person_data)
        
        if summary:
            profiles.append({
                'name': name,
                'title': person_data['title'],
                'quote_count': quote_count,
                'direct_quotes': person_data['direct_quotes'],
                'paraphrases': person_data['paraphrases'],
                'topics': person_data['topics'],
                'counties': person_data['counties'],
                'date_range': person_data['date_range'],
                'beatbook_summary': summary
            })
            print(f"✓ Generated ({len(summary)} chars)")
            
            # Save progress after each successful generation
            with open(output_file, 'w') as f:
                json.dump({
                    'metadata': {
                        'total_profiles': len(profiles),
                        'generated_date': '2025-12-07',
                        'model': 'groq/openai/gpt-oss-120b'
                    },
                    'profiles': profiles
                }, f, indent=2)
        else:
            print(f"✗ Failed to generate summary")
        
        print()
    
    # Save profiles
    print(f"Saving {len(profiles)} profiles to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump({
            'metadata': {
                'total_profiles': len(profiles),
                'generated_date': '2025-12-07',
                'model': 'groq/llama-3.3-70b-versatile'
            },
            'profiles': profiles
        }, f, indent=2)
    
    print("\n" + "="*80)
    print("BEATBOOK PROFILES GENERATED")
    print("="*80)
    print(f"Total profiles: {len(profiles)}")
    print(f"Saved to: {output_file}")
    print("="*80)

if __name__ == '__main__':
    main()
