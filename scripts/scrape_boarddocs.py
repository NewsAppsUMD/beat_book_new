import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
from datetime import datetime
import time
import re
import PyPDF2
import io

# BoardDocs URLs for each county
BOARDDOCS_URLS = {
    "dorchester": "https://go.boarddocs.com/mabe/dcps/Board.nsf/Public",
    "talbot": "https://go.boarddocs.com/mabe/talbot/Board.nsf/Public",
    "kent": "https://go.boarddocs.com/mabe/kentmd/Board.nsf/Public",
    "queen_annes": "https://go.boarddocs.com/mabe/qac/Board.nsf/Public",
    "caroline": "https://go.boarddocs.com/mabe/caroline/Board.nsf/Public"
}

def extract_pdf_text(pdf_url, max_pages=5):
    """Download and extract text from PDF"""
    try:
        print(f"        Downloading PDF...")
        response = requests.get(pdf_url, timeout=20)
        if response.status_code == 200:
            pdf_file = io.BytesIO(response.content)
            reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            num_pages = min(len(reader.pages), max_pages)
            for i in range(num_pages):
                text += reader.pages[i].extract_text()
            
            return text[:3000]  # First 3000 chars
    except Exception as e:
        return f"Error: {str(e)}"
    return ""

def scrape_boarddocs(county_key, county_name, boarddocs_url):
    """Scrape BoardDocs for meeting minutes"""
    
    meetings = []
    
    try:
        print(f"  Fetching BoardDocs page...")
        response = requests.get(boarddocs_url, timeout=15)
        
        if response.status_code != 200:
            print(f"    Error: Status {response.status_code}")
            return meetings
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for meeting links - BoardDocs uses specific patterns
        # Find links that contain "goto" which are meeting detail links
        meeting_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            link_text = link.get_text().strip()
            
            # BoardDocs meeting links usually contain 'goto' or specific patterns
            if 'goto' in href.lower() or 'meeting' in href.lower():
                if link_text and len(link_text) > 5:  # Has meaningful text
                    # Make absolute URL
                    if not href.startswith('http'):
                        base = boarddocs_url.rsplit('/Board.nsf', 1)[0]
                        href = base + '/Board.nsf/' + href
                    
                    meeting_links.append({
                        'text': link_text,
                        'url': href
                    })
        
        print(f"    Found {len(meeting_links)} potential meeting links")
        
        # Process first 10 meeting links
        for i, meeting_link in enumerate(meeting_links[:10]):
            print(f"    [{i+1}] Processing: {meeting_link['text'][:50]}...")
            
            try:
                # Visit meeting detail page
                time.sleep(1)
                meeting_response = requests.get(meeting_link['url'], timeout=15)
                
                if meeting_response.status_code == 200:
                    meeting_soup = BeautifulSoup(meeting_response.content, 'html.parser')
                    
                    # Look for PDF links on the meeting page
                    pdf_links = []
                    for pdf_link in meeting_soup.find_all('a', href=True):
                        pdf_href = pdf_link['href']
                        pdf_text = pdf_link.get_text().strip()
                        
                        if '.pdf' in pdf_href.lower() or 'file' in pdf_href.lower():
                            if any(word in pdf_text.lower() for word in ['minute', 'agenda', 'packet']):
                                # Make absolute URL
                                if not pdf_href.startswith('http'):
                                    if pdf_href.startswith('/'):
                                        base = '/'.join(boarddocs_url.split('/')[:3])
                                        pdf_href = base + pdf_href
                                    else:
                                        base = meeting_link['url'].rsplit('/', 1)[0]
                                        pdf_href = base + '/' + pdf_href
                                
                                pdf_links.append({
                                    'text': pdf_text,
                                    'url': pdf_href,
                                    'type': 'minutes' if 'minute' in pdf_text.lower() else 'agenda'
                                })
                    
                    # Extract date from meeting title
                    date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', meeting_link['text'])
                    if not date_match:
                        date_match = re.search(r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})', meeting_link['text'], re.IGNORECASE)
                    
                    date_str = date_match.group(1) if date_match else "Date not found"
                    
                    # Process PDF links
                    for pdf in pdf_links:
                        meeting_data = {
                            "date": date_str,
                            "meeting_title": meeting_link['text'],
                            "document_title": pdf['text'],
                            "url": pdf['url'],
                            "type": pdf['type'],
                            "meeting_page": meeting_link['url']
                        }
                        
                        # Download and extract text from first few minutes PDFs only
                        if pdf['type'] == 'minutes' and len([m for m in meetings if m.get('type') == 'minutes']) < 3:
                            print(f"        Extracting text from minutes PDF...")
                            text = extract_pdf_text(pdf['url'])
                            meeting_data['extracted_text'] = text
                            meeting_data['text_length'] = len(text)
                        
                        meetings.append(meeting_data)
                        
            except Exception as e:
                print(f"        Error processing meeting: {e}")
                continue
        
    except Exception as e:
        print(f"    Error: {e}")
    
    return meetings

def main():
    counties = [
        ('dorchester', 'Dorchester'),
        ('talbot', 'Talbot'),
        ('kent', 'Kent'),
        ('queen_annes', "Queen Anne's"),
        ('caroline', 'Caroline')
    ]
    
    output_dir = Path("../scraped_data")
    all_results = {}
    
    for county_key, county_name in counties:
        boarddocs_url = BOARDDOCS_URLS.get(county_key)
        
        if not boarddocs_url:
            print(f"\n{county_name}: No BoardDocs URL configured")
            continue
        
        print(f"\n{'='*60}")
        print(f"{county_name} County - BoardDocs Scraping")
        print(f"{'='*60}")
        print(f"URL: {boarddocs_url}")
        
        meetings = scrape_boarddocs(county_key, county_name, boarddocs_url)
        
        data = {
            "county_name": county_name,
            "scraped_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "boarddocs_url": boarddocs_url,
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
        
        print(f"\n  ✓ Found {len(meetings)} documents")
        print(f"  ✓ Parsed {data['parsed_count']} minutes with text extraction")
        print(f"  ✓ Saved to {output_file}")
        
        all_results[county_key] = data
        
        time.sleep(2)
    
    # Save combined file
    combined_file = output_dir / "counties_minutes.json"
    with open(combined_file, 'w') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    total_docs = 0
    total_parsed = 0
    for county_key, data in all_results.items():
        total_docs += data['total_found']
        total_parsed += data['parsed_count']
        print(f"{data['county_name']:15s}: {data['total_found']:2d} documents, {data['parsed_count']:2d} parsed")
    
    print(f"\nTOTAL: {total_docs} documents, {total_parsed} with extracted text")
    print(f"\n✓ Combined file: {combined_file}")

if __name__ == "__main__":
    main()
