from playwright.sync_api import sync_playwright
import json
from pathlib import Path
from datetime import datetime
import time
import re

def scrape_with_playwright(county_key, county_name, url):
    """Use Playwright to scrape JavaScript-rendered pages"""
    
    meetings = []
    
    try:
        with sync_playwright() as p:
            print(f"  Launching browser for {county_name}...")
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            print(f"  Loading {url}...")
            page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait a bit for JavaScript to fully load
            page.wait_for_timeout(3000)
            
            # Get page content
            content = page.content()
            
            # Look for meeting items - these vary by site
            # Try to find meeting rows/items
            meeting_items = page.query_selector_all('[class*="meeting"], [class*="agenda"], .catAgendaRow, .catAgendaItem')
            
            print(f"    Found {len(meeting_items)} potential meeting items")
            
            for item in meeting_items[:20]:  # Limit to 20
                try:
                    # Try to extract date
                    date_elem = item.query_selector('[class*="date"], .catAgendaDate, [class*="Date"]')
                    date_text = date_elem.inner_text().strip() if date_elem else "Date unknown"
                    
                    # Try to find document links
                    links = item.query_selector_all('a[href]')
                    
                    for link in links:
                        link_text = link.inner_text().strip()
                        href = link.get_attribute('href')
                        
                        if href and any(word in link_text.lower() for word in ['minutes', 'agenda', 'packet']):
                            # Make absolute URL
                            if href.startswith('/'):
                                base = '/'.join(url.split('/')[:3])
                                href = base + href
                            elif not href.startswith('http'):
                                href = url + '/' + href
                            
                            meetings.append({
                                "date": date_text,
                                "title": link_text[:100],
                                "url": href,
                                "type": "minutes" if "minute" in link_text.lower() else "agenda"
                            })
                
                except Exception as e:
                    continue
            
            # Alternative: look for all PDF links
            if len(meetings) < 5:
                print(f"    Trying alternative method - looking for PDF links...")
                pdf_links = page.query_selector_all('a[href*=".pdf"], a[href*="ViewFile"], a[href*="Download"]')
                
                for link in pdf_links[:20]:
                    try:
                        link_text = link.inner_text().strip()
                        href = link.get_attribute('href')
                        
                        if href and any(word in link_text.lower() for word in ['minutes', 'agenda', 'meeting']):
                            if href.startswith('/'):
                                base = '/'.join(url.split('/')[:3])
                                href = base + href
                            elif not href.startswith('http'):
                                href = url + '/' + href
                            
                            meetings.append({
                                "date": "Check document",
                                "title": link_text[:100],
                                "url": href,
                                "type": "document"
                            })
                    except:
                        continue
            
            browser.close()
            print(f"    Extracted {len(meetings)} meeting documents")
            
    except Exception as e:
        print(f"    Error: {e}")
    
    return meetings

def main():
    counties = [
        ('talbot', 'Talbot', 'https://www.talbotcountymd.gov/AgendaCenter/County-Council-3'),
        ('dorchester', 'Dorchester', 'https://docogonet.com/AgendaCenter/County-Council-1'),
        ('kent', 'Kent', 'https://www.kentcounty.com/AgendaCenter/Commissioners-1'),
        ('queen_annes', "Queen Anne's", 'https://www.qac.org/AgendaCenter/Commissioners-1'),
        ('caroline', 'Caroline', 'https://www.carolinemd.org/AgendaCenter/Commissioners-1')
    ]
    
    output_dir = Path("../scraped_data")
    all_results = {}
    
    for county_key, county_name, url in counties:
        print(f"\nScraping {county_name} County meeting minutes...")
        
        meetings = scrape_with_playwright(county_key, county_name, url)
        
        data = {
            "county_name": county_name,
            "scraped_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_url": url,
            "meeting_documents": meetings,
            "total_found": len(meetings)
        }
        
        # Save individual county file
        county_dir = output_dir / county_key
        county_dir.mkdir(exist_ok=True)
        
        output_file = county_dir / f"{county_key}_minutes.json"
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Saved to {output_file}")
        
        all_results[county_key] = data
        
        time.sleep(2)
    
    # Save combined file
    combined_file = output_dir / "counties_minutes.json"
    with open(combined_file, 'w') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for county_key, data in all_results.items():
        print(f"{data['county_name']:15s}: {data['total_found']:2d} documents")
    
    print(f"\n✓ Combined data saved to {combined_file}")

if __name__ == "__main__":
    main()
