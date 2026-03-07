import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import time
import re
from datetime import datetime, timedelta

def scrape_county_minutes(county_key, county_name):
    """Scrape meeting minutes from county websites"""
    
    # URLs for meeting minutes/agendas
    county_info = {
        "talbot": {
            "url": "https://www.talbotcountymd.gov/223/County-Council",
            "minutes_url": "https://www.talbotcountymd.gov/AgendaCenter/County-Council-3"
        },
        "dorchester": {
            "url": "https://docogonet.com/county-council",
            "minutes_url": "https://docogonet.com/AgendaCenter/County-Council-1"
        },
        "kent": {
            "url": "https://www.kentcounty.com/commissioners",
            "minutes_url": "https://www.kentcounty.com/AgendaCenter/Commissioners-1"
        },
        "queen_annes": {
            "url": "https://www.qac.org/196/Commissioners",
            "minutes_url": "https://www.qac.org/AgendaCenter/Commissioners-1"
        },
        "caroline": {
            "url": "https://www.carolinemd.org/commissioners",
            "minutes_url": "https://www.carolinemd.org/AgendaCenter/Commissioners-1"
        }
    }
    
    info = county_info.get(county_key, {})
    meetings = []
    
    # Calculate 6 months ago
    six_months_ago = datetime.now() - timedelta(days=180)
    
    try:
        print(f"  Checking {info['minutes_url']}...")
        response = requests.get(info['minutes_url'], timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for meeting links - pattern varies by county CMS
            # Method 1: Look for links with "minutes" or "agenda" in text
            for link in soup.find_all('a', href=True):
                link_text = link.get_text().strip()
                href = link['href']
                
                # Check if it's a meeting-related link
                if any(word in link_text.lower() for word in ['minutes', 'agenda', 'packet']):
                    # Try to extract date
                    date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', link_text)
                    if not date_match:
                        date_match = re.search(r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})', link_text, re.IGNORECASE)
                    
                    date_str = date_match.group(1) if date_match else "Date unknown"
                    
                    # Make sure URL is absolute
                    if href.startswith('/'):
                        if 'talbotcountymd.gov' in info['minutes_url']:
                            href = 'https://www.talbotcountymd.gov' + href
                        elif 'docogonet.com' in info['minutes_url']:
                            href = 'https://docogonet.com' + href
                        elif 'kentcounty.com' in info['minutes_url']:
                            href = 'https://www.kentcounty.com' + href
                        elif 'qac.org' in info['minutes_url']:
                            href = 'https://www.qac.org' + href
                        elif 'carolinemd.org' in info['minutes_url']:
                            href = 'https://www.carolinemd.org' + href
                    
                    meeting_info = {
                        "date": date_str,
                        "title": link_text[:100],  # Truncate long titles
                        "url": href,
                        "type": "minutes" if "minutes" in link_text.lower() else "agenda"
                    }
                    
                    meetings.append(meeting_info)
                    
                    # Limit to first 20 matches to avoid overwhelming
                    if len(meetings) >= 20:
                        break
            
            print(f"    Found {len(meetings)} meeting documents")
            
    except Exception as e:
        print(f"    Error: {e}")
    
    # Try alternative method - look for CivicPlus pattern
    if not meetings:
        try:
            print(f"  Trying main page {info['url']}...")
            response = requests.get(info['url'], timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for any PDF links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.endswith('.pdf') or 'ViewFile' in href or 'Download' in href:
                        link_text = link.get_text().strip()
                        if any(word in link_text.lower() for word in ['minutes', 'agenda', 'meeting']):
                            meetings.append({
                                "date": "Check document for date",
                                "title": link_text[:100],
                                "url": href if href.startswith('http') else info['url'] + href,
                                "type": "document"
                            })
                
                print(f"    Found {len(meetings)} documents")
                
        except Exception as e:
            print(f"    Error on fallback: {e}")
    
    return meetings

def main():
    counties = [
        ('talbot', 'Talbot'),
        ('dorchester', 'Dorchester'),
        ('kent', 'Kent'),
        ('queen_annes', "Queen Anne's"),
        ('caroline', 'Caroline')
    ]
    
    output_dir = Path("../scraped_data")
    
    all_results = {}
    
    for county_key, county_name in counties:
        print(f"\nScraping {county_name} County meeting minutes...")
        
        meetings = scrape_county_minutes(county_key, county_name)
        
        data = {
            "county_name": county_name,
            "scraped_date": datetime.now().strftime("%Y-%m-%d"),
            "meeting_documents": meetings,
            "total_found": len(meetings)
        }
        
        # Save individual county file
        county_dir = output_dir / county_key
        county_dir.mkdir(exist_ok=True)
        
        output_file = county_dir / f"{county_key}_minutes.json"
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Saved to {output_file}")
        
        all_results[county_key] = data
        
        time.sleep(2)  # Be polite to servers
    
    # Save combined file
    combined_file = output_dir / "counties_minutes.json"
    with open(combined_file, 'w') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Combined minutes data saved to {combined_file}")
    print(f"\n✓ Total documents found:")
    for county_key, data in all_results.items():
        print(f"  • {data['county_name']}: {data['total_found']} documents")

if __name__ == "__main__":
    main()
