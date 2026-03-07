import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import time
import re

def scrape_county_council(county_key, county_name):
    """Scrape council/commissioner member information"""
    
    county_urls = {
        "talbot": "https://www.talbotcountymd.gov/223/County-Council",
        "dorchester": "https://docogonet.com/county-council",
        "kent": "https://www.kentcounty.com/commissioners",
        "queen_annes": "https://www.qac.org/196/Commissioners",
        "caroline": "https://www.carolinemd.org/commissioners"
    }
    
    url = county_urls.get(county_key)
    members_found = []
    
    try:
        print(f"  Scraping {url}...")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for member names in various patterns
            # Method 1: Look for headings with "Commissioner" or "Council"
            for heading in soup.find_all(['h2', 'h3', 'h4', 'strong', 'b']):
                text = heading.get_text().strip()
                # Check if it contains a name pattern (Commissioner/Council Member + Name)
                if any(word in text for word in ['Commissioner', 'Council Member', 'Councilman', 'Councilwoman']):
                    # Extract name
                    name_match = re.search(r'(?:Commissioner|Council Member|Councilman|Councilwoman)\s+(.+?)(?:\s*[-–]\s*District|\s*,|\s*$)', text)
                    if name_match:
                        name = name_match.group(1).strip()
                        district_match = re.search(r'District\s+(\d+|At-Large)', text, re.IGNORECASE)
                        district = district_match.group(0) if district_match else "Unknown"
                        
                        members_found.append({
                            "name": name,
                            "district": district
                        })
            
            # Method 2: Look for structured lists
            for ul in soup.find_all('ul'):
                for li in ul.find_all('li'):
                    text = li.get_text().strip()
                    if any(word in text for word in ['Commissioner', 'Council Member']):
                        members_found.append({
                            "name": text,
                            "district": "Check website for district"
                        })
            
            print(f"    Found {len(members_found)} potential members")
            
    except Exception as e:
        print(f"    Error: {e}")
    
    return members_found

def main():
    counties = [
        ('talbot', 'Talbot'),
        ('dorchester', 'Dorchester'),
        ('kent', 'Kent'),
        ('queen_annes', "Queen Anne's"),
        ('caroline', 'Caroline')
    ]
    
    output_dir = Path("../scraped_data")
    
    for county_key, county_name in counties:
        print(f"\nScraping {county_name} County council/commissioners...")
        
        # Read existing file
        county_file = output_dir / county_key / f"{county_key}_council.json"
        with open(county_file) as f:
            data = json.load(f)
        
        # Scrape for members
        members_found = scrape_county_council(county_key, county_name)
        
        if members_found:
            data["members_scraped"] = members_found
            print(f"    Added scraped members to file")
        
        # Save updated file
        with open(county_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Updated {county_file}")
        
        time.sleep(1)
    
    print(f"\n✓ Scraping complete")

if __name__ == "__main__":
    main()
