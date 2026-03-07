import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
from datetime import datetime, timedelta
import time
import re
import PyPDF2
import io

def get_pdf_text(pdf_url):
    """Download and extract text from PDF"""
    try:
        response = requests.get(pdf_url, timeout=15)
        if response.status_code == 200:
            pdf_file = io.BytesIO(response.content)
            reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in reader.pages[:10]:  # First 10 pages only
                text += page.extract_text()
            
            return text[:5000]  # First 5000 chars
    except Exception as e:
        return f"Error extracting: {str(e)}"
    return ""

def scrape_county_minutes(county_key, county_name, base_url):
    """Scrape and download meeting minutes"""
    
    meetings = []
    
    try:
        print(f"  Fetching {base_url}...")
        response = requests.get(base_url, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all links
            all_links = soup.find_all('a', href=True)
            print(f"    Found {len(all_links)} total links on page")
            
            pdf_count = 0
            for link in all_links:
                href = link['href']
                link_text = link.get_text().strip()
                
                # Look for PDF links or document links
                if '.pdf' in href.lower() or 'viewfile' in href.lower() or 'download' in href.lower():
                    # Check if it's minutes/agenda related
                    if any(word in link_text.lower() or word in href.lower() for word in ['minute', 'agenda', 'packet']):
                        # Make absolute URL
                        if href.startswith('/'):
                            domain = '/'.join(base_url.split('/')[:3])
                            full_url = domain + href
                        elif not href.startswith('http'):
                            full_url = base_url.rsplit('/', 1)[0] + '/' + href
                        else:
                            full_url = href
                        
                        # Try to extract date from link text or URL
                        date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', link_text + ' ' + href)
                        if not date_match:
                            date_match = re.search(r'(20\d{2})', href)
                        
                        date_str = date_match.group(1) if date_match else "Unknown date"
                        
                        meeting_info = {
                            "date": date_str,
                            "title": link_text[:150] if link_text else "Meeting Document",
                            "url": full_url,
                            "type": "minutes" if "minute" in link_text.lower() else "agenda"
                        }
                        
                        meetings.append(meeting_info)
                        pdf_count += 1
                        
                        # Limit to 15 documents
                        if pdf_count >= 15:
                            break
            
            print(f"    Found {len(meetings)} meeting documents")
            
            # Now download and parse a few recent ones
            print(f"    Downloading and parsing up to 5 recent documents...")
            for i, meeting in enumerate(meetings[:5]):
                print(f"      [{i+1}] Downloading {meeting['date']}...")
                text = get_pdf_text(meeting['url'])
                meeting['extracted_text'] = text[:2000]  # First 2000 chars
                meeting['text_length'] = len(text)
                time.sleep(1)
            
    except Exception as e:
        print(f"    Error: {e}")
    
    return meetings

def main():
    counties = [
        ('talbot', 'Talbot', 'https://www.talbotcountymd.gov/223/County-Council'),
        ('dorchester', 'Dorchester', 'https://docogonet.com/county-council'),
        ('kent', 'Kent', 'https://www.kentcounty.com/commissioners'),
        ('queen_annes', "Queen Anne's", 'https://www.qac.org/196/Commissioners'),
        ('caroline', 'Caroline', 'https://www.carolinemd.org/commissioners')
    ]
    
    output_dir = Path("../scraped_data")
    all_results = {}
    
    for county_key, county_name, url in counties:
        print(f"\n{'='*60}")
        print(f"Scraping {county_name} County...")
        print(f"{'='*60}")
        
        meetings = scrape_county_minutes(county_key, county_name, url)
        
        data = {
            "county_name": county_name,
            "scraped_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_url": url,
            "meeting_documents": meetings,
            "total_found": len(meetings),
            "parsed_count": len([m for m in meetings if 'extracted_text' in m])
        }
        
        # Save individual county file
        county_dir = output_dir / county_key
        county_dir.mkdir(exist_ok=True)
        
        output_file = county_dir / f"{county_key}_minutes.json"
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n  ✓ Saved {len(meetings)} documents to {output_file}")
        print(f"  ✓ Parsed {data['parsed_count']} documents with text extraction")
        
        all_results[county_key] = data
        
        time.sleep(2)
    
    # Save combined file
    combined_file = output_dir / "counties_minutes.json"
    with open(combined_file, 'w') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    for county_key, data in all_results.items():
        print(f"{data['county_name']:15s}: {data['total_found']:2d} documents found, {data['parsed_count']:2d} parsed")
    
    print(f"\n✓ All data saved to scraped_data/")
    print(f"✓ Combined file: {combined_file}")

if __name__ == "__main__":
    main()
