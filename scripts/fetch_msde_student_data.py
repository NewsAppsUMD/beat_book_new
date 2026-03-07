"""
Fetch student demographic and support services data from Maryland State Department of Education
Data includes: Free/Reduced Lunch, Homeless (McKinney-Vento), ELL, Special Ed, Attendance

MSDE Report Card: https://reportcard.msde.maryland.gov/
"""

import requests
import json
from pathlib import Path
import time

# County codes for MSDE API
COUNTIES = {
    "kent": {
        "name": "Kent",
        "lss_number": "13",
        "schools": [
            {"name": "Galena Elementary School", "code": None},
            {"name": "H. H. Garnett Elementary", "code": None},
            {"name": "Rock Hall Elementary", "code": None},
            {"name": "Kent County Middle School", "code": None},
            {"name": "Kent County High", "code": None}
        ]
    },
    "dorchester": {
        "name": "Dorchester",
        "lss_number": "09",
        "schools": []
    },
    "caroline": {
        "name": "Caroline",
        "lss_number": "05",
        "schools": []
    },
    "queen_annes": {
        "name": "Queen Anne's",
        "lss_number": "17",
        "schools": []
    },
    "talbot": {
        "name": "Talbot",
        "lss_number": "20",
        "schools": []
    }
}

def fetch_msde_data(county_code, school_year="2024"):
    """
    Fetch data from MSDE Report Card API
    Note: MSDE may require manual data collection from their website
    as they don't always have a public API
    """
    
    # MSDE Report Card base URL
    base_url = "https://reportcard.msde.maryland.gov"
    
    print(f"MSDE Data Sources for {county_code}:")
    print(f"1. Report Card Website: {base_url}")
    print(f"2. Search for County LSS Number: {COUNTIES[county_code]['lss_number']}")
    print(f"3. Download school-level data files (CSV/Excel)")
    print()
    
    # Data typically available:
    data_elements = {
        "enrollment": "Total enrollment by school",
        "farms": "Free and Reduced Meals (FARMS) - economic disadvantage indicator",
        "homeless": "McKinney-Vento homeless students",
        "ell": "English Language Learners",
        "special_ed": "Students with disabilities (IDEA)",
        "attendance": "Average daily attendance rate",
        "chronic_absence": "Chronic absenteeism (missing 10%+ of school days)"
    }
    
    print("Data Elements to Collect:")
    for key, description in data_elements.items():
        print(f"  - {key}: {description}")
    print()
    
    return {
        "status": "manual_collection_needed",
        "url": base_url,
        "county": COUNTIES[county_code]["name"],
        "lss_number": COUNTIES[county_code]["lss_number"],
        "instructions": [
            "1. Visit https://reportcard.msde.maryland.gov/",
            "2. Select 'School' from dropdown",
            "3. Search for county name",
            "4. Download 'Data Downloads' section",
            "5. Extract demographics and attendance data",
            "6. Update the county_student_demographics.json file"
        ]
    }

def create_scraping_instructions():
    """Create a markdown file with detailed scraping instructions"""
    
    instructions = """# MSDE Student Demographics Data Collection Guide

## Data Sources

### Primary Source: MSDE Report Card
- **URL**: https://reportcard.msde.maryland.gov/
- **Data Updated**: Annually (typically fall for previous school year)
- **Years Available**: 2018-present

### Alternative Sources:
1. **Maryland Longitudinal Data System (MLDS)**: https://mldscenter.maryland.gov/
2. **District Websites**: Each county has data dashboards
3. **MSDE Open Data Portal**: https://www.marylandpublicschools.org/about/Pages/DAAIT/index.aspx

## Data Elements to Collect

### 1. Free/Reduced Lunch (FARMS)
- **Metric**: Percentage of students eligible for free or reduced-price meals
- **Location in Report Card**: "Student Characteristics" section
- **Note**: Indicator of economic disadvantage

### 2. McKinney-Vento Homeless Students
- **Metric**: Count and percentage of homeless students
- **Location**: "Special Populations" or "Student Groups"
- **Federal Program**: McKinney-Vento Homeless Assistance Act
- **Note**: May be suppressed if <10 students for privacy

### 3. English Language Learners (ELL)
- **Metric**: Count and percentage of ELL students
- **Location**: "Student Characteristics" > "English Learners"
- **Also Called**: ESOL students, English Learners

### 4. Special Education
- **Metric**: Percentage of students with IEPs (Individualized Education Programs)
- **Location**: "Special Populations" > "Students with Disabilities"
- **Federal Law**: IDEA (Individuals with Disabilities Education Act)

### 5. Attendance & Chronic Absenteeism
- **Metrics**: 
  - Average Daily Attendance Rate
  - Chronic Absenteeism Rate (missing 10%+ of school days)
- **Location**: "Attendance" section
- **Note**: Critical indicator for Blueprint accountability

## Step-by-Step Instructions

### For Each County:

1. **Navigate to MSDE Report Card**
   ```
   https://reportcard.msde.maryland.gov/
   ```

2. **Select School Level**
   - Choose "School" from dropdown
   - Or choose "LEA" (Local Education Agency) for district-level data

3. **Search for Schools**
   - Enter school name or county name
   - County LSS numbers:
     - Kent: 13
     - Dorchester: 09
     - Caroline: 05
     - Queen Anne's: 17
     - Talbot: 20

4. **Navigate to Data Sections**
   - Click on each school
   - Find "Student Characteristics"
   - Find "Attendance"
   - Find "Special Populations"

5. **Download Data**
   - Look for "Download Data" or "Export" buttons
   - Save as CSV or Excel
   - Or manually record data in JSON template

6. **Data Privacy Notes**
   - Cells with <10 students may show "***" for privacy
   - Record these as "suppressed" in the JSON

## County-Specific Notes

### Kent County Public Schools
- Total enrollment: ~1,880
- 5 schools total
- Website: https://www.kent.k12.md.us/

### Dorchester County Public Schools  
- Website: https://www.dcpsmd.org/

### Caroline County Public Schools
- Website: https://www.carolineday.org/

### Queen Anne's County Public Schools
- Website: https://www.qacps.org/

### Talbot County Public Schools
- Website: https://www.talbotschools.org/

## Updating JSON Files

After collecting data, update the corresponding files:
```
scraped_county_data/[county]/[county]_student_demographics.json
```

Replace `null` values with actual numbers or percentages.

## Example Data Entry

```json
{
  "school_name": "Rock Hall Elementary",
  "enrollment": 250,
  "free_reduced_lunch": {
    "count": 125,
    "percentage": 50.0
  },
  "homeless_students": {
    "count": "suppressed",
    "percentage": null,
    "mckinney_vento_eligible": "suppressed"
  },
  "english_learners": {
    "count": 8,
    "percentage": 3.2
  }
}
```

## Verification

Cross-reference with:
- District annual reports
- Local newspaper coverage
- Blueprint implementation reports
- County budget documents

## Questions or Issues

If data is unavailable:
- Contact district data coordinator
- File MPIA (Maryland Public Information Act) request
- Check previous years' data
"""
    
    output_file = Path(__file__).parent / "MSDE_DATA_COLLECTION_GUIDE.md"
    with open(output_file, 'w') as f:
        f.write(instructions)
    
    print(f"Created: {output_file}")
    return output_file

if __name__ == "__main__":
    print("=" * 60)
    print("MSDE Student Demographics Data Fetcher")
    print("=" * 60)
    print()
    
    # Create instruction guide
    guide_path = create_scraping_instructions()
    print(f"\n✓ Created collection guide: {guide_path}")
    print()
    
    # Show data collection info for each county
    for county_key, county_data in COUNTIES.items():
        print(f"\n{county_data['name']} County")
        print("-" * 40)
        result = fetch_msde_data(county_key)
        
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Read the MSDE_DATA_COLLECTION_GUIDE.md")
    print("2. Visit https://reportcard.msde.maryland.gov/")
    print("3. Collect data for each county's schools")
    print("4. Update the *_student_demographics.json files")
    print()
    print("TIP: Start with Kent County (smallest district)")
    print("=" * 60)
