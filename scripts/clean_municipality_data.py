import json
from pathlib import Path

# List of strings to filter out (not actual municipalities)
FILTER_OUT = [
    'COUNTY, MARYLAND',
    'MUNICIPALITIES',
    'Maryland Constitutional',
    'Maryland Departments',
    'Maryland Independent',
    'Maryland Executive',
    'Maryland Universities',
    'Maryland Counties',
    'Maryland Municipalities',
    'Maryland at a Glance',
    'Maryland Manual',
    'Search the Manual',
    'Education & Outreach',
    'Archives of Maryland'
]

def should_keep(municipality_name):
    """Check if this is an actual municipality"""
    for filter_term in FILTER_OUT:
        if filter_term in municipality_name:
            return False
    return True

def clean_municipality_data():
    """Clean up municipality JSON files"""
    
    data_dir = Path('data')
    muni_files = list(data_dir.glob('*_municipalities.json'))
    
    print("Cleaning municipality data files...")
    print("="*70)
    
    for filepath in muni_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Skip if no municipalities key
        if 'municipalities' not in data:
            print(f"\n⚠️  Skipping {filepath.name} - no municipalities key")
            continue
        
        # Filter municipalities
        original_count = len(data['municipalities'])
        data['municipalities'] = [
            m for m in data['municipalities']
            if should_keep(m['name'])
        ]
        cleaned_count = len(data['municipalities'])
        
        # Save cleaned data
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        county_name = data['county']
        print(f"\n{county_name} County:")
        print(f"  Removed {original_count - cleaned_count} non-municipality entries")
        print(f"  Kept {cleaned_count} actual municipalities")
        
        # Show municipalities and official counts
        for muni in data['municipalities']:
            official_count = len(muni.get('officials', []))
            if official_count > 0:
                print(f"    ✓ {muni['name']}: {official_count} officials")
            else:
                print(f"    - {muni['name']}: no officials found")
    
    # Also clean the all_municipalities.json file
    all_muni_path = data_dir / 'all_municipalities.json'
    if all_muni_path.exists():
        with open(all_muni_path, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
        
        for county in all_data.values():
            county['municipalities'] = [
                m for m in county['municipalities']
                if should_keep(m['name'])
            ]
        
        with open(all_muni_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Cleaned all_municipalities.json")

if __name__ == "__main__":
    clean_municipality_data()
    print("\n✅ Cleanup complete!")
