import requests
from bs4 import BeautifulSoup
import json
import time
import re

# Counties and their codes
COUNTIES = {
    'Dorchester': 'do',
    'Queen Annes': 'qa',
    'Talbot': 'ta',
    'Kent': 'ke',
    'Caroline': 'caro'
}

# URLs to scrape for each county (based on actual page structure)
def get_county_urls(county_code):
    """Generate list of URLs to scrape for a county"""
    base = f'https://msa.maryland.gov/msa/mdmanual/36loc/{county_code}'
    
    return {
        'main': f'{base}/html/{county_code}.html',
        'budget': f'{base}/html/{county_code}b.html',
        'election_returns': f'{base}/elect/general/00list.html',
        'executive_branch': f'{base}/html/{county_code}ex.html',
        'historical_chronology': f'{base}/chron/html/{county_code}chron.html',
        'judicial_branch': f'{base}/html/{county_code}j.html',
        'legislative_branch': f'{base}/html/{county_code}l.html',
        'municipalities': f'{base}/html/{county_code}mu.html',
        'records': f'{base}/records/html/00list.html',
    }

def scrape_page(url, county, section):
    """Scrape a single page and extract relevant information"""
    try:
        print(f"Scraping {county} - {section}: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text(strip=True) if title else 'No title'
        
        # Extract main content
        # Note: These pages have malformed HTML with no proper body tag
        # Just get all text from the soup
        text_content = soup.get_text(separator='\n', strip=True)
        
        # Extract tables (often contain official rosters)
        tables = []
        for table in soup.find_all('table'):
            table_data = []
            for row in table.find_all('tr'):
                cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                if cells:
                    table_data.append(cells)
            if table_data:
                tables.append(table_data)
        
        # Extract lists (often contain officials)
        lists = []
        for ul in soup.find_all(['ul', 'ol']):
            items = [li.get_text(strip=True) for li in ul.find_all('li')]
            if items:
                lists.append(items)
        
        return {
            'url': url,
            'title': title_text,
            'text_content': text_content,
            'tables': tables,
            'lists': lists
        }
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def scrape_all_counties():
    """Scrape all sections for all counties"""
    all_data = {}
    
    for county, county_code in COUNTIES.items():
        print(f"\n{'='*70}")
        print(f"Scraping {county} County")
        print('='*70)
        
        all_data[county] = {}
        
        urls = get_county_urls(county_code)
        
        for section_name, url in urls.items():
            page_data = scrape_page(url, county, section_name)
            
            if page_data:
                all_data[county][section_name] = page_data
            else:
                print(f"  ⚠️  Failed to scrape {section_name}")
            
            # Be polite to the server
            time.sleep(0.5)
    
    return all_data

def save_results(data):
    """Save the scraped data to JSON file"""
    output_file = 'data/maryland_manual_raw.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*70}")
    print(f"Data saved to {output_file}")
    print('='*70)
    
    # Print summary
    for county, sections in data.items():
        print(f"\n{county} County: {len(sections)} sections scraped")
        for section in sections.keys():
            print(f"  ✓ {section}")

if __name__ == "__main__":
    print("Maryland Manual Scraper")
    print("="*70)
    
    # Count sections
    sample_urls = get_county_urls('do')
    num_sections = len(sample_urls)
    
    print(f"Scraping {len(COUNTIES)} counties × {num_sections} sections = {len(COUNTIES) * num_sections} pages")
    print()
    
    data = scrape_all_counties()
    save_results(data)
    
    print("\n✅ Scraping complete!")
