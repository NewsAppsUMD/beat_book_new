#!/usr/bin/env python3
"""
Generate a comprehensive local government beat book by combining:
1. Story coverage data (top_issues_by_county.json, top_recurring_issues.json)
2. County demographic and census data
3. County officials and government structure data
4. School data
5. Budget and meeting minutes analysis

Uses LLM to synthesize narrative sections that merge issue coverage with contextual data.
"""

import json
import subprocess
import re
from pathlib import Path
import time
from datetime import datetime

MODEL_NAME = "groq/meta-llama/llama-4-maverick-17b-128e-instruct"

COUNTIES = {
    "caroline": "Caroline",
    "dorchester": "Dorchester",
    "kent": "Kent",
    "queen_annes": "Queen Anne's",
    "talbot": "Talbot"
}

BASE_DIR = Path("/workspaces/jour329w_fall2025/murphy/stardem_draft_v3")
DATA_DIR = BASE_DIR / "scraped_county_data"
OUTPUT_FILE = BASE_DIR / "comprehensive_local_govt_beatbook.md"

# Story data files
ISSUES_WITH_STORIES = BASE_DIR / "issues_with_stories.json"
TOP_ISSUES_BY_COUNTY = BASE_DIR / "top_issues_by_county.json"
TOP_RECURRING_ISSUES = BASE_DIR / "top_recurring_issues.json"


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
                timeout=120  # 2 minute timeout
            )
            if result.returncode != 0:
                error_msg = result.stderr.decode("utf-8")
                print(f"  Attempt {attempt + 1} failed: {error_msg}")
                if attempt < max_retries - 1:
                    time.sleep(5)  # Wait 5 seconds before retry
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
# Format data for LLM prompts
# ---------------------------------------------------------
def format_census_data(census_data: dict) -> str:
    """Convert census JSON data to readable text for LLM."""
    if not census_data:
        return "No census data available"
    
    text = "Demographics & Economics (U.S. Census 2022):\n\n"
    
    pop_data = census_data.get('census_api_data', {}).get('population', {})
    econ_data = census_data.get('census_api_data', {}).get('economics', {})
    enhanced = census_data.get('census_api_data', {}).get('enhanced', {})
    
    text += f"- Total Population: {pop_data.get('total', 0):,}\n"
    text += f"- Median Age: {pop_data.get('median_age', 'N/A')} years\n"
    text += f"- Median Household Income: {format_currency(econ_data.get('median_household_income'))}\n"
    text += f"- Median Home Value: {format_currency(econ_data.get('median_home_value'))}\n"
    
    if enhanced:
        poverty = enhanced.get('poverty', {})
        housing = enhanced.get('housing_affordability', {})
        broadband = enhanced.get('broadband_access', {})
        health = enhanced.get('health_insurance', {})
        
        text += f"\n- Poverty Rate: {format_percent(poverty.get('poverty_rate'))}\n"
        text += f"- Homeownership Rate: {format_percent(housing.get('homeownership_rate'))}\n"
        text += f"- Median Rent: {format_currency(housing.get('median_rent'))}\n"
        text += f"- Renters Cost-Burdened (30%+ income): {format_percent(housing.get('renters_cost_burdened_30plus_pct'))}\n"
        text += f"- Broadband Access: {format_percent(broadband.get('broadband_pct'))}\n"
        text += f"- Uninsured Rate: {format_percent(health.get('uninsured_rate'))}\n"
    
    return text


def format_officials_data(officials_data: dict) -> str:
    """Convert officials JSON data to readable text for LLM."""
    if not officials_data:
        return "No officials data available"
    
    text = "County Government:\n\n"
    text += f"- Government Type: {officials_data.get('government_type', 'N/A')}\n"
    text += f"- Website: {officials_data.get('website', 'N/A')}\n\n"
    
    if officials_data.get('commissioners'):
        text += "County Commissioners:\n"
        for comm in officials_data['commissioners']:
            text += f"- {comm.get('name', 'Unknown')} - {comm.get('title', 'Commissioner')}\n"
        text += "\n"
    
    return text


def format_schools_data(schools_data: dict) -> str:
    """Convert schools JSON data to readable text for LLM."""
    if not schools_data:
        return "No schools data available"
    
    school_info = schools_data.get('schools', {})
    text = f"School District: {school_info.get('district_name', 'N/A')}\n"
    text += f"Total Enrollment: ~{school_info.get('total_enrollment', 0):,} students\n"
    text += f"Number of Schools: {len(school_info.get('schools', []))}\n\n"
    
    return text


def format_story_issues_with_content(county_issues: list, max_issues: int = 10, max_stories_per_issue: int = 5) -> str:
    """Format story issues with full story content for LLM context."""
    if not county_issues:
        return "No story coverage data available"
    
    text = "Top Issues from Recent News Coverage:\n\n"
    
    for i, issue in enumerate(county_issues[:max_issues], 1):
        issue_name = issue.get('issue_name', 'Unknown')
        story_count = issue.get('story_count', 0)
        date_range = issue.get('date_range', 'N/A')
        significance = issue.get('significance', '')
        recent_dev = issue.get('recent_developments', '')
        tag = issue.get('tag', 'N/A')
        
        text += f"{'='*60}\n"
        text += f"ISSUE {i}: {issue_name}\n"
        text += f"Tag: {tag} | Stories: {story_count} | Period: {date_range}\n"
        text += f"{'='*60}\n\n"
        text += f"Significance: {significance}\n\n"
        text += f"Recent Developments: {recent_dev}\n\n"
        
        # Add full story details
        stories = issue.get('stories', [])
        if stories:
            text += f"STORIES ({min(len(stories), max_stories_per_issue)} of {len(stories)} shown):\n\n"
            for j, story in enumerate(stories[:max_stories_per_issue], 1):
                text += f"Story {j}: {story.get('title', 'Untitled')} ({story.get('date', 'N/A')})\n"
                text += f"Author: {story.get('author', 'Unknown')}\n"
                
                if story.get('summary'):
                    text += f"Summary: {story.get('summary')}\n"
                
                if story.get('key_people'):
                    text += f"Key People: {', '.join(story.get('key_people', [])[:8])}\n"
                
                if story.get('key_organizations'):
                    text += f"Key Organizations: {', '.join(story.get('key_organizations', [])[:6])}\n"
                
                if story.get('key_initiatives'):
                    text += f"Key Initiatives: {', '.join(story.get('key_initiatives', [])[:4])}\n"
                
                if story.get('municipalities'):
                    text += f"Municipalities: {', '.join(story.get('municipalities', [])[:4])}\n"
                
                text += "\n"
        
        text += "\n"
    
    return text


def get_county_issues_from_full_data(issues_data: list, county_name: str) -> list:
    """Extract issues relevant to a specific county from issues_with_stories.json."""
    county_issues = []
    
    for issue in issues_data:
        primary_counties = issue.get('primary_counties', [])
        # Check if this county is in the primary counties or if stories mention it
        if county_name + " County" in primary_counties:
            county_issues.append(issue)
        else:
            # Check if any stories are tagged with this county
            stories = issue.get('stories', [])
            county_stories = [s for s in stories if county_name + " County" in s.get('counties', [])]
            if county_stories:
                # Create a filtered version of this issue with only relevant stories
                county_specific_issue = issue.copy()
                county_specific_issue['stories'] = county_stories
                county_specific_issue['story_count'] = len(county_stories)
                county_issues.append(county_specific_issue)
    
    # Sort by story count descending
    county_issues.sort(key=lambda x: x.get('story_count', 0), reverse=True)
    
    return county_issues


# ---------------------------------------------------------
# Generate County Overview with LLM
# ---------------------------------------------------------
def build_county_overview_prompt(county_name, census_text, officials_text, schools_text, story_issues_text, budget_excerpt, minutes_excerpt):
    return f"""
You are writing a "County Overview & Context" section for {county_name} County, Maryland in a local government beat book for a new reporter.

County Demographic Data:
{census_text}

Government Structure:
{officials_text}

Education Context:
{schools_text}

Recent News Coverage by Issue:
{story_issues_text}

Budget Analysis Context:
{budget_excerpt[:800] if budget_excerpt else "Budget analysis not available"}

Recent Meeting Minutes Context:
{minutes_excerpt[:800] if minutes_excerpt else "Meeting minutes analysis not available"}

Write a comprehensive overview section that helps a new reporter understand {county_name} County's local government landscape.

Requirements:
- Start with 2-3 paragraphs of narrative that synthesizes the demographic data, governance structure, and major issues
- Highlight notable patterns (e.g., poverty levels, housing affordability, infrastructure challenges, governance conflicts)
- Connect the demographic context to the policy issues emerging in news coverage
- Reference story coverage using numbered footnotes [1], [2], etc. DO NOT use title references
- Write in a direct, newsroom style - no fluff
- After the narrative, include a "Quick Facts" subsection with key numbers in BULLETED FORM
- Data years: Census from 2022 ACS 5-year estimates. News coverage from 2023-2025.
- Focus on developments from 2025 when mentioning dates/events
"""


# ---------------------------------------------------------
# Generate Top Issues with LLM
# ---------------------------------------------------------
def build_top_issues_prompt(county_name, census_text, officials_text, story_issues_text, budget_excerpt):
    return f"""
You are writing the "Top Three Issues on the Local Government Beat" section for {county_name} County, Maryland.

County Context:
{census_text[:600]}

Government Structure:
{officials_text[:400]}

Story Coverage Data:
{story_issues_text}

Budget Context:
{budget_excerpt[:600] if budget_excerpt else "Budget data not available"}

Write a "Top Three Issues on the Local Government Beat" section.

Requirements:
- Produce **exactly three issues**, each as an **H3 heading (###)**
- Under each heading, write **2-4 paragraphs** of narrative prose
- **Do NOT use bullets or lists in the main narrative**
- Ground each issue in both the story coverage AND the demographic/government context
- Reference stories using numbered footnotes [1], [2], etc. DO NOT use title references
- Issues should be ongoing challenges or policy debates, not one-time events
- Focus on systemic problems: budget constraints, infrastructure needs, housing/development conflicts, governance accountability, service delivery
- Write like a beat reporter briefing a colleague
- Connect demographic realities (poverty, aging population, housing costs) to policy debates
- Focus primarily on developments from 2025 when mentioning specific dates
"""


# ---------------------------------------------------------
# Generate Key Sources with LLM
# ---------------------------------------------------------
def build_sources_prompt(county_name, officials_text, story_issues_text):
    return f"""
You are writing the "Key Sources to Know" section for {county_name} County, Maryland.

Government Officials:
{officials_text}

Story Coverage Context:
{story_issues_text[:1500]}

Write a "Key Sources to Know" section.

CRITICAL EXCLUSIONS - DO NOT INCLUDE:
- Journalists or media personnel
- Candidates for office (unless they hold current positions)
- Citizens quoted in stories (unless they hold official positions)
- Neighboring county officials
- One-time commenters or attendees

CATEGORIES TO INCLUDE:
- County Commissioners/Council Members
- County Department Heads (if available)
- Municipal Officials (mayors, town commissioners)
- State Legislators (ONLY if directly connected to county issues - explain their role)

Requirements:
- Use **H4 headings (####)** to label source categories
- Under each heading, use **bulleted lists**
- Each bullet should identify:
  - A specific person and their position
  - What decisions/areas they influence or oversee
  - Use consistent name formatting and spelling
- For state legislators: explain their specific connection to county governance
- Keep bullets concise and factual
- Focus on 2025 positions and roles
"""


# ---------------------------------------------------------
# Generate Coverage Themes with LLM
# ---------------------------------------------------------
def build_coverage_themes_prompt(county_name, story_issues_text):
    return f"""
You are analyzing local government coverage in {county_name} County, Maryland to identify recurring themes and patterns.

Story Coverage by Issue:
{story_issues_text}

Write a "Recent Coverage Themes" section that identifies 3-5 recurring patterns in local government reporting.

Requirements:
- Use **H4 headings (####)** for each theme
- Under each heading, write 1-2 paragraphs explaining:
  - What stories fell into this theme (use numbered footnotes [1], [2], etc.)
  - What angle or perspective dominated
  - Key findings or developments from the coverage
  - What questions remain unresolved
- Themes might include: budget battles, development conflicts, infrastructure projects, governance transparency, public safety, tax policy, service delivery
- Write in a newsroom analysis style
- Focus on coverage from 2025 when mentioning specific dates
- Connect themes to broader policy challenges
"""


# ---------------------------------------------------------
# MAIN SCRIPT
# ---------------------------------------------------------
def main():
    print("="*60)
    print("LOCAL GOVERNMENT BEAT BOOK GENERATOR (LLM-Enhanced)")
    print("="*60)
    print()
    
    # Load story data
    print("Loading story coverage data...")
    issues_with_stories = load_json(ISSUES_WITH_STORIES)
    top_issues_by_county = load_json(TOP_ISSUES_BY_COUNTY)
    recurring_issues = load_json(TOP_RECURRING_ISSUES)
    
    if not issues_with_stories:
        print("ERROR: Could not load issues_with_stories.json")
        return
    
    print(f"  Loaded {len(issues_with_stories)} issues with full story content")
    
    # Create output file
    with open(OUTPUT_FILE, "w") as out:
        out.write("# Comprehensive Local Government Beat Book\n")
        out.write("## Eastern Shore Maryland: Five Counties\n\n")
        out.write("*A complete reference guide for local government reporters covering Caroline, Dorchester, Kent, Queen Anne's, and Talbot Counties*\n\n")
        out.write(f"*Generated {datetime.now().strftime('%B %d, %Y')}*\n\n")
        out.write("**Data Sources:** U.S. Census Bureau ACS 2022 (5-year estimates), County government websites, News coverage 2023-2025\n\n")
        out.write("---\n\n")
        
        # Table of Contents
        out.write("## Table of Contents\n\n")
        for county_key, county_name in COUNTIES.items():
            anchor = county_name.lower().replace(' ', '-').replace("'", '')
            out.write(f"- [{county_name} County](#{anchor}-county)\n")
        out.write("\n---\n\n")
        
        # Process each county
        for county_key, county_name in COUNTIES.items():
            print(f"\n{'='*60}")
            print(f"Processing {county_name} County...")
            print(f"{'='*60}")
            
            # Load county data
            county_dir = DATA_DIR / county_key
            census = load_json(county_dir / f"{county_key}_census.json")
            officials = load_json(county_dir / f"{county_key}_county_officials.json")
            schools = load_json(county_dir / f"{county_key}_schools.json")
            
            # Load budget and minutes if available
            budget_file = county_dir / f"{county_key}_budget_analysis.md"
            minutes_file = county_dir / f"{county_key}_recent_minutes_analysis.md"
            
            budget_excerpt = ""
            if budget_file.exists():
                with open(budget_file, 'r') as f:
                    budget_excerpt = f.read()
            
            minutes_excerpt = ""
            if minutes_file.exists():
                with open(minutes_file, 'r') as f:
                    minutes_excerpt = f.read()
            
            # Get story issues for this county from full data
            county_issues = get_county_issues_from_full_data(issues_with_stories, county_name)
            story_count = sum(issue.get('story_count', 0) for issue in county_issues)
            
            print(f"  Found {len(county_issues)} issues with {story_count} stories")
            
            # Format data for LLM
            census_text = format_census_data(census)
            officials_text = format_officials_data(officials)
            schools_text = format_schools_data(schools)
            story_issues_text = format_story_issues_with_content(county_issues, max_issues=8, max_stories_per_issue=4)
            
            # Write county header
            out.write(f"# {county_name} County\n\n")
            out.write(f"**Stories analyzed:** {story_count} covering {len(county_issues)} major issue areas\n\n")
            out.write("---\n\n")
            
            # 1. COUNTY OVERVIEW & CONTEXT
            print(f"  Generating county overview...")
            overview_prompt = build_county_overview_prompt(
                county_name, census_text, officials_text, schools_text,
                story_issues_text, budget_excerpt, minutes_excerpt
            )
            overview_text = run_llm(overview_prompt)
            out.write("## County Overview & Context\n\n")
            out.write(overview_text.strip() + "\n\n")
            out.write("---\n\n")
            
            # 2. TOP THREE ISSUES
            print(f"  Generating top three issues...")
            issues_prompt = build_top_issues_prompt(
                county_name, census_text, officials_text, story_issues_text, budget_excerpt
            )
            issues_text = run_llm(issues_prompt)
            out.write("## Top Three Issues on the Local Government Beat\n\n")
            out.write(issues_text.strip() + "\n\n")
            out.write("---\n\n")
            
            # 3. KEY SOURCES
            print(f"  Generating key sources...")
            sources_prompt = build_sources_prompt(
                county_name, officials_text, story_issues_text
            )
            sources_text = run_llm(sources_prompt)
            out.write("## Key Sources to Know\n\n")
            out.write(sources_text.strip() + "\n\n")
            out.write("---\n\n")
            
            # 4. COVERAGE THEMES
            print(f"  Analyzing coverage themes...")
            themes_prompt = build_coverage_themes_prompt(
                county_name, story_issues_text
            )
            themes_text = run_llm(themes_prompt)
            out.write("## Recent Coverage Themes\n\n")
            out.write(themes_text.strip() + "\n\n")
            out.write("---\n\n")
    
    print(f"\n{'='*60}")
    print(f"✓ Beat book generated: {OUTPUT_FILE}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
