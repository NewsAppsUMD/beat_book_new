#!/usr/bin/env python3
"""
Scrape municipal officials directly from town websites.
"""

import json
import subprocess
import re
from pathlib import Path
from bs4 import BeautifulSoup

SCRAPED_DIR = Path("scraped_county_data")

# Major municipalities with their official websites
MUNICIPALITIES = {
    "Caroline": [
        {"name": "Denton", "url": "https://www.dentonmaryland.com/"},
        {"name": "Federalsburg", "url": "https://www.federalsburgmd.us/"},
        {"name": "Greensboro", "url": "https://www.greensboromaryland.com/"},
        {"name": "Ridgely", "url": "http://ridgelymd.org/"},
    ],
    "Dorchester": [
        {"name": "Cambridge", "url": "https://www.choosecambridge.com/"},
        {"name": "Hurlock", "url": "https://www.hurlock.org/"},
    ],
    "Kent": [
        {"name": "Chestertown", "url": "https://www.chestertown.com/"},
        {"name": "Rock Hall", "url": "https://www.rockhallmd.gov/"},
    ],
    "Queen Anne's": [
        {"name": "Centreville", "url": "https://www.townofcentreville.org/"},
        {"name": "Queenstown", "url": "https://www.queenstownmd.gov/"},
    ],
    "Talbot": [
        {"name": "Easton", "url": "https://eastonmd.gov/"},
        {"name": "Oxford", "url": "https://www.oxfordmd.net/"},
        {"name": "St. Michaels", "url": "https://www.stmichaelsmd.org/"},
        {"name": "Trappe", "url": "https://www.trappemd.org/"},
    ]
}

def fetch_page(url):
    """Fetch webpage content."""
    try:
        result = subprocess.run(
            ['curl', '-s', '-L', '-A', 'Mozilla/5.0', url],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout
    except:
        return None

def scrape_municipal_page(county, municipality):
    """Scrape a municipal website for officials."""
    name = municipality['name']
    base_url = municipality['url']
    
    print(f"  Scraping {name}...", end=" ", flush=True)
    
    # Common paths to try
    paths = [
        '',
        'government',
        'government/town-council',
        'government/city-council',
        'government/mayor',
        'about/government',
        'town-council',
        'city-council',
        'mayor-and-council',
        'commissioners'
    ]
    
    officials_data = {
        "municipality_name": name,
        "county": county,
        "website": base_url,
        "chief_executive": None,
        "council_members": [],
        "source_urls": [],
        "scraped_date": "2025-11-29"
    }
    
    # Try each path
    for path in paths:
        url = base_url.rstrip('/') + '/' + path if path else base_url
        html = fetch_page(url)
        
        if not html:
            continue
            
        # Look for names and titles
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        
        # Common patterns for officials
        patterns = [
            r'Mayor[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'Town Manager[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'City Manager[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'President[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match and not officials_data['chief_executive']:
                officials_data['chief_executive'] = {
                    "name": match.group(1),
                    "title": pattern.split('[')[0].strip()
                }
                officials_data['source_urls'].append(url)
                break
        
        # Look for council members
        council_patterns = [
            r'Council Member[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'Commissioner[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        ]
        
        for pattern in council_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match not in [m['name'] for m in officials_data['council_members']]:
                    officials_data['council_members'].append({
                        "name": match,
                        "title": pattern.split('[')[0].strip()
                    })
        
        if officials_data['chief_executive'] or officials_data['council_members']:
            break
    
    if officials_data['chief_executive'] or officials_data['council_members']:
        print(f"✅ ({len(officials_data['council_members'])} members)")
        return officials_data
    else:
        print("⚠️ No data found")
        return officials_data  # Return with empty data rather than None

def main():
    print("=" * 80)
    print("SCRAPING MUNICIPAL OFFICIALS FROM TOWN WEBSITES")
    print("=" * 80)
    print()
    
    all_results = {}
    
    for county_name, municipalities in MUNICIPALITIES.items():
        print(f"[{county_name} County] - {len(municipalities)} municipalities")
        
        results = []
        for muni in municipalities:
            data = scrape_municipal_page(county_name, muni)
            if data:
                results.append(data)
        
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
            
            print(f"✅ {county_name}: {len(results)} municipalities → {output_file.name}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_found = 0
    for county, results in all_results.items():
        found = sum(1 for r in results if r.get('chief_executive') or r.get('council_members'))
        total_found += found
        print(f"  {county}: {found}/{len(results)} municipalities with data")
    
    print(f"\nTotal with officials data: {total_found}/{sum(len(m) for m in MUNICIPALITIES.values())}")

if __name__ == "__main__":
    main()
