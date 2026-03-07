#!/usr/bin/env python3
"""
Scrape student demographic data from MSDE Report Card for multiple years
Using the publicly available data downloads

Usage:
    python scrape_msde_data_multi_year.py --years 2023 2022 2021
    python scrape_msde_data_multi_year.py --start-year 2021 --end-year 2024
"""

import requests
import json
import argparse
from pathlib import Path
import pandas as pd
import sys

# County codes for filtering data
COUNTIES = {
    "kent": {"lss_number": "13", "name": "Kent County"},
    "dorchester": {"lss_number": "09", "name": "Dorchester County"},
    "caroline": {"lss_number": "05", "name": "Caroline County"},
    "queen_annes": {"lss_number": "17", "name": "Queen Anne's County"},
    "talbot": {"lss_number": "20", "name": "Talbot County"}
}

def get_msde_data_urls(year):
    """
    Generate MSDE data download URLs for a given year
    MSDE typically publishes data in fall for the previous school year
    e.g., in fall 2024, they publish 2023-2024 school year data (labeled as 2024)
    """
    # The folder year is typically one year ahead of the data year
    folder_year = int(year) + 1
    
    base_url = f"https://reportcard.msde.maryland.gov/DataDownloads/{folder_year}"
    
    data_files = {
        "enrollment": f"{base_url}/{year}/Enrollment_{year}.csv",
        "attendance": f"{base_url}/{year}/Attendance_{year}.csv",
        "demographics": f"{base_url}/{year}/Demographics_{year}.csv",
        "student_group": f"{base_url}/{year}/StudentGroup_{year}.csv",
    }
    
    return data_files

def fetch_msde_file(url, data_type, year):
    """Fetch a single MSDE data file"""
    print(f"  Fetching {data_type} for {year}...")
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            print(f"    ✓ Successfully downloaded {data_type}")
            return response.text
        else:
            print(f"    ✗ Failed: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return None

def filter_county_data(df, county_lss_numbers):
    """Filter dataframe to only include our counties"""
    # Common column names in MSDE data
    lss_columns = ['LSS Number', 'LSS_NUMBER', 'LEA Number', 'LEA_NUMBER', 'LEA']
    
    for col in lss_columns:
        if col in df.columns:
            # Convert to string and pad with zeros if needed
            df[col] = df[col].astype(str).str.zfill(2)
            return df[df[col].isin(county_lss_numbers)]
    
    print(f"    ⚠ Warning: Could not find LSS/LEA column. Available columns: {df.columns.tolist()}")
    return df

def process_year_data(year, output_dir):
    """Process all data files for a given year"""
    print(f"\n{'='*60}")
    print(f"Processing Year: {year}")
    print(f"{'='*60}")
    
    data_urls = get_msde_data_urls(year)
    county_lss_numbers = [info['lss_number'] for info in COUNTIES.values()]
    
    year_data = {}
    
    for data_type, url in data_urls.items():
        print(f"\n{data_type.upper()}:")
        print(f"  URL: {url}")
        
        csv_content = fetch_msde_file(url, data_type, year)
        
        if csv_content:
            try:
                # Parse CSV
                from io import StringIO
                df = pd.read_csv(StringIO(csv_content))
                
                print(f"    Total records: {len(df)}")
                
                # Filter to our counties
                filtered_df = filter_county_data(df, county_lss_numbers)
                print(f"    County records: {len(filtered_df)}")
                
                if len(filtered_df) > 0:
                    # Save filtered data
                    output_file = output_dir / f"{data_type}_{year}.csv"
                    filtered_df.to_csv(output_file, index=False)
                    print(f"    💾 Saved to: {output_file}")
                    
                    year_data[data_type] = {
                        "file": str(output_file),
                        "records": len(filtered_df),
                        "schools": filtered_df.get('School Name', filtered_df.get('School_Name', pd.Series([]))).nunique()
                    }
                else:
                    print(f"    ⚠ No county data found")
                    
            except Exception as e:
                print(f"    ✗ Error processing CSV: {e}")
        else:
            print(f"    ⚠ Skipping {data_type}")
    
    return year_data

def create_summary_report(all_data, output_dir):
    """Create a summary report of all collected data"""
    print(f"\n{'='*60}")
    print("SUMMARY REPORT")
    print(f"{'='*60}\n")
    
    summary = {
        "collection_date": pd.Timestamp.now().isoformat(),
        "years_processed": list(all_data.keys()),
        "counties": list(COUNTIES.keys()),
        "data_by_year": all_data
    }
    
    # Save JSON summary
    summary_file = output_dir / "collection_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"📊 Summary saved to: {summary_file}\n")
    
    # Print summary table
    print("Data Collection Summary:")
    print("-" * 60)
    for year in sorted(all_data.keys()):
        print(f"\n{year}:")
        year_data = all_data[year]
        if year_data:
            for data_type, info in year_data.items():
                print(f"  {data_type:20} {info['records']:5} records, {info.get('schools', 0):3} schools")
        else:
            print("  No data collected")
    
    return summary

def main():
    parser = argparse.ArgumentParser(
        description='Fetch MSDE student demographic data for multiple years'
    )
    parser.add_argument(
        '--years',
        nargs='+',
        type=int,
        help='Specific years to fetch (e.g., 2023 2022 2021)'
    )
    parser.add_argument(
        '--start-year',
        type=int,
        help='Start year for range (inclusive)'
    )
    parser.add_argument(
        '--end-year',
        type=int,
        help='End year for range (inclusive)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='msde_historical_data',
        help='Output directory for downloaded data (default: msde_historical_data)'
    )
    
    args = parser.parse_args()
    
    # Determine which years to process
    if args.years:
        years = args.years
    elif args.start_year and args.end_year:
        years = list(range(args.start_year, args.end_year + 1))
    else:
        # Default: last 3 years
        current_year = 2024
        years = [current_year, current_year - 1, current_year - 2]
        print(f"No years specified. Defaulting to: {years}")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    print(f"\n📁 Output directory: {output_dir.absolute()}")
    
    # Process each year
    all_data = {}
    for year in sorted(years, reverse=True):  # Process newest first
        try:
            year_data = process_year_data(year, output_dir)
            all_data[str(year)] = year_data
        except Exception as e:
            print(f"\n❌ Error processing year {year}: {e}")
            all_data[str(year)] = {}
    
    # Create summary report
    if all_data:
        create_summary_report(all_data, output_dir)
    
    print(f"\n✅ Done! Check {output_dir} for all downloaded data.")
    print(f"\n💡 Next steps:")
    print(f"   1. Review the CSV files in {output_dir}")
    print(f"   2. Check collection_summary.json for overview")
    print(f"   3. Use this data to populate your county demographics files")

if __name__ == "__main__":
    main()
