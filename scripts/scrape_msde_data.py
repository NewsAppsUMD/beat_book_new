#!/usr/bin/env python3
"""
Scrape student demographic data from MSDE Report Card
Using the publicly available data downloads
"""

import requests
import json
from pathlib import Path
import re

def scrape_msde_school_data():
    """
    MSDE publishes annual data files at:
    https://reportcard.msde.maryland.gov/DataDownloads/
    
    Files are typically named like:
    - SchoolProfile_[Year].csv
    - Enrollment_[Year].csv
    - Attendance_[Year].csv
    """
    
    # Known MSDE data download URLs for 2024 school year
    base_url = "https://reportcard.msde.maryland.gov/DataDownloads/2025"
    
    data_files = {
        "enrollment": f"{base_url}/2024/Enrollment_2024.csv",
        "attendance": f"{base_url}/2024/Attendance_2024.csv",
        "demographics": f"{base_url}/2024/Demographics_2024.csv",
    }
    
    # Kent County schools info
    kent_schools = {
        "13": {  # LSS Number for Kent County
            "name": "Kent County",
            "schools": [
                {"name": "Galena Elementary School", "number": "0201"},
                {"name": "H. H. Garnett Elementary", "number": "0211"},
                {"name": "Rock Hall Elementary", "number": "0221"},
                {"name": "Kent County Middle School", "number": "0401"},
                {"name": "Kent County High", "number": "0601"}
            ]
        }
    }
    
    print("Attempting to fetch MSDE data files...")
    print()
    
    for data_type, url in data_files.items():
        print(f"Trying {data_type}: {url}")
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"  ✓ Found {data_type} data!")
                # Save the file
                output_file = Path(f"/tmp/msde_{data_type}_2024.csv")
                output_file.write_text(response.text)
                print(f"  Saved to: {output_file}")
            else:
                print(f"  ✗ Status {response.status_code}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        print()
    
    return kent_schools

def try_direct_school_pages():
    """
    Try accessing individual school pages
    Format: https://reportcard.msde.maryland.gov/Graphs/#/DataDownloads/datadownload/3/[LSS]/[SCHOOL]/99/XXXX/2024
    """
    
    print("\n" + "="*60)
    print("ALTERNATIVE: Direct School Page Access")
    print("="*60)
    
    kent_schools = [
        {"name": "Galena Elementary", "lss": "13", "school": "0201"},
        {"name": "H. H. Garnett Elementary", "lss": "13", "school": "0211"},
        {"name": "Rock Hall Elementary", "lss": "13", "school": "0221"},
        {"name": "Kent County Middle", "lss": "13", "school": "0401"},
        {"name": "Kent County High", "lss": "13", "school": "0601"},
    ]
    
    for school in kent_schools:
        url = f"https://reportcard.msde.maryland.gov/Graphs/#/DataDownloads/datadownload/3/{school['lss']}/{school['school']}/99/XXXX/2024"
        print(f"\n{school['name']}:")
        print(f"  URL: {url}")
        print(f"  → Open this URL in a browser to download data")

def create_manual_collection_script():
    """
    Create instructions for manual data collection
    """
    
    print("\n" + "="*60)
    print("MANUAL DATA COLLECTION INSTRUCTIONS")
    print("="*60)
    
    instructions = """
## Since MSDE requires JavaScript/browser interaction, here's how to collect the data:

### Method 1: Use the Report Card Website (Recommended)

1. **Go to**: https://reportcard.msde.maryland.gov/

2. **For each school**:
   - Search for "Kent County" or use LSS #13
   - Click on each school name
   - Navigate to these sections:
     
     a) **Student Characteristics** (for demographics):
        - Free/Reduced Meals (FARMS) percentage
        - English Learners count/percentage
        - Students with Disabilities percentage
     
     b) **Attendance** (for attendance data):
        - Average Daily Attendance
        - Chronic Absenteeism Rate
     
     c) **Special Populations** (for homeless data):
        - McKinney-Vento Homeless Students
        - May be marked as "***" if <10 students

3. **Download option**: 
   - Look for "Download Data" button on each school page
   - Export as CSV or Excel
   - Or manually record in the JSON template

### Method 2: Use MSDE Data Downloads Page

1. **Go to**: https://reportcard.msde.maryland.gov/DataDownloads/

2. **Download these files** (if available):
   - School Profiles 2024
   - Enrollment by Demographics 2024  
   - Attendance Data 2024
   - Special Populations 2024

3. **Filter for Kent County** (LSS #13) in the downloaded files

### Method 3: Contact the District

**Kent County Public Schools**
- Website: https://www.kent.k12.md.us/
- Phone: 410-778-1595
- Email: info@kent.k12.md.us

Request:
- School profiles with demographic data
- Attendance reports (including chronic absenteeism)
- McKinney-Vento homeless student counts
- English Learner enrollment
- Special education enrollment

## Data Points to Collect for Each School:

```
School: _______________
Enrollment: ___________

Free/Reduced Lunch:
  - Count: _______
  - Percentage: _______

Homeless Students (McKinney-Vento):
  - Count: _______
  - Percentage: _______

English Language Learners:
  - Count: _______
  - Percentage: _______

Special Education:
  - Count: _______
  - Percentage: _______

Attendance:
  - Attendance Rate: _______%
  - Chronic Absenteeism Rate: _______%
  - Chronic Absenteeism Count: _______
```

## Kent County Schools to Collect:

1. Galena Elementary School
2. H. H. Garnett Elementary  
3. Rock Hall Elementary
4. Kent County Middle School
5. Kent County High

"""
    
    print(instructions)
    
    # Save instructions to file
    output_file = Path("/workspaces/jour329w_fall2025/murphy/stardem_draft_v3/scripts/MANUAL_DATA_COLLECTION.md")
    output_file.write_text(instructions)
    print(f"\n✓ Instructions saved to: {output_file}")

if __name__ == "__main__":
    print("="*60)
    print("MSDE Student Demographics Data Scraper")
    print("="*60)
    
    # Try automated scraping
    scrape_msde_school_data()
    
    # Show direct school page links
    try_direct_school_pages()
    
    # Create manual collection guide
    create_manual_collection_script()
    
    print("\n" + "="*60)
    print("RECOMMENDATION")
    print("="*60)
    print("The MSDE website requires browser interaction.")
    print("Best approach:")
    print("1. Open browser to https://reportcard.msde.maryland.gov/")
    print("2. Search for each Kent County school")
    print("3. Copy data into the JSON template")
    print("4. Or download CSV files from Data Downloads section")
    print("="*60)
