import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import time

def scrape_county_infrastructure(county_key, county_name):
    """Collect infrastructure data for a county"""
    
    infrastructure_data = {
        "county_name": county_name,
        "public_works": {},
        "transportation": {},
        "water_sewer": {},
        "parks_recreation": {},
        "solid_waste": {},
        "major_projects": []
    }
    
    # County-specific URLs
    county_info = {
        "talbot": {
            "public_works_url": "https://www.talbotcountymd.gov/227/Public-Works",
            "parks_url": "https://www.talbotcountymd.gov/225/Parks-Recreation",
            "main_url": "https://www.talbotcountymd.gov"
        },
        "dorchester": {
            "public_works_url": "https://docogonet.com/public-works",
            "parks_url": "https://docogonet.com/recreation-parks",
            "main_url": "https://docogonet.com"
        },
        "kent": {
            "public_works_url": "https://www.kentcounty.com/departments/roads-public-works",
            "parks_url": "https://www.kentcounty.com/departments/parks-recreation",
            "main_url": "https://www.kentcounty.com"
        },
        "queen_annes": {
            "public_works_url": "https://www.qac.org/172/Public-Works",
            "parks_url": "https://www.qac.org/151/Parks-Recreation",
            "main_url": "https://www.qac.org"
        },
        "caroline": {
            "public_works_url": "https://www.carolinemd.org/departments/public-works",
            "parks_url": "https://www.carolinemd.org/departments/parks-recreation",
            "main_url": "https://www.carolinemd.org"
        }
    }
    
    info = county_info.get(county_key, {})
    
    # Try to scrape public works info
    try:
        print(f"  Scraping public works for {county_name}...")
        response = requests.get(info["public_works_url"], timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            infrastructure_data["public_works"]["website"] = info["public_works_url"]
            
            # Look for contact info
            text = soup.get_text()
            
            import re
            phones = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
            if phones:
                infrastructure_data["public_works"]["phone"] = phones[0]
            
            emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
            if emails:
                infrastructure_data["public_works"]["email"] = emails[0]
    
    except Exception as e:
        print(f"    Error scraping public works: {e}")
    
    # Try to scrape parks info
    try:
        print(f"  Scraping parks & recreation for {county_name}...")
        response = requests.get(info["parks_url"], timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            infrastructure_data["parks_recreation"]["website"] = info["parks_url"]
            
            text = soup.get_text()
            
            import re
            phones = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
            if phones:
                infrastructure_data["parks_recreation"]["phone"] = phones[0]
    
    except Exception as e:
        print(f"    Error scraping parks: {e}")
    
    return infrastructure_data

def main():
    counties = [
        ('talbot', 'Talbot'),
        ('dorchester', 'Dorchester'),
        ('kent', 'Kent'),
        ('queen_annes', "Queen Anne's"),
        ('caroline', 'Caroline')
    ]
    
    output_dir = Path("scraped_data")
    
    all_infrastructure = []
    
    for county_key, county_name in counties:
        print(f"\nScraping infrastructure data for {county_name} County...")
        
        infrastructure_data = scrape_county_infrastructure(county_key, county_name)
        
        # Save individual county file
        county_dir = output_dir / county_key
        county_dir.mkdir(exist_ok=True)
        
        output_file = county_dir / f"{county_key}_infrastructure.json"
        with open(output_file, 'w') as f:
            json.dump(infrastructure_data, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Saved to {output_file}")
        
        all_infrastructure.append(infrastructure_data)
        
        time.sleep(1)
    
    # Save combined file
    combined_file = output_dir / "counties_infrastructure.json"
    with open(combined_file, 'w') as f:
        json.dump(all_infrastructure, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Combined infrastructure data saved to {combined_file}")
    print(f"✓ Collected infrastructure data for {len(counties)} counties")

if __name__ == "__main__":
    main()
