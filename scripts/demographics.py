from playwright.sync_api import sync_playwright
import pandas as pd
import json
import time
import re
import os

CHECKPOINT_FILE = 'scraper_checkpoint.json'
ENROLLMENT_DATA_DIR = 'enrollment_data'

def load_checkpoint_from_files():
    """Load checkpoint data by scanning existing enrollment files"""
    completed_schools = {}
    completed_counties = []
    
    # Scan for individual school enrollment files
    if os.path.exists(ENROLLMENT_DATA_DIR):
        for filename in os.listdir(ENROLLMENT_DATA_DIR):
            if filename.startswith('enrollment_') and filename.endswith('.json'):
                # Extract county and school code from filename
                # New format: enrollment_05_0301.json -> county=05, school=0301
                # Old format: enrollment_0301.json -> school=0301
                parts = filename.replace('enrollment_', '').replace('.json', '').split('_')
                
                if len(parts) == 2:  # New format with county code
                    county_code = parts[0]
                    school_code = parts[1]
                    if county_code not in completed_schools:
                        completed_schools[county_code] = []
                    completed_schools[county_code].append(school_code)
                elif len(parts) == 1 and parts[0].isdigit() and len(parts[0]) == 4:  # Old format
                    school_code = parts[0]
                    # Determine county from school code first two digits
                    county_code = school_code[:2]
                    if county_code not in completed_schools:
                        completed_schools[county_code] = []
                    completed_schools[county_code].append(school_code)
        
        # Check for completed county files
        county_files = {
            '05': 'caroline_county_enrollment.json',
            '09': 'dorchester_county_enrollment.json',
            '14': 'kent_county_enrollment.json',
            '17': 'queen_annes_county_enrollment.json',
            '20': 'talbot_county_enrollment.json'
        }
        
        for county_code, filename in county_files.items():
            if os.path.exists(os.path.join(ENROLLMENT_DATA_DIR, filename)):
                completed_counties.append(county_code)
    
    return {'completed_counties': completed_counties, 'completed_schools': completed_schools}

def load_checkpoint():
    """Load checkpoint data from files or checkpoint file"""
    # First try to load from actual scraped files
    checkpoint = load_checkpoint_from_files()
    
    # Then merge with checkpoint file if it exists
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r') as f:
            saved_checkpoint = json.load(f)
            # Merge completed counties
            checkpoint['completed_counties'] = list(set(
                checkpoint['completed_counties'] + saved_checkpoint.get('completed_counties', [])
            ))
            # Merge completed schools
            for county, schools in saved_checkpoint.get('completed_schools', {}).items():
                if county not in checkpoint['completed_schools']:
                    checkpoint['completed_schools'][county] = []
                checkpoint['completed_schools'][county] = list(set(
                    checkpoint['completed_schools'][county] + schools
                ))
    
    return checkpoint

def save_checkpoint(checkpoint_data):
    """Save checkpoint data"""
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint_data, f, indent=2)
    print(f"✓ Checkpoint saved")

def get_all_schools(county_code):
    """
    Get list of all schools from the schools list page for a specific county
    County codes: 05=Caroline, 09=Dorchester, 14=Kent, 17=Queen Anne's, 20=Talbot
    """
    print(f"Fetching school list for county {county_code}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            url = f"https://reportcard.msde.maryland.gov/SchoolsList/Index?l={county_code}"
            page.goto(url, wait_until='networkidle', timeout=60000)
            print("Waiting for schools to load...")
            time.sleep(8)
            
            schools = []
            
            # The schools are displayed as links with school names and codes in parentheses
            # Example: "Denton Elementary School (0301)"
            
            # Wait longer and try multiple approaches
            time.sleep(5)
            
            # First, try to find table or list container
            try:
                # Wait for content to load - look for school-related text
                page.wait_for_selector('a', timeout=10000)
            except:
                print("⚠ Warning: Timeout waiting for links")
            
            # Get page content for debugging
            page_text = page.content()
            
            # Find all links that contain school codes in parentheses
            links = page.locator('a').all()
            
            print(f"Scanning {len(links)} links...")
            
            # Also try broader pattern matching on all text
            all_text = page.locator('body').text_content()
            
            for link in links:
                text = link.text_content().strip()
                
                # Look for pattern: "School Name (####)"
                match = re.match(r'(.+?)\s*\((\d{4})\)', text)
                if match:
                    school_name = match.group(1).strip()
                    school_code = match.group(2)
                    
                    schools.append({
                        'name': school_name,
                        'code': school_code
                    })
                    print(f"  Found: {school_name} ({school_code})")
            
            # If no schools found, try alternative pattern in body text
            if not schools:
                print("\n⚠ No schools found with link pattern, trying body text search...")
                # Look for school codes in format (####)
                code_pattern = re.findall(r'([^\n]+?)\s*\((\d{4})\)', all_text)
                for name, code in code_pattern:
                    name = name.strip()
                    # Filter out non-school entries
                    if len(name) > 3 and code.startswith(county_code):
                        schools.append({
                            'name': name,
                            'code': code
                        })
                        print(f"  Found in text: {name} ({code})")
            
            # Take screenshot for debugging
            screenshot_path = os.path.join(ENROLLMENT_DATA_DIR, 'pngs', f'schools_list_{county_code}.png')
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"\n✓ Saved {screenshot_path}")
            
            print(f"\nTotal schools found: {len(schools)}")
            
            return schools
            
        except Exception as e:
            print(f"Error fetching schools: {e}")
            import traceback
            traceback.print_exc()
            return []
            
        finally:
            browser.close()


def extract_from_table(page):
    """
    Extract enrollment number from the data table
    """
    try:
        # Wait for table to appear
        time.sleep(2)
        
        # Look for table rows
        table = page.locator('table').first
        
        if table.is_visible(timeout=3000):
            rows = table.locator('tr').all()
            
            for row in rows:
                cells = row.locator('td').all()
                if len(cells) >= 3:
                    year = cells[0].text_content().strip()
                    group = cells[1].text_content().strip()
                    number = cells[2].text_content().strip()
                    
                    # Check if suppressed data (*)
                    if number.strip() == '*':
                        return '*'
                    
                    # Make sure it's a data row with 2025
                    if year == '2025' and number.replace(',', '').isdigit():
                        return int(number.replace(',', ''))
        
        # If table not visible, look in the chart text
        body_text = page.locator('body').text_content()
        
        # Look for "Number of Students" pattern
        match = re.search(r'Number of Students[^0-9*]+([0-9*]+|[\*])', body_text)
        if match:
            val = match.group(1).strip()
            if val == '*':
                return '*'
            if val.isdigit():
                return int(val)
                
    except Exception as e:
        print(f"    Error in extract_from_table: {e}")
    
    return None


def scrape_enrollment(page, school_code, school_name, county_code):
    """
    Scrape enrollment data for all demographic breakdowns
    """
    base_url = f"https://reportcard.msde.maryland.gov/Graphs/#/Demographics/Enrollment/3/17/6/{county_code}/{school_code}/2025"
    
    enrollment_data = []
    
    demographics = {
        'Race/Ethnicity': [
            'All Students', 'Asian', 'African Am.', 'Hispanic', 'White',
            'Am.Ind/AK', 'HI/Pac.Isl.', '2+'
        ],
        'Gender': ['All Students', 'Male', 'Female'],
        'Grade': [
            'All Students', 'Pre-Kindergarten', 'Kindergarten',
            'Grade 1', 'Grade 2', 'Grade 3', 'Grade 4', 'Grade 5', 'Elementary'
        ]
    }
    
    # Navigate to enrollment page
    print(f"\nNavigating to: {base_url}")
    try:
        page.goto(base_url, wait_until='networkidle', timeout=90000)
        time.sleep(10)
    except Exception as e:
        print(f"⚠ Navigation timeout or error: {e}")
        print("Attempting to continue anyway...")
        time.sleep(5)
    
    for category, options in demographics.items():
        print(f"\n--- {category.upper()} ---")
        
        for display_name in options:
            try:
                print(f"Processing: {display_name}")
                
                # Refresh page
                page.goto(base_url, wait_until='networkidle', timeout=60000)
                time.sleep(5)
                
                # Use JavaScript to click option
                script = f"""
                (async function() {{
                    const links = Array.from(document.querySelectorAll('a.cbox__link'));
                    const option = links.find(l => l.textContent.trim() === '{display_name}');
                    
                    if (option) {{
                        const button = option.closest('.cbox').querySelector('button');
                        if (button) {{
                            button.click();
                            await new Promise(r => setTimeout(r, 1000));
                        }}
                        option.click();
                        await new Promise(r => setTimeout(r, 2000));
                        return true;
                    }}
                    return false;
                }})()
                """
                
                result = page.evaluate(script)
                
                if result:
                    time.sleep(3)
                    
                    # Click "Show Table"
                    try:
                        show_table = page.locator('text="Show Table"').first
                        if show_table.is_visible(timeout=2000):
                            show_table.click()
                            time.sleep(2)
                    except:
                        pass
                    
                    enrollment = extract_from_table(page)
                    
                    if enrollment:
                        enrollment_data.append({
                            'category': category,
                            'group': display_name,
                            'enrollment': enrollment,
                            'year': '2025'
                        })
                        print(f"  ✓ {display_name}: {enrollment} students")
                    else:
                        print(f"  ✗ Could not extract enrollment")
                else:
                    print(f"  ✗ Could not select option")
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
    
    return enrollment_data


def scrape_attendance(page, school_code, school_name, county_code):
    """
    Scrape chronic absenteeism attendance data - includes all race/ethnicity breakdowns
    """
    url = f"https://reportcard.msde.maryland.gov/Graphs/#/Demographics/Attendance/3/17/6/{county_code}/{school_code}/2025"
    
    print(f"\nNavigating to: {url}")
    page.goto(url, wait_until='networkidle', timeout=60000)
    time.sleep(10)
    
    attendance_data = []
    
    # Click "Show Table" to see the data
    try:
        show_table = page.locator('text="Show Table"').first
        if show_table.is_visible(timeout=3000):
            show_table.click()
            time.sleep(4)
            print("✓ Showed table")
        else:
            hide_table = page.locator('text="Hide Table"').first
            if hide_table.is_visible(timeout=2000):
                print("✓ Table already visible")
    except Exception as e:
        print(f"Could not click Show Table: {e}")
    
    # Extract table data
    try:
        time.sleep(2)
        table = page.locator('table').first
        
        if table.is_visible(timeout=5000):
            # Get headers
            headers = []
            header_cells = table.locator('th').all()
            headers = [h.text_content().strip() for h in header_cells if h.text_content().strip()]
            print(f"Headers: {headers}")
            
            # Get all rows
            rows = table.locator('tbody tr').all()
            print(f"Found {len(rows)} data rows")
            
            for row in rows:
                cells = row.locator('td').all()
                if cells:
                    row_data = {}
                    for i, cell in enumerate(cells):
                        cell_text = cell.text_content().strip()
                        header = headers[i] if i < len(headers) else f'Column_{i}'
                        row_data[header] = cell_text
                    
                    if row_data:
                        attendance_data.append(row_data)
                        # Show abbreviated output
                        race = row_data.get('Race/Ethnicity', 'Unknown')
                        rate = row_data.get('Chronic Absenteeism Rate (%) (All Students)', 'N/A')
                        count = row_data.get('Count chronically absent/Total Students (All Students)', 'N/A')
                        print(f"  ✓ {race}: {rate}% (Count: {count})")
        else:
            print("Table not visible")
    
    except Exception as e:
        print(f"Error extracting attendance table: {e}")
        import traceback
        traceback.print_exc()
    
    return attendance_data


def scrape_student_groups(page, school_code, school_name, county_code):
    """
    Scrape student group populations data - includes all special services groups
    """
    url = f"https://reportcard.msde.maryland.gov/Graphs/#/Demographics/StudentGroupPopulations/3/17/6/{county_code}/{school_code}/2025"
    
    print(f"\nNavigating to: {url}")
    page.goto(url, wait_until='networkidle', timeout=60000)
    time.sleep(12)  # Even longer wait
    
    student_groups_data = []
    
    # Verify we're on the correct page by checking the URL hash
    current_url = page.url
    print(f"Current URL: {current_url}")
    
    if 'StudentGroupPopulations' not in current_url:
        print("⚠ Warning: URL doesn't contain 'StudentGroupPopulations'. Trying to navigate again...")
        # Try clicking the Student Group Populations link from sidebar
        try:
            nav_link = page.locator('text="Student Group Populations"').first
            if nav_link.is_visible(timeout=3000):
                nav_link.click()
                time.sleep(5)
                print("✓ Clicked Student Group Populations navigation")
        except:
            pass
    
    # Wait for specific text that only appears on student groups page
    try:
        # Look for student group names that would only be on this page
        page.wait_for_selector('text=/FARMS|Eco Disadv|SWD/i', timeout=10000)
        print("✓ Detected student groups page content")
    except:
        print("⚠ Could not verify student groups content")
    
    # Click "Show Table"
    try:
        show_table = page.locator('text="Show Table"').first
        if show_table.is_visible(timeout=3000):
            show_table.click()
            time.sleep(4)
            print("✓ Showed table")
        else:
            hide_table = page.locator('text="Hide Table"').first
            if hide_table.is_visible(timeout=2000):
                print("✓ Table already visible")
    except Exception as e:
        print(f"Could not click Show Table: {e}")
    
    # Extract table data
    try:
        time.sleep(2)
        table = page.locator('table').first
        
        if table.is_visible(timeout=5000):
            # Get headers
            headers = []
            header_cells = table.locator('th').all()
            headers = [h.text_content().strip() for h in header_cells if h.text_content().strip()]
            print(f"Headers: {headers}")
            
            # Verify we have the right table
            if 'Student Group' not in headers or 'Result' not in ' '.join(headers):
                print(f"⚠ ERROR: Wrong table! Expected 'Student Group' and 'Result' in headers.")
                print(f"This appears to be the enrollment table instead of student groups.")
                print(f"Skipping this section...")
                return []
            
            # Get all rows
            rows = table.locator('tbody tr').all()
            print(f"Found {len(rows)} data rows")
            
            for row in rows:
                cells = row.locator('td').all()
                if cells:
                    row_data = {}
                    for i, cell in enumerate(cells):
                        cell_text = cell.text_content().strip()
                        header = headers[i] if i < len(headers) else f'Column_{i}'
                        row_data[header] = cell_text
                    
                    if row_data:
                        student_groups_data.append(row_data)
                        # Show abbreviated output
                        group = row_data.get('Student Group', 'Unknown')
                        result = row_data.get('Result (%) (All Students)', 'N/A')
                        count = row_data.get('Count', 'N/A')
                        total = row_data.get('Total', 'N/A')
                        print(f"  ✓ {group}: {result}% ({count}/{total} students)")
        else:
            print("Table not visible")
    
    except Exception as e:
        print(f"Error extracting student groups table: {e}")
        import traceback
        traceback.print_exc()
    
    return student_groups_data


def scrape_school_demographics(school_code, school_name="", county_code="05"):
    """
    Scrape enrollment demographic data for a school
    """
    
    print("Starting browser...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()
        
        try:
            school_name_display = school_name or f"School {school_code}"
            
            all_data = {
                'school_name': school_name_display,
                'school_code': school_code,
                'county_code': county_code,
                'enrollment_data': []
            }
            
            print("\n" + "="*80)
            print("SCRAPING ENROLLMENT DATA")
            print("="*80)
            
            enrollment_data = scrape_enrollment(page, school_code, school_name_display, county_code)
            all_data['enrollment_data'] = enrollment_data
            
            # Save data
            print("\n" + "="*80)
            print("SAVING DATA")
            print("="*80)
            
            # Ensure enrollment_data directory exists
            os.makedirs(ENROLLMENT_DATA_DIR, exist_ok=True)
            
            # Include county code in filename to avoid overwriting schools with same code
            filename_base = f'enrollment_{county_code}_{school_code}'
            json_path = os.path.join(ENROLLMENT_DATA_DIR, f'{filename_base}.json')
            csv_path = os.path.join(ENROLLMENT_DATA_DIR, f'{filename_base}.csv')
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=2, ensure_ascii=False)
            print(f"✓ Saved {json_path}")
            
            # Save enrollment CSV
            if all_data['enrollment_data']:
                df = pd.DataFrame(all_data['enrollment_data'])
                df.to_csv(csv_path, index=False)
                print(f"✓ Saved {csv_path}")
                
                print("\n" + "="*80)
                print("ENROLLMENT SUMMARY")
                print("="*80)
                print(f"Total records: {len(all_data['enrollment_data'])}")
            
            print("\n" + "="*80)
            print("SCRAPING COMPLETE!")
            print("="*80)
            
            return all_data
            
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
            return None
                
        finally:
            print("\nClosing browser...")
            browser.close()


if __name__ == "__main__":
    print("Maryland School Enrollment Scraper - Multiple Counties")
    print("="*80)
    print("\nThis will scrape ENROLLMENT data only for multiple counties")
    print("\n" + "="*80 + "\n")
    
    # Load checkpoint to resume from where we left off
    checkpoint = load_checkpoint()
    completed_counties = set(checkpoint.get('completed_counties', []))
    completed_schools = checkpoint.get('completed_schools', {})
    
    if completed_counties or completed_schools:
        print("\n⚠ RESUMING FROM CHECKPOINT")
        print(f"  Completed counties: {list(completed_counties)}")
        for county, schools in completed_schools.items():
            if schools:
                print(f"  Completed schools in {county}: {len(schools)}")
        print()
    
    # Define counties to scrape
    counties = {
        '05': 'Caroline County',
        '09': 'Dorchester County',
        '14': 'Kent County',
        '17': "Queen Anne's County",
        '20': 'Talbot County'
    }
    
    all_counties_data = []
    
    for county_code, county_name in counties.items():
        # Skip county if already completed
        if county_code in completed_counties:
            print(f"\n✓ SKIPPING {county_name} (already completed)")
            continue
         
        print(f"\n{'#'*80}")
        print(f"# PROCESSING: {county_name} (Code: {county_code})")
        print(f"{'#'*80}\n")
        
        try:
            # Get schools for this county
            schools = get_all_schools(county_code)
            
            if not schools:
                print(f"No schools found for {county_name}. Skipping.")
                continue
            
            # Initialize completed schools list for this county if not exists
            if county_code not in completed_schools:
                completed_schools[county_code] = []
            
            completed_in_county = set(completed_schools[county_code])
            
            print(f"\nFound {len(schools)} schools in {county_name}.")
            if completed_in_county:
                print(f"Resuming: {len(completed_in_county)} already completed, {len(schools) - len(completed_in_county)} remaining\n")
            else:
                print(f"Starting scrape...\n")
            
            for i, school in enumerate(schools, 1):
                # Skip school if already completed
                if school['code'] in completed_in_county:
                    print(f"\n✓ SKIPPING SCHOOL {i}/{len(schools)}: {school['name']} ({school['code']}) - already completed")
                    continue
                
                print(f"\n{'='*80}")
                print(f"SCHOOL {i}/{len(schools)}: {school['name']} ({school['code']})")
                print(f"{'='*80}")
                
                try:
                    data = scrape_school_demographics(school['code'], school['name'], county_code)
                    if data:
                        data['county_name'] = county_name
                        all_counties_data.append(data)
                        
                        # Mark this school as completed and save checkpoint
                        completed_schools[county_code].append(school['code'])
                        checkpoint['completed_schools'] = completed_schools
                        save_checkpoint(checkpoint)
                    else:
                        print(f"⚠ Warning: No data returned for {school['name']}, but continuing...")
                        # Still mark as attempted to avoid re-trying
                        completed_schools[county_code].append(school['code'])
                        checkpoint['completed_schools'] = completed_schools
                        save_checkpoint(checkpoint)
                        
                    # Longer delay between schools to prevent timeouts
                    if i < len(schools):
                        print(f"Waiting 5 seconds before next school...")
                        time.sleep(5)
                        
                except KeyboardInterrupt:
                    print("\n⚠ Interrupted by user. Progress has been saved.")
                    raise
                except Exception as e:
                    print(f"⚠ Error scraping {school['name']}: {e}")
                    import traceback
                    traceback.print_exc()
                    # Mark as attempted even on error to skip on retry
                    completed_schools[county_code].append(school['code'])
                    checkpoint['completed_schools'] = completed_schools
                    save_checkpoint(checkpoint)
                    print(f"Continuing to next school...")
                    time.sleep(5)
                    continue
            
            # Save county-specific master file
            county_filename = county_name.lower().replace("'", "").replace(" ", "_")
            
            county_schools = [d for d in all_counties_data if d.get('county_name') == county_name]
            
            county_json_path = os.path.join(ENROLLMENT_DATA_DIR, f'{county_filename}_enrollment.json')
            with open(county_json_path, 'w', encoding='utf-8') as f:
                json.dump(county_schools, f, indent=2, ensure_ascii=False)
            print(f"\n✓ Saved {county_json_path}")
            
            # Mark this county as completed in checkpoint
            completed_counties.add(county_code)
            checkpoint['completed_counties'] = list(completed_counties)
            save_checkpoint(checkpoint)
            
        except Exception as e:
            print(f"\nError processing {county_name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Create master files for all counties combined
    print(f"\n{'='*80}")
    print("CREATING MASTER FILES FOR ALL COUNTIES")
    print(f"{'='*80}")
    
    all_json_path = os.path.join(ENROLLMENT_DATA_DIR, 'all_counties_enrollment.json')
    with open(all_json_path, 'w', encoding='utf-8') as f:
        json.dump(all_counties_data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved {all_json_path}")
    
    # Create combined enrollment CSV
    enrollment_rows = []
    for school_data in all_counties_data:
        for enrollment in school_data.get('enrollment_data', []):
            enrollment_rows.append({
                'county_name': school_data.get('county_name', ''),
                'county_code': school_data.get('county_code', ''),
                'school_name': school_data['school_name'],
                'school_code': school_data['school_code'],
                'category': enrollment['category'],
                'group': enrollment['group'],
                'enrollment': enrollment['enrollment'],
                'year': enrollment['year']
            })
    
    if enrollment_rows:
        df = pd.DataFrame(enrollment_rows)
        all_csv_path = os.path.join(ENROLLMENT_DATA_DIR, 'all_counties_enrollment.csv')
        df.to_csv(all_csv_path, index=False)
        print(f"✓ Saved {all_csv_path} ({len(enrollment_rows)} records)")
    
    print(f"\n{'='*80}")
    print("ALL COUNTIES COMPLETE!")
    print(f"{'='*80}")
    print(f"\nTotal schools scraped: {len(all_counties_data)}")
    print(f"Total enrollment records: {len(enrollment_rows)}")