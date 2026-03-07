#!/usr/bin/env python3
"""
Scrape municipal officials from town websites by exploring page structure.
"""

import subprocess
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

SCRAPED_DIR = Path("scraped_county_data")

# Municipalities with their websites
MUNICIPALITIES = [
    {"name": "Denton", "county": "Caroline", "url": "http://www.dentonmaryland.com/"},
    {"name": "Federalsburg", "county": "Caroline", "url": "https://www.townoffederalsburg.org/"},
    {"name": "Greensboro", "county": "Caroline", "url": "http://www.greensboromd.org/"},
    {"name": "Ridgely", "county": "Caroline", "url": "http://ridgelymd.org/"},
    {"name": "Cambridge", "county": "Dorchester", "url": "http://www.choosecambridge.com/"},
    {"name": "Hurlock", "county": "Dorchester", "url": "http://www.hurlock-md.gov/"},
    {"name": "Chestertown", "county": "Kent", "url": "http://www.chestertown.com/"},
    {"name": "Rock Hall", "county": "Kent", "url": "http://www.rockhallmd.com/"},
    {"name": "Centreville", "county": "Queen Anne's", "url": "http://www.townofcentreville.org/"},
    {"name": "Queenstown", "county": "Queen Anne's", "url": "http://www.queenstown-md.com/"},
    {"name": "Easton", "county": "Talbot", "url": "http://www.town-eastonmd.com/"},
    {"name": "Oxford", "county": "Talbot", "url": "http://www.oxfordmd.net/"},
    {"name": "St. Michaels", "county": "Talbot", "url": "https://www.stmichaelsmd.gov/"},
    {"name": "Trappe", "county": "Talbot", "url": "http://trappemd.net/"},
]

def fetch_page(url, timeout=30):
    """Fetch webpage content."""
    try:
        result = subprocess.run(
            ['curl', '-s', '-L', '-m', str(timeout), '-A', 'Mozilla/5.0', url],
            capture_output=True,
            text=True,
            timeout=timeout + 5
        )
        return result.stdout if result.returncode == 0 else None
    except:
        return None

def find_officials_link(html, base_url):
    """Find link to officials/council/commissioners page."""
    # Common patterns for officials pages
    patterns = [
        r'href="([^"]*(?:town[- ]?council|city[- ]?council|commissioner|mayor|official|government)[^"]*)"',
        r'href="([^"]*(?:about|staff|directory)[^"]*)"'
    ]
    
    links = []
    for pattern in patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for match in matches:
            full_url = urljoin(base_url, match)
            links.append(full_url)
    
    return list(set(links))

def extract_officials(html):
    """Extract official names and titles from HTML."""
    officials = []
    
    # Remove script and style tags
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Patterns for officials
    # Pattern 1: Title: Name or Title - Name
    patterns = [
        r'(Mayor|Town Manager|City Manager|President|Commissioner|Council Member)[:\s-]+([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)',
        r'([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)[,\s-]+(Mayor|Town Manager|City Manager|President|Commissioner|Council Member)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html)
        for match in matches:
            if 'mayor' in match[0].lower() or 'manager' in match[0].lower():
                title, name = match[0], match[1]
            else:
                name, title = match[0], match[1]
            
            # Clean up
            name = name.strip()
            title = title.strip()
            
            # Avoid duplicates
            if name and title and not any(o['name'] == name for o in officials):
                officials.append({"name": name, "title": title})
    
    return officials

def scrape_municipality(muni):
    """Scrape officials for one municipality."""
    name = muni['name']
    county = muni['county']
    base_url = muni['url']
    
    print(f"  [{name}]", end=" ", flush=True)
    
    result = {
        "municipality_name": name,
        "county": county,
        "website": base_url,
        "chief_executive": None,
        "council_members": [],
        "source_urls": [],
        "scraped_date": "2025-11-29"
    }
    
    # Fetch main page
    print(".", end="", flush=True)
    html = fetch_page(base_url)
    if not html:
        print(" ❌ Failed to load")
        return result
    
    # Find potential officials links
    print(".", end="", flush=True)
    links = find_officials_link(html, base_url)
    
    # Try main page first
    officials = extract_officials(html)
    if officials:
        result['source_urls'].append(base_url)
    
    # Try each link
    for link in links[:5]:  # Limit to first 5 links
        print(".", end="", flush=True)
        page_html = fetch_page(link)
        if page_html:
            page_officials = extract_officials(page_html)
            if page_officials:
                officials.extend(page_officials)
                result['source_urls'].append(link)
    
    # Deduplicate officials
    seen = set()
    unique_officials = []
    for official in officials:
        key = (official['name'], official['title'])
        if key not in seen:
            seen.add(key)
            unique_officials.append(official)
    
    # Categorize officials
    for official in unique_officials:
        title_lower = official['title'].lower()
        if 'mayor' in title_lower or 'manager' in title_lower or 'president' in title_lower:
            if not result['chief_executive']:
                result['chief_executive'] = official
        else:
            result['council_members'].append(official)
    
    if result['chief_executive'] or result['council_members']:
        print(f" ✅ ({len(result['council_members'])} members)")
    else:
        print(" ⚠️ No data")
    
    return result

def main():
    print("=" * 80)
    print("SCRAPING MUNICIPAL OFFICIALS")
    print("=" * 80)
    print()
    
    # Group by county
    by_county = {}
    for muni in MUNICIPALITIES:
        county = muni['county']
        if county not in by_county:
            by_county[county] = []
        by_county[county].append(muni)
    
    # Scrape each county
    for county_name, munis in by_county.items():
        print(f"[{county_name} County]")
        
        results = []
        for muni in munis:
            result = scrape_municipality(muni)
            results.append(result)
        
        # Save to file
        county_dir = SCRAPED_DIR / county_name.lower().replace(" ", "_").replace("'", "")
        county_file = county_name.lower().replace(' ', '_').replace("'", '')
        output_file = county_dir / f"{county_file}_municipal_officials.json"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    for county_name, munis in by_county.items():
        county_dir = SCRAPED_DIR / county_name.lower().replace(" ", "_").replace("'", "")
        county_file = county_name.lower().replace(' ', '_').replace("'", '')
        output_file = county_dir / f"{county_file}_municipal_officials.json"
        
        with open(output_file) as f:
            data = json.load(f)
        
        with_data = sum(1 for d in data if d.get('chief_executive') or d.get('council_members'))
        print(f"  {county_name}: {with_data}/{len(data)} municipalities with officials data")

if __name__ == "__main__":
    main()
