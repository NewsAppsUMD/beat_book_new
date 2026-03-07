import requests
from bs4 import BeautifulSoup
import json
import time
import re

# Counties to get census data for
COUNTIES = {
    'Dorchester': '019',
    'Queen Annes': '035',
    'Talbot': '041',
    'Kent': '029',
    'Caroline': '011'
}

def get_census_data_from_api(county_fips):
    """Get census data from Census API"""
    try:
        # Census API endpoint for ACS 5-Year Data
        # Get key demographic and economic data
        base_url = "https://api.census.gov/data/2022/acs/acs5"
        
        # Variables to retrieve:
        # B01003_001E - Total Population
        # B01002_001E - Median Age
        # B19013_001E - Median Household Income
        # B25077_001E - Median Home Value
        # B23025_005E - Unemployment
        # B01001_002E - Male Population
        # B01001_026E - Female Population
        # B02001_002E - White Alone
        # B02001_003E - Black/African American Alone
        # B03003_003E - Hispanic/Latino
        # B15003_022E - Bachelor's Degree
        # B15003_023E - Master's Degree
        # B15003_024E - Professional Degree
        # B15003_025E - Doctorate Degree
        
        variables = [
            'B01003_001E',  # Total Population
            'B01002_001E',  # Median Age
            'B19013_001E',  # Median Household Income
            'B25077_001E',  # Median Home Value
            'B23025_005E',  # Unemployed
            'B23025_002E',  # Labor Force
            'B01001_002E',  # Male
            'B01001_026E',  # Female
            'B02001_002E',  # White
            'B02001_003E',  # Black
            'B03003_003E',  # Hispanic
            'B15003_022E',  # Bachelor's
            'B15003_023E',  # Master's
            'B15003_024E',  # Professional
            'B15003_025E',  # Doctorate
            'B25001_001E',  # Total Housing Units
            'B25002_002E',  # Occupied Housing Units
            'B25002_003E',  # Vacant Housing Units
        ]
        
        params = {
            'get': ','.join(variables),
            'for': f'county:{county_fips}',
            'in': 'state:24',  # Maryland FIPS code
        }
        
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if len(data) < 2:
            return None
        
        # Parse the response
        headers = data[0]
        values = data[1]
        
        census_dict = dict(zip(headers, values))
        
        return {
            'population': {
                'total': int(census_dict.get('B01003_001E', 0)),
                'male': int(census_dict.get('B01001_002E', 0)),
                'female': int(census_dict.get('B01001_026E', 0)),
                'median_age': float(census_dict.get('B01002_001E', 0)),
            },
            'race_ethnicity': {
                'white_alone': int(census_dict.get('B02001_002E', 0)),
                'black_alone': int(census_dict.get('B02001_003E', 0)),
                'hispanic_latino': int(census_dict.get('B03003_003E', 0)),
            },
            'economics': {
                'median_household_income': int(census_dict.get('B19013_001E', 0)),
                'median_home_value': int(census_dict.get('B25077_001E', 0)),
                'labor_force': int(census_dict.get('B23025_002E', 0)),
                'unemployed': int(census_dict.get('B23025_005E', 0)),
            },
            'education': {
                'bachelors_degree': int(census_dict.get('B15003_022E', 0)),
                'masters_degree': int(census_dict.get('B15003_023E', 0)),
                'professional_degree': int(census_dict.get('B15003_024E', 0)),
                'doctorate_degree': int(census_dict.get('B15003_025E', 0)),
            },
            'housing': {
                'total_units': int(census_dict.get('B25001_001E', 0)),
                'occupied_units': int(census_dict.get('B25002_002E', 0)),
                'vacant_units': int(census_dict.get('B25002_003E', 0)),
            }
        }
        
    except Exception as e:
        print(f"    Error fetching Census API data: {e}")
        return None

def get_census_quickfacts(county_name):
    """Scrape Census QuickFacts for additional data"""
    try:
        # Format county name for URL
        county_url = county_name.lower().replace(' ', '')
        if county_url == 'queenannes':
            county_url = 'queenannescounty'
        else:
            county_url = county_url + 'county'
        
        url = f"https://www.census.gov/quickfacts/{county_url}maryland"
        print(f"    Fetching from: {url}")
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract key facts from the page
        quickfacts = {}
        
        # Find all fact rows
        fact_rows = soup.find_all('tr')
        for row in fact_rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                
                if label and value and value != 'N/A':
                    quickfacts[label] = value
        
        return quickfacts
        
    except Exception as e:
        print(f"    Error fetching QuickFacts: {e}")
        return {}

def fetch_all_census_data():
    """Fetch census data for all counties"""
    all_data = {}
    
    for county_name, fips_code in COUNTIES.items():
        print(f"\n{'='*70}")
        print(f"Fetching Census Data for {county_name} County")
        print('='*70)
        
        county_data = {
            'county_name': county_name,
            'fips_code': f"24{fips_code}",
            'census_api_data': None,
            'quickfacts': None
        }
        
        # Get API data
        print("  Fetching from Census API...")
        api_data = get_census_data_from_api(fips_code)
        if api_data:
            county_data['census_api_data'] = api_data
            print(f"    ✓ Population: {api_data['population']['total']:,}")
            print(f"    ✓ Median Income: ${api_data['economics']['median_household_income']:,}")
            print(f"    ✓ Median Home Value: ${api_data['economics']['median_home_value']:,}")
        else:
            print("    ⚠️  Failed to fetch API data")
        
        # Get QuickFacts
        print("  Fetching from Census QuickFacts...")
        quickfacts = get_census_quickfacts(county_name)
        if quickfacts:
            county_data['quickfacts'] = quickfacts
            print(f"    ✓ Retrieved {len(quickfacts)} additional facts")
        
        all_data[county_name] = county_data
        
        time.sleep(1)  # Be respectful to the API
    
    return all_data

def save_census_data(data):
    """Save census data to JSON files"""
    
    # Save all data in one file
    all_file = 'scraped_data/all_census_data.json'
    with open(all_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*70}")
    print(f"All census data saved to {all_file}")
    print('='*70)
    
    # Save individual county files
    for county_name, county_data in data.items():
        filename = f"scraped_data/{county_name.lower().replace(' ', '_')}_census.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(county_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n{county_name} County:")
        print(f"  ✓ Saved to {filename}")
        
        if county_data.get('census_api_data'):
            pop = county_data['census_api_data']['population']['total']
            print(f"  ✓ Population: {pop:,}")

def main():
    print("="*70)
    print("CENSUS DATA COLLECTOR")
    print("="*70)
    print(f"Collecting data for {len(COUNTIES)} Maryland counties")
    print("Data sources:")
    print("  1. Census API (2022 ACS 5-Year Data)")
    print("  2. Census QuickFacts")
    print()
    
    data = fetch_all_census_data()
    save_census_data(data)
    
    print("\n✅ Census data collection complete!")

if __name__ == "__main__":
    main()
