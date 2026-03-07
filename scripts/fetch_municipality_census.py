import requests
import json
import time
from pathlib import Path

# Maryland FIPS code
STATE_FIPS = '24'

# Load municipalities from our data
def load_municipalities():
    """Load all municipalities from our collected data"""
    with open('data/all_municipalities.json', 'r') as f:
        return json.load(f)

def get_municipality_census_data(place_name, county_name, state_fips='24'):
    """Get census data for a specific municipality using Census API"""
    try:
        # Census API endpoint for places
        base_url = "https://api.census.gov/data/2022/acs/acs5"
        
        # First, we need to find the place FIPS code
        # Get all places in Maryland
        params = {
            'get': 'NAME,B01003_001E,B19013_001E,B25077_001E,B01002_001E',
            'for': 'place:*',
            'in': f'state:{state_fips}'
        }
        
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Find matching place
        place_fips = None
        for row in data[1:]:  # Skip header
            if place_name.lower() in row[0].lower():
                place_fips = row[-1]  # Last element is place FIPS
                break
        
        if not place_fips:
            return None
        
        # Now get detailed data for this place
        variables = [
            'B01003_001E',  # Total Population
            'B01002_001E',  # Median Age
            'B19013_001E',  # Median Household Income
            'B25077_001E',  # Median Home Value
            'B01001_002E',  # Male
            'B01001_026E',  # Female
            'B02001_002E',  # White
            'B02001_003E',  # Black
            'B03003_003E',  # Hispanic
            'B25001_001E',  # Total Housing Units
            'B25002_002E',  # Occupied
            'B25002_003E',  # Vacant
        ]
        
        params = {
            'get': ','.join(variables),
            'for': f'place:{place_fips}',
            'in': f'state:{state_fips}'
        }
        
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if len(data) < 2:
            return None
        
        headers = data[0]
        values = data[1]
        census_dict = dict(zip(headers, values))
        
        # Handle null values (Census returns -666666666 for unavailable data)
        def safe_int(val):
            try:
                num = int(val)
                return num if num >= 0 else None
            except:
                return None
        
        def safe_float(val):
            try:
                num = float(val)
                return num if num >= 0 else None
            except:
                return None
        
        return {
            'place_name': place_name,
            'place_fips': place_fips,
            'population': {
                'total': safe_int(census_dict.get('B01003_001E')),
                'male': safe_int(census_dict.get('B01001_002E')),
                'female': safe_int(census_dict.get('B01001_026E')),
                'median_age': safe_float(census_dict.get('B01002_001E')),
            },
            'race_ethnicity': {
                'white_alone': safe_int(census_dict.get('B02001_002E')),
                'black_alone': safe_int(census_dict.get('B02001_003E')),
                'hispanic_latino': safe_int(census_dict.get('B03003_003E')),
            },
            'economics': {
                'median_household_income': safe_int(census_dict.get('B19013_001E')),
                'median_home_value': safe_int(census_dict.get('B25077_001E')),
            },
            'housing': {
                'total_units': safe_int(census_dict.get('B25001_001E')),
                'occupied_units': safe_int(census_dict.get('B25002_002E')),
                'vacant_units': safe_int(census_dict.get('B25002_003E')),
            }
        }
        
    except Exception as e:
        print(f"      Error: {e}")
        return None

def fetch_all_municipality_census_data():
    """Fetch census data for all municipalities"""
    
    municipalities_data = load_municipalities()
    results = {}
    
    for county, county_data in municipalities_data.items():
        print(f"\n{'='*70}")
        print(f"Fetching Census Data for {county} County Municipalities")
        print('='*70)
        
        results[county] = {
            'county_name': county,
            'municipalities': []
        }
        
        munis = county_data.get('municipalities', [])
        print(f"  Processing {len(munis)} municipalities...")
        
        for muni in munis:
            muni_name = muni['name']
            print(f"    {muni_name}...", end=' ')
            
            census_data = get_municipality_census_data(muni_name, county)
            
            if census_data and census_data['population']['total']:
                print(f"✓ Pop: {census_data['population']['total']:,}")
                results[county]['municipalities'].append(census_data)
            else:
                print("⚠️  No data available")
            
            time.sleep(0.5)  # Be respectful to the API
    
    return results

def save_municipality_census_data(data):
    """Save municipality census data to files"""
    
    output_dir = Path('scraped_data')
    output_dir.mkdir(exist_ok=True)
    
    # Save all data
    all_file = output_dir / 'all_municipalities_census.json'
    with open(all_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*70}")
    print(f"All municipality census data saved to {all_file}")
    print('='*70)
    
    # Save individual county files
    for county, county_data in data.items():
        filename = output_dir / f"{county.lower().replace(' ', '_')}_municipalities_census.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(county_data, f, indent=2, ensure_ascii=False)
        
        munis_with_data = len(county_data['municipalities'])
        print(f"\n{county} County:")
        print(f"  ✓ Saved to {filename}")
        print(f"  ✓ {munis_with_data} municipalities with census data")
        
        # List municipalities with population
        for muni in county_data['municipalities']:
            pop = muni['population']['total']
            if pop:
                print(f"      • {muni['place_name']}: {pop:,}")

def main():
    print("="*70)
    print("MUNICIPALITY CENSUS DATA COLLECTOR")
    print("="*70)
    print("Collecting census data for all municipalities")
    print("Data source: U.S. Census Bureau, 2022 ACS 5-Year Estimates")
    print()
    
    data = fetch_all_municipality_census_data()
    save_municipality_census_data(data)
    
    print("\n✅ Municipality census data collection complete!")

if __name__ == "__main__":
    main()
