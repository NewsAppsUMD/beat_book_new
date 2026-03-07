"""
Scrape detailed budget information from county budget pages.
Extract total budgets, revenues, and major expenditure categories.
"""

import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
import time
import re

COUNTIES = {
    "dorchester": {
        "name": "Dorchester",
        "urls": [
            "https://dorchestermd.gov/budget-info/",
            "https://dorchestermd.gov/departments/finance-treasury/finance/"
        ]
    },
    "queen_annes": {
        "name": "Queen Anne's",
        "urls": [
            "http://www.qac.org/587/Budget-Section",
            "http://www.qac.org/DocumentCenter/Index/186"
        ]
    },
    "talbot": {
        "name": "Talbot",
        "urls": [
            "https://www.talbotcountymd.gov/fy2026budget",
            "https://www.talbotcountymd.gov/finance"
        ]
    },
    "kent": {
        "name": "Kent",
        "urls": [
            "https://www.kentcounty.com/government/departments/finance/"
        ]
    },
    "caroline": {
        "name": "Caroline",
        "urls": [
            "https://www.carolinemd.org/178/Budget"
        ]
    }
}

def extract_dollar_amounts(text):
    """Extract dollar amounts from text"""
    patterns = [
        r'\$\s*([\d,]+(?:\.\d{2})?)\s*(?:million|M)',  # $50 million
        r'\$\s*([\d,]+(?:\.\d{2})?)\s*(?:billion|B)',  # $1 billion
        r'\$\s*([\d,]+(?:\.\d{2})?)',  # $50,000
    ]
    
    amounts = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            amounts.append(match.group(0))
    
    return amounts

def scrape_budget_page(url, county_name):
    """Scrape a single budget page"""
    print(f"\n  Scraping {url}")
    
    data = {
        "url": url,
        "text_content": "",
        "tables": [],
        "pdf_links": [],
        "dollar_amounts": []
    }
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get main text content
        main_content = soup.find('main') or soup.find('div', class_=re.compile('content|main', re.I)) or soup.body
        if main_content:
            data['text_content'] = main_content.get_text(separator=' ', strip=True)
        
        # Extract tables
        for table in soup.find_all('table'):
            table_data = []
            for row in table.find_all('tr')[:20]:  # First 20 rows
                cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                if cells:
                    table_data.append(cells)
            if table_data:
                data['tables'].append(table_data)
        
        # Find PDF links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if href.endswith('.pdf'):
                full_url = href if href.startswith('http') else url.rsplit('/', 1)[0] + '/' + href
                link_text = link.get_text(strip=True) or href.split('/')[-1]
                
                # Filter for relevant budget PDFs
                if any(term in link_text.lower() or term in href.lower() for term in 
                       ['budget', 'fiscal', 'financial', 'revenue', 'cafr', 'expenditure']):
                    data['pdf_links'].append({
                        'title': link_text,
                        'url': full_url
                    })
        
        # Extract dollar amounts
        data['dollar_amounts'] = extract_dollar_amounts(data['text_content'])
        
        print(f"    Found: {len(data['tables'])} tables, {len(data['pdf_links'])} PDFs, {len(data['dollar_amounts'])} $ amounts")
        
    except Exception as e:
        print(f"    Error: {e}")
    
    return data

def parse_budget_info(scraped_data, county_name):
    """Parse scraped data to extract structured budget information"""
    
    budget_info = {
        "county_name": county_name,
        "fiscal_year": None,
        "total_operating_budget": None,
        "total_revenue": None,
        "major_revenue_sources": {},
        "major_expenditures": {},
        "fund_balance": None,
        "source_documents": []
    }
    
    all_text = ""
    for page_data in scraped_data:
        all_text += " " + page_data['text_content']
        
        # Add PDF links
        for pdf in page_data['pdf_links'][:10]:  # Top 10
            budget_info['source_documents'].append(pdf)
    
    # Try to find fiscal year
    fy_patterns = [
        r'(?:FY|Fiscal Year)\s*(\d{4})',
        r'(\d{4})\s*(?:Budget|Fiscal Year)',
        r'FY\s*(\d{2})'
    ]
    
    for pattern in fy_patterns:
        match = re.search(pattern, all_text, re.IGNORECASE)
        if match:
            year = match.group(1)
            if len(year) == 2:
                year = "20" + year
            budget_info['fiscal_year'] = year
            break
    
    # Try to find total budget
    budget_patterns = [
        r'(?:total|operating|general fund)\s+(?:budget|appropriation)[:\s]+\$\s*([\d,]+(?:\.\d{2})?)\s*(?:million|M)?',
        r'\$\s*([\d,]+(?:\.\d{2})?)\s*(?:million|M)\s+(?:budget|total)',
    ]
    
    for pattern in budget_patterns:
        match = re.search(pattern, all_text, re.IGNORECASE)
        if match:
            amount = match.group(1)
            if 'million' in match.group(0).lower() or 'M' in match.group(0):
                budget_info['total_operating_budget'] = f"${amount} million"
            else:
                budget_info['total_operating_budget'] = f"${amount}"
            break
    
    # Look for revenue information
    revenue_keywords = ['property tax', 'income tax', 'transfer tax', 'grants', 'fees', 'charges']
    
    for keyword in revenue_keywords:
        pattern = rf'{keyword}[:\s]+\$\s*([\d,]+(?:\.\d{{2}})?)'
        match = re.search(pattern, all_text, re.IGNORECASE)
        if match:
            budget_info['major_revenue_sources'][keyword.title()] = f"${match.group(1)}"
    
    # Look for expenditure categories
    expense_keywords = ['education', 'public safety', 'public works', 'health', 'general government']
    
    for keyword in expense_keywords:
        pattern = rf'{keyword}[:\s]+\$\s*([\d,]+(?:\.\d{{2}})?)'
        match = re.search(pattern, all_text, re.IGNORECASE)
        if match:
            budget_info['major_expenditures'][keyword.title()] = f"${match.group(1)}"
    
    # Parse tables for budget data
    for page_data in scraped_data:
        for table in page_data['tables']:
            # Look for revenue/expenditure tables
            for row in table:
                if len(row) >= 2:
                    label = row[0].lower()
                    value = row[-1]  # Last column often has amounts
                    
                    # Check if it's a revenue line
                    if any(kw in label for kw in ['revenue', 'tax', 'grant', 'fee']):
                        if '$' in value or value.replace(',', '').replace('.', '').isdigit():
                            budget_info['major_revenue_sources'][row[0]] = value
                    
                    # Check if it's an expenditure line
                    elif any(kw in label for kw in ['education', 'safety', 'public works', 'health', 'government']):
                        if '$' in value or value.replace(',', '').replace('.', '').isdigit():
                            budget_info['major_expenditures'][row[0]] = value
    
    return budget_info

def main():
    output_dir = Path("scraped_data")
    all_budget_data = {}
    
    for county_key, county_info in COUNTIES.items():
        print(f"\n{'='*60}")
        print(f"Processing {county_info['name']} County")
        print('='*60)
        
        scraped_pages = []
        
        for url in county_info['urls']:
            page_data = scrape_budget_page(url, county_info['name'])
            scraped_pages.append(page_data)
            time.sleep(2)  # Be respectful
        
        # Parse the scraped data
        budget_info = parse_budget_info(scraped_pages, county_info['name'])
        
        # Load existing budget data
        existing_file = output_dir / f"{county_key}_budget.json"
        with open(existing_file, 'r') as f:
            existing_data = json.load(f)
        
        # Merge with existing data
        existing_data.update({
            'detailed_budget': budget_info
        })
        
        # Save updated file
        with open(existing_file, 'w') as f:
            json.dump(existing_data, f, indent=2)
        
        all_budget_data[county_info['name']] = existing_data
        
        print(f"\n  ✓ Updated {existing_file}")
    
    # Update combined file
    combined_file = output_dir / "counties_budget.json"
    with open(combined_file, 'w') as f:
        json.dump(all_budget_data, f, indent=2)
    
    print(f"\n{'='*60}")
    print("Summary of Budget Data Collected")
    print('='*60)
    
    for county_name, data in all_budget_data.items():
        print(f"\n{county_name} County:")
        detailed = data.get('detailed_budget', {})
        
        if detailed.get('fiscal_year'):
            print(f"  Fiscal Year: {detailed['fiscal_year']}")
        if detailed.get('total_operating_budget'):
            print(f"  Total Budget: {detailed['total_operating_budget']}")
        if detailed.get('major_revenue_sources'):
            print(f"  Revenue Sources: {len(detailed['major_revenue_sources'])} found")
        if detailed.get('major_expenditures'):
            print(f"  Expenditure Categories: {len(detailed['major_expenditures'])} found")
        if detailed.get('source_documents'):
            print(f"  Budget Documents: {len(detailed['source_documents'])} PDFs")
    
    print(f"\n✓ All budget data saved to {output_dir}")

if __name__ == "__main__":
    main()
