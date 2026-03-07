import json
import re
from pathlib import Path

def extract_officials_info(data):
    """Extract relevant government officials and information from scraped data"""
    
    result = {}
    
    for county, sections in data.items():
        county_info = {
            'county_name': county,
            'county_officials': {},
            'municipalities': [],
            'other_info': {}
        }
        
        # Extract from legislative branch (county council/commissioners)
        if 'legislative_branch' in sections:
            leg_text = sections['legislative_branch'].get('text_content', '')
            
            # Extract council/commissioner names and roles
            officials = []
            
            # Look for patterns like "Name (Party), Title, District"
            # Example: "George L. (Lenny) Pfeffer, Jr. (R), President (chosen by Council in Dec., 1-year term), Dist. 4"
            pattern = r'([A-Z][a-z]+(?:\s+[A-Z]\.?)?(?:\s+\([A-Za-z]+\))?(?:\s+[A-Z][a-z]+(?:,\s+Jr\.?|,\s+Sr\.?)?)+)\s*\(([RD])\),?\s*([^,\n]+)'
            
            for match in re.finditer(pattern, leg_text):
                name = match.group(1).strip()
                party = match.group(2)
                role = match.group(3).strip()
                
                officials.append({
                    'name': name,
                    'party': party,
                    'role': role
                })
            
            # Also extract meeting times and contact info
            meeting_match = re.search(r'Meetings?:\s*([^\n]+)', leg_text, re.IGNORECASE)
            if meeting_match:
                county_info['other_info']['meeting_schedule'] = meeting_match.group(1).strip()
            
            # Extract address
            address_match = re.search(r'(P\.?\s*O\.?\s*Box[^\n]+|[0-9]+[^\n]+(?:Street|St\.|Lane|Ln\.|Road|Rd\.|Avenue|Ave\.),[^\n]+MD\s+\d{5}[^\n]*)', leg_text, re.IGNORECASE)
            if address_match:
                county_info['other_info']['address'] = address_match.group(1).strip()
            
            # Extract phone
            phone_match = re.search(r'\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}', leg_text)
            if phone_match:
                county_info['other_info']['phone'] = phone_match.group(0)
            
            # Extract website
            web_match = re.search(r'web:\s*<?([^<>\s]+)>?', leg_text, re.IGNORECASE)
            if web_match:
                county_info['other_info']['website'] = web_match.group(1)
            
            county_info['county_officials']['legislative_branch'] = officials
        
        # Extract from judicial branch
        if 'judicial_branch' in sections:
            jud_text = sections['judicial_branch'].get('text_content', '')
            
            # Look for judges, clerks, etc.
            judges = []
            
            # Pattern for judges
            judge_pattern = r'(?:Judge|Clerk|Register)[:\s]*([A-Z][a-z]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][a-z]+)+)'
            
            for match in re.finditer(judge_pattern, jud_text):
                name = match.group(1).strip()
                if name not in [j.get('name') for j in judges]:
                    judges.append({'name': name})
            
            if judges:
                county_info['county_officials']['judicial_branch'] = judges
        
        # Extract municipalities
        if 'municipalities' in sections:
            mun_text = sections['municipalities'].get('text_content', '')
            
            # Look for town/city names and their officials
            # Common patterns: "Town of X", "City of X", followed by mayor/council info
            
            # Extract town names
            town_pattern = r'(?:Town of|City of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
            towns = re.findall(town_pattern, mun_text)
            
            # Also look for standalone town names in headers
            town_header_pattern = r'^([A-Z][A-Z\s]+)$'
            
            # Store municipalities found
            municipalities_found = set(towns)
            
            # Look for mayors, commissioners, council members
            mayor_pattern = r'Mayor[:\s]*([A-Z][a-z]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][a-z]+)+)'
            mayors = re.findall(mayor_pattern, mun_text)
            
            if municipalities_found or mayors:
                county_info['municipalities'] = {
                    'town_names': list(municipalities_found),
                    'officials_mentioned': mayors
                }
        
        # Extract from main page (overview info)
        if 'main' in sections:
            main_text = sections['main'].get('text_content', '')
            
            # Extract county seat
            seat_match = re.search(r'County Seat:\s*([A-Z][a-z]+)', main_text)
            if seat_match:
                county_info['county_seat'] = seat_match.group(1)
            
            # Extract population
            pop_match = re.search(r'2020 census:\s*([\d,]+)', main_text)
            if pop_match:
                county_info['population_2020'] = pop_match.group(1)
        
        result[county] = county_info
    
    return result

def save_county_files(extracted_data, output_dir='data'):
    """Save each county's data to its own JSON file"""
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    for county, data in extracted_data.items():
        # Create a filename-safe version of the county name
        filename = county.lower().replace(' ', '_') + '_officials.json'
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved {county} County data to {filepath}")
        
        # Print summary
        if data.get('county_officials', {}).get('legislative_branch'):
            print(f"  - Found {len(data['county_officials']['legislative_branch'])} legislative officials")
        if data.get('county_officials', {}).get('judicial_branch'):
            print(f"  - Found {len(data['county_officials']['judicial_branch'])} judicial officials")
        if data.get('municipalities'):
            mun_data = data['municipalities']
            if isinstance(mun_data, dict) and mun_data.get('town_names'):
                print(f"  - Found {len(mun_data['town_names'])} municipalities")

if __name__ == "__main__":
    print("Extracting officials from scraped Maryland Manual data...")
    print("="*70)
    
    # Load the raw scraped data
    with open('data/maryland_manual_raw.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    # Extract relevant information
    extracted = extract_officials_info(raw_data)
    
    # Save to individual county files
    print("\nSaving individual county files...")
    print("="*70)
    save_county_files(extracted)
    
    print("\n✅ Extraction complete!")
    print(f"\nTotal counties processed: {len(extracted)}")
