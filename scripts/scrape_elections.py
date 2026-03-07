import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import time

def scrape_county_elections(county_key, county_name):
    """Scrape elections data for a county"""
    
    elections_data = {
        "county_name": county_name,
        "board_of_elections": {},
        "voter_registration": {},
        "polling_locations": [],
        "recent_elections": [],
        "upcoming_elections": [],
        "election_info": {}
    }
    
    # County-specific URLs and data
    county_info = {
        "talbot": {
            "boe_url": "https://elections.maryland.gov/about/county_boards.html",
            "county_url": "https://www.talbotcountymd.gov/235/Board-of-Elections",
            "local_boe": "https://talbotcountymd.gov/235/Board-of-Elections"
        },
        "dorchester": {
            "boe_url": "https://elections.maryland.gov/about/county_boards.html",
            "county_url": "https://docogonet.com/boe",
            "local_boe": "https://docogonet.com/boe"
        },
        "kent": {
            "boe_url": "https://elections.maryland.gov/about/county_boards.html",
            "county_url": "https://www.kentcounty.com/departments/board-of-elections",
            "local_boe": "https://www.kentcounty.com/departments/board-of-elections"
        },
        "queen_annes": {
            "boe_url": "https://elections.maryland.gov/about/county_boards.html",
            "county_url": "https://www.qac.org/153/Board-of-Elections",
            "local_boe": "https://www.qac.org/153/Board-of-Elections"
        },
        "caroline": {
            "boe_url": "https://elections.maryland.gov/about/county_boards.html",
            "county_url": "https://www.carolinemd.org/departments/board-of-elections",
            "local_boe": "https://www.carolinemd.org/departments/board-of-elections"
        }
    }
    
    info = county_info.get(county_key, {})
    
    # Try to scrape state BOE page for county contact info
    try:
        print(f"  Scraping Maryland State BOE for {county_name} info...")
        response = requests.get(info["boe_url"], timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Look for county name in the page
            county_section = None
            for tag in soup.find_all(['h2', 'h3', 'h4', 'strong']):
                if county_name in tag.get_text():
                    county_section = tag.find_parent()
                    break
            
            if county_section:
                # Extract contact info
                text = county_section.get_text()
                if 'Phone' in text or 'phone' in text:
                    elections_data["board_of_elections"]["found_info"] = True
    except Exception as e:
        print(f"    Error scraping state BOE: {e}")
    
    # Try county-specific BOE page
    try:
        print(f"  Scraping {county_name} County BOE website...")
        response = requests.get(info["local_boe"], timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            elections_data["board_of_elections"]["website"] = info["local_boe"]
            
            # Look for contact info
            text = soup.get_text()
            
            # Find phone numbers
            import re
            phones = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
            if phones:
                elections_data["board_of_elections"]["phone"] = phones[0]
            
            # Find email
            emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
            if emails:
                elections_data["board_of_elections"]["email"] = emails[0]
            
            # Find address
            for tag in soup.find_all(['p', 'div']):
                txt = tag.get_text()
                if 'Maryland' in txt and any(word in txt.lower() for word in ['street', 'road', 'avenue', 'drive', 'court', 'box']):
                    elections_data["board_of_elections"]["address"] = txt.strip()
                    break
    
    except Exception as e:
        print(f"    Error scraping county BOE: {e}")
    
    # Add Maryland State BOE info
    elections_data["election_info"] = {
        "state_board_website": "https://elections.maryland.gov",
        "voter_lookup": "https://voterservices.elections.maryland.gov/VoterSearch",
        "polling_place_lookup": "https://voterservices.elections.maryland.gov/PollingPlaceSearch",
        "online_voter_registration": "https://voterservices.elections.maryland.gov/OnlineVoterRegistration",
        "absentee_ballot_request": "https://voterservices.elections.maryland.gov/OnlineVoterRegistration/AbsenteeApplication",
        "election_results": "https://elections.maryland.gov/elections/results_index.html"
    }
    
    # Add notes about upcoming elections
    elections_data["notes"] = [
        "2026 Gubernatorial Election: Primary June 24, 2026; General Election November 3, 2026",
        "Local elections typically held in odd-numbered years",
        "Early voting available at designated locations",
        "Mail-in voting available upon request"
    ]
    
    return elections_data

def main():
    counties = [
        ('talbot', 'Talbot'),
        ('dorchester', 'Dorchester'),
        ('kent', 'Kent'),
        ('queen_annes', "Queen Anne's"),
        ('caroline', 'Caroline')
    ]
    
    output_dir = Path("scraped_data")
    
    all_elections = []
    
    for county_key, county_name in counties:
        print(f"\nScraping elections data for {county_name} County...")
        
        elections_data = scrape_county_elections(county_key, county_name)
        
        # Save individual county file
        county_dir = output_dir / county_key
        county_dir.mkdir(exist_ok=True)
        
        output_file = county_dir / f"{county_key}_elections.json"
        with open(output_file, 'w') as f:
            json.dump(elections_data, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Saved to {output_file}")
        
        all_elections.append(elections_data)
        
        time.sleep(1)  # Be polite to servers
    
    # Save combined file
    combined_file = output_dir / "counties_elections.json"
    with open(combined_file, 'w') as f:
        json.dump(all_elections, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Combined elections data saved to {combined_file}")
    print(f"✓ Collected elections data for {len(counties)} counties")

if __name__ == "__main__":
    main()
