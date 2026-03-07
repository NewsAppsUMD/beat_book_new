"""
Find correct county government websites and budget pages.
"""

import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import time

# Known county government websites (main sites)
COUNTIES = {
    "dorchester": {
        "name": "Dorchester",
        "main_site": "https://www.docogonet.com",
        "search_terms": ["budget", "finance", "fiscal"]
    },
    "queen_annes": {
        "name": "Queen Anne's",
        "main_site": "https://www.qac.org",
        "search_terms": ["budget", "finance", "fiscal"]
    },
    "talbot": {
        "name": "Talbot",
        "main_site": "https://www.talbotcountymd.gov",
        "search_terms": ["budget", "finance", "fiscal"]
    },
    "kent": {
        "name": "Kent",
        "main_site": "https://www.kentcounty.com",
        "search_terms": ["budget", "finance", "fiscal"]
    },
    "caroline": {
        "name": "Caroline",
        "main_site": "https://www.carolinemd.org",
        "search_terms": ["budget", "finance", "fiscal"]
    }
}

def find_budget_links(county_key, county_info):
    """Find budget/finance links on county main site"""
    print(f"\nSearching {county_info['name']} County website...")
    
    budget_links = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(county_info['main_site'], headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text().strip().lower()
            
            # Check if link relates to budget/finance
            if any(term in text for term in county_info['search_terms']):
                full_url = href if href.startswith('http') else county_info['main_site'] + href
                budget_links.append({
                    'text': link.get_text().strip(),
                    'url': full_url
                })
        
        # Also look for PDF links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if href.endswith('.pdf') and any(term in href.lower() for term in county_info['search_terms']):
                full_url = href if href.startswith('http') else county_info['main_site'] + href
                budget_links.append({
                    'text': link.get_text().strip() or href.split('/')[-1],
                    'url': full_url,
                    'type': 'pdf'
                })
        
        print(f"  Found {len(budget_links)} budget-related links")
        
    except Exception as e:
        print(f"  Error: {e}")
    
    return budget_links

def main():
    all_findings = {}
    
    for county_key, county_info in COUNTIES.items():
        links = find_budget_links(county_key, county_info)
        all_findings[county_info['name']] = {
            'main_site': county_info['main_site'],
            'budget_links': links
        }
        time.sleep(1)
    
    # Save findings
    output_file = Path("scraped_data") / "budget_links_found.json"
    with open(output_file, 'w') as f:
        json.dump(all_findings, f, indent=2)
    
    print(f"\n\nSaved findings to {output_file}")
    
    # Print summary
    print("\n=== Budget Links Found ===")
    for county, data in all_findings.items():
        print(f"\n{county} ({data['main_site']}):")
        if data['budget_links']:
            for link in data['budget_links'][:5]:  # Show first 5
                print(f"  - {link['text']}: {link['url']}")
        else:
            print("  No links found automatically")

if __name__ == "__main__":
    main()
