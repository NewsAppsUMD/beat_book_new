"""
Scrape all county budget PDFs to extract detailed budget numbers.
"""

import requests
import PyPDF2
import io
import re
import json
from pathlib import Path
import time

def extract_pdf_text(url, max_pages=15):
    """Download and extract text from PDF"""
    try:
        print(f"    Downloading: {url[:80]}...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        pdf_file = io.BytesIO(response.content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        total_pages = len(pdf_reader.pages)
        print(f"    PDF has {total_pages} pages, extracting first {min(max_pages, total_pages)}...")
        
        text = ""
        for i in range(min(max_pages, total_pages)):
            page_text = pdf_reader.pages[i].extract_text()
            text += page_text + "\n"
        
        print(f"    Extracted {len(text):,} characters")
        return text
    except Exception as e:
        print(f"    ERROR: {e}")
        return ""

def parse_budget_from_text(text, county_name):
    """Parse budget information from extracted text"""
    
    budget = {
        "fiscal_year": None,
        "total_revenue": None,
        "total_appropriations": None,
        "total_expenditures": None,
        "revenues": {},
        "expenditures": {}
    }
    
    # Find fiscal year
    fy_patterns = [
        r'FY\s*(\d{4})',
        r'Fiscal Year\s*(\d{4})',
        r'(\d{4})\s+Budget',
        r'FY\s*(\d{2})'
    ]
    
    for pattern in fy_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            year = match.group(1)
            if len(year) == 2:
                year = "20" + year
            budget['fiscal_year'] = year
            break
    
    # Find total budget amounts
    total_patterns = [
        (r'Total\s+Revenue[s]?[:\s]+\$?\s*([\d,]+)', 'total_revenue'),
        (r'Total\s+Appropriation[s]?[:\s]+\$?\s*([\d,]+)', 'total_appropriations'),
        (r'Total\s+Expenditure[s]?[:\s]+\$?\s*([\d,]+)', 'total_expenditures'),
        (r'Total\s+Budget[:\s]+\$?\s*([\d,]+)', 'total_appropriations'),
        (r'Grand\s+Total[:\s]+\$?\s*([\d,]+)', 'total_appropriations'),
    ]
    
    for pattern, key in total_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            amount_str = match.group(1).replace(',', '')
            if amount_str.isdigit() and len(amount_str) >= 7:  # At least millions
                if not budget[key]:  # Take first valid match
                    budget[key] = int(amount_str)
    
    # Parse line items - look for category followed by amount
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        # Clean the line
        line = line.strip()
        if not line or len(line) < 5:
            continue
        
        # Look for revenue categories
        revenue_keywords = ['property tax', 'income tax', 'transfer tax', 'sales tax', 
                          'grant', 'federal', 'state aid', 'fee', 'charge', 'license',
                          'interest income', 'other local']
        
        for keyword in revenue_keywords:
            if keyword in line.lower():
                # Try to find amount on same line or next few lines
                amount_match = re.search(r'\$?\s*([\d,]+)(?:\.\d{2})?', line)
                if amount_match:
                    amount_str = amount_match.group(1).replace(',', '')
                    if amount_str.isdigit() and int(amount_str) > 1000:
                        category = line.split('$')[0].strip() if '$' in line else line[:50].strip()
                        if category:
                            budget['revenues'][category] = int(amount_str)
        
        # Look for expenditure categories
        expense_keywords = ['education', 'school', 'public safety', 'police', 'sheriff',
                          'fire', 'emergency', 'public works', 'roads', 'health',
                          'general government', 'recreation', 'parks', 'library',
                          'debt service', 'capital', 'administration']
        
        for keyword in expense_keywords:
            if keyword in line.lower():
                amount_match = re.search(r'\$?\s*([\d,]+)(?:\.\d{2})?', line)
                if amount_match:
                    amount_str = amount_match.group(1).replace(',', '')
                    if amount_str.isdigit() and int(amount_str) > 10000:
                        category = line.split('$')[0].strip() if '$' in line else line[:50].strip()
                        if category and category not in budget['expenditures']:
                            budget['expenditures'][category] = int(amount_str)
    
    return budget

def scrape_county_budget_pdfs(county_key, county_name):
    """Scrape budget PDFs for a county"""
    
    print(f"\n{'='*80}")
    print(f"Scraping {county_name} County Budget PDFs")
    print(f"{'='*80}")
    
    # Load existing data to get PDF URLs
    budget_file = Path("scraped_data") / f"{county_key}_budget.json"
    with open(budget_file) as f:
        data = json.load(f)
    
    # Get PDF links
    source_docs = data.get('detailed_budget', {}).get('source_documents', [])
    if not source_docs:
        print("  No budget PDFs found")
        return None
    
    print(f"  Found {len(source_docs)} budget documents")
    
    # Try the most recent budget PDF (usually first)
    all_budget_data = []
    
    for doc in source_docs[:3]:  # Try first 3 PDFs
        print(f"\n  Processing: {doc['title']}")
        text = extract_pdf_text(doc['url'])
        
        if text:
            budget_data = parse_budget_from_text(text, county_name)
            
            if budget_data['fiscal_year']:
                print(f"    ✓ Found FY{budget_data['fiscal_year']} data")
            if budget_data['total_revenue']:
                print(f"    ✓ Total Revenue: ${budget_data['total_revenue']:,}")
            if budget_data['total_appropriations']:
                print(f"    ✓ Total Appropriations: ${budget_data['total_appropriations']:,}")
            if budget_data['revenues']:
                print(f"    ✓ Found {len(budget_data['revenues'])} revenue categories")
            if budget_data['expenditures']:
                print(f"    ✓ Found {len(budget_data['expenditures'])} expenditure categories")
            
            all_budget_data.append(budget_data)
        
        time.sleep(2)  # Be respectful
    
    # Merge data from multiple PDFs (take most complete)
    if all_budget_data:
        # Sort by completeness (most data first)
        all_budget_data.sort(key=lambda x: (
            len(x['revenues']) + len(x['expenditures']) +
            (1 if x['total_revenue'] else 0) +
            (1 if x['total_appropriations'] else 0)
        ), reverse=True)
        
        return all_budget_data[0]
    
    return None

def main():
    counties = {
        'dorchester': 'Dorchester',
        'queen_annes': "Queen Anne's",
        'kent': 'Kent',
        'caroline': 'Caroline'
    }
    
    output_dir = Path("scraped_data")
    
    for county_key, county_name in counties.items():
        budget_data = scrape_county_budget_pdfs(county_key, county_name)
        
        if budget_data:
            # Load existing file
            budget_file = output_dir / f"{county_key}_budget.json"
            with open(budget_file) as f:
                data = json.load(f)
            
            # Update with parsed budget
            if 'detailed_budget' not in data:
                data['detailed_budget'] = {}
            
            data['detailed_budget']['parsed_budget'] = budget_data
            
            # Save
            with open(budget_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"\n  ✓ Updated {budget_file}")
    
    # Print final summary
    print(f"\n\n{'='*80}")
    print("FINAL BUDGET DATA SUMMARY - ALL COUNTIES")
    print(f"{'='*80}\n")
    
    all_counties = {
        'talbot': 'Talbot',
        'dorchester': 'Dorchester',
        'kent': 'Kent',
        'queen_annes': "Queen Anne's",
        'caroline': 'Caroline'
    }
    
    for county_key, county_name in all_counties.items():
        budget_file = output_dir / f"{county_key}_budget.json"
        if not budget_file.exists():
            continue
        
        with open(budget_file) as f:
            data = json.load(f)
        
        print(f"{county_name} County:")
        print(f"  Property Tax Rate: ${data.get('property_tax_rate', 'N/A')} per $100")
        
        parsed = data.get('detailed_budget', {}).get('parsed_budget', {})
        if parsed:
            if parsed.get('fiscal_year'):
                print(f"  Fiscal Year: {parsed['fiscal_year']}")
            if parsed.get('total_revenue'):
                print(f"  Total Revenue: ${parsed['total_revenue']:,}")
            if parsed.get('total_appropriations'):
                print(f"  Total Appropriations: ${parsed['total_appropriations']:,}")
            if parsed.get('revenues'):
                print(f"  Revenue Categories: {len(parsed['revenues'])}")
            if parsed.get('expenditures'):
                print(f"  Expenditure Categories: {len(parsed['expenditures'])}")
        else:
            print(f"  No detailed budget data parsed")
        
        print()

if __name__ == "__main__":
    main()
