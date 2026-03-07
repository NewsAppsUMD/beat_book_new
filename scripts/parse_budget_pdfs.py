"""
Extract detailed budget numbers from county budget PDFs.
Parse actual revenue and expenditure data.
"""

import requests
import PyPDF2
import io
import re
import json
from pathlib import Path

def extract_pdf_text(url):
    """Download and extract text from PDF"""
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        
        pdf_file = io.BytesIO(response.content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        # Extract from first 10 pages (budget summary usually in first pages)
        for i in range(min(10, len(pdf_reader.pages))):
            text += pdf_reader.pages[i].extract_text()
        
        return text
    except Exception as e:
        print(f"  Error extracting PDF: {e}")
        return ""

def parse_talbot_budget():
    """Parse Talbot County FY2026 budget"""
    print("\nParsing Talbot County FY2026 Budget...")
    
    url = "https://www.talbotcountymd.gov/uploads/File/finance/2026%20Budget/FY26%20APPROVED%20Budget%20Summary.pdf"
    text = extract_pdf_text(url)
    
    if not text:
        return None
    
    budget = {
        "fiscal_year": "FY2026",
        "total_revenue": None,
        "total_appropriations": None,
        "revenues": {},
        "expenditures": {}
    }
    
    # Extract revenues
    lines = text.split('\n')
    in_revenue_section = False
    in_expenditure_section = False
    
    for i, line in enumerate(lines):
        # Revenue section
        if 'REVENUES' in line and 'APPROVED' in line:
            in_revenue_section = True
            continue
        
        if 'APPROPRIATIONS' in line:
            in_revenue_section = False
            in_expenditure_section = True
            continue
        
        if in_revenue_section:
            # Try to extract revenue line items
            match = re.match(r'(.*?)\s+([\d,]+)\s+([\d,]+)', line)
            if match:
                category = match.group(1).strip()
                fy2026_amount = match.group(3).replace(',', '')
                if category and fy2026_amount.isdigit():
                    budget['revenues'][category] = int(fy2026_amount)
        
        if in_expenditure_section:
            # Try to extract expenditure line items
            match = re.match(r'([A-Z][A-Za-z\s&]+)\s+([\d,]+)\s+([\d,]+)', line)
            if match:
                category = match.group(1).strip()
                fy2026_amount = match.group(3).replace(',', '')
                if category and fy2026_amount.isdigit():
                    budget['expenditures'][category] = int(fy2026_amount)
    
    # Calculate totals
    if budget['revenues']:
        budget['total_revenue'] = sum(budget['revenues'].values())
    if budget['expenditures']:
        budget['total_appropriations'] = sum(budget['expenditures'].values())
    
    return budget

def parse_dorchester_budget():
    """Parse Dorchester County FY2026 budget"""
    print("\nParsing Dorchester County FY2026 Budget...")
    
    url = "https://dorchestermd.gov/wp-content/uploads/2025/05/Bill-No-2025-4-FY26-Budget-Appropriation-Ordinance-1.pdf"
    text = extract_pdf_text(url)
    
    if not text:
        return None
    
    budget = {
        "fiscal_year": "FY2026",
        "total_appropriations": None,
        "expenditures": {},
        "notes": "Budget ordinance - detailed breakdown available in full PDF"
    }
    
    # Look for total budget amount
    total_match = re.search(r'total.*?(?:appropriation|budget).*?\$\s*([\d,]+)', text, re.IGNORECASE)
    if total_match:
        budget['total_appropriations'] = int(total_match.group(1).replace(',', ''))
    
    # Look for major categories
    categories = ['General Government', 'Public Safety', 'Public Works', 'Health', 'Education']
    for category in categories:
        pattern = rf'{category}.*?\$\s*([\d,]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            budget['expenditures'][category] = int(match.group(1).replace(',', ''))
    
    return budget

def main():
    output_dir = Path("scraped_data")
    
    # Parse each county's budget
    talbot_budget = parse_talbot_budget()
    dorchester_budget = parse_dorchester_budget()
    
    # Update Talbot file
    if talbot_budget:
        talbot_file = output_dir / "talbot_budget.json"
        with open(talbot_file, 'r') as f:
            data = json.load(f)
        
        data['detailed_budget']['parsed_budget'] = talbot_budget
        
        with open(talbot_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n✓ Updated Talbot budget with parsed data")
        print(f"  Total Revenue: ${talbot_budget.get('total_revenue', 0):,}")
        print(f"  Total Appropriations: ${talbot_budget.get('total_appropriations', 0):,}")
        print(f"  Revenue Categories: {len(talbot_budget.get('revenues', {}))}")
        print(f"  Expenditure Categories: {len(talbot_budget.get('expenditures', {}))}")
    
    # Update Dorchester file
    if dorchester_budget:
        dorchester_file = output_dir / "dorchester_budget.json"
        with open(dorchester_file, 'r') as f:
            data = json.load(f)
        
        data['detailed_budget']['parsed_budget'] = dorchester_budget
        
        with open(dorchester_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n✓ Updated Dorchester budget with parsed data")
        if dorchester_budget.get('total_appropriations'):
            print(f"  Total Appropriations: ${dorchester_budget['total_appropriations']:,}")
    
    # Print summary
    print("\n" + "="*60)
    print("TALBOT COUNTY FY2026 BUDGET SUMMARY")
    print("="*60)
    
    if talbot_budget and talbot_budget.get('revenues'):
        print("\nTop Revenue Sources:")
        revenues = sorted(talbot_budget['revenues'].items(), key=lambda x: x[1], reverse=True)[:5]
        for cat, amount in revenues:
            print(f"  {cat[:40]:40s}: ${amount:>12,}")
    
    if talbot_budget and talbot_budget.get('expenditures'):
        print("\nTop Expenditure Categories:")
        expenses = sorted(talbot_budget['expenditures'].items(), key=lambda x: x[1], reverse=True)[:5]
        for cat, amount in expenses:
            print(f"  {cat[:40]:40s}: ${amount:>12,}")

if __name__ == "__main__":
    main()
