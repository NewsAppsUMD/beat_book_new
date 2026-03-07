"""
Parse budget PDFs for all remaining counties.
"""

import requests
import PyPDF2
import io
import re
import json
from pathlib import Path
import time

def extract_pdf_text(url):
    """Download and extract text from PDF"""
    try:
        print(f"    Downloading PDF...")
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        
        pdf_file = io.BytesIO(response.content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        # Extract from first 10 pages
        for i in range(min(10, len(pdf_reader.pages))):
            text += pdf_reader.pages[i].extract_text()
        
        print(f"    Extracted {len(text)} characters from {len(pdf_reader.pages)} pages")
        return text
    except Exception as e:
        print(f"    Error: {e}")
        return ""

def parse_queen_annes_budget():
    """Parse Queen Anne's County budget"""
    print("\nParsing Queen Anne's County Budget...")
    
    # Try to find budget document from their website
    budget = {
        "fiscal_year": "FY2025",
        "notes": "Budget details available at http://www.qac.org/587/Budget-Section"
    }
    
    return budget

def parse_kent_budget():
    """Parse Kent County budget"""
    print("\nParsing Kent County Budget...")
    
    # Load the existing data to get PDF links
    with open("scraped_data/kent_budget.json") as f:
        existing = json.load(f)
    
    budget = {
        "fiscal_year": "FY2025",
        "expenditures": {},
        "revenues": {}
    }
    
    # Try the PDFs found
    if existing.get('detailed_budget', {}).get('source_documents'):
        for doc in existing['detailed_budget']['source_documents'][:2]:
            url = doc['url']
            print(f"  Trying: {doc['title']}")
            text = extract_pdf_text(url)
            
            if text:
                # Look for budget amounts
                total_match = re.search(r'total.*?budget.*?\$\s*([\d,]+)', text, re.IGNORECASE)
                if total_match:
                    budget['total_budget'] = int(total_match.group(1).replace(',', ''))
                
                # Look for major categories
                categories = {
                    'General Government': r'general\s+government.*?\$\s*([\d,]+)',
                    'Public Safety': r'public\s+safety.*?\$\s*([\d,]+)',
                    'Public Works': r'public\s+works.*?\$\s*([\d,]+)',
                    'Health': r'health.*?\$\s*([\d,]+)',
                    'Education': r'education.*?\$\s*([\d,]+)'
                }
                
                for cat, pattern in categories.items():
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        budget['expenditures'][cat] = int(match.group(1).replace(',', ''))
            
            time.sleep(1)
    
    return budget

def parse_caroline_budget():
    """Parse Caroline County budget"""
    print("\nParsing Caroline County Budget...")
    
    # Load existing data
    with open("scraped_data/caroline_budget.json") as f:
        existing = json.load(f)
    
    budget = {
        "fiscal_year": "FY2025",
        "expenditures": {},
        "revenues": {}
    }
    
    if existing.get('detailed_budget', {}).get('source_documents'):
        for doc in existing['detailed_budget']['source_documents'][:1]:
            url = doc['url']
            print(f"  Trying: {doc['title']}")
            text = extract_pdf_text(url)
            
            if text:
                # Look for total budget
                patterns = [
                    r'total.*?appropriation.*?\$\s*([\d,]+)',
                    r'\$\s*([\d,]+).*?total.*?budget'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        budget['total_appropriations'] = int(match.group(1).replace(',', ''))
                        break
            
            time.sleep(1)
    
    return budget

def parse_dorchester_detailed():
    """Parse Dorchester budget in more detail"""
    print("\nParsing Dorchester County FY2026 Budget (detailed)...")
    
    url = "https://dorchestermd.gov/wp-content/uploads/2025/05/Bill-No-2025-4-FY26-Budget-Appropriation-Ordinance-1.pdf"
    text = extract_pdf_text(url)
    
    budget = {
        "fiscal_year": "FY2026",
        "expenditures": {},
        "revenues": {},
        "total_appropriations": None
    }
    
    if text:
        # Look for total appropriation
        total_patterns = [
            r'sum\s+of\s+\$\s*([\d,]+)',
            r'total.*?appropriat.*?\$\s*([\d,]+)',
            r'hereby\s+appropriated.*?\$\s*([\d,]+)'
        ]
        
        for pattern in total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = match.group(1).replace(',', '')
                if len(amount) >= 7:  # At least millions
                    budget['total_appropriations'] = int(amount)
                    break
        
        # Parse line by line for categories
        lines = text.split('\n')
        current_category = None
        
        for line in lines:
            # Look for major department/category headers
            if re.match(r'^[A-Z\s&]+$', line.strip()) and len(line.strip()) > 3:
                current_category = line.strip()
            
            # Look for amounts on the line
            amount_match = re.search(r'\$\s*([\d,]+)', line)
            if amount_match and current_category:
                amount = int(amount_match.group(1).replace(',', ''))
                if amount > 10000:  # Filter small amounts
                    if current_category not in budget['expenditures']:
                        budget['expenditures'][current_category] = amount
    
    return budget

def main():
    output_dir = Path("scraped_data")
    
    # Parse each county
    counties = {
        'queen_annes': parse_queen_annes_budget(),
        'kent': parse_kent_budget(),
        'caroline': parse_caroline_budget(),
        'dorchester': parse_dorchester_detailed()
    }
    
    # Update files
    for county_key, parsed_budget in counties.items():
        if not parsed_budget:
            continue
        
        file_path = output_dir / f"{county_key}_budget.json"
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if 'parsed_budget' not in data.get('detailed_budget', {}):
            data['detailed_budget']['parsed_budget'] = parsed_budget
        else:
            # Update existing
            data['detailed_budget']['parsed_budget'].update(parsed_budget)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n✓ Updated {county_key}")
        
        if parsed_budget.get('total_appropriations'):
            print(f"  Total Budget: ${parsed_budget['total_appropriations']:,}")
        if parsed_budget.get('total_budget'):
            print(f"  Total Budget: ${parsed_budget['total_budget']:,}")
        if parsed_budget.get('expenditures'):
            print(f"  Expenditure Categories: {len(parsed_budget['expenditures'])}")
        if parsed_budget.get('revenues'):
            print(f"  Revenue Sources: {len(parsed_budget['revenues'])}")
    
    # Print summary
    print("\n" + "="*70)
    print("BUDGET DATA SUMMARY - ALL COUNTIES")
    print("="*70)
    
    all_data = {}
    for county_file in output_dir.glob("*_budget.json"):
        with open(county_file) as f:
            data = json.load(f)
            county_name = data['county_name']
            all_data[county_name] = data
    
    for county_name in sorted(all_data.keys()):
        data = all_data[county_name]
        print(f"\n{county_name} County:")
        print(f"  Property Tax Rate: ${data['property_tax_rate']} per $100")
        print(f"  Fiscal Year: {data['fiscal_year']}")
        
        parsed = data.get('detailed_budget', {}).get('parsed_budget', {})
        
        if parsed.get('total_revenue'):
            print(f"  Total Revenue: ${parsed['total_revenue']:,}")
        if parsed.get('total_appropriations'):
            print(f"  Total Appropriations: ${parsed['total_appropriations']:,}")
        if parsed.get('total_budget'):
            print(f"  Total Budget: ${parsed['total_budget']:,}")
        
        docs = data.get('detailed_budget', {}).get('source_documents', [])
        if docs:
            print(f"  Budget Documents: {len(docs)} available")

if __name__ == "__main__":
    main()
