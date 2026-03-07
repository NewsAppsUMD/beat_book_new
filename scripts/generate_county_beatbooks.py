#!/usr/bin/env python3
"""
Generate comprehensive county beat books (one per county) incorporating:
1. Full story coverage from stories_by_county/*.json
2. County officials and government structure
3. Municipal officials for all towns/cities
4. Census demographics and economics
5. School data and ratings
6. Election results
7. Budget analysis
8. Recent meeting minutes analysis
9. Top issues analysis (from top_issues_by_county.json)

Uses LLM to synthesize narrative sections that merge story coverage with all available data.
"""

import json
import subprocess
import re
from pathlib import Path
import time
from datetime import datetime
from collections import Counter

MODEL_NAME = "groq/meta-llama/llama-4-maverick-17b-128e-instruct"

BASE_DIR = Path("/workspaces/jour329w_fall2025/murphy/stardem_draft_v3")
DATA_DIR = BASE_DIR / "scraped_county_data"
STORIES_DIR = BASE_DIR / "stories_by_county"
OUTPUT_DIR = BASE_DIR / "county_beatbooks"

# Story data files
TOP_ISSUES_BY_COUNTY = BASE_DIR / "top_issues_by_county.json"
TOP_RECURRING_ISSUES = BASE_DIR / "top_recurring_issues.json"

COUNTIES = {
    "caroline": "Caroline",
    "dorchester": "Dorchester",
    "kent": "Kent",
    "queen_annes": "Queen Anne's",
    "talbot": "Talbot"
}


# ---------------------------------------------------------
# LLM utility with <think> tag stripping and retry logic
# ---------------------------------------------------------
def run_llm(prompt: str, max_retries: int = 3) -> str:
    """Runs the LLM through the command-line interface and strips <think> tags."""
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                ["llm", "-m", MODEL_NAME],
                input=prompt.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=180  # 3 minute timeout
            )
            if result.returncode != 0:
                error_msg = result.stderr.decode("utf-8")
                print(f"  Attempt {attempt + 1} failed: {error_msg}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                raise RuntimeError(error_msg)
            
            output = result.stdout.decode("utf-8")
            
            # Strip out <think>...</think> content
            output = re.sub(r'<think>.*?</think>', '', output, flags=re.DOTALL)
            
            return output.strip()
        except subprocess.TimeoutExpired:
            print(f"  Attempt {attempt + 1} timed out")
            if attempt < max_retries - 1:
                time.sleep(5)
                continue
            raise RuntimeError("LLM request timed out after multiple attempts")
    
    raise RuntimeError("Failed to get LLM response after all retries")


# ---------------------------------------------------------
# Data loading utilities
# ---------------------------------------------------------
def load_json(filepath):
    """Load JSON file, return None if not found"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except:
        return None


def format_currency(value):
    """Format number as currency"""
    if value is None:
        return "N/A"
    return f"${value:,.0f}"


def format_percent(value):
    """Format as percentage"""
    if value is None:
        return "N/A"
    return f"{value}%"


# ---------------------------------------------------------
# Extract entities from stories
# ---------------------------------------------------------
def extract_story_metadata(stories):
    """Extract key metadata from stories for analysis."""
    people = Counter()
    organizations = Counter()
    initiatives = Counter()
    tags = Counter()
    
    for story in stories:
        for person in story.get('key_people', []):
            people[person] += 1
        for org in story.get('key_organizations', []):
            organizations[org] += 1
        for init in story.get('key_initiatives', []):
            initiatives[init] += 1
        
        tag = story.get('beatbook_tag', 'Other')
        tags[tag] += 1
    
    return {
        'top_people': [p for p, _ in people.most_common(20)],
        'top_organizations': [o for o, _ in organizations.most_common(15)],
        'top_initiatives': [i for i, _ in initiatives.most_common(15)],
        'tags': tags
    }


# ---------------------------------------------------------
# Format stories for LLM prompts
# ---------------------------------------------------------
def format_stories_for_prompt(stories, max_stories=20):
    """Format stories with full content for LLM."""
    text = ""
    
    for i, story in enumerate(stories[:max_stories], 1):
        text += f"\n{'='*60}\n"
        text += f"STORY {i}: {story.get('title', 'Untitled')}\n"
        text += f"{'='*60}\n"
        text += f"Date: {story.get('date', 'N/A')} | Author: {story.get('author', 'Unknown')}\n"
        text += f"Tag: {story.get('beatbook_tag', 'N/A')}\n\n"
        
        if story.get('summary'):
            text += f"Summary: {story.get('summary')}\n\n"
        
        if story.get('key_people'):
            text += f"Key People: {', '.join(story.get('key_people', [])[:10])}\n"
        
        if story.get('key_organizations'):
            text += f"Organizations: {', '.join(story.get('key_organizations', [])[:8])}\n"
        
        if story.get('key_initiatives'):
            text += f"Initiatives: {', '.join(story.get('key_initiatives', [])[:6])}\n"
        
        if story.get('municipalities'):
            text += f"Municipalities: {', '.join(story.get('municipalities', [])[:4])}\n"
        
        text += "\n"
    
    return text


# ---------------------------------------------------------
# Build LLM prompts for narrative sections
# ---------------------------------------------------------
def build_overview_narrative_prompt(county_name, census_data, officials_data, schools_data, 
                                    stories_text, metadata, top_issues_summary):
    return f"""
You are writing an "Overview & Recent Developments" narrative section for {county_name} County, Maryland in a local government beat book.

This narrative should synthesize demographic/government data WITH recent news coverage to give a new reporter context.

DEMOGRAPHIC & GOVERNMENT DATA:
{census_data[:1500]}

{officials_data[:800]}

{schools_data[:600]}

TOP ISSUES FROM COVERAGE ANALYSIS:
{top_issues_summary[:1000]}

STORY METADATA:
- Total stories analyzed: {len(metadata.get('top_people', []))}
- Key people mentioned: {', '.join(metadata.get('top_people', [])[:12])}
- Key organizations: {', '.join(metadata.get('top_organizations', [])[:10])}
- Top initiatives: {', '.join(metadata.get('top_initiatives', [])[:8])}

RECENT STORIES (for context and examples):
{stories_text[:3000]}

TASK: Write 3-4 paragraphs that:
1. Introduce {county_name} County's demographic profile and government structure
2. Connect demographic realities (poverty rate, housing costs, population trends) to policy issues emerging in coverage
3. Highlight major ongoing issues from recent news coverage (reference stories using numbered footnotes [1], [2], etc.)
4. Identify key decision-makers and power dynamics
5. Set context for understanding current county debates

Requirements:
- Write in direct, newsroom style - no fluff
- Reference specific stories using numbered footnotes [1], [2], etc. based on the story list provided
- Connect data to stories (e.g., "With a poverty rate of 15.4% and median income of $57,490, the county faces budget pressures reflected in recent coverage of tax increase proposals [3]")
- Focus on developments from 2023-2025
- Do NOT use title references - only numbered footnotes
"""


def build_top_issues_narrative_prompt(county_name, stories_text, metadata, top_issues_data):
    return f"""
You are writing a "Top Three Issues" section for {county_name} County, Maryland.

TOP ISSUES DATA (from analysis):
{top_issues_data[:2000]}

STORY COVERAGE WITH DETAILS:
{stories_text[:4000]}

COVERAGE METADATA:
- Most mentioned people: {', '.join(metadata.get('top_people', [])[:15])}
- Key organizations: {', '.join(metadata.get('top_organizations', [])[:12])}
- Major initiatives: {', '.join(metadata.get('top_initiatives', [])[:10])}

TASK: Write "Top Three Issues on the Beat" section with **exactly three issues** as H3 headings (###).

For each issue:
- Write 2-4 paragraphs of narrative prose (NO bullet lists)
- Ground the issue in specific story coverage (reference stories using numbered footnotes [1], [2], etc.)
- Explain why it matters and what's at stake
- Identify key players and their positions
- Note unresolved questions or upcoming decisions

Focus on systemic, ongoing challenges like:
- Budget/fiscal pressures
- Infrastructure needs
- Development conflicts
- Housing affordability
- Governance/transparency
- Service delivery
- Environmental challenges

Requirements:
- Use H3 headings (###) for each issue
- Write narrative paragraphs, NOT bullet lists
- Reference stories using numbered footnotes [1], [2], etc.
- Focus on 2024-2025 developments
- Explain consequences and stakes
"""


# ---------------------------------------------------------
# Generate full county beat book
# ---------------------------------------------------------
def generate_county_beatbook(county_key, county_name):
    """Generate complete beat book for one county."""
    
    print(f"\n{'='*70}")
    print(f"GENERATING BEAT BOOK: {county_name} County")
    print(f"{'='*70}\n")
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / f"{county_key}_county_beatbook.md"
    
    # Load all data
    print("Loading data files...")
    county_dir = DATA_DIR / county_key
    
    # Load scraped county data
    census = load_json(county_dir / f"{county_key}_census.json")
    officials = load_json(county_dir / f"{county_key}_county_officials.json")
    muni_officials = load_json(county_dir / f"{county_key}_municipal_officials.json")
    schools = load_json(county_dir / f"{county_key}_schools.json")
    elections = load_json(county_dir / f"{county_key}_elections.json")
    muni_census = load_json(county_dir / f"{county_key}_municipalities_census.json")
    
    # Load stories
    stories_file = STORIES_DIR / f"{county_key}_county.json"
    stories = load_json(stories_file)
    
    if not stories:
        print(f"  ERROR: No stories found for {county_name} County")
        return
    
    print(f"  Loaded {len(stories)} stories")
    
    # Load top issues
    top_issues_all = load_json(TOP_ISSUES_BY_COUNTY)
    county_issues = top_issues_all.get(f"{county_name} County", []) if top_issues_all else []
    
    # Extract metadata
    metadata = extract_story_metadata(stories)
    
    # Sort stories by date (most recent first)
    stories.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    # Format data sections
    census_text = format_census_section(census)
    officials_text = format_officials_section(officials)
    muni_officials_text = format_municipal_officials_section(muni_officials)
    schools_text = format_schools_section(schools)
    elections_text = format_elections_section(elections)
    muni_census_text = format_municipal_census_section(muni_census)
    
    # Format stories for prompts
    recent_stories_text = format_stories_for_prompt(stories, max_stories=20)
    top_issues_summary = format_top_issues_summary(county_issues)
    top_issues_detailed = format_top_issues_detailed(county_issues)
    
    # Generate beat book
    with open(output_file, 'w') as out:
        # Header
        out.write(f"# {county_name} County Beat Book\n\n")
        out.write(f"**Local Government Coverage Guide**\n\n")
        out.write(f"*Generated: {datetime.now().strftime('%B %d, %Y')}*\n\n")
        out.write(f"*Coverage period: 2023-2025 | {len(stories)} stories analyzed*\n\n")
        out.write("---\n\n")
        
        # Table of Contents
        out.write("## Table of Contents\n\n")
        out.write("1. [Overview & Recent Developments](#overview--recent-developments)\n")
        out.write("2. [Top Three Issues](#top-three-issues)\n")
        out.write("3. [County Government](#county-government)\n")
        out.write("4. [Municipal Governments](#municipal-governments)\n")
        out.write("5. [Demographics & Census Data](#demographics--census-data)\n")
        out.write("6. [Schools & Education](#schools--education)\n")
        out.write("7. [Elections & Voting](#elections--voting)\n")
        out.write("8. [Key Sources & Contacts](#key-sources--contacts)\n")
        out.write("\n---\n\n")
        
        # 1. OVERVIEW NARRATIVE (LLM-generated)
        print("  Generating overview narrative...")
        overview_prompt = build_overview_narrative_prompt(
            county_name, census_text, officials_text, schools_text,
            recent_stories_text, metadata, top_issues_summary
        )
        overview_narrative = run_llm(overview_prompt)
        
        out.write("## Overview & Recent Developments\n\n")
        out.write(overview_narrative + "\n\n")
        out.write("---\n\n")
        
        # 2. TOP THREE ISSUES (LLM-generated)
        print("  Generating top three issues...")
        issues_prompt = build_top_issues_narrative_prompt(
            county_name, recent_stories_text, metadata, top_issues_detailed
        )
        issues_narrative = run_llm(issues_prompt)
        
        out.write("## Top Three Issues\n\n")
        out.write(issues_narrative + "\n\n")
        out.write("---\n\n")
        
        # 3. COUNTY GOVERNMENT (structured data)
        print("  Writing county government section...")
        out.write("## County Government\n\n")
        out.write(officials_text + "\n\n")
        out.write("---\n\n")
        
        # 4. MUNICIPAL GOVERNMENTS (structured data)
        print("  Writing municipal governments section...")
        out.write("## Municipal Governments\n\n")
        out.write(muni_officials_text + "\n\n")
        out.write("---\n\n")
        
        # 5. DEMOGRAPHICS & CENSUS (structured data)
        print("  Writing demographics section...")
        out.write("## Demographics & Census Data\n\n")
        out.write(census_text + "\n\n")
        if muni_census_text:
            out.write("### Municipal Demographics\n\n")
            out.write(muni_census_text + "\n\n")
        out.write("---\n\n")
        
        # 6. SCHOOLS (structured data)
        print("  Writing schools section...")
        out.write("## Schools & Education\n\n")
        out.write(schools_text + "\n\n")
        out.write("---\n\n")
        
        # 7. ELECTIONS (structured data)
        print("  Writing elections section...")
        out.write("## Elections & Voting\n\n")
        out.write(elections_text + "\n\n")
        out.write("---\n\n")
        
        # 8. KEY SOURCES (extracted from stories + officials)
        print("  Compiling key sources...")
        sources_text = compile_key_sources(metadata, officials, muni_officials)
        out.write("## Key Sources & Contacts\n\n")
        out.write(sources_text + "\n\n")
    
    print(f"\n✓ Beat book saved: {output_file}")
    print(f"{'='*70}\n")


# ---------------------------------------------------------
# Format structured data sections
# ---------------------------------------------------------
def format_census_section(census):
    """Format census data as structured section."""
    if not census:
        return "Census data not available."
    
    text = "**Data Source:** U.S. Census Bureau, American Community Survey 2022 (5-year estimates)\n\n"
    
    census_data = census.get('census_api_data', {})
    pop = census_data.get('population', {})
    race = census_data.get('race_ethnicity', {})
    econ = census_data.get('economics', {})
    housing = census_data.get('housing', {})
    enhanced = census_data.get('enhanced', {})
    
    # Population
    text += "### Population\n\n"
    total_pop = pop.get('total', 0)
    text += f"- **Total Population:** {total_pop:,}\n"
    text += f"- **Male:** {pop.get('male', 0):,} ({pop.get('male', 0)/total_pop*100:.1f}%)\n"
    text += f"- **Female:** {pop.get('female', 0):,} ({pop.get('female', 0)/total_pop*100:.1f}%)\n"
    text += f"- **Median Age:** {pop.get('median_age', 'N/A')} years\n\n"
    
    # Race/Ethnicity
    text += "### Race & Ethnicity\n\n"
    text += f"- **White (alone):** {race.get('white_alone', 0):,} ({race.get('white_alone', 0)/total_pop*100:.1f}%)\n"
    text += f"- **Black (alone):** {race.get('black_alone', 0):,} ({race.get('black_alone', 0)/total_pop*100:.1f}%)\n"
    text += f"- **Hispanic/Latino:** {race.get('hispanic_latino', 0):,} ({race.get('hispanic_latino', 0)/total_pop*100:.1f}%)\n"
    text += f"- **Asian (alone):** {race.get('asian_alone', 0):,} ({race.get('asian_alone', 0)/total_pop*100:.1f}%)\n\n"
    
    # Economics
    text += "### Economics\n\n"
    text += f"- **Median Household Income:** {format_currency(econ.get('median_household_income'))}\n"
    text += f"- **Per Capita Income:** {format_currency(econ.get('per_capita_income'))}\n"
    text += f"- **Labor Force:** {econ.get('labor_force', 0):,}\n"
    text += f"- **Unemployed:** {econ.get('unemployed', 0):,}\n"
    text += f"- **Unemployment Rate:** {econ.get('unemployed', 0)/econ.get('labor_force', 1)*100:.1f}%\n\n"
    
    if enhanced:
        poverty = enhanced.get('poverty', {})
        housing_aff = enhanced.get('housing_affordability', {})
        age = enhanced.get('age_breakdown', {})
        broadband = enhanced.get('broadband_access', {})
        edu = enhanced.get('education_attainment_full', {})
        health = enhanced.get('health_insurance', {})
        
        # Poverty
        text += "### Poverty\n\n"
        text += f"- **Poverty Rate:** {format_percent(poverty.get('poverty_rate'))}\n"
        text += f"- **People in Poverty:** {poverty.get('people_in_poverty', 0):,}\n"
        text += f"- **Children in Poverty:** {poverty.get('children_in_poverty', 0):,}\n"
        text += f"- **Seniors in Poverty:** {poverty.get('seniors_in_poverty', 0):,}\n\n"
        
        # Housing
        text += "### Housing\n\n"
        text += f"- **Total Units:** {housing.get('total_units', 0):,}\n"
        text += f"- **Occupied:** {housing.get('occupied_units', 0):,}\n"
        text += f"- **Vacant:** {housing.get('vacant_units', 0):,}\n"
        text += f"- **Median Home Value:** {format_currency(econ.get('median_home_value'))}\n"
        text += f"- **Median Rent:** {format_currency(housing_aff.get('median_rent'))}\n"
        text += f"- **Homeownership Rate:** {format_percent(housing_aff.get('homeownership_rate'))}\n"
        text += f"- **Renters Cost-Burdened (30%+ income):** {format_percent(housing_aff.get('renters_cost_burdened_30plus_pct'))}\n"
        text += f"- **Owners Cost-Burdened (30%+ income):** {format_percent(housing_aff.get('owners_cost_burdened_30plus_pct'))}\n\n"
        
        # Age Distribution
        text += "### Age Distribution\n\n"
        text += f"- **Under 5:** {age.get('under_5_years', 0):,} ({format_percent(age.get('under_5_pct'))})\n"
        text += f"- **School Age (5-17):** {age.get('school_age_5_17', 0):,} ({format_percent(age.get('school_age_pct'))})\n"
        text += f"- **Working Age (18-64):** {age.get('working_age_18_64', 0):,} ({format_percent(age.get('working_age_pct'))})\n"
        text += f"- **Seniors (65+):** {age.get('seniors_65_plus', 0):,} ({format_percent(age.get('seniors_pct'))})\n\n"
        
        # Broadband
        text += "### Digital Access\n\n"
        text += f"- **With Broadband:** {broadband.get('with_broadband', 0):,} ({format_percent(broadband.get('broadband_pct'))})\n"
        text += f"- **No Internet:** {broadband.get('no_internet', 0):,} ({format_percent(broadband.get('no_internet_pct'))})\n\n"
        
        # Education
        text += "### Education Attainment (Age 25+)\n\n"
        text += f"- **Less than High School:** {format_percent(edu.get('less_than_high_school_pct'))}\n"
        text += f"- **High School Graduate:** {format_percent(edu.get('high_school_graduate_pct'))}\n"
        text += f"- **Some College:** {format_percent(edu.get('some_college_pct'))}\n"
        text += f"- **Associate's Degree:** {format_percent(edu.get('associates_degree_pct'))}\n"
        text += f"- **Bachelor's Degree:** {format_percent(edu.get('bachelors_degree_pct'))}\n"
        text += f"- **Graduate Degree:** {format_percent(edu.get('graduate_degree_pct'))}\n\n"
        
        # Health Insurance
        text += "### Health Insurance\n\n"
        text += f"- **Uninsured Rate:** {format_percent(health.get('uninsured_rate'))}\n"
        text += f"- **Total Uninsured:** {health.get('uninsured_total', 0):,}\n"
        text += f"- **Children Uninsured:** {health.get('children_uninsured', 0):,}\n"
    
    return text


def format_officials_section(officials):
    """Format county officials as structured section."""
    if not officials:
        return "County officials data not available."
    
    text = f"**Government Type:** {officials.get('government_type', 'N/A')}\n\n"
    text += f"**Website:** {officials.get('website', 'N/A')}\n\n"
    
    if officials.get('meeting_schedule'):
        text += f"**Meeting Schedule:** {officials['meeting_schedule']}\n\n"
    
    # Commissioners
    if officials.get('commissioners'):
        text += "### County Commissioners\n\n"
        text += "| Name | Title | Term Ends | Phone | Email |\n"
        text += "|------|-------|-----------|-------|-------|\n"
        for comm in officials['commissioners']:
            name = comm.get('name', 'Unknown')
            title = comm.get('title', 'Commissioner')
            term = comm.get('term_ends', '')
            phone = comm.get('phone', '')
            email = comm.get('email', '')
            text += f"| {name} | {title} | {term} | {phone} | {email} |\n"
        text += "\n"
    
    # Key staff
    if officials.get('key_staff'):
        text += "### Key County Staff\n\n"
        text += "| Name | Title | Department | Phone | Email |\n"
        text += "|------|-------|------------|-------|-------|\n"
        for staff in officials['key_staff']:
            name = staff.get('name', 'Unknown')
            title = staff.get('title', '')
            dept = staff.get('department', '')
            phone = staff.get('phone', '')
            email = staff.get('email', '')
            text += f"| {name} | {title} | {dept} | {phone} | {email} |\n"
        text += "\n"
    
    # Contact info
    if officials.get('contact'):
        contact = officials['contact']
        text += "### County Contact Information\n\n"
        text += f"- **Address:** {contact.get('address', 'N/A')}\n"
        text += f"- **Phone:** {contact.get('phone', 'N/A')}\n"
        text += f"- **Email:** {contact.get('email', 'N/A')}\n"
    
    return text


def format_municipal_officials_section(muni_officials):
    """Format municipal officials as structured section."""
    if not muni_officials:
        return "Municipal officials data not available."
    
    text = ""
    
    for muni in muni_officials:
        muni_name = muni.get('municipality_name', 'Unknown')
        text += f"### {muni_name}\n\n"
        text += f"**Website:** {muni.get('website', 'N/A')}\n\n"
        
        # Chief executive
        if muni.get('chief_executive'):
            ce = muni['chief_executive']
            text += f"**{ce.get('title', 'Mayor')}:** {ce.get('name', 'N/A')}"
            if ce.get('term_expires'):
                text += f" (term ends {ce['term_expires']})"
            if ce.get('phone'):
                text += f" | {ce['phone']}"
            if ce.get('email'):
                text += f" | {ce['email']}"
            text += "\n\n"
        
        # Council members
        if muni.get('council_members'):
            text += "**Council/Commissioners:**\n\n"
            for member in muni['council_members']:
                text += f"- {member.get('name', 'Unknown')} - {member.get('title', 'Member')}"
                if member.get('term_expires'):
                    text += f" (term ends {member['term_expires']})"
                if member.get('phone'):
                    text += f" | {member['phone']}"
                if member.get('email'):
                    text += f" | {member['email']}"
                text += "\n"
            text += "\n"
        
        # Meeting schedule
        if muni.get('meeting_schedule'):
            text += f"**Meetings:** {muni['meeting_schedule']}\n\n"
    
    return text


def format_schools_section(schools):
    """Format schools as structured section."""
    if not schools:
        return "Schools data not available."
    
    school_data = schools.get('schools', {})
    text = f"**School District:** {school_data.get('district_name', 'N/A')}\n\n"
    text += f"**Website:** {school_data.get('website', 'N/A')}\n\n"
    text += f"**Superintendent:** {school_data.get('superintendent', 'N/A')}\n\n"
    text += f"**Total Enrollment:** ~{school_data.get('total_enrollment', 0):,} students\n\n"
    
    school_list = school_data.get('schools', [])
    if school_list:
        text += f"### Schools ({len(school_list)} total)\n\n"
        text += "| School Name | Level | Star Rating | Percentile |\n"
        text += "|-------------|-------|-------------|------------|\n"
        
        for school in sorted(school_list, key=lambda x: (x.get('level', ''), x.get('name', ''))):
            name = school.get('name', 'Unknown')
            level = school.get('level', 'N/A')
            stars = school.get('star_rating', 'N/A')
            pct = school.get('percentile', 'N/A')
            text += f"| {name} | {level} | {stars} | {pct} |\n"
        
        text += "\n**Note:** Ratings from Maryland State Department of Education\n"
    
    return text


def format_elections_section(elections):
    """Format election results as structured section."""
    if not elections:
        return "Election data not available."
    
    text = "**Recent Election Results**\n\n"
    
    # 2024 General Election
    if elections.get('2024_general'):
        results = elections['2024_general']
        text += "### 2024 General Election\n\n"
        
        if results.get('president'):
            text += "**President:**\n\n"
            for candidate, votes in sorted(results['president'].items(), key=lambda x: x[1], reverse=True):
                text += f"- {candidate}: {votes:,} votes\n"
            text += "\n"
        
        if results.get('us_senate'):
            text += "**U.S. Senate:**\n\n"
            for candidate, votes in sorted(results['us_senate'].items(), key=lambda x: x[1], reverse=True):
                text += f"- {candidate}: {votes:,} votes\n"
            text += "\n"
    
    # Registration stats
    if elections.get('registration'):
        reg = elections['registration']
        text += "### Voter Registration\n\n"
        text += f"- **Total Registered:** {reg.get('total', 0):,}\n"
        text += f"- **Democrats:** {reg.get('democrat', 0):,}\n"
        text += f"- **Republicans:** {reg.get('republican', 0):,}\n"
        text += f"- **Unaffiliated:** {reg.get('unaffiliated', 0):,}\n"
    
    return text


def format_municipal_census_section(muni_census):
    """Format municipal census data."""
    if not muni_census:
        return ""
    
    # Handle nested structure
    municipalities = muni_census.get('municipalities', []) if isinstance(muni_census, dict) else []
    
    if not municipalities:
        return ""
    
    text = "| Municipality | Population | Median Age | Median Income |\n"
    text += "|--------------|------------|------------|---------------|\n"
    
    for muni in municipalities:
        name = muni.get('place_name', 'Unknown')
        pop_data = muni.get('population', {})
        pop = pop_data.get('total', 0)
        age = pop_data.get('median_age', 'N/A')
        econ = muni.get('economics', {})
        income = econ.get('median_household_income')
        text += f"| {name} | {pop:,} | {age} | {format_currency(income)} |\n"
    
    return text


def format_top_issues_summary(issues):
    """Brief summary of top issues."""
    if not issues:
        return "No top issues data available."
    
    text = ""
    for i, issue in enumerate(issues[:5], 1):
        text += f"{i}. {issue.get('issue_name', 'Unknown')} ({issue.get('story_count', 0)} stories)\n"
        text += f"   {issue.get('significance', '')}\n\n"
    
    return text


def format_top_issues_detailed(issues):
    """Detailed top issues for LLM."""
    if not issues:
        return "No top issues data available."
    
    text = ""
    for i, issue in enumerate(issues[:8], 1):
        text += f"\nISSUE {i}: {issue.get('issue_name', 'Unknown')}\n"
        text += f"Stories: {issue.get('story_count', 0)} | Period: {issue.get('date_range', 'N/A')}\n"
        text += f"Significance: {issue.get('significance', '')}\n"
        text += f"Recent: {issue.get('recent_developments', '')}\n"
        
        refs = issue.get('story_references', [])
        if refs:
            text += "Sample stories:\n"
            for ref in refs[:4]:
                text += f"- {ref.get('title', 'Untitled')} ({ref.get('date', 'N/A')})\n"
        text += "\n"
    
    return text


def compile_key_sources(metadata, officials, muni_officials):
    """Compile key sources from stories and officials data."""
    text = "### County Officials\n\n"
    
    if officials and officials.get('commissioners'):
        for comm in officials['commissioners']:
            name = comm.get('name', 'Unknown')
            title = comm.get('title', 'Commissioner')
            text += f"- **{name}** - {title}\n"
    
    text += "\n### Municipal Officials\n\n"
    
    if muni_officials:
        for muni in muni_officials:
            muni_name = muni.get('municipality_name', 'Unknown')
            text += f"**{muni_name}:**\n"
            
            if muni.get('chief_executive'):
                ce = muni['chief_executive']
                text += f"- {ce.get('name', 'N/A')} - {ce.get('title', 'Mayor')}\n"
            
            if muni.get('council_members'):
                for member in muni['council_members'][:3]:
                    text += f"- {member.get('name', 'Unknown')} - {member.get('title', 'Member')}\n"
            text += "\n"
    
    text += "### Frequently Mentioned in Coverage\n\n"
    
    if metadata.get('top_people'):
        text += "**People:**\n"
        for person in metadata['top_people'][:15]:
            text += f"- {person}\n"
        text += "\n"
    
    if metadata.get('top_organizations'):
        text += "**Organizations:**\n"
        for org in metadata['top_organizations'][:12]:
            text += f"- {org}\n"
    
    return text


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
def main():
    print("\n" + "="*70)
    print("COMPREHENSIVE COUNTY BEAT BOOK GENERATOR")
    print("="*70)
    print("\nGenerating five separate beat books with:")
    print("  - Full story coverage analysis")
    print("  - Government structure & officials")
    print("  - Demographics & census data")
    print("  - Schools & education")
    print("  - Elections & voting")
    print("  - LLM-generated narrative synthesis")
    print()
    
    for county_key, county_name in COUNTIES.items():
        generate_county_beatbook(county_key, county_name)
    
    print("\n" + "="*70)
    print("✓ ALL BEAT BOOKS GENERATED")
    print(f"✓ Output directory: {OUTPUT_DIR}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
