"""
Create county budget and revenue data files with property tax rates
and links to budget documents.
"""

import json
from pathlib import Path

# Data compiled from Maryland SDAT and county websites (FY2024-2025)
BUDGET_DATA = {
    "Dorchester": {
        "county_name": "Dorchester",
        "fiscal_year": "FY2025",
        "property_tax_rate": "0.8925",
        "tax_rate_notes": "Per $100 of assessed value",
        "budget_website": "https://dorchestermd.gov/budget-info/",
        "finance_department": {
            "website": "https://dorchestermd.gov/departments/finance-treasury/finance/",
            "phone": "410-228-4343"
        },
        "budget_documents": [
            {
                "title": "Budget Information",
                "url": "https://dorchestermd.gov/budget-info/"
            },
            {
                "title": "Fiscal Policies",
                "url": "https://dorchestermd.gov/fiscal-policies/"
            }
        ],
        "notes": [
            "Check budget website for most recent adopted budget",
            "CAFR (Comprehensive Annual Financial Report) typically published annually"
        ]
    },
    "Queen Anne's": {
        "county_name": "Queen Anne's",
        "fiscal_year": "FY2025",
        "property_tax_rate": "0.898",
        "tax_rate_notes": "Per $100 of assessed value",
        "budget_website": "http://www.qac.org/587/Budget-Section",
        "finance_department": {
            "website": "http://www.qac.org/207/Finance-Budget",
            "phone": "410-758-4098"
        },
        "budget_documents": [
            {
                "title": "Budget Section",
                "url": "http://www.qac.org/587/Budget-Section"
            }
        ],
        "notes": [
            "Operating budget documents available on website",
            "Capital improvement plan updated annually"
        ]
    },
    "Talbot": {
        "county_name": "Talbot",
        "fiscal_year": "FY2026",
        "property_tax_rate": "0.812",
        "tax_rate_notes": "Per $100 of assessed value (lowest rate in the 5 counties)",
        "budget_website": "https://www.talbotcountymd.gov/fy2026budget",
        "finance_department": {
            "website": "https://www.talbotcountymd.gov/finance",
            "phone": "410-770-8010"
        },
        "budget_documents": [
            {
                "title": "FY2026 Budget",
                "url": "https://www.talbotcountymd.gov/fy2026budget"
            },
            {
                "title": "Budget Archives",
                "url": "https://www.talbotcountymd.gov/budgetarchives"
            }
        ],
        "notes": [
            "Current and historical budget documents available",
            "Finance page includes audit reports"
        ]
    },
    "Kent": {
        "county_name": "Kent",
        "fiscal_year": "FY2025",
        "property_tax_rate": "0.8745",
        "tax_rate_notes": "Per $100 of assessed value",
        "budget_website": "https://www.kentcounty.com/government/departments/finance/",
        "finance_department": {
            "website": "https://www.kentcounty.com/government/departments/finance/",
            "phone": "410-778-7477"
        },
        "budget_documents": [
            {
                "title": "Finance Department",
                "url": "https://www.kentcounty.com/government/departments/finance/"
            }
        ],
        "notes": [
            "Contact finance department for detailed budget documents",
            "Financial reports available on request"
        ]
    },
    "Caroline": {
        "county_name": "Caroline",
        "fiscal_year": "FY2025",
        "property_tax_rate": "0.9620",
        "tax_rate_notes": "Per $100 of assessed value (highest rate in the 5 counties)",
        "budget_website": "https://www.carolinemd.org/178/Budget",
        "finance_department": {
            "website": "https://www.carolinemd.org/178/Budget",
            "phone": "410-479-4030"
        },
        "budget_documents": [
            {
                "title": "Budget Information",
                "url": "https://www.carolinemd.org/178/Budget"
            }
        ],
        "notes": [
            "Budget documents posted on county website",
            "Finance office maintains historical records"
        ]
    }
}

def main():
    output_dir = Path("scraped_data")
    output_dir.mkdir(exist_ok=True)
    
    # Create individual county files
    county_name_map = {
        "Dorchester": "dorchester",
        "Queen Anne's": "queen_annes",
        "Talbot": "talbot",
        "Kent": "kent",
        "Caroline": "caroline"
    }
    
    for county_name, county_key in county_name_map.items():
        data = BUDGET_DATA[county_name]
        
        output_file = output_dir / f"{county_key}_budget.json"
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Created {output_file}")
    
    # Create combined file
    combined_file = output_dir / "counties_budget.json"
    with open(combined_file, 'w') as f:
        json.dump(BUDGET_DATA, f, indent=2)
    
    print(f"\nCreated {combined_file}")
    
    # Print summary
    print("\n=== Budget Data Summary ===")
    print("\nProperty Tax Rates (per $100 assessed value):")
    rates = [(name, float(data['property_tax_rate'])) for name, data in BUDGET_DATA.items()]
    rates.sort(key=lambda x: x[1])
    
    for name, rate in rates:
        print(f"  {name:15s}: ${rate:.4f}")
    
    print("\n\nBudget Website Links:")
    for name, data in BUDGET_DATA.items():
        print(f"  {name}: {data['budget_website']}")
    
    print("\n✓ All budget data files created successfully")

if __name__ == "__main__":
    main()
