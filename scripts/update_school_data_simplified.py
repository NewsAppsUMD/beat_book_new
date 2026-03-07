"""
Simplify school data to include:
- District total enrollment
- Individual school star ratings and percentiles
"""

import json
from pathlib import Path

def clean_school_name(name):
    """Remove school code from name"""
    import re
    return re.sub(r'\s*\(\d{4}\)', '', name)

def extract_level_from_url(url):
    """Extract school level from URL"""
    if "/E/" in url:
        return "Elementary"
    elif "/M/" in url:
        return "Middle"
    elif "/H/" in url:
        return "High"
    elif "/MH/" in url or "/EM/" in url:
        return "Middle/High" if "/MH/" in url else "Elementary/Middle"
    elif "/UC/" in url:
        return "Other"
    else:
        return "Other"

def main():
    v2_path = Path("/workspaces/jour329w_fall2025/murphy/stardem_draft_v2/things_to_use")
    
    # Load enrollment data
    with open(v2_path / "enrollment_by_race_percentages.json") as f:
        enrollment_data = json.load(f)
    
    # Load school list and enhanced data
    with open(v2_path / "schools_list.json") as f:
        schools_list = json.load(f)
    
    with open(v2_path / "schools_enhanced_data.json") as f:
        enhanced_data = json.load(f)
    
    # Create lookup by name
    enhanced_lookup = {item['school_name']: item for item in enhanced_data}
    
    # County name mapping
    county_name_map = {
        "Talbot": "talbot",
        "Kent": "kent",
        "Dorchester": "dorchester",
        "Caroline": "caroline",
        "Queen Anne's": "queen_annes"
    }
    
    # Organize by county
    counties_data = {}
    
    for school in schools_list:
        county = school['county']
        if county not in counties_data:
            counties_data[county] = []
        
        # Get enhanced data
        enhanced = enhanced_lookup.get(school['name'], {})
        
        school_data = {
            "name": clean_school_name(school['name']),
            "level": extract_level_from_url(school['url']),
            "star_rating": enhanced.get('star_rating'),
            "percentile": enhanced.get('percentile_rank')
        }
        
        # Only include schools with star ratings (excludes career/tech centers)
        if school_data['star_rating'] is not None:
            counties_data[county].append(school_data)
    
    # Save to scraped_data
    output_dir = Path("scraped_data")
    
    for county, schools in counties_data.items():
        county_key = county_name_map.get(county)
        if not county_key:
            continue
        
        # Get district enrollment
        district_enrollment = enrollment_data.get(county, {}).get('total_k12_enrollment')
        
        # Update the schools_historical file
        hist_file = output_dir / f"{county_key}_schools_historical.json"
        
        with open(hist_file, 'r') as f:
            data = json.load(f)
        
        # Update schools section
        data['schools']['total_enrollment'] = district_enrollment
        data['schools']['schools'] = schools
        
        with open(hist_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Updated {county}: {len(schools)} schools, {district_enrollment:,} total enrollment")
    
    # Also update the combined file
    combined_file = output_dir / "counties_schools_historical.json"
    with open(combined_file, 'r') as f:
        combined_data = json.load(f)
    
    # combined_data is a dict with county names as keys
    for county_key, county_data in combined_data.items():
        # Find matching county in our data
        for display_name, key in county_name_map.items():
            if key == county_key.lower():
                if display_name in counties_data:
                    district_enrollment = enrollment_data.get(display_name, {}).get('total_k12_enrollment')
                    county_data['schools']['total_enrollment'] = district_enrollment
                    county_data['schools']['schools'] = counties_data[display_name]
                break
    
    with open(combined_file, 'w') as f:
        json.dump(combined_data, f, indent=2)
    
    print(f"\nUpdated combined file")
    
    # Print summary
    print("\nSummary:")
    total_schools = 0
    for county, schools in sorted(counties_data.items()):
        district_enrollment = enrollment_data.get(county, {}).get('total_k12_enrollment', 0)
        print(f"{county}: {len(schools)} schools, {district_enrollment:,} students")
        total_schools += len(schools)
        
        by_level = {}
        for school in schools:
            level = school['level']
            by_level[level] = by_level.get(level, 0) + 1
        
        for level, count in sorted(by_level.items()):
            print(f"  {level}: {count}")
    
    print(f"\nTotal: {total_schools} schools across 5 counties")

if __name__ == "__main__":
    main()
