#!/usr/bin/env python3
"""
Scrape municipal officials (mayors, town councils) for major municipalities in the 5 counties.
"""

import json
import subprocess
from pathlib import Path

SCRAPED_DIR = Path("scraped_county_data")

# Major municipalities by county based on census data and news coverage
MUNICIPALITIES = {
    "Caroline": [
        {"name": "Denton", "county": "Caroline", "type": "Town"},
        {"name": "Federalsburg", "county": "Caroline", "type": "Town"},
        {"name": "Greensboro", "county": "Caroline", "type": "Town"},
        {"name": "Ridgely", "county": "Caroline", "type": "Town"},
    ],
    "Dorchester": [
        {"name": "Cambridge", "county": "Dorchester", "type": "City"},
        {"name": "Hurlock", "county": "Dorchester", "type": "Town"},
    ],
    "Kent": [
        {"name": "Chestertown", "county": "Kent", "type": "Town"},
        {"name": "Rock Hall", "county": "Kent", "type": "Town"},
    ],
    "Queen Anne's": [
        {"name": "Centreville", "county": "Queen Anne's", "type": "Town"},
        {"name": "Queenstown", "county": "Queen Anne's", "type": "Town"},
    ],
    "Talbot": [
        {"name": "Easton", "county": "Talbot", "type": "Town"},
        {"name": "Oxford", "county": "Talbot", "type": "Town"},
        {"name": "St. Michaels", "county": "Talbot", "type": "Town"},
        {"name": "Trappe", "county": "Talbot", "type": "Town"},
    ]
}

SCRAPE_PROMPT = """Search the web for current government officials for {municipality_name}, {county} County, Maryland.

Find:
1. Mayor OR Town Manager OR City Manager (name and title)
2. Town Council OR City Council members (names)
3. Meeting schedule if available
4. Contact information (address, phone, website)

Focus on CURRENT officials (2024-2025). Look for:
- Official municipal websites
- Maryland Municipal League
- County government pages
- Recent news articles mentioning officials

Return ONLY a JSON object with this structure:
{{
  "municipality_name": "{municipality_name}",
  "municipality_type": "{municipality_type}",
  "county": "{county}",
  "chief_executive": {{
    "name": "First Last",
    "title": "Mayor/Town Manager/City Manager"
  }},
  "council_members": [
    {{"name": "First Last", "title": "Council President/Council Member"}},
    {{"name": "First Last", "title": "Council Member"}}
  ],
  "meeting_schedule": "Day, Time",
  "contact": {{
    "address": "Address",
    "phone": "Phone",
    "website": "URL"
  }},
  "source": "URL or description of where you found this info",
  "as_of_date": "2025-11-29"
}}

JSON only - no explanatory text:"""

def scrape_municipal_officials(municipality: dict) -> dict:
    """Scrape officials for one municipality."""
    name = municipality['name']
    county = municipality['county']
    muni_type = municipality['type']
    
    print(f"  Scraping {name}...")
    
    prompt = SCRAPE_PROMPT.format(
        municipality_name=name,
        county=county,
        municipality_type=muni_type
    )
    
    try:
        result = subprocess.run(
            ['llm', '-m', 'claude-3.7-sonnet', prompt],
            capture_output=True,
            text=True,
            check=True,
            timeout=60
        )
        
        response = result.stdout.strip()
        
        # Try to extract JSON
        if response.startswith('```'):
            lines = response.split('\n')
            response = '\n'.join(lines[1:-1])
            if response.startswith('json'):
                response = '\n'.join(response.split('\n')[1:])
        
        # Find JSON object
        start = response.find('{')
        if start != -1:
            end = response.rfind('}')
            if end != -1:
                response = response[start:end+1]
        
        data = json.loads(response)
        return data
        
    except subprocess.TimeoutExpired:
        print(f"    ⚠️  Timeout")
        return None
    except json.JSONDecodeError as e:
        print(f"    ⚠️  JSON parse error: {e}")
        print(f"    Response: {response[:200]}...")
        return None
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return None

def main():
    print("=" * 80)
    print("SCRAPING MUNICIPAL OFFICIALS")
    print("=" * 80)
    print()
    
    all_results = {}
    
    for county_name, municipalities in MUNICIPALITIES.items():
        print(f"[{county_name} County] - {len(municipalities)} municipalities")
        
        results = []
        for muni in municipalities:
            data = scrape_municipal_officials(muni)
            if data:
                results.append(data)
                print(f"    ✅ {muni['name']}")
            else:
                print(f"    ❌ {muni['name']} - Failed")
        
        all_results[county_name] = results
        print()
    
    # Save to individual county files
    print("=" * 80)
    print("SAVING RESULTS")
    print("=" * 80)
    
    for county_name, results in all_results.items():
        if results:
            county_dir = SCRAPED_DIR / county_name.lower().replace(" ", "_").replace("'", "")
            county_file = county_name.lower().replace(' ', '_').replace("'", '')
            output_file = county_dir / f"{county_file}_municipal_officials.json"
            
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"✅ {county_name}: {len(results)} municipalities → {output_file}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    total = sum(len(r) for r in all_results.values())
    print(f"Total municipalities scraped: {total}")
    for county, results in all_results.items():
        print(f"  {county}: {len(results)} municipalities")

if __name__ == "__main__":
    main()
