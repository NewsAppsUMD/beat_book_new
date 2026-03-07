#!/usr/bin/env python3
"""
Generate individual beat books for each county using LLM analysis of scraped data.
This script creates analytical, explanatory, descriptive beat books based solely on 
the data in scraped_county_data/ - no external story coverage, just county data.

Uses groq/llama-3.3-70b-versatile by default, with fallback to openai/gpt-4o or deepseek/deepseek-chat
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Configuration
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "scraped_county_data"
OUTPUT_DIR = BASE_DIR / "county_beatbooks"

COUNTIES = {
    "caroline": "Caroline County",
    "dorchester": "Dorchester County",
    "kent": "Kent County",
    "queen_annes": "Queen Anne's County",
    "talbot": "Talbot County"
}

# Model selection - try in order
MODELS = [
    "groq/openai/gpt-oss-120b"
]

def run_llm(prompt: str, model: str, max_retries: int = 2) -> str:
    """Run LLM with the given prompt and model."""
    for attempt in range(max_retries):
        try:
            print(f"    Attempting with model: {model} (attempt {attempt + 1}/{max_retries})")
            result = subprocess.run(
                ["uv", "run", "llm", "-m", model],
                input=prompt.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=180  # 3 minute timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.decode("utf-8")
                print(f"    Error: {error_msg}")
                if attempt < max_retries - 1:
                    continue
                raise RuntimeError(error_msg)
            
            output = result.stdout.decode("utf-8")
            return output.strip()
            
        except subprocess.TimeoutExpired:
            print(f"    Timeout on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                continue
            raise RuntimeError("LLM request timed out")
    
    raise RuntimeError(f"Failed with model {model}")


def try_models(prompt: str) -> str:
    """Try each model in sequence until one works."""
    last_error = None
    
    for model in MODELS:
        try:
            return run_llm(prompt, model)
        except Exception as e:
            print(f"    Failed with {model}: {e}")
            last_error = e
            continue
    
    raise RuntimeError(f"All models failed. Last error: {last_error}")


def load_json(filepath: Path) -> dict | list | None:
    """Load JSON file, return None if not found."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"    Warning: Could not load {filepath}: {e}")
        return None


def load_text(filepath: Path) -> str:
    """Load text file, return empty string if not found."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"    Warning: Could not load {filepath}: {e}")
        return ""


def format_census_data(census_data: dict) -> str:
    """Format census data as readable text."""
    if not census_data:
        return "No census data available."
    
    text = ""
    
    # Get census API data
    api_data = census_data.get('census_api_data', {})
    
    # Population
    pop = api_data.get('population', {})
    if pop:
        text += f"Total Population: {pop.get('total', 0):,}\n"
        text += f"Median Age: {pop.get('median_age', 'N/A')} years\n"
        text += f"Male: {pop.get('male', 0):,} | Female: {pop.get('female', 0):,}\n\n"
    
    # Race/Ethnicity
    race = api_data.get('race_ethnicity', {})
    if race:
        text += "Race/Ethnicity:\n"
        text += f"  White alone: {race.get('white_alone', 0):,}\n"
        text += f"  Black alone: {race.get('black_alone', 0):,}\n"
        text += f"  Hispanic/Latino: {race.get('hispanic_latino', 0):,}\n\n"
    
    # Economics
    econ = api_data.get('economics', {})
    if econ:
        text += "Economics:\n"
        text += f"  Median Household Income: ${econ.get('median_household_income', 0):,}\n"
        text += f"  Median Home Value: ${econ.get('median_home_value', 0):,}\n"
        text += f"  Labor Force: {econ.get('labor_force', 0):,}\n"
        text += f"  Unemployed: {econ.get('unemployed', 0):,}\n\n"
    
    # Enhanced data
    enhanced = api_data.get('enhanced', {})
    if enhanced:
        # Poverty
        poverty = enhanced.get('poverty', {})
        if poverty:
            text += "Poverty:\n"
            text += f"  Poverty Rate: {poverty.get('poverty_rate', 0)}%\n"
            text += f"  People in Poverty: {poverty.get('people_in_poverty', 0):,}\n\n"
        
        # Housing affordability
        housing = enhanced.get('housing_affordability', {})
        if housing:
            text += "Housing:\n"
            text += f"  Homeownership Rate: {housing.get('homeownership_rate', 0)}%\n"
            text += f"  Median Rent: ${housing.get('median_rent', 0):,}\n"
            text += f"  Renters Cost-Burdened (30%+): {housing.get('renters_cost_burdened_30plus_pct', 0)}%\n\n"
        
        # Broadband
        broadband = enhanced.get('broadband_access', {})
        if broadband:
            text += f"Broadband Access: {broadband.get('broadband_pct', 0)}%\n\n"
        
        # Health insurance
        health = enhanced.get('health_insurance', {})
        if health:
            text += f"Uninsured Rate: {health.get('uninsured_rate', 0)}%\n\n"
    
    # Education
    edu = api_data.get('education', {})
    if edu:
        text += "Education (Degrees):\n"
        text += f"  Bachelor's: {edu.get('bachelors_degree', 0):,}\n"
        text += f"  Master's: {edu.get('masters_degree', 0):,}\n"
        text += f"  Professional: {edu.get('professional_degree', 0):,}\n"
        text += f"  Doctorate: {edu.get('doctorate_degree', 0):,}\n\n"
    
    return text


def format_officials_data(officials_data: dict) -> str:
    """Format officials data as readable text."""
    if not officials_data:
        return "No officials data available."
    
    text = ""
    
    # County seat and population
    if officials_data.get('county_seat'):
        text += f"County Seat: {officials_data.get('county_seat')}\n"
    if officials_data.get('population_2020'):
        text += f"Population (2020): {officials_data.get('population_2020')}\n\n"
    
    # Get nested county_officials if it exists
    county_officials = officials_data.get('county_officials', officials_data)
    
    # Legislative branch (Commissioners/Council)
    if county_officials.get('legislative_branch'):
        text += "County Commissioners/Council:\n"
        for comm in county_officials['legislative_branch']:
            name = comm.get('name', 'Unknown')
            title = comm.get('title', 'Commissioner')
            party = comm.get('party', '')
            party_str = f" ({party})" if party else ""
            text += f"  - {name} - {title}{party_str}\n"
        text += "\n"
    
    # Judicial branch
    if county_officials.get('judicial_branch'):
        text += "Judicial Branch:\n"
        for judge in county_officials['judicial_branch']:
            name = judge.get('name', 'Unknown')
            title = judge.get('title', 'Judge')
            text += f"  - {name} - {title}\n"
        text += "\n"
    
    # Executive branch (if any)
    if county_officials.get('executive_branch'):
        text += "Executive Branch:\n"
        for official in county_officials['executive_branch']:
            name = official.get('name', 'Unknown')
            title = official.get('title', 'Official')
            text += f"  - {name} - {title}\n"
        text += "\n"
    
    # Contact info
    if officials_data.get('other_info'):
        contact = officials_data['other_info']
        text += "Contact Information:\n"
        text += f"  Phone: {contact.get('phone', 'N/A')}\n"
        text += f"  Address: {contact.get('address', 'N/A')}\n"
        text += f"  Meeting Schedule: {contact.get('meeting_schedule', 'N/A')}\n"
        if contact.get('website'):
            text += f"  Website: {contact.get('website', 'N/A')}\n"
        text += "\n"
    
    return text


def format_municipal_officials(muni_data: list) -> str:
    """Format municipal officials data."""
    if not muni_data or not isinstance(muni_data, list):
        return "No municipal data available."
    
    text = ""
    for muni in muni_data:
        muni_name = muni.get('municipality_name', 'Unknown')
        text += f"\n{muni_name}:\n"
        
        # Chief executive (Mayor, etc.)
        if muni.get('chief_executive'):
            chief = muni['chief_executive']
            name = chief.get('name', 'Unknown')
            title = chief.get('title', 'Mayor')
            text += f"  {title}: {name}\n"
            if chief.get('email'):
                text += f"    Email: {chief['email']}\n"
            if chief.get('term_ends') or chief.get('term_expires'):
                term = chief.get('term_ends') or chief.get('term_expires')
                text += f"    Term: {term}\n"
        
        # Council members
        if muni.get('council_members'):
            text += "  Council Members:\n"
            for member in muni['council_members']:
                name = member.get('name', 'Unknown')
                title = member.get('title', 'Council Member')
                text += f"    - {name} ({title})\n"
                if member.get('email'):
                    text += f"      Email: {member['email']}\n"
        
        # Meeting schedule
        if muni.get('meeting_schedule'):
            text += f"  Meetings: {muni['meeting_schedule']}\n"
        
        # Website
        if muni.get('website'):
            text += f"  Website: {muni['website']}\n"
        
        text += "\n"
    
    return text


def format_elections_data(elections_data: dict) -> str:
    """Format elections data as readable text."""
    if not elections_data:
        return "No elections data available."
    
    text = ""
    # Get most recent 2-3 elections
    years = sorted(elections_data.keys(), reverse=True)[:3]
    
    for year in years:
        text += f"\n{year} Election Results:\n"
        results = elections_data[year]
        
        if isinstance(results, dict):
            for race, data in results.items():
                text += f"  {race}:\n"
                if isinstance(data, dict):
                    for candidate, votes in data.items():
                        text += f"    {candidate}: {votes}\n"
                elif isinstance(data, list):
                    for item in data:
                        text += f"    {item}\n"
        text += "\n"
    
    return text


def build_beatbook_prompt(county_name: str, county_key: str, 
                         census_text: str, officials_text: str,
                         muni_text: str, elections_text: str,
                         budget_text: str, minutes_text: str) -> str:
    """Build the comprehensive prompt for generating a county beat book."""
    
    return f"""You are an expert journalist and data analyst creating a comprehensive BEAT BOOK for {county_name}, Maryland. This beat book will serve as a reference guide for reporters covering local government in this county.

Your task is to write an ANALYTICAL, EXPLANATORY, and DESCRIPTIVE beat book based SOLELY on the data provided below. Do not make suggestions or recommendations. Focus on describing patterns, trends, challenges, and the current state of affairs.

=== DATA FOR {county_name.upper()} ===

CENSUS & DEMOGRAPHIC DATA (2022 ACS 5-Year Estimates):
{census_text}

COUNTY OFFICIALS & GOVERNMENT STRUCTURE:
{officials_text}

MUNICIPAL GOVERNMENTS:
{muni_text}

RECENT ELECTION RESULTS:
{elections_text}

BUDGET ANALYSIS (FY2026):
{budget_text[:4000] if budget_text else "No budget data available."}

RECENT MEETING MINUTES ANALYSIS:
{minutes_text[:4000] if minutes_text else "No meeting minutes analysis available."}

=== WRITING INSTRUCTIONS ===

Write a comprehensive beat book with the following sections in EXACTLY this structure:

# {county_name} Beat Book

## 1. County Overview
Write 3-4 paragraphs describing:
- The county's demographic profile (population, age, race/ethnicity breakdown)
- Economic conditions (median income, employment, poverty rate)
- Housing characteristics (homeownership rate, median home value, median rent, cost-burden)
- Broadband access and health insurance coverage
- Educational attainment levels

## 2. Government Structure & Leadership
- State the form of government and county seat
- Create a table listing all County Commissioners/Council members with their names, titles, and party affiliations
- List Judicial Branch officials (judges)
- List any Executive Branch officials if present
- Include contact information (phone, address, meeting schedule, website)
- Describe governance patterns from meeting minutes (voting patterns, public participation)

## 3. Key Policy Areas & Challenges
Identify and describe 4-6 major policy areas. For each, use this subsection format:

### [Policy Area Name]
- **Issue**: Brief description of the challenge
- **Budget/Data Context**: Cite specific budget allocations and relevant demographic statistics
- **Recent Developments**: Describe actions from meeting minutes or budget documents
- **Tensions/Trade-offs**: Explain competing priorities or difficult choices

Policy areas should be drawn from: infrastructure (detention centers, wastewater, roads), housing affordability, public safety/emergency services, economic development, healthcare/social services, education funding, environmental regulations

## 4. Municipal Governments
Create a table with columns: Municipality Name | Key Officials | Notable Issues
- List all incorporated towns/cities
- Include mayors, council members, or managers from the municipal officials data
- Note cross-municipality patterns or shared challenges

## 5. Political Landscape
- Describe recent election results (last 2-3 elections)
- Note party composition of county government
- Describe voter turnout patterns or political shifts
- If election data is limited, note what information is missing

## 6. Financial Picture
- State total budget, operating budget, and capital budget for FY2026
- Create a revenue breakdown table showing major sources and percentages
- Create an expenditure breakdown table showing major categories and percentages
- Highlight notable increases/decreases
- Note any use of fund balance or financial constraints

## 7. Key Contacts & Information
Create a quick reference table with:
- Position | Name | Department/Role | Contact
- Include all commissioners, key department heads
- Add meeting schedule and website links
- If specific names are missing from data, note that reporters should verify current officials

=== STYLE GUIDELINES ===

- Write in a clear, journalistic style
- Be descriptive and analytical, not prescriptive
- Use specific numbers and data points
- Connect different data sources (e.g., how demographic trends relate to budget priorities)
- Avoid editorial commentary or suggestions
- Focus on facts and patterns
- Use proper markdown formatting
- When citing specific information from meeting minutes or budgets, be specific

Generate the complete beat book now:"""


def generate_county_beatbook(county_key: str, county_name: str) -> bool:
    """Generate beat book for a single county."""
    
    print(f"\n{'='*70}")
    print(f"Generating beat book for {county_name}")
    print(f"{'='*70}\n")
    
    county_dir = DATA_DIR / county_key
    
    # Load all data files
    print("  Loading data files...")
    census_data = load_json(county_dir / f"{county_key}_census.json")
    officials_data = load_json(county_dir / f"{county_key}_county_officials.json")
    muni_data = load_json(county_dir / f"{county_key}_municipal_officials.json")
    elections_data = load_json(county_dir / f"{county_key}_elections.json")
    budget_text = load_text(county_dir / f"{county_key}_budget_analysis.md")
    minutes_text = load_text(county_dir / f"{county_key}_recent_minutes_analysis.md")
    
    # Format data
    print("  Formatting data...")
    census_text = format_census_data(census_data)
    officials_text = format_officials_data(officials_data)
    muni_text = format_municipal_officials(muni_data)
    elections_text = format_elections_data(elections_data)
    
    # Build prompt
    print("  Building prompt...")
    prompt = build_beatbook_prompt(
        county_name, county_key,
        census_text, officials_text,
        muni_text, elections_text,
        budget_text, minutes_text
    )
    
    # Generate with LLM
    print("  Generating beat book with LLM...")
    try:
        beatbook_content = try_models(prompt)
    except Exception as e:
        print(f"  ERROR: Failed to generate beat book: {e}")
        return False
    
    # Save output
    output_file = OUTPUT_DIR / f"{county_key}_beatbook.md"
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Add metadata header
        f.write(f"<!-- Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')} -->\n")
        f.write(f"<!-- Data sources: Census 2022 ACS, County FY2026 Budget, Recent meeting minutes -->\n\n")
        f.write(beatbook_content)
    
    print(f"  ✓ Beat book saved to: {output_file}")
    print(f"  ✓ Length: {len(beatbook_content):,} characters\n")
    
    return True


def main():
    """Generate beat books for all counties."""
    
    print("\n" + "="*70)
    print("COUNTY BEAT BOOK GENERATOR")
    print("Analytical, explanatory, descriptive beat books from scraped data")
    print("="*70)
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Process each county
    success_count = 0
    for county_key, county_name in COUNTIES.items():
        if generate_county_beatbook(county_key, county_name):
            success_count += 1
    
    # Summary
    print("\n" + "="*70)
    print(f"COMPLETED: {success_count}/{len(COUNTIES)} beat books generated successfully")
    print(f"Output directory: {OUTPUT_DIR}")
    print("="*70 + "\n")
    
    return 0 if success_count == len(COUNTIES) else 1


if __name__ == "__main__":
    sys.exit(main())
