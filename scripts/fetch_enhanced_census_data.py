#!/usr/bin/env python3
"""
Fetch enhanced Census data for Eastern Shore counties:
1. Poverty data
2. Housing affordability
3. Age breakdown
4. Broadband/Internet access
6. Full education attainment
7. Health insurance coverage
"""

import requests
import json
from pathlib import Path

# Census API configuration
CENSUS_API_KEY = "d841b1c083caf828ed62944bd5e0eae691e31941"
BASE_URL = "https://api.census.gov/data/2022/acs/acs5"

# County FIPS codes
COUNTIES = {
    "kent": {"name": "Kent", "fips": "24029"},
    "dorchester": {"name": "Dorchester", "fips": "24019"},
    "caroline": {"name": "Caroline", "fips": "24011"},
    "queen_annes": {"name": "Queen Annes", "fips": "24035"},
    "talbot": {"name": "Talbot", "fips": "24041"}
}

# Census variables to fetch
VARIABLES = {
    # Poverty
    "B17001_001E": "total_pop_poverty_status",
    "B17001_002E": "income_below_poverty",
    "B17001_004E": "children_under_18_poverty",
    "B17001_015E": "seniors_65plus_poverty",
    
    # Housing affordability
    "B25003_001E": "total_occupied_housing",
    "B25003_002E": "owner_occupied",
    "B25003_003E": "renter_occupied",
    "B25064_001E": "median_gross_rent",
    "B25070_001E": "total_renters_cost_burden",
    "B25070_007E": "renters_30_34_percent",
    "B25070_008E": "renters_35_39_percent",
    "B25070_009E": "renters_40_49_percent",
    "B25070_010E": "renters_50plus_percent",
    "B25091_001E": "total_owners_cost_burden",
    "B25091_008E": "owners_30_34_percent",
    "B25091_009E": "owners_35_39_percent",
    "B25091_010E": "owners_40_49_percent",
    "B25091_011E": "owners_50plus_percent",
    
    # Age breakdown
    "B01001_001E": "total_population",
    "B01001_003E": "male_under_5",
    "B01001_027E": "female_under_5",
    "B01001_004E": "male_5_9",
    "B01001_005E": "male_10_14",
    "B01001_006E": "male_15_17",
    "B01001_028E": "female_5_9",
    "B01001_029E": "female_10_14",
    "B01001_030E": "female_15_17",
    "B01001_020E": "male_65_66",
    "B01001_021E": "male_67_69",
    "B01001_022E": "male_70_74",
    "B01001_023E": "male_75_79",
    "B01001_024E": "male_80_84",
    "B01001_025E": "male_85plus",
    "B01001_044E": "female_65_66",
    "B01001_045E": "female_67_69",
    "B01001_046E": "female_70_74",
    "B01001_047E": "female_75_79",
    "B01001_048E": "female_80_84",
    "B01001_049E": "female_85plus",
    
    # Broadband access
    "B28002_001E": "total_households_internet",
    "B28002_004E": "broadband_subscription",
    "B28002_013E": "no_internet_access",
    
    # Education attainment (25+)
    "B15003_001E": "total_pop_25plus",
    "B15003_002E": "no_schooling",
    "B15003_003E": "nursery_school",
    "B15003_004E": "kindergarten",
    "B15003_005E": "grade_1",
    "B15003_006E": "grade_2",
    "B15003_007E": "grade_3",
    "B15003_008E": "grade_4",
    "B15003_009E": "grade_5",
    "B15003_010E": "grade_6",
    "B15003_011E": "grade_7",
    "B15003_012E": "grade_8",
    "B15003_013E": "grade_9",
    "B15003_014E": "grade_10",
    "B15003_015E": "grade_11",
    "B15003_016E": "grade_12_no_diploma",
    "B15003_017E": "high_school_graduate",
    "B15003_018E": "ged_equivalent",
    "B15003_019E": "some_college_less_1_year",
    "B15003_020E": "some_college_1_or_more_years",
    "B15003_021E": "associates_degree",
    "B15003_022E": "bachelors_degree",
    "B15003_023E": "masters_degree",
    "B15003_024E": "professional_degree",
    "B15003_025E": "doctorate_degree",
    
    # Health insurance
    "B27001_001E": "total_pop_insurance_status",
    "B27001_005E": "uninsured_under_6",
    "B27001_008E": "uninsured_6_17",
    "B27001_011E": "uninsured_18_24",
    "B27001_014E": "uninsured_25_34",
    "B27001_017E": "uninsured_35_44",
    "B27001_020E": "uninsured_45_54",
    "B27001_023E": "uninsured_55_64",
    "B27001_026E": "uninsured_65_74",
    "B27001_029E": "uninsured_75plus",
}

def fetch_census_data(county_fips):
    """Fetch data from Census API in batches (API has variable limit)"""
    
    # If no API key, return None
    if CENSUS_API_KEY == "YOUR_KEY_HERE":
        print(f"  ⚠ No Census API key - using mock data")
        return None
    
    # Split variables into batches of 40 (API limit is ~50)
    var_keys = list(VARIABLES.keys())
    batch_size = 40
    all_data = {}
    
    for i in range(0, len(var_keys), batch_size):
        batch = var_keys[i:i + batch_size]
        var_list = ",".join(batch)
        
        params = {
            "get": var_list,
            "for": f"county:{county_fips[2:]}",  # Remove state code
            "in": f"state:{county_fips[:2]}",
            "key": CENSUS_API_KEY
        }
        
        try:
            response = requests.get(BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Parse response (first row is headers, second row is data)
            if len(data) > 1:
                headers = data[0]
                values = data[1]
                all_data.update(dict(zip(headers, values)))
        
        except Exception as e:
            print(f"  ✗ Error fetching batch {i//batch_size + 1}: {e}")
            return None
    
    return all_data if all_data else None

def calculate_derived_stats(raw_data):
    """Calculate percentages and aggregated statistics"""
    
    if not raw_data:
        return None
    
    def safe_int(val):
        try:
            return int(val) if val else 0
        except:
            return 0
    
    def safe_pct(numerator, denominator):
        try:
            num = safe_int(numerator)
            den = safe_int(denominator)
            return round((num / den * 100), 1) if den > 0 else 0
        except:
            return 0
    
    # Poverty calculations
    total_poverty_status = safe_int(raw_data.get("B17001_001E"))
    below_poverty = safe_int(raw_data.get("B17001_002E"))
    children_poverty = safe_int(raw_data.get("B17001_004E"))
    seniors_poverty = safe_int(raw_data.get("B17001_015E"))
    
    poverty_data = {
        "poverty_rate": safe_pct(below_poverty, total_poverty_status),
        "people_in_poverty": below_poverty,
        "children_in_poverty": children_poverty,
        "children_poverty_rate": safe_pct(children_poverty, total_poverty_status),
        "seniors_in_poverty": seniors_poverty,
        "seniors_poverty_rate": safe_pct(seniors_poverty, total_poverty_status)
    }
    
    # Housing affordability
    total_occupied = safe_int(raw_data.get("B25003_001E"))
    owner_occupied = safe_int(raw_data.get("B25003_002E"))
    renter_occupied = safe_int(raw_data.get("B25003_003E"))
    median_rent = safe_int(raw_data.get("B25064_001E"))
    
    # Cost burdened renters (30%+)
    renters_30_plus = (
        safe_int(raw_data.get("B25070_007E")) +
        safe_int(raw_data.get("B25070_008E")) +
        safe_int(raw_data.get("B25070_009E")) +
        safe_int(raw_data.get("B25070_010E"))
    )
    
    # Severely cost burdened renters (50%+)
    renters_50_plus = safe_int(raw_data.get("B25070_010E"))
    
    # Cost burdened owners (30%+)
    owners_30_plus = (
        safe_int(raw_data.get("B25091_008E")) +
        safe_int(raw_data.get("B25091_009E")) +
        safe_int(raw_data.get("B25091_010E")) +
        safe_int(raw_data.get("B25091_011E"))
    )
    
    # Severely cost burdened owners (50%+)
    owners_50_plus = safe_int(raw_data.get("B25091_011E"))
    
    total_renters = safe_int(raw_data.get("B25070_001E"))
    total_owners = safe_int(raw_data.get("B25091_001E"))
    
    housing_data = {
        "homeownership_rate": safe_pct(owner_occupied, total_occupied),
        "owner_occupied": owner_occupied,
        "renter_occupied": renter_occupied,
        "median_rent": median_rent,
        "renters_cost_burdened_30plus": renters_30_plus,
        "renters_cost_burdened_30plus_pct": safe_pct(renters_30_plus, total_renters),
        "renters_severely_cost_burdened_50plus": renters_50_plus,
        "renters_severely_cost_burdened_50plus_pct": safe_pct(renters_50_plus, total_renters),
        "owners_cost_burdened_30plus": owners_30_plus,
        "owners_cost_burdened_30plus_pct": safe_pct(owners_30_plus, total_owners),
        "owners_severely_cost_burdened_50plus": owners_50_plus,
        "owners_severely_cost_burdened_50plus_pct": safe_pct(owners_50_plus, total_owners)
    }
    
    # Age breakdown
    under_5 = safe_int(raw_data.get("male_under_5")) + safe_int(raw_data.get("female_under_5"))
    
    school_age = (
        safe_int(raw_data.get("male_5_9")) + safe_int(raw_data.get("male_10_14")) + safe_int(raw_data.get("male_15_17")) +
        safe_int(raw_data.get("female_5_9")) + safe_int(raw_data.get("female_10_14")) + safe_int(raw_data.get("female_15_17"))
    )
    
    seniors_65plus = (
        safe_int(raw_data.get("male_65_66")) + safe_int(raw_data.get("male_67_69")) + 
        safe_int(raw_data.get("male_70_74")) + safe_int(raw_data.get("male_75_79")) +
        safe_int(raw_data.get("male_80_84")) + safe_int(raw_data.get("male_85plus")) +
        safe_int(raw_data.get("female_65_66")) + safe_int(raw_data.get("female_67_69")) +
        safe_int(raw_data.get("female_70_74")) + safe_int(raw_data.get("female_75_79")) +
        safe_int(raw_data.get("female_80_84")) + safe_int(raw_data.get("female_85plus"))
    )
    
    total_pop = safe_int(raw_data.get("B01001_001E"))
    working_age = total_pop - under_5 - school_age - seniors_65plus
    
    age_data = {
        "under_5_years": under_5,
        "under_5_pct": safe_pct(under_5, total_pop),
        "school_age_5_17": school_age,
        "school_age_pct": safe_pct(school_age, total_pop),
        "working_age_18_64": working_age,
        "working_age_pct": safe_pct(working_age, total_pop),
        "seniors_65_plus": seniors_65plus,
        "seniors_pct": safe_pct(seniors_65plus, total_pop)
    }
    
    # Broadband access
    total_households = safe_int(raw_data.get("B28002_001E"))
    broadband = safe_int(raw_data.get("B28002_004E"))
    no_internet = safe_int(raw_data.get("B28002_013E"))
    
    broadband_data = {
        "total_households": total_households,
        "with_broadband": broadband,
        "broadband_pct": safe_pct(broadband, total_households),
        "no_internet": no_internet,
        "no_internet_pct": safe_pct(no_internet, total_households)
    }
    
    # Education attainment
    total_25plus = safe_int(raw_data.get("B15003_001E"))
    
    less_than_hs = sum([
        safe_int(raw_data.get(f"B15003_{str(i).zfill(3)}E")) 
        for i in range(2, 17)  # No schooling through grade 12 no diploma
    ])
    
    hs_grad = safe_int(raw_data.get("B15003_017E")) + safe_int(raw_data.get("B15003_018E"))
    
    some_college = (
        safe_int(raw_data.get("B15003_019E")) + 
        safe_int(raw_data.get("B15003_020E"))
    )
    
    associates = safe_int(raw_data.get("B15003_021E"))
    bachelors = safe_int(raw_data.get("B15003_022E"))
    masters = safe_int(raw_data.get("B15003_023E"))
    professional = safe_int(raw_data.get("B15003_024E"))
    doctorate = safe_int(raw_data.get("B15003_025E"))
    
    education_data = {
        "total_pop_25plus": total_25plus,
        "less_than_high_school": less_than_hs,
        "less_than_high_school_pct": safe_pct(less_than_hs, total_25plus),
        "high_school_graduate": hs_grad,
        "high_school_graduate_pct": safe_pct(hs_grad, total_25plus),
        "some_college": some_college,
        "some_college_pct": safe_pct(some_college, total_25plus),
        "associates_degree": associates,
        "associates_degree_pct": safe_pct(associates, total_25plus),
        "bachelors_degree": bachelors,
        "bachelors_degree_pct": safe_pct(bachelors, total_25plus),
        "graduate_degree": masters + professional + doctorate,
        "graduate_degree_pct": safe_pct(masters + professional + doctorate, total_25plus)
    }
    
    # Health insurance
    total_insurance_pop = safe_int(raw_data.get("B27001_001E"))
    
    total_uninsured = sum([
        safe_int(raw_data.get("B27001_005E")),  # under 6
        safe_int(raw_data.get("B27001_008E")),  # 6-17
        safe_int(raw_data.get("B27001_011E")),  # 18-24
        safe_int(raw_data.get("B27001_014E")),  # 25-34
        safe_int(raw_data.get("B27001_017E")),  # 35-44
        safe_int(raw_data.get("B27001_020E")),  # 45-54
        safe_int(raw_data.get("B27001_023E")),  # 55-64
        safe_int(raw_data.get("B27001_026E")),  # 65-74
        safe_int(raw_data.get("B27001_029E")),  # 75+
    ])
    
    children_uninsured = (
        safe_int(raw_data.get("B27001_005E")) +
        safe_int(raw_data.get("B27001_008E"))
    )
    
    health_data = {
        "uninsured_total": total_uninsured,
        "uninsured_rate": safe_pct(total_uninsured, total_insurance_pop),
        "children_uninsured": children_uninsured,
        "children_uninsured_rate": safe_pct(children_uninsured, total_insurance_pop),
        "adults_18_64_uninsured": total_uninsured - children_uninsured - safe_int(raw_data.get("B27001_026E")) - safe_int(raw_data.get("B27001_029E")),
        "seniors_65plus_uninsured": safe_int(raw_data.get("B27001_026E")) + safe_int(raw_data.get("B27001_029E"))
    }
    
    return {
        "poverty": poverty_data,
        "housing_affordability": housing_data,
        "age_breakdown": age_data,
        "broadband_access": broadband_data,
        "education_attainment_full": education_data,
        "health_insurance": health_data
    }

def main():
    print("="*60)
    print("Enhanced Census Data Fetcher")
    print("="*60)
    print()
    
    for county_key, county_info in COUNTIES.items():
        print(f"Processing {county_info['name']} County...")
        
        # Load existing census file
        census_file = Path(f"/workspaces/jour329w_fall2025/murphy/stardem_draft_v3/scraped_county_data/{county_key}/{county_key}_census.json")
        
        if not census_file.exists():
            print(f"  ✗ Census file not found: {census_file}")
            continue
        
        with open(census_file, 'r') as f:
            census_data = json.load(f)
        
        # Fetch new data
        raw_data = fetch_census_data(county_info['fips'])
        
        if raw_data:
            enhanced_data = calculate_derived_stats(raw_data)
            
            # Add to existing data
            census_data['census_api_data']['enhanced'] = enhanced_data
            census_data['last_updated'] = "2025-11-29"
            
            # Save updated file
            with open(census_file, 'w') as f:
                json.dump(census_data, f, indent=2)
            
            print(f"  ✓ Updated {census_file.name}")
        else:
            print(f"  ⚠ Could not fetch data - API key needed")
            print(f"    Get free key at: https://api.census.gov/data/key_signup.html")
        
        print()
    
    print("="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Get a free Census API key at:")
    print("   https://api.census.gov/data/key_signup.html")
    print("2. Edit this script and replace 'YOUR_KEY_HERE'")
    print("3. Run again to fetch actual data")
    print("="*60)

if __name__ == "__main__":
    main()
