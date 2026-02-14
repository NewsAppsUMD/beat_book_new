# How to Create a Beat Book Using AI
*A step-by-step guide for journalists who want to turn news stories into a practical reference guide*

---

## What is a Beat Book?

A **beat book** is like a cheat sheet for your reporting area. It tells you:
- What topics you usually cover
- Who the key people are
- Which organizations matter most
- Where stories typically happen
- What angles you might have missed

Think of it as the document you'd create to bring a new reporter up to speed on your beat in one afternoon instead of one month.

**Why make one?**
- Get organized quickly when starting a new beat
- Spot patterns and gaps in your coverage
- Keep track of important contacts and background information
- Share knowledge with colleagues

---

## Overview: The 5 Main Steps

```
1. Collect your stories
         ↓
2. Extract who, what, and where
         ↓
3. Count what appears most often
         ↓
4. Ask an AI to write the beat book
         ↓
5. Check and polish the final version
```

Each step has simple commands you can copy and paste - no programming knowledge required.

---

## Step 1: Collect Your Stories

**What you need:** A file with all your news articles in one place.

### Getting Your Stories

You have a few options:

**Option A: Export from your newsroom's CMS**
Most content management systems let you export articles as a CSV or JSON file. Ask your data team for help if needed.

**Option B: Use Datasette**
If your newsroom uses Datasette, click "Export → JSON" on your stories table.

**Option C: Manual collection**
For a small number of stories, create a simple spreadsheet with these columns:
- `title` - The headline
- `content` - The full article text
- `date` - Publication date
- `url` - Link to the story

Save it as a CSV, then convert to JSON using this command:
```bash
uv run python -m csvkit.utilities.csvjson your_stories.csv > stories.json
```

### What the file should look like

```json
[
  {
    "title": "Police arrest suspect in downtown robbery",
    "content": "EASTON — Police arrested a suspect Monday...",
    "date": "2024-09-28",
    "url": "https://example.com/story1"
  },
  {
    "title": "Fire department rescues family from flooded home",
    "content": "ST. MICHAELS — Firefighters worked through...",
    "date": "2024-10-03",
    "url": "https://example.com/story2"
  }
]
```

**Save this file as `source_stories.json` in a folder on your computer.**

---

## Step 2: Extract People, Places, and Organizations

This step identifies all the important names, locations, and groups mentioned in your stories.

### Create the extraction script

Copy this code and save it as `extract_entities.py`:

```python
#!/usr/bin/env python3
import json
import subprocess
import sys

def extract_entities(story):
    """Send one story to the AI and get back people, places, organizations"""
    prompt = f"""Extract all people, places, and organizations from this news article.
Return ONLY a JSON object with three arrays: "people", "places", "organizations".
Include full names and titles when available.

Title: {story['title']}
Content: {story['content'][:2000]}

Return only valid JSON, no other text."""

    result = subprocess.run(
        ['uv', 'run', 'llm', '-m', 'groq/llama-3.3-70b-versatile'],
        input=prompt,
        text=True,
        capture_output=True
    )
    
    try:
        # Parse the AI's response
        entities = json.loads(result.stdout.strip())
        return entities
    except:
        # If AI returns bad format, return empty lists
        return {"people": [], "places": [], "organizations": []}

# Read your stories
with open('source_stories.json', 'r') as f:
    stories = json.load(f)

enriched_stories = []

for i, story in enumerate(stories):
    print(f"Processing story {i+1}/{len(stories)}: {story['title'][:50]}...")
    
    # Get entities from AI
    entities = extract_entities(story)
    
    # Add entities to the story
    story['people'] = entities.get('people', [])
    story['places'] = entities.get('places', [])
    story['organizations'] = entities.get('organizations', [])
    
    enriched_stories.append(story)

# Save enriched stories
with open('stories_with_entities.json', 'w') as f:
    json.dump(enriched_stories, f, indent=2)

print(f"\n✓ Done! Processed {len(enriched_stories)} stories")
print(f"Results saved to: stories_with_entities.json")
```

### Run the extraction

```bash
python extract_entities.py
```

This will process each story and create a new file called `stories_with_entities.json` that includes the extracted information.

**Note:** This might take a few minutes depending on how many stories you have. The AI processes them one at a time.

---

## Step 3: Count What Matters Most

Now you'll count which people, places, and organizations appear most frequently. These become the "key players" in your beat book.

### Create the counting script

Save this as `count_entities.py`:

```python
#!/usr/bin/env python3
import json
from collections import Counter

# Read the enriched stories
with open('stories_with_entities.json', 'r') as f:
    stories = json.load(f)

# Count entities
people_count = Counter()
places_count = Counter()
orgs_count = Counter()

for story in stories:
    # Count each entity
    people_count.update(story.get('people', []))
    places_count.update(story.get('places', []))
    orgs_count.update(story.get('organizations', []))

# Keep only entities mentioned 3+ times
threshold = 3

top_people = {name: count for name, count in people_count.items() if count >= threshold}
top_places = {name: count for name, count in places_count.items() if count >= threshold}
top_orgs = {name: count for name, count in orgs_count.items() if count >= threshold}

# Create summary
summary = {
    "total_stories": len(stories),
    "people": dict(sorted(top_people.items(), key=lambda x: x[1], reverse=True)),
    "places": dict(sorted(top_places.items(), key=lambda x: x[1], reverse=True)),
    "organizations": dict(sorted(top_orgs.items(), key=lambda x: x[1], reverse=True))
}

# Save summary
with open('entity_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

# Print results
print(f"\n=== BEAT BOOK SUMMARY ===")
print(f"Total stories analyzed: {summary['total_stories']}")
print(f"\nTop People ({len(top_people)}):")
for name, count in list(summary['people'].items())[:10]:
    print(f"  {name}: {count} mentions")

print(f"\nTop Places ({len(top_places)}):")
for name, count in list(summary['places'].items())[:10]:
    print(f"  {name}: {count} mentions")

print(f"\nTop Organizations ({len(top_orgs)}):")
for name, count in list(summary['organizations'].items())[:10]:
    print(f"  {name}: {count} mentions")

print(f"\n✓ Full summary saved to: entity_summary.json")
```

### Run the counter

```bash
python count_entities.py
```

This creates `entity_summary.json` with all your key entities ranked by frequency.

---

## Step 4: Generate the Beat Book

Now you'll use AI to write the actual beat book based on your data.

### Create the generator script

Save this as `generate_beatbook.py`:

```python
#!/usr/bin/env python3
import json
import subprocess

# Read the summary
with open('entity_summary.json', 'r') as f:
    summary = json.load(f)

# Read some sample stories (first 10)
with open('stories_with_entities.json', 'r') as f:
    stories = json.load(f)
    sample_stories = stories[:10]

# Build the prompt
prompt = f"""You are helping create a beat book for a journalist. A beat book is a practical reference guide about a reporting area.

Based on this data, write a clear, useful beat book in markdown format.

COVERAGE DATA:
- Total stories: {summary['total_stories']}
- Time period: Based on news coverage

TOP PEOPLE (most mentioned):
{json.dumps(summary['people'], indent=2)}

TOP PLACES:
{json.dumps(summary['places'], indent=2)}

TOP ORGANIZATIONS:
{json.dumps(summary['organizations'], indent=2)}

SAMPLE STORY HEADLINES:
{chr(10).join('- ' + s['title'] for s in sample_stories[:5])}

INSTRUCTIONS:
Write a beat book with these sections:

1. **Introduction** (2-3 paragraphs)
   - What this beat covers
   - Why it matters to the community

2. **Who's Who** 
   - Table with top 5-10 people
   - Include their role/title and why they matter
   - Use ONLY people from the data above

3. **Key Organizations**
   - List top 5-10 organizations
   - Brief description of each
   - Use ONLY organizations from the data above

4. **Geographic Coverage**
   - Main locations on this beat
   - What typically happens in each place
   - Use ONLY places from the data above

5. **Common Story Types**
   - What kinds of stories appear on this beat
   - Based on the sample headlines

6. **Tips for New Reporters**
   - 3-5 practical tips for covering this beat
   - Who to contact for what
   - Important background to know

IMPORTANT: Do NOT invent any names, organizations, or facts not in the data provided. If you're unsure, say "See story archive for details" instead of making something up.

Write in a conversational, helpful tone - like a senior reporter briefing a colleague."""

# Send to AI
print("Generating beat book...")
result = subprocess.run(
    ['uv', 'run', 'llm', '-m', 'groq/llama-3.3-70b-versatile'],
    input=prompt,
    text=True,
    capture_output=True,
    timeout=120
)

if result.returncode == 0:
    # Save the beat book
    with open('beatbook.md', 'w') as f:
        f.write(result.stdout)
    
    print("\n✓ Beat book generated successfully!")
    print("Saved to: beatbook.md")
    print("\nNext step: Open beatbook.md and fact-check the content")
else:
    print(f"\n✗ Error: {result.stderr}")
```

### Run the generator

```bash
python generate_beatbook.py
```

This creates `beatbook.md` - your first draft!

---

## Step 5: Fact-Check and Polish

Even smart AI can make mistakes. Here's how to verify your beat book:

### What to check

1. **Names and titles**
   - Open `stories_with_entities.json` 
   - Search for each person mentioned in your beat book
   - Verify their title is correct
   - Make sure it's not two different people with similar names

2. **Organizations**
   - Check official names (is it "Police Department" or "Police Dept."?)
   - Verify they're real organizations, not AI inventions

3. **Places**
   - Confirm city/county names are spelled correctly
   - Make sure locations actually exist

4. **Numbers**
   - Double-check mention counts match your `entity_summary.json`
   - Verify date ranges if mentioned

### Quick verification commands

**Check how many times a person is mentioned:**
```bash
cat entity_summary.json | grep "John Smith"
```

**See all people mentioned 10+ times:**
```bash
cat entity_summary.json | grep -A 100 "people"
```

### Editing the beat book

Open `beatbook.md` in any text editor and make corrections:
- Fix misspelled names
- Add context you know from your reporting
- Remove anything that seems wrong
- Add sections that would be helpful

Save your changes and you're done!

---

## Keeping Your Beat Book Updated

### Adding new stories

Every month or quarter:

1. Export new stories and add them to `source_stories.json`
2. Run all the scripts again:
   ```bash
   python extract_entities.py
   python count_entities.py
   python generate_beatbook.py
   ```
3. Review and update `beatbook.md`

### What to update manually

Between automated updates, you can manually add to your beat book:
- Breaking news contacts you discover
- Important background information
- Trends you notice
- Story ideas

---

## Troubleshooting

### "Command not found: uv"

You need to install `uv` first:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### "Module not found: json"

You're using a very old Python. Update to Python 3.7 or newer:
```bash
python3 --version
```

### "API rate limit exceeded"

The AI service is limiting your requests. Solutions:
- Add `time.sleep(2)` between API calls in `extract_entities.py`
- Process stories in smaller batches
- Try a different AI model

### "Empty arrays for entities"

The AI might not understand the prompt. Check:
- Is your `content` field actually full article text?
- Try a different AI model (e.g., `anthropic/claude-3.5-sonnet`)
- Add more context to the extraction prompt

### "JSON syntax error"

Your file has a formatting issue. Validate it:
```bash
python -m json.tool source_stories.json
```

If it shows an error, use a JSON validator website to find and fix the problem.

---

## Complete Workflow Summary

Here's everything in order:

```bash
# 1. Put your stories in source_stories.json

# 2. Extract entities
python extract_entities.py

# 3. Count what matters
python count_entities.py

# 4. Generate beat book
python generate_beatbook.py

# 5. Review and edit beatbook.md
```

**Total time:** 30-60 minutes for 100-300 stories, depending on your computer and internet speed.

---

## What You've Accomplished

By following this guide, you've:
- ✅ Organized all your beat coverage in one place
- ✅ Identified the most important people, places, and organizations
- ✅ Created a reference guide that would take weeks to write manually
- ✅ Built a system you can rerun whenever you need updates

Your beat book is now a living document that grows with your reporting. Share it with colleagues, use it to onboard new reporters, and update it regularly to keep it useful.

**Remember:** The beat book is a tool to help you report better, not a replacement for actual reporting. Use it to see patterns, find gaps, and stay organized - then get out there and tell great stories!
