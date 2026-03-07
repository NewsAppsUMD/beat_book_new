#!/usr/bin/env python3
"""
Fix enrollment file names by adding county codes based on the county_code field in the JSON
"""
import json
import os
import shutil

ENROLLMENT_DATA_DIR = 'enrollment_data'

# Get all enrollment files (not county summary files)
files = [f for f in os.listdir(ENROLLMENT_DATA_DIR) 
         if f.startswith('enrollment_') and f.endswith('.json') and '_county_' not in f]

renamed_count = 0
skipped_count = 0

for filename in files:
    filepath = os.path.join(ENROLLMENT_DATA_DIR, filename)
    
    # Check if already in new format (has underscore between county and school code)
    parts = filename.replace('enrollment_', '').replace('.json', '').split('_')
    if len(parts) == 2:
        print(f"✓ Skip (already correct): {filename}")
        skipped_count += 1
        continue
    
    # Read the JSON to get the actual county code
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        county_code = data.get('county_code', '')
        school_code = data.get('school_code', '')
        
        if not county_code or not school_code:
            print(f"⚠ Skip (missing codes): {filename}")
            skipped_count += 1
            continue
        
        # Create new filename with county code
        new_filename = f'enrollment_{county_code}_{school_code}.json'
        new_filepath = os.path.join(ENROLLMENT_DATA_DIR, new_filename)
        
        # Also rename CSV if it exists
        old_csv = filepath.replace('.json', '.csv')
        new_csv = new_filepath.replace('.json', '.csv')
        
        # Rename files
        shutil.move(filepath, new_filepath)
        print(f"✓ Renamed: {filename} -> {new_filename}")
        renamed_count += 1
        
        if os.path.exists(old_csv):
            shutil.move(old_csv, new_csv)
            print(f"  + CSV: {filename.replace('.json', '.csv')} -> {new_filename.replace('.json', '.csv')}")
        
    except Exception as e:
        print(f"✗ Error processing {filename}: {e}")
        skipped_count += 1

print(f"\n{'='*60}")
print(f"Complete! Renamed: {renamed_count}, Skipped: {skipped_count}")
print(f"{'='*60}")
