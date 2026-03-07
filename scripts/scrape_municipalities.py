import requests
from bs4 import BeautifulSoup
import json
import time
import re

# Counties to scrape
COUNTIES = {
    'Dorchester': 'do',
    'Queen Annes': 'qa',
    'Talbot': 'ta',
    'Kent': 'ke',
    'Caroline': 'caro'
}

def scrape_municipality_page(url):
    """Scrape a single municipality page"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get all text
        text_content = soup.get_text(separator='\n', strip=True)
        
        # Extract all links to individual municipality pages
        muni_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            # Look for links to specific municipalities (usually in /msa/mdmanual/37mun/ or similar)
            if '/msa/mdmanual/37mun/' in href or '/html/' in href:
                link_text = link.get_text(strip=True)
                if link_text and len(link_text) > 2:  # Filter out tiny links
                    full_url = href if href.startswith('http') else f"https://msa.maryland.gov{href}"
                    muni_links.append({
                        'name': link_text,
                        'url': full_url
                    })
        
        return {
            'text_content': text_content,
            'municipality_links': muni_links
        }
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def scrape_individual_municipality(url, name):
    """Scrape an individual municipality's page"""
    try:
        print(f"  Scraping {name}...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        text_content = soup.get_text(separator='\n', strip=True)
        
        # Extract key information
        info = {
            'name': name,
            'url': url,
            'officials': [],
            'contact_info': {}
        }
        
        # Extract officials with more sophisticated patterns
        # Pattern: Name, Role, Year or District
        # Example: "Megan J. M. Cook, Mayor, 2027"
        # Example: "Donald M. Abbatiello, President (4-year term), 2029"
        # Example: "Maureen E. Curry, Ward 1, 2027"
        
        official_pattern = r'([A-Z][a-z]+(?:\s+[A-Z]\.?(?:\s+[A-Z]\.?)?)?\s+[A-Z][a-z]+(?:,\s+Jr\.?|,\s+Sr\.?)?),\s+(?:<i>)?(Mayor|President|Vice[- ]President|Ward\s+\d+|District\s+\d+|Commissioner|Council\s+Member|Town\s+Administrator|Town\s+Manager|City\s+Manager)'
        
        matches = re.finditer(official_pattern, text_content, re.IGNORECASE)
        
        for match in matches:
            name = match.group(1).strip()
            role = match.group(2).strip()
            
            info['officials'].append({
                'name': name,
                'role': role
            })
        
        # Extract phone
        phone_match = re.search(r'\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}', text_content)
        if phone_match:
            info['contact_info']['phone'] = phone_match.group(0)
        
        # Extract email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text_content)
        if email_match:
            info['contact_info']['email'] = email_match.group(0)
        
        # Extract website
        web_match = re.search(r'web:\s*<?([^<>\s]+)>?', text_content, re.IGNORECASE)
        if web_match:
            info['contact_info']['website'] = web_match.group(1)
        
        # Extract population
        pop_match = re.search(r'2020 census:\s*([\d,]+)', text_content)
        if pop_match:
            info['population_2020'] = pop_match.group(1)
        
        # Extract address
        address_match = re.search(r'(P\.?\s*O\.?\s*Box[^\n]+|[0-9]+[^\n]+(?:Street|St\.|Lane|Ln\.|Road|Rd\.|Avenue|Ave\.),[^\n]+MD\s+\d{5}[^\n]*)', text_content, re.IGNORECASE)
        if address_match:
            info['contact_info']['address'] = address_match.group(1).strip()
        
        # Store full text for reference
        info['full_text'] = text_content
        
        return info
        
    except Exception as e:
        print(f"    Error scraping {name}: {e}")
        return None

def scrape_all_municipalities():
    """Scrape all municipalities for the target counties"""
    all_data = {}
    
    for county, county_code in COUNTIES.items():
        print(f"\n{'='*70}")
        print(f"Scraping {county} County Municipalities")
        print('='*70)
        
        # Get the municipality listing page
        muni_url = f'https://msa.maryland.gov/msa/mdmanual/36loc/{county_code}/html/{county_code}mu.html'
        
        page_data = scrape_municipality_page(muni_url)
        
        if not page_data:
            print(f"  ⚠️  Failed to scrape municipality listing")
            continue
        
        all_data[county] = {
            'county': county,
            'municipalities': []
        }
        
        print(f"Found {len(page_data['municipality_links'])} municipality links")
        
        # Scrape each individual municipality
        for muni_link in page_data['municipality_links']:
            muni_data = scrape_individual_municipality(muni_link['url'], muni_link['name'])
            
            if muni_data:
                all_data[county]['municipalities'].append(muni_data)
                if muni_data['officials']:
                    print(f"    ✓ Found {len(muni_data['officials'])} officials")
            
            time.sleep(0.3)  # Be polite
    
    return all_data

def save_results(data):
    """Save results to JSON files"""
    
    # Save all municipalities in one file
    output_file = 'data/all_municipalities.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*70}")
    print(f"All municipality data saved to {output_file}")
    print('='*70)
    
    # Save individual county municipality files
    for county, county_data in data.items():
        filename = f"data/{county.lower().replace(' ', '_')}_municipalities.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(county_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n{county} County:")
        print(f"  ✓ Saved to {filename}")
        print(f"  ✓ {len(county_data['municipalities'])} municipalities")
        
        total_officials = sum(len(m.get('officials', [])) for m in county_data['municipalities'])
        print(f"  ✓ {total_officials} total officials found")

if __name__ == "__main__":
    print("Maryland Municipalities Scraper")
    print("="*70)
    print(f"Scraping municipalities for {len(COUNTIES)} counties")
    print()
    
    data = scrape_all_municipalities()
    save_results(data)
    
    print("\n✅ Scraping complete!")
