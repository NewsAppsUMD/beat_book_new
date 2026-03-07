from playwright.sync_api import sync_playwright
import pandas as pd
import json
import time
import re

def get_all_schools(county_code):
    """Get list of all schools for a county"""
    print(f"Fetching school list for county {county_code}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            url = f"https://reportcard.msde.maryland.gov/SchoolsList/Index?l={county_code}"
            page.goto(url, wait_until='networkidle', timeout=60000)
            time.sleep(8)
            
            schools = []
            links = page.locator('a').all()
            
            for link in links:
                text = link.text_content().strip()
                match = re.match(r'(.+?)\s*\((\d{4})\)', text)
                if match:
                    schools.append({
                        'name': match.group(1).strip(),
                        'code': match.group(2)
                    })
            
            print(f"Found {len(schools)} schools")
            return schools
            
        finally:
            browser.close()


def scrape_attendance_and_groups(school_code, school_name, county_code):
    """Scrape both attendance and student groups for one school"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()
        
        data = {
            'school_name': school_name,
            'school_code': school_code,
            'county_code': county_code,
            'attendance_data': [],
            'student_groups_data': []
        }
        
        try:
            # ATTENDANCE
            print(f"\n--- Scraping Attendance ---")
            attendance_url = f"https://reportcard.msde.maryland.gov/Graphs/#/Demographics/Attendance/3/17/6/{county_code}/{school_code}/2025"
            page.goto(attendance_url, wait_until='networkidle', timeout=60000)
            time.sleep(8)
            
            # Click Attendance in sidebar
            try:
                att_link = page.locator('a:has-text("Attendance")').first
                att_link.click()
                time.sleep(5)
                print("✓ Clicked Attendance")
            except:
                print("⚠ Could not click Attendance")
            
            # Show table
            try:
                show_btn = page.locator('text="Show Table"').first
                if show_btn.is_visible(timeout=2000):
                    show_btn.click()
                    time.sleep(3)
            except:
                pass
            
            # Extract attendance table
            try:
                table = page.locator('table').first
                if table.is_visible(timeout=5000):
                    headers = [h.text_content().strip() for h in table.locator('th').all()]
                    print(f"Headers: {headers}")
                    
                    rows = table.locator('tbody tr').all()
                    for row in rows:
                        cells = row.locator('td').all()
                        if cells:
                            row_data = {}
                            for i, cell in enumerate(cells):
                                header = headers[i] if i < len(headers) else f'Column_{i}'
                                row_data[header] = cell.text_content().strip()
                            if row_data:
                                data['attendance_data'].append(row_data)
                    
                    print(f"✓ Scraped {len(data['attendance_data'])} attendance rows")
            except Exception as e:
                print(f"✗ Attendance error: {e}")
            
            # STUDENT GROUPS
            print(f"\n--- Scraping Student Groups ---")
            groups_url = f"https://reportcard.msde.maryland.gov/Graphs/#/Demographics/StudentGroupPopulations/3/17/6/{county_code}/{school_code}/2025"
            page.goto(groups_url, wait_until='networkidle', timeout=60000)
            time.sleep(8)
            
            # Click Student Group Populations in sidebar
            try:
                sg_link = page.locator('a:has-text("Student Group Populations")').first
                sg_link.click()
                time.sleep(5)
                print("✓ Clicked Student Group Populations")
            except:
                print("⚠ Could not click Student Group Populations")
            
            # Show table
            try:
                show_btn = page.locator('text="Show Table"').first
                if show_btn.is_visible(timeout=2000):
                    show_btn.click()
                    time.sleep(3)
            except:
                pass
            
            # Extract student groups table
            try:
                table = page.locator('table').first
                if table.is_visible(timeout=5000):
                    headers = [h.text_content().strip() for h in table.locator('th').all()]
                    print(f"Headers: {headers}")
                    
                    # Verify correct table
                    if 'Student Group' in headers and 'Result' in ' '.join(headers):
                        rows = table.locator('tbody tr').all()
                        for row in rows:
                            cells = row.locator('td').all()
                            if cells:
                                row_data = {}
                                for i, cell in enumerate(cells):
                                    header = headers[i] if i < len(headers) else f'Column_{i}'
                                    row_data[header] = cell.text_content().strip()
                                if row_data:
                                    data['student_groups_data'].append(row_data)
                        
                        print(f"✓ Scraped {len(data['student_groups_data'])} student group rows")
                    else:
                        print(f"✗ Wrong table (wrong headers)")
            except Exception as e:
                print(f"✗ Student groups error: {e}")
            
        finally:
            browser.close()
        
        return data


if __name__ == "__main__":
    print("Attendance & Student Groups Scraper")
    print("="*80)
    
    counties = {
        '05': 'Caroline County',
        '09': 'Dorchester County',
        '14': 'Kent County',
        '17': "Queen Anne's County",
        '20': 'Talbot County'
    }
    
    all_data = []
    
    for county_code, county_name in counties.items():
        print(f"\n{'#'*80}")
        print(f"# {county_name} (Code: {county_code})")
        print(f"{'#'*80}")
        
        schools = get_all_schools(county_code)
        
        if not schools:
            print(f"No schools found for {county_name}")
            continue
        
        for i, school in enumerate(schools, 1):
            print(f"\n[{i}/{len(schools)}] {school['name']} ({school['code']})")
            
            try:
                data = scrape_attendance_and_groups(school['code'], school['name'], county_code)
                data['county_name'] = county_name
                all_data.append(data)
                
                # Save individual school file
                with open(f"att_groups_{county_code}_{school['code']}.json", 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                time.sleep(3)  # Delay between schools
                
            except Exception as e:
                print(f"✗ Error: {e}")
                continue
    
    # Save master files
    print(f"\n{'='*80}")
    print("SAVING MASTER FILES")
    print(f"{'='*80}")
    
    with open('all_attendance_groups.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2)
    print("✓ Saved all_attendance_groups.json")
    
    # Attendance CSV
    att_rows = []
    for school in all_data:
        for att in school.get('attendance_data', []):
            att_copy = att.copy()
            att_copy['county_name'] = school.get('county_name', '')
            att_copy['county_code'] = school.get('county_code', '')
            att_copy['school_name'] = school['school_name']
            att_copy['school_code'] = school['school_code']
            att_rows.append(att_copy)
    
    if att_rows:
        df = pd.DataFrame(att_rows)
        df.to_csv('all_attendance.csv', index=False)
        print(f"✓ Saved all_attendance.csv ({len(att_rows)} records)")
    
    # Student groups CSV
    sg_rows = []
    for school in all_data:
        for sg in school.get('student_groups_data', []):
            sg_copy = sg.copy()
            sg_copy['county_name'] = school.get('county_name', '')
            sg_copy['county_code'] = school.get('county_code', '')
            sg_copy['school_name'] = school['school_name']
            sg_copy['school_code'] = school['school_code']
            sg_rows.append(sg_copy)
    
    if sg_rows:
        df = pd.DataFrame(sg_rows)
        df.to_csv('all_student_groups.csv', index=False)
        print(f"✓ Saved all_student_groups.csv ({len(sg_rows)} records)")
    
    print(f"\n{'='*80}")
    print("COMPLETE!")
    print(f"{'='*80}")
    print(f"Schools scraped: {len(all_data)}")
    print(f"Attendance records: {len(att_rows)}")
    print(f"Student group records: {len(sg_rows)}")