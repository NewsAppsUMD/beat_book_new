"""
Extract simplified school data from beatbook v2:
- School name and level (Elementary, Middle, High)
- Enrollment
- Star rating
"""

import json
import re
from pathlib import Path

def extract_level_from_name(name):
    """Extract school level from name"""
    if "Elementary" in name or "/E/" in name:
        return "Elementary"
    elif "Middle" in name or "/M/" in name:
        if "High" in name or "MH" in name:
            return "Middle/High"
        return "Middle"
    elif "High" in name or "/H/" in name:
        return "High"
    elif "Career" in name or "Technology" in name:
        return "Career/Tech"
    elif "Early Childhood" in name:
        return "Early Childhood"
    else:
        return "Other"

def extract_enrollment(demographics_text):
    """Extract enrollment from demographics text"""
    if not demographics_text:
        return None
    
    # Look for enrollment data patterns
    patterns = [
        r'Enrollment Data \(2025\).*?(\d+)',
        r'Enrollment.*?(\d{2,4})',
        r'Total.*?(\d{2,4})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, demographics_text)
        if match:
            return int(match.group(1))
    
    return None

def clean_school_name(name):
    """Remove school code from name"""
    # Remove codes like (0401), (0104), etc.
    return re.sub(r'\s*\(\d{4}\)', '', name)

def main():
    v2_path = Path("/workspaces/jour329w_fall2025/murphy/stardem_draft_v2/things_to_use")
    
    # Load school list and enhanced data
    with open(v2_path / "schools_list.json") as f:
        schools_list = json.load(f)
    
    with open(v2_path / "schools_enhanced_data.json") as f:
        enhanced_data = json.load(f)
    
    # Create lookup by name
    enhanced_lookup = {item['school_name']: item for item in enhanced_data}
    
    # Organize by county
    counties_data = {}
    
    for school in schools_list:
        county = school['county']
        if county not in counties_data:
            counties_data[county] = []
        
        # Get enhanced data
        enhanced = enhanced_lookup.get(school['name'], {})
        
        # Extract enrollment
        enrollment = extract_enrollment(enhanced.get('demographics_full'))
        
        school_data = {
            "name": clean_school_name(school['name']),
            "level": extract_level_from_name(school['name']),
            "enrollment": enrollment,
            "star_rating": enhanced.get('star_rating')
        }
        
        counties_data[county].append(school_data)
    
    # Save to scraped_data
    output_dir = Path("scraped_data")
    
    # Map county names to match existing files
    county_name_map = {
        "Talbot": "talbot",
        "Kent": "kent",
        "Dorchester": "dorchester",
        "Caroline": "caroline",
        "Queen Anne's": "queen_annes"
    }
    
    for county, schools in counties_data.items():
        county_key = county_name_map.get(county)
        if not county_key:
            continue
        
        # Update the schools_historical file
        hist_file = output_dir / f"{county_key}_schools_historical.json"
        
        with open(hist_file, 'r') as f:
            data = json.load(f)
        
        # Replace the schools section with detailed school list
        data['schools']['schools'] = schools
        
        with open(hist_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Updated {county}: {len(schools)} schools")
    
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
                    county_data['schools']['schools'] = counties_data[display_name]
                break
    
    with open(combined_file, 'w') as f:
        json.dump(combined_data, f, indent=2)
    
    print(f"\nUpdated combined file")
    
    # Print summary
    print("\nSummary:")
    for county, schools in sorted(counties_data.items()):
        print(f"{county}: {len(schools)} schools")
        by_level = {}
        for school in schools:
            level = school['level']
            by_level[level] = by_level.get(level, 0) + 1
        for level, count in sorted(by_level.items()):
            print(f"  {level}: {count}")

if __name__ == "__main__":
    main()
