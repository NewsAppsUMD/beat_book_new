#!/usr/bin/env python3
"""
Eastern Shore Beat Book Generator
Transforms scraped JSON data into formatted markdown beat book
"""

import json
from pathlib import Path
from datetime import datetime

# County configuration
COUNTIES = {
    "caroline": "Caroline",
    "dorchester": "Dorchester",
    "kent": "Kent",
    "queen_annes": "Queen Anne's",
    "talbot": "Talbot"
}

BASE_DIR = Path("/workspaces/jour329w_fall2025/murphy/stardem_draft_v3")
DATA_DIR = BASE_DIR / "scraped_county_data"
OUTPUT_DIR = BASE_DIR / "beatbook_output"

# Story data files
TOP_ISSUES_BY_COUNTY = BASE_DIR / "top_issues_by_county.json"
TOP_RECURRING_ISSUES = BASE_DIR / "top_recurring_issues.json"

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

def generate_county_at_a_glance(county_key, county_name):
    """Generate 1-page county snapshot"""
    
    county_dir = DATA_DIR / county_key
    census = load_json(county_dir / f"{county_key}_census.json")
    officials = load_json(county_dir / f"{county_key}_county_officials.json")
    schools = load_json(county_dir / f"{county_key}_schools.json")
    
    content = f"""# {county_name} County At-A-Glance

**Generated:** {datetime.now().strftime("%B %d, %Y")}

---

## Quick Facts

"""
    
    # Demographics
    if census:
        pop_data = census.get('census_api_data', {}).get('population', {})
        econ_data = census.get('census_api_data', {}).get('economics', {})
        enhanced = census.get('census_api_data', {}).get('enhanced', {})
        
        content += f"""### Demographics
- **Population:** {pop_data.get('total', 'N/A'):,}
- **Median Age:** {pop_data.get('median_age', 'N/A')} years
- **Median Household Income:** {format_currency(econ_data.get('median_household_income'))}
- **Median Home Value:** {format_currency(econ_data.get('median_home_value'))}
"""
        
        if enhanced:
            poverty = enhanced.get('poverty', {})
            housing = enhanced.get('housing_affordability', {})
            broadband = enhanced.get('broadband_access', {})
            
            content += f"""- **Poverty Rate:** {format_percent(poverty.get('poverty_rate'))}
- **Homeownership Rate:** {format_percent(housing.get('homeownership_rate'))}
- **Broadband Access:** {format_percent(broadband.get('broadband_pct'))}

"""
    
    # Government
    if officials:
        content += f"""### County Government
- **Form:** {officials.get('government_type', 'Commissioners')}
- **Website:** {officials.get('website', 'N/A')}

**Officials:**
"""
        if officials.get('commissioners'):
            for comm in officials['commissioners']:
                name = comm.get('name', 'Unknown')
                title = comm.get('title', 'Commissioner')
                phone = comm.get('phone', '')
                phone_str = f" | {phone}" if phone else ""
                content += f"- {name} - {title}{phone_str}\n"
    
    content += "\n"
    
    # Schools
    if schools:
        school_data = schools.get('schools', {})
        district = school_data.get('district_name', 'N/A')
        total_enrollment = school_data.get('total_enrollment', 'N/A')
        school_list = school_data.get('schools', [])
        
        content += f"""### Education
- **School District:** {district}
- **Total Enrollment:** {total_enrollment:,} students (approx)
- **Number of Schools:** {len(school_list)}

"""
    
    content += """---

**For detailed information, see:**
- Demographics & Census Data
- Government & Officials
- Budget & Fiscal Analysis
- Education
- Recent Issues & Meeting Analysis

"""
    
    return content

def generate_demographics(county_key, county_name):
    """Generate detailed demographics page"""
    
    census = load_json(DATA_DIR / county_key / f"{county_key}_census.json")
    muni_census = load_json(DATA_DIR / county_key / f"{county_key}_municipalities_census.json")
    
    if not census:
        return f"# {county_name} County Demographics\n\nData not available.\n"
    
    content = f"""# {county_name} County Demographics & Census Data

**Data Source:** U.S. Census Bureau, American Community Survey 2022 (5-year estimates)  
**Generated:** {datetime.now().strftime("%B %d, %Y")}

---

## Population Overview

"""
    
    pop_data = census.get('census_api_data', {}).get('population', {})
    race_data = census.get('census_api_data', {}).get('race_ethnicity', {})
    
    total_pop = pop_data.get('total', 0)
    
    content += f"""- **Total Population:** {total_pop:,}
- **Male:** {pop_data.get('male', 0):,} ({pop_data.get('male', 0)/total_pop*100:.1f}%)
- **Female:** {pop_data.get('female', 0):,} ({pop_data.get('female', 0)/total_pop*100:.1f}%)
- **Median Age:** {pop_data.get('median_age', 'N/A')} years

### Race & Ethnicity
- **White (alone):** {race_data.get('white_alone', 0):,} ({race_data.get('white_alone', 0)/total_pop*100:.1f}%)
- **Black (alone):** {race_data.get('black_alone', 0):,} ({race_data.get('black_alone', 0)/total_pop*100:.1f}%)
- **Hispanic/Latino:** {race_data.get('hispanic_latino', 0):,} ({race_data.get('hispanic_latino', 0)/total_pop*100:.1f}%)

---

## Economic Indicators

"""
    
    econ_data = census.get('census_api_data', {}).get('economics', {})
    enhanced = census.get('census_api_data', {}).get('enhanced', {})
    
    content += f"""### Income
- **Median Household Income:** {format_currency(econ_data.get('median_household_income'))}
- **Labor Force:** {econ_data.get('labor_force', 0):,}
- **Unemployed:** {econ_data.get('unemployed', 0):,}
- **Unemployment Rate:** {econ_data.get('unemployed', 0)/econ_data.get('labor_force', 1)*100:.1f}%

"""
    
    if enhanced and 'poverty' in enhanced:
        poverty = enhanced['poverty']
        content += f"""### Poverty
- **Poverty Rate:** {format_percent(poverty.get('poverty_rate'))}
- **People in Poverty:** {poverty.get('people_in_poverty', 0):,}
- **Children in Poverty:** {poverty.get('children_in_poverty', 0):,}
- **Seniors in Poverty:** {poverty.get('seniors_in_poverty', 0):,}

"""
    
    # Housing
    housing_data = census.get('census_api_data', {}).get('housing', {})
    
    content += f"""---

## Housing

### Supply
- **Total Housing Units:** {housing_data.get('total_units', 0):,}
- **Occupied Units:** {housing_data.get('occupied_units', 0):,}
- **Vacant Units:** {housing_data.get('vacant_units', 0):,}
- **Vacancy Rate:** {housing_data.get('vacant_units', 0)/housing_data.get('total_units', 1)*100:.1f}%

"""
    
    if enhanced and 'housing_affordability' in enhanced:
        afford = enhanced['housing_affordability']
        content += f"""### Affordability
- **Median Home Value:** {format_currency(econ_data.get('median_home_value'))}
- **Median Rent:** {format_currency(afford.get('median_rent'))}
- **Homeownership Rate:** {format_percent(afford.get('homeownership_rate'))}
- **Owner-Occupied:** {afford.get('owner_occupied', 0):,}
- **Renter-Occupied:** {afford.get('renter_occupied', 0):,}

### Cost Burden
**Renters:**
- Paying 30%+ of income on housing: {format_percent(afford.get('renters_cost_burdened_30plus_pct'))}
- Paying 50%+ of income on housing: {format_percent(afford.get('renters_severely_cost_burdened_50plus_pct'))}

**Homeowners:**
- Paying 30%+ of income on housing: {format_percent(afford.get('owners_cost_burdened_30plus_pct'))}
- Paying 50%+ of income on housing: {format_percent(afford.get('owners_severely_cost_burdened_50plus_pct'))}

"""
    
    # Age breakdown
    if enhanced and 'age_breakdown' in enhanced:
        age = enhanced['age_breakdown']
        content += f"""---

## Age Distribution

- **Under 5 years:** {age.get('under_5_years', 0):,} ({format_percent(age.get('under_5_pct'))})
- **School age (5-17):** {age.get('school_age_5_17', 0):,} ({format_percent(age.get('school_age_pct'))})
- **Working age (18-64):** {age.get('working_age_18_64', 0):,} ({format_percent(age.get('working_age_pct'))})
- **Seniors (65+):** {age.get('seniors_65_plus', 0):,} ({format_percent(age.get('seniors_pct'))})

"""
    
    # Education
    if enhanced and 'education_attainment_full' in enhanced:
        edu = enhanced['education_attainment_full']
        content += f"""---

## Education Attainment (Age 25+)

- **Total Population 25+:** {edu.get('total_pop_25plus', 0):,}

### Educational Achievement
- **Less than High School:** {format_percent(edu.get('less_than_high_school_pct'))}
- **High School Graduate:** {format_percent(edu.get('high_school_graduate_pct'))}
- **Some College:** {format_percent(edu.get('some_college_pct'))}
- **Associate's Degree:** {format_percent(edu.get('associates_degree_pct'))}
- **Bachelor's Degree:** {format_percent(edu.get('bachelors_degree_pct'))}
- **Graduate Degree:** {format_percent(edu.get('graduate_degree_pct'))}

"""
    
    # Broadband
    if enhanced and 'broadband_access' in enhanced:
        bb = enhanced['broadband_access']
        content += f"""---

## Digital Access

- **Total Households:** {bb.get('total_households', 0):,}
- **With Broadband:** {bb.get('with_broadband', 0):,} ({format_percent(bb.get('broadband_pct'))})
- **No Internet Access:** {bb.get('no_internet', 0):,} ({format_percent(bb.get('no_internet_pct'))})

"""
    
    # Health insurance
    if enhanced and 'health_insurance' in enhanced:
        health = enhanced['health_insurance']
        content += f"""---

## Health Insurance Coverage

- **Uninsured Rate:** {format_percent(health.get('uninsured_rate'))}
- **Total Uninsured:** {health.get('uninsured_total', 0):,}
- **Children Uninsured:** {health.get('children_uninsured', 0):,}
- **Adults (18-64) Uninsured:** {health.get('adults_18_64_uninsured', 0):,}
- **Seniors (65+) Uninsured:** {health.get('seniors_65plus_uninsured', 0):,}

"""
    
    # Municipalities
    if muni_census:
        content += f"""---

## Municipalities

| Municipality | Population | Median Age | Median Income |
|--------------|------------|------------|---------------|
"""
        for muni in muni_census:
            name = muni.get('name', 'Unknown')
            pop = muni.get('population', 0)
            age = muni.get('median_age', 'N/A')
            income = muni.get('median_household_income')
            content += f"| {name} | {pop:,} | {age} | {format_currency(income)} |\n"
    
    content += f"""
---

**County Origin:** {census.get('origin', 'Not available')}

"""
    
    return content

def generate_government(county_key, county_name):
    """Generate government & officials page"""
    
    officials = load_json(DATA_DIR / county_key / f"{county_key}_county_officials.json")
    muni_officials = load_json(DATA_DIR / county_key / f"{county_key}_municipal_officials.json")
    
    content = f"""# {county_name} County Government & Officials

**Generated:** {datetime.now().strftime("%B %d, %Y")}

---

## County Government

"""
    
    if officials:
        content += f"""### Structure
- **Government Type:** {officials.get('government_type', 'N/A')}
- **Website:** {officials.get('website', 'N/A')}

### Meeting Schedule
{officials.get('meeting_schedule', 'Check county website for current schedule')}

"""
        
        # Commissioners/Council
        if officials.get('commissioners'):
            content += f"""### County Commissioners

| Name | Title | Term Ends | Phone | Email |
|------|-------|-----------|-------|-------|
"""
            for comm in officials['commissioners']:
                name = comm.get('name', 'Unknown')
                title = comm.get('title', 'Commissioner')
                term = comm.get('term_ends', 'N/A')
                phone = comm.get('phone', '')
                email = comm.get('email', '')
                content += f"| {name} | {title} | {term} | {phone} | {email} |\n"
            
            content += "\n"
        
        # Key staff
        if officials.get('key_staff'):
            content += f"""### Key County Staff

| Name | Title | Department | Phone | Email |
|------|-------|------------|-------|-------|
"""
            for staff in officials['key_staff']:
                name = staff.get('name', 'Unknown')
                title = staff.get('title', '')
                dept = staff.get('department', '')
                phone = staff.get('phone', '')
                email = staff.get('email', '')
                content += f"| {name} | {title} | {dept} | {phone} | {email} |\n"
            
            content += "\n"
        
        # Contact
        if officials.get('contact'):
            contact = officials['contact']
            content += f"""### County Contact Information
- **Address:** {contact.get('address', 'N/A')}
- **Phone:** {contact.get('phone', 'N/A')}
- **Email:** {contact.get('email', 'N/A')}
- **Website:** {contact.get('website', officials.get('website', 'N/A'))}

"""
    
    # Municipalities
    if muni_officials:
        content += f"""---

## Municipal Governments

"""
        for muni in muni_officials:
            muni_name = muni.get('municipality_name', 'Unknown')
            content += f"""### {muni_name}
- **Website:** {muni.get('website', 'N/A')}
"""
            
            # Chief executive
            if muni.get('chief_executive'):
                ce = muni['chief_executive']
                content += f"- **{ce.get('title', 'Mayor')}:** {ce.get('name', 'N/A')}"
                if ce.get('term_expires'):
                    content += f" (term ends {ce['term_expires']})"
                if ce.get('phone'):
                    content += f" | {ce['phone']}"
                if ce.get('email'):
                    content += f" | {ce['email']}"
                content += "\n"
            
            # Council members
            if muni.get('council_members'):
                content += f"\n**Council Members:**\n"
                for member in muni['council_members']:
                    content += f"- {member.get('name', 'Unknown')} - {member.get('title', 'Council Member')}"
                    if member.get('term_expires'):
                        content += f" (term ends {member['term_expires']})"
                    if member.get('phone'):
                        content += f" | {member['phone']}"
                    if member.get('email'):
                        content += f" | {member['email']}"
                    content += "\n"
            
            # Meeting schedule
            if muni.get('meeting_schedule'):
                content += f"\n**Meetings:** {muni['meeting_schedule']}\n"
            
            content += "\n"
    
    return content

def generate_budget_fiscal(county_key, county_name):
    """Copy and format existing budget analysis"""
    
    budget_file = DATA_DIR / county_key / f"{county_key}_budget_analysis.md"
    
    if budget_file.exists():
        with open(budget_file, 'r') as f:
            return f.read()
    else:
        return f"""# {county_name} County Budget & Fiscal Analysis

Budget analysis not yet available.

**To add:**
- Total budget
- Revenue sources
- Major expenditures
- Tax rates
- Fund balance
- Capital projects
- Multi-year trends

"""

def generate_education(county_key, county_name):
    """Generate education page"""
    
    schools = load_json(DATA_DIR / county_key / f"{county_key}_schools.json")
    
    content = f"""# {county_name} County Education

**Generated:** {datetime.now().strftime("%B %d, %Y")}

---

## School District

"""
    
    if schools:
        school_data = schools.get('schools', {})
        district = school_data.get('district_name', 'N/A')
        website = school_data.get('website', 'N/A')
        superintendent = school_data.get('superintendent', 'Contact via district website')
        total_enrollment = school_data.get('total_enrollment', 'N/A')
        school_list = school_data.get('schools', [])
        
        content += f"""- **District Name:** {district}
- **Website:** {website}
- **Superintendent:** {superintendent}
- **Total Enrollment:** {total_enrollment:,} students (approximate)

---

## Schools ({len(school_list)} total)

| School Name | Level | Star Rating | Percentile |
|-------------|-------|-------------|------------|
"""
        
        for school in sorted(school_list, key=lambda x: (x.get('level', ''), x.get('name', ''))):
            name = school.get('name', 'Unknown')
            level = school.get('level', 'N/A')
            stars = school.get('star_rating', 'N/A')
            pct = school.get('percentile', 'N/A')
            content += f"| {name} | {level} | {stars} | {pct} |\n"
        
        content += f"""
**Note:** Star ratings and percentiles from Maryland State Department of Education Report Card.

"""
    else:
        content += "School data not available.\n"
    
    content += f"""
---

## School Board

**TO ADD:**
- School board member names
- Board president
- Meeting schedule
- Contact information

## Student Demographics

**TO ADD:**
- Free/reduced lunch percentages
- English language learners
- Special education
- Homeless students (McKinney-Vento)
- Attendance rates
- Chronic absenteeism

## District Budget

**TO ADD:**
- Total education budget
- Per-pupil spending
- Blueprint for Maryland's Future implementation
- Major capital projects
- Staffing levels

"""
    
    return content

def generate_recent_issues(county_key, county_name):
    """Generate recent issues page with story data"""
    
    # Load story data
    top_issues = load_json(TOP_ISSUES_BY_COUNTY)
    
    content = f"""# {county_name} County Recent Issues & Story Coverage

**Generated:** {datetime.now().strftime("%B %d, %Y")}

---

## Top Issues by Story Count

"""
    
    if top_issues and county_name + " County" in top_issues:
        county_issues = top_issues[county_name + " County"]
        
        for issue in county_issues[:10]:  # Top 10 issues
            issue_name = issue.get('issue_name', 'Unknown')
            story_count = issue.get('story_count', 0)
            date_range = issue.get('date_range', 'N/A')
            significance = issue.get('significance', '')
            recent_dev = issue.get('recent_developments', '')
            
            content += f"""### {issue_name}
**{story_count} stories** | {date_range}

**Why it matters:** {significance}

**Recent developments:** {recent_dev}

"""
            
            # Add 3-5 recent story examples
            story_refs = issue.get('story_references', [])
            if story_refs:
                content += "**Recent stories:**\n"
                for story in story_refs[:5]:
                    title = story.get('title', 'Untitled')
                    date = story.get('date', 'N/A')
                    content += f"- {title} ({date})\n"
                content += "\n"
            
            content += "---\n\n"
    
    else:
        content += f"Story data not available for {county_name} County.\n\n"
    
    # Add meeting minutes analysis if available
    minutes_file = DATA_DIR / county_key / f"{county_key}_recent_minutes_analysis.md"
    
    if minutes_file.exists():
        content += f"""---

## County Commissioner Meeting Analysis

"""
        with open(minutes_file, 'r') as f:
            minutes_content = f.read()
            # Skip the title if it exists
            if minutes_content.startswith('#'):
                minutes_content = '\n'.join(minutes_content.split('\n')[1:])
            content += minutes_content
    
    return content

def generate_comparative_overview():
    """Generate region-wide comparative data"""
    
    content = f"""# Eastern Shore Counties: Comparative Overview

**Counties:** Caroline, Dorchester, Kent, Queen Anne's, Talbot  
**Generated:** {datetime.now().strftime("%B %d, %Y")}

---

## Regional Recurring Issues

"""
    
    # Add recurring issues across all counties
    recurring_issues = load_json(TOP_RECURRING_ISSUES)
    
    if recurring_issues:
        content += "**Top issues across the region (by story count):**\n\n"
        
        for i, issue in enumerate(recurring_issues[:15], 1):
            issue_name = issue.get('issue_name', 'Unknown')
            story_count = issue.get('story_count', 0)
            counties = issue.get('primary_counties', [])
            tag = issue.get('tag', '')
            
            counties_str = ', '.join(counties) if counties else 'Multiple counties'
            content += f"{i}. **{issue_name}** ({story_count} stories) - {counties_str}\n"
        
        content += "\n---\n\n"
    
    content += """## Demographics Comparison

| County | Population | Median Age | Poverty Rate | Median Income | Median Home Value |
|--------|------------|------------|--------------|---------------|-------------------|
"""
    
    for county_key, county_name in COUNTIES.items():
        census = load_json(DATA_DIR / county_key / f"{county_key}_census.json")
        if census:
            pop_data = census.get('census_api_data', {}).get('population', {})
            econ_data = census.get('census_api_data', {}).get('economics', {})
            enhanced = census.get('census_api_data', {}).get('enhanced', {})
            
            pop = pop_data.get('total', 0)
            age = pop_data.get('median_age', 'N/A')
            poverty = enhanced.get('poverty', {}).get('poverty_rate', 'N/A') if enhanced else 'N/A'
            poverty_str = format_percent(poverty) if poverty != 'N/A' else 'N/A'
            income = format_currency(econ_data.get('median_household_income'))
            home_value = format_currency(econ_data.get('median_home_value'))
            
            content += f"| {county_name} | {pop:,} | {age} | {poverty_str} | {income} | {home_value} |\n"
    
    content += f"""
---

## Housing Affordability

| County | Homeownership Rate | Median Rent | Renters Cost-Burdened (30%+) |
|--------|-------------------|-------------|------------------------------|
"""
    
    for county_key, county_name in COUNTIES.items():
        census = load_json(DATA_DIR / county_key / f"{county_key}_census.json")
        if census:
            enhanced = census.get('census_api_data', {}).get('enhanced', {})
            if enhanced and 'housing_affordability' in enhanced:
                housing = enhanced['housing_affordability']
                ownership = format_percent(housing.get('homeownership_rate'))
                rent = format_currency(housing.get('median_rent'))
                burdened = format_percent(housing.get('renters_cost_burdened_30plus_pct'))
                content += f"| {county_name} | {ownership} | {rent} | {burdened} |\n"
    
    content += f"""
---

## Digital Access & Education

| County | Broadband Access | Uninsured Rate | Less than HS |
|--------|-----------------|----------------|--------------|
"""
    
    for county_key, county_name in COUNTIES.items():
        census = load_json(DATA_DIR / county_key / f"{county_key}_census.json")
        if census:
            enhanced = census.get('census_api_data', {}).get('enhanced', {})
            if enhanced:
                broadband = format_percent(enhanced.get('broadband_access', {}).get('broadband_pct'))
                uninsured = format_percent(enhanced.get('health_insurance', {}).get('uninsured_rate'))
                less_hs = format_percent(enhanced.get('education_attainment_full', {}).get('less_than_high_school_pct'))
                content += f"| {county_name} | {broadband} | {uninsured} | {less_hs} |\n"
    
    content += f"""
---

## Age Distribution

| County | Under 5 | School Age (5-17) | Working Age (18-64) | Seniors (65+) |
|--------|---------|-------------------|---------------------|---------------|
"""
    
    for county_key, county_name in COUNTIES.items():
        census = load_json(DATA_DIR / county_key / f"{county_key}_census.json")
        if census:
            enhanced = census.get('census_api_data', {}).get('enhanced', {})
            if enhanced and 'age_breakdown' in enhanced:
                age = enhanced['age_breakdown']
                under5 = format_percent(age.get('under_5_pct'))
                school = format_percent(age.get('school_age_pct'))
                working = format_percent(age.get('working_age_pct'))
                seniors = format_percent(age.get('seniors_pct'))
                content += f"| {county_name} | {under5} | {school} | {working} | {seniors} |\n"
    
    content += f"""
---

## Schools

| County | District | Total Enrollment | Number of Schools |
|--------|----------|------------------|-------------------|
"""
    
    for county_key, county_name in COUNTIES.items():
        schools = load_json(DATA_DIR / county_key / f"{county_key}_schools.json")
        if schools:
            school_data = schools.get('schools', {})
            district = school_data.get('district_name', 'N/A')
            enrollment = school_data.get('total_enrollment', 'N/A')
            num_schools = len(school_data.get('schools', []))
            
            enroll_str = f"{enrollment:,}" if isinstance(enrollment, int) else enrollment
            content += f"| {county_name} | {district} | {enroll_str} | {num_schools} |\n"
    
    content += """
---

## Key Takeaways

**Wealthiest:** Queen Anne's County (highest median income, home values)  
**Highest Poverty:** Dorchester County  
**Best Broadband:** Talbot County  
**Youngest Population:** Caroline County (lowest median age)  
**Oldest Population:** Talbot County (highest median age)

**Regional Challenges:**
- Housing affordability (high cost burden rates)
- Educational attainment gaps
- Blueprint implementation funding
- Infrastructure aging
- Broadband access in rural areas

"""
    
    return content

def generate_story_ideas():
    """Generate story ideas from recurring issues and gaps"""
    
    recurring_issues = load_json(TOP_RECURRING_ISSUES)
    top_issues = load_json(TOP_ISSUES_BY_COUNTY)
    
    content = f"""# Story Ideas & Coverage Opportunities

**Generated:** {datetime.now().strftime("%B %d, %Y")}

---

## Regional Story Angles

Based on recurring issues across all 5 counties:

"""
    
    if recurring_issues:
        # Group by tag
        by_tag = {}
        for issue in recurring_issues[:20]:
            tag = issue.get('tag', 'Other')
            if tag not in by_tag:
                by_tag[tag] = []
            by_tag[tag].append(issue)
        
        for tag, issues in sorted(by_tag.items()):
            content += f"""### {tag}

"""
            for issue in issues:
                issue_name = issue.get('issue_name', 'Unknown')
                story_count = issue.get('story_count', 0)
                counties = issue.get('primary_counties', [])
                significance = issue.get('significance', '')
                
                content += f"""**{issue_name}** ({story_count} stories across {len(counties)} counties)
- Why it matters: {significance}
- Counties affected: {', '.join(counties)}
- **Story angle:** Compare how each county is handling this issue

"""
    
    content += """---

## County-Specific Story Ideas

"""
    
    if top_issues:
        for county_name in ["Caroline County", "Dorchester County", "Kent County", "Queen Anne's County", "Talbot County"]:
            if county_name in top_issues:
                content += f"""### {county_name}

"""
                county_issues = top_issues[county_name]
                for issue in county_issues[:3]:
                    issue_name = issue.get('issue_name', 'Unknown')
                    recent_dev = issue.get('recent_developments', '')
                    content += f"- **{issue_name}:** {recent_dev}\n"
                content += "\n"
    
    content += """---

## Follow-Up Opportunities

**Based on story patterns, consider:**

1. **Budget deep-dives** - Compare how all 5 counties are handling FY2026 budget challenges
2. **Infrastructure comparisons** - Sewer/water capacity issues across multiple counties
3. **Development conflicts** - Housing affordability vs. growth management
4. **Solar energy** - Regional approach to renewable energy projects
5. **Blueprint implementation** - How education funding mandates affect each county differently
6. **Governance accountability** - Campaign finance, transparency, public participation trends
7. **Climate adaptation** - Flood mitigation, sea level rise responses by county
8. **Economic development** - Tourism strategies, business attraction efforts
9. **Public safety** - Police department restructuring, accountability measures
10. **Municipal services** - Town-county relationships, service delivery models

---

## Data Gaps to Fill

**For stronger beat coverage, collect:**

1. School district leadership contacts and board member details
2. Student demographics (FARMS, ELL, special ed, attendance) for all schools
3. Historical budget trends (5-year comparison)
4. Department head contacts for all counties
5. State delegation information
6. Major employers and economic indicators
7. Community organization contacts
8. Development pipeline (projects in planning)
9. Infrastructure capital improvement plans
10. Meeting schedules and public hearing calendars

"""
    
    return content

def generate_contact_quick_reference():
    """Generate 1-page contact sheet for all counties"""
    
    content = f"""# Eastern Shore Counties: Quick Contact Reference

**Generated:** {datetime.now().strftime("%B %d, %Y")}

---

"""
    
    for county_key, county_name in COUNTIES.items():
        officials = load_json(DATA_DIR / county_key / f"{county_key}_county_officials.json")
        schools = load_json(DATA_DIR / county_key / f"{county_key}_schools.json")
        
        content += f"""## {county_name} County

"""
        
        if officials:
            content += f"**County Government:** {officials.get('website', 'N/A')}  \n"
            if officials.get('contact', {}).get('phone'):
                content += f"**Phone:** {officials['contact']['phone']}  \n"
            
            if officials.get('commissioners'):
                # Get president/chair
                for comm in officials['commissioners']:
                    if 'president' in comm.get('title', '').lower() or 'chair' in comm.get('title', '').lower():
                        content += f"**{comm.get('title')}:** {comm.get('name', 'Unknown')}"
                        if comm.get('phone'):
                            content += f" | {comm['phone']}"
                        if comm.get('email'):
                            content += f" | {comm['email']}"
                        content += "  \n"
                        break
        
        if schools:
            school_data = schools.get('schools', {})
            content += f"**Schools:** {school_data.get('website', 'N/A')}  \n"
            content += f"**Superintendent:** {school_data.get('superintendent', 'N/A')}  \n"
        
        content += "\n"
    
    content += """---

**TIP:** For comprehensive contact information, see individual county Government & Officials pages.

"""
    
    return content

def main():
    """Generate complete beat book"""
    
    print("="*60)
    print("Eastern Shore Beat Book Generator")
    print("="*60)
    print()
    
    # Create output directory structure
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "00_OVERVIEW").mkdir(exist_ok=True)
    
    # Generate overview section
    print("Generating overview...")
    
    overview_dir = OUTPUT_DIR / "00_OVERVIEW"
    
    with open(overview_dir / "comparative_data.md", 'w') as f:
        f.write(generate_comparative_overview())
    print("  ✓ comparative_data.md")
    
    with open(overview_dir / "contact_quick_reference.md", 'w') as f:
        f.write(generate_contact_quick_reference())
    print("  ✓ contact_quick_reference.md")
    
    with open(overview_dir / "story_ideas.md", 'w') as f:
        f.write(generate_story_ideas())
    print("  ✓ story_ideas.md")
    
    # Generate county-specific pages
    for county_key, county_name in COUNTIES.items():
        print(f"\nGenerating {county_name} County...")
        
        county_dir = OUTPUT_DIR / county_key.upper()
        county_dir.mkdir(exist_ok=True)
        
        pages = {
            "01_at_a_glance.md": generate_county_at_a_glance(county_key, county_name),
            "02_demographics.md": generate_demographics(county_key, county_name),
            "03_government.md": generate_government(county_key, county_name),
            "04_budget_fiscal.md": generate_budget_fiscal(county_key, county_name),
            "05_education.md": generate_education(county_key, county_name),
            "07_recent_issues.md": generate_recent_issues(county_key, county_name),
        }
        
        for filename, content in pages.items():
            with open(county_dir / filename, 'w') as f:
                f.write(content)
            print(f"  ✓ {filename}")
    
    # Generate index
    print("\nGenerating index...")
    index_content = f"""# Eastern Shore Beat Book

**Coverage Area:** Caroline, Dorchester, Kent, Queen Anne's, and Talbot Counties, Maryland  
**Generated:** {datetime.now().strftime("%B %d, %Y")}

---

## Contents

### Overview
- [Comparative Data](00_OVERVIEW/comparative_data.md) - All 5 counties side-by-side with regional issues
- [Quick Contact Reference](00_OVERVIEW/contact_quick_reference.md) - Key officials, 1 page
- [Story Ideas](00_OVERVIEW/story_ideas.md) - Coverage opportunities and follow-up angles

### County Pages

Each county has:
1. **At-A-Glance** - 1-page snapshot
2. **Demographics** - Census data, detailed
3. **Government** - Officials, structure, contacts
4. **Budget & Fiscal** - Financial analysis
5. **Education** - Schools, district data
6. **Recent Issues** - Meeting analysis

#### Counties
"""
    
    for county_key, county_name in COUNTIES.items():
        index_content += f"- [{county_name} County]({county_key.upper()}/01_at_a_glance.md)\n"
    
    index_content += f"""
---

## Data Sources

- U.S. Census Bureau, American Community Survey 2022 (5-year estimates)
- Maryland State Department of Education
- County government websites
- Municipal government websites
- County commissioner/council meeting minutes
- Maryland State Board of Elections

## Using This Beat Book

This beat book is designed for quick reference and story research:

1. **Quick Facts** - Use At-A-Glance pages for fast background
2. **Story Angles** - Check Recent Issues for newsworthy topics
3. **Context** - Use Demographics and Budget pages for context
4. **Contacts** - Government pages have full official listings
5. **Comparison** - Use Overview section to spot regional trends

## Updates

This beat book should be updated:
- **Quarterly** - New meeting minutes, budget developments
- **Annually** - New census estimates, school data
- **As Needed** - Elections, leadership changes, major events

---

**Last Updated:** {datetime.now().strftime("%B %d, %Y")}

"""
    
    with open(OUTPUT_DIR / "README.md", 'w') as f:
        f.write(index_content)
    print("  ✓ README.md (index)")
    
    print()
    print("="*60)
    print("BEAT BOOK COMPLETE!")
    print("="*60)
    print(f"Location: {OUTPUT_DIR}")
    print()
    print("Structure:")
    print("  00_OVERVIEW/")
    print("    - comparative_data.md")
    print("    - contact_quick_reference.md")
    print()
    for county_key, county_name in COUNTIES.items():
        print(f"  {county_key.upper()}/ ({county_name})")
        print("    - 01_at_a_glance.md")
        print("    - 02_demographics.md")
        print("    - 03_government.md")
        print("    - 04_budget_fiscal.md")
        print("    - 05_education.md")
        print("    - 07_recent_issues.md")
        print()
    
    print("Open README.md to navigate the beat book.")
    print("="*60)

if __name__ == "__main__":
    main()
