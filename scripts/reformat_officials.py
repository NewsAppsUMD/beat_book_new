import json
import re
from pathlib import Path

def parse_role_info(role_text, county_name):
    """Parse role text to extract title, district, and selection info"""
    # Determine default title based on county
    if county_name in ['Dorchester', 'Talbot']:
        default_title = 'Council Member'
    else:  # Kent, Queen Annes, Caroline have Commissioners
        default_title = 'Commissioner'
    
    result = {
        'title': default_title,
        'district': None,
        'selection_method': None,
        'term_length': None
    }
    
    # Extract selection method (e.g., "chosen by Council in Dec., 1-year term")
    # Handle both closed and unclosed parentheses
    selection_match = re.search(r'\(([^)]*chosen[^)]*)\)?', role_text)
    if selection_match:
        selection_text = selection_match.group(1)
        
        # Extract term length from selection text
        term_match = re.search(r'(\d+-year term)', selection_text)
        if term_match:
            result['term_length'] = term_match.group(1)
            selection_text = selection_text.replace(term_match.group(0), '').strip(', ')
        
        # Clean up the selection text
        selection_text = selection_text.rstrip('.,; ')
        if selection_text:
            result['selection_method'] = selection_text
    
    # Check for leadership positions first
    is_president = False
    is_vice_president = False
    
    if 'Vice-President' in role_text or 'Vice President' in role_text:
        is_vice_president = True
    elif 'President' in role_text:
        is_president = True
    
    # Determine title
    if is_president:
        result['title'] = 'President'
    elif is_vice_president:
        result['title'] = 'Vice President'
    elif 'At Large' in role_text:
        result['title'] = f"{default_title} At-Large"
    else:
        # Use the default title (Council Member or Commissioner)
        result['title'] = default_title
    
    # Extract district
    dist_match = re.search(r'Dist\.?\s*(\d+)', role_text, re.IGNORECASE)
    if dist_match:
        result['district'] = f"District {dist_match.group(1)}"
    
    return result

def expand_party(party_abbr):
    """Expand party abbreviations"""
    party_map = {
        'R': 'Republican',
        'D': 'Democrat',
        'D)': 'Democrat',
        'R)': 'Republican'
    }
    return party_map.get(party_abbr, party_abbr)

def reformat_county_officials(input_path):
    """Reformat a county officials JSON file"""
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    county_name = data['county_name']
    print(f"\nProcessing {county_name} County...")
    
    # Process legislative branch
    if 'legislative_branch' in data.get('county_officials', {}):
        reformatted = []
        
        for official in data['county_officials']['legislative_branch']:
            # Parse the role information
            role_info = parse_role_info(official.get('role', ''), county_name)
            
            reformatted_official = {
                'name': official['name'],
                'party': expand_party(official.get('party', '')),
                'title': role_info['title'],
            }
            
            # Add optional fields only if they exist
            if role_info['district']:
                reformatted_official['district'] = role_info['district']
            
            if role_info['selection_method']:
                reformatted_official['selection_method'] = role_info['selection_method']
            
            if role_info['term_length']:
                reformatted_official['term_length'] = role_info['term_length']
            
            reformatted.append(reformatted_official)
            print(f"  ✓ {reformatted_official['name']}: {reformatted_official['title']}" + 
                  (f" - {reformatted_official.get('district', '')}" if reformatted_official.get('district') else ""))
        
        data['county_officials']['legislative_branch'] = reformatted
    
    # Judicial branch officials don't have party/district, so just ensure proper structure
    if 'judicial_branch' in data.get('county_officials', {}):
        for official in data['county_officials']['judicial_branch']:
            if 'title' not in official:
                official['title'] = 'Judge'  # Default title
    
    return data

def main():
    print("="*70)
    print("REFORMATTING COUNTY OFFICIALS DATA")
    print("="*70)
    
    data_dir = Path('data')
    official_files = list(data_dir.glob('*_officials.json'))
    
    for filepath in sorted(official_files):
        reformatted_data = reformat_county_officials(filepath)
        
        # Save the reformatted data
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(reformatted_data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*70)
    print("✅ Reformatting complete!")
    print("="*70)

if __name__ == "__main__":
    main()
