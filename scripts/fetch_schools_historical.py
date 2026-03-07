import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path

# Counties and their school districts
COUNTY_SCHOOL_DISTRICTS = {
    'Dorchester': ['Dorchester County Public Schools'],
    'Queen Annes': ['Queen Anne\'s County Public Schools'],
    'Talbot': ['Talbot County Public Schools'],
    'Kent': ['Kent County Public Schools'],
    'Caroline': ['Caroline County Public Schools']
}

def scrape_maryland_manual_schools(county_code, county_name):
    """Scrape school information from Maryland Manual"""
    try:
        url = f"https://msa.maryland.gov/msa/mdmanual/36loc/{county_code}/html/{county_code}.html"
        print(f"    Fetching from Maryland Manual...")
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()
        
        # Look for school-related information
        schools_info = {
            'school_district': COUNTY_SCHOOL_DISTRICTS.get(county_name, ['Unknown'])[0],
            'schools_mentioned': []
        }
        
        # Extract school names (common patterns: "School", "High School", "Elementary", "Middle")
        import re
        school_patterns = [
            r'([A-Z][a-zA-Z\s]+(?:Elementary|High|Middle|Primary)\s+School)',
            r'([A-Z][a-zA-Z\s]+School)'
        ]
        
        for pattern in school_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match not in schools_info['schools_mentioned']:
                    schools_info['schools_mentioned'].append(match)
        
        return schools_info
        
    except Exception as e:
        print(f"      Error: {e}")
        return None

def get_msde_data():
    """Try to get data from Maryland State Department of Education"""
    # Note: MSDE doesn't have a simple API, but we can document the districts
    return {
        'Dorchester': {
            'district_name': 'Dorchester County Public Schools',
            'superintendent': 'Contact via district website',
            'website': 'https://www.dcpsmd.org',
            'schools': [
                'Cambridge-South Dorchester High School',
                'North Dorchester High School',
                'Maces Lane Middle School',
                'Sandy Hill Elementary School',
                'Maple Elementary School',
                'and others'
            ]
        },
        'Queen Annes': {
            'district_name': "Queen Anne's County Public Schools",
            'superintendent': 'Contact via district website',
            'website': 'https://www.qacps.org',
            'schools': [
                'Kent Island High School',
                'Queen Anne\'s County High School',
                'Matapeake Middle School',
                'Centreville Elementary School',
                'and others'
            ]
        },
        'Talbot': {
            'district_name': 'Talbot County Public Schools',
            'superintendent': 'Contact via district website',
            'website': 'https://www.tcps.k12.md.us',
            'schools': [
                'Easton High School',
                'St. Michaels Middle High School',
                'Chapel District Elementary School',
                'Easton Elementary School',
                'and others'
            ]
        },
        'Kent': {
            'district_name': 'Kent County Public Schools',
            'superintendent': 'Contact via district website',
            'website': 'https://www.kent.k12.md.us',
            'schools': [
                'Kent County High School',
                'Kent County Middle School',
                'Rock Hall Elementary School',
                'Galena Elementary School',
                'and others'
            ]
        },
        'Caroline': {
            'district_name': 'Caroline County Public Schools',
            'superintendent': 'Contact via district website',
            'website': 'https://www.carolineschools.org',
            'schools': [
                'Colonel Richardson High School',
                'North Caroline High School',
                'Lockerman Middle School',
                'Federalsburg Elementary School',
                'and others'
            ]
        }
    }

def scrape_historical_info(county_code, county_name):
    """Scrape historical information from Maryland Manual"""
    try:
        # Check main page
        url = f"https://msa.maryland.gov/msa/mdmanual/36loc/{county_code}/html/{county_code}.html"
        print(f"    Fetching historical data from Maryland Manual...")
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()
        
        historical = {
            'origin': None,
            'named_for': None,
            'county_seat': None,
            'incorporated': None
        }
        
        # Extract origin/founding information
        import re
        
        origin_match = re.search(r'Origin:?\s*([^\n]+(?:\n[^\n]+)?)', text, re.IGNORECASE)
        if origin_match:
            historical['origin'] = origin_match.group(1).strip()
        
        named_match = re.search(r'(?:named for|Named after):?\s*([^\n]+)', text, re.IGNORECASE)
        if named_match:
            historical['named_for'] = named_match.group(1).strip()
        
        seat_match = re.search(r'County Seat:?\s*([A-Z][a-zA-Z\s]+)', text)
        if seat_match:
            historical['county_seat'] = seat_match.group(1).strip()
        
        return historical
        
    except Exception as e:
        print(f"      Error: {e}")
        return None

def fetch_all_additional_data():
    """Fetch school and historical data for all counties"""
    
    county_codes = {
        'Dorchester': 'do',
        'Queen Annes': 'qa',
        'Talbot': 'ta',
        'Kent': 'ke',
        'Caroline': 'caro'
    }
    
    # Get MSDE data
    msde_data = get_msde_data()
    
    all_data = {}
    
    for county_name, county_code in county_codes.items():
        print(f"\n{'='*70}")
        print(f"{county_name} County - Schools & Historical Data")
        print('='*70)
        
        county_data = {
            'county_name': county_name,
            'schools': msde_data.get(county_name, {}),
            'historical': None
        }
        
        # Get historical info
        historical = scrape_historical_info(county_code, county_name)
        if historical:
            county_data['historical'] = historical
            if historical.get('origin'):
                print(f"    ✓ Origin: {historical['origin'][:80]}...")
        
        all_data[county_name] = county_data
        
        time.sleep(0.5)
    
    return all_data

def save_additional_data(data):
    """Save the additional data to files"""
    
    output_dir = Path('scraped_data')
    output_dir.mkdir(exist_ok=True)
    
    # Save all data
    all_file = output_dir / 'counties_schools_historical.json'
    with open(all_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*70}")
    print(f"All data saved to {all_file}")
    print('='*70)
    
    # Save individual county files
    for county_name, county_data in data.items():
        filename = output_dir / f"{county_name.lower().replace(' ', '_')}_schools_historical.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(county_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n{county_name} County:")
        print(f"  ✓ Saved to {filename}")
        print(f"  ✓ School District: {county_data['schools'].get('district_name', 'N/A')}")
        if county_data.get('historical', {}).get('origin'):
            print(f"  ✓ Historical data included")

def main():
    print("="*70)
    print("SCHOOLS & HISTORICAL DATA COLLECTOR")
    print("="*70)
    print("Collecting school and historical information for 5 counties")
    print()
    
    data = fetch_all_additional_data()
    save_additional_data(data)
    
    print("\n✅ Data collection complete!")

if __name__ == "__main__":
    main()
