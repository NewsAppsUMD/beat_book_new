import json
import subprocess
import argparse
import sys
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

def call_llm(prompt, model):
    """Call LLM with a prompt and return the response."""
    try:
        result = subprocess.run([
            'llm', '-m', model, prompt
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"[LLM Error: {result.stderr[:100]}]"
    except subprocess.TimeoutExpired:
        return "[LLM Error: Request timed out]"
    except Exception as e:
        return f"[LLM Error: {str(e)}]"

def extract_key_people(stories):
    """Extract notable people mentioned across stories."""
    people_freq = Counter()
    for story in stories:
        people = story.get('people') or []
        if isinstance(people, list):
            people_freq.update(people)
    return [name for name, count in people_freq.most_common(20) if count > 1]

def extract_key_organizations(stories):
    """Extract notable organizations mentioned across stories."""
    org_freq = Counter()
    for story in stories:
        orgs = story.get('organizations') or []
        if isinstance(orgs, list):
            org_freq.update(orgs)
    return [org for org, count in org_freq.most_common(15)]

def extract_geographic_coverage(stories):
    """Extract geographic areas covered."""
    locations = Counter()
    for story in stories:
        place_list = story.get('places') or []
        if isinstance(place_list, list):
            locations.update(place_list)
    return [loc for loc, count in locations.most_common(10)]

def summary_blurb(text, max_chars=280):
    """Return first sentence-ish summary from pre-extracted summary text."""
    if not text:
        return "No summary available."
    compact = " ".join(str(text).split())
    if not compact:
        return "No summary available."
    if '.' in compact:
        candidate = compact.split('.', 1)[0].strip() + '.'
    else:
        candidate = compact
    if len(candidate) > max_chars:
        return candidate[:max_chars].rstrip() + '...'
    return candidate

def get_story_examples(stories, theme=None, season=None, limit=3):
    """Get specific story examples for a theme/season."""
    filtered = stories
    if theme:
        filtered = [s for s in filtered if s.get('primary_theme') == theme]
    if season:
        filtered = [s for s in filtered if s.get('season') == season]

    filtered.sort(key=lambda x: (
        x.get('severity_level') == 'major',
        x.get('date', '')
    ), reverse=True)

    return [{
        'title': s.get('title', 'Untitled'),
        'date': s.get('date', 'Unknown date'),
        'summary': s.get('content', '')[:300] + '...' if len(s.get('content', '')) > 300 else s.get('content', ''),
        'theme': s.get('primary_theme'),
        'incident_type': s.get('incident_type')
    } for s in filtered[:limit]]

def build_year_story_briefing(year, year_bucket):
    """Build a story-driven yearly briefing using summaries and metadata."""
    stories = year_bucket.get('stories', [])
    if not stories:
        return f"**{year}**\n- No story details available for this year.\n\n"

    theme_groups = defaultdict(list)
    for story in stories:
        theme = story.get('primary_theme') or 'other'
        theme_groups[theme].append(story)

    top_themes = sorted(theme_groups.items(), key=lambda item: len(item[1]), reverse=True)[:3]

    major_stories = [s for s in stories if (s.get('severity_level') or '').lower() == 'major']
    non_major_stories = [
        s for s in stories
        if (s.get('severity_level') or '').lower() in ['minor', 'moderate']
    ]

    major_stories = sorted(major_stories, key=lambda s: s.get('date', ''), reverse=True)[:2]
    non_major_stories = sorted(non_major_stories, key=lambda s: s.get('date', ''), reverse=True)[:2]

    lines = [f"**{year}**"]
    lines.append("- What coverage focused on:")

    for theme, theme_stories in top_themes:
        theme_title = theme.replace('_', ' ').title() if theme else 'Other'
        sample_story = sorted(theme_stories, key=lambda s: s.get('date', ''), reverse=True)[0]
        lines.append(
            f"  - **{theme_title}:** {summary_blurb(sample_story.get('content', ''))}"
        )

    if major_stories:
        lines.append("- Major-incident details:")
        for story in major_stories:
            lines.append(
                f"  - **{story.get('title', 'Untitled')}** ({story.get('date', 'Unknown date')}): "
                f"{summary_blurb(story.get('content', ''))}"
            )

    if non_major_stories:
        lines.append("- Minor/moderate details:")
        for story in non_major_stories:
            lines.append(
                f"  - **{story.get('title', 'Untitled')}** ({story.get('date', 'Unknown date')}): "
                f"{summary_blurb(story.get('content', ''))}"
            )

    lines.append("")
    return "\n".join(lines)

def get_story_blurb(story):
    """Get a short summary/title for a story."""
    content = story.get('content', '')
    # Take first sentence or up to 200 chars
    first_sentence = content.split('.')[0] if content else story.get('title', 'Untitled')
    return first_sentence[:200] + ('...' if len(first_sentence) > 200 else '')

def analyze_temporal_periods(stories):
    """Analyze patterns over time periods (by year)."""
    temporal_data = defaultdict(lambda: {
        'count': 0,
        'themes': Counter(),
        'severity': Counter(),
        'locations': Counter(),
        'incidents': Counter(),
        'outcomes': Counter(),
        'stories': []
    })
    
    for story in stories:
        year = story.get('year')
        if not year:
            continue
        
        temporal_data[year]['count'] += 1
        temporal_data[year]['themes'][story.get('primary_theme', 'unknown')] += 1
        temporal_data[year]['severity'][story.get('severity_level', 'unknown')] += 1
        temporal_data[year]['locations'][story.get('location_type', 'unknown')] += 1
        temporal_data[year]['incidents'][story.get('incident_type', 'unknown')] += 1
        temporal_data[year]['outcomes'][story.get('outcome', 'unknown')] += 1
        temporal_data[year]['stories'].append(story)
    
    return dict(temporal_data)

def analyze_seasonal_patterns(stories):
    """Analyze patterns by season (if seasonal trends exist)."""
    seasonal_data = defaultdict(lambda: {
        'count': 0,
        'themes': Counter(),
        'severity': Counter(),
        'locations': Counter(),
        'incidents': Counter(),
        'stories': []
    })
    
    for story in stories:
        season = story.get('season')
        if not season:
            continue
        
        seasonal_data[season]['count'] += 1
        seasonal_data[season]['themes'][story.get('primary_theme', 'unknown')] += 1
        seasonal_data[season]['severity'][story.get('severity_level', 'unknown')] += 1
        seasonal_data[season]['locations'][story.get('location_type', 'unknown')] += 1
        seasonal_data[season]['incidents'][story.get('incident_type', 'unknown')] += 1
        seasonal_data[season]['stories'].append(story)
    
    return dict(seasonal_data)

def analyze_weekend_patterns(stories):
    """Analyze weekend vs weekday patterns."""
    weekend_data = {'weekend': {'count': 0, 'themes': Counter(), 'stories': []},
                    'weekday': {'count': 0, 'themes': Counter(), 'stories': []}}
    
    for story in stories:
        is_weekend = story.get('is_weekend')
        if is_weekend is None:
            continue
        
        key = 'weekend' if is_weekend else 'weekday'
        weekend_data[key]['count'] += 1
        weekend_data[key]['themes'][story.get('primary_theme', 'unknown')] += 1
        weekend_data[key]['stories'].append(story)
    
    return weekend_data

def analyze_theme_trends(stories):
    """Analyze trends by primary theme over time."""
    theme_data = defaultdict(lambda: {
        'count': 0,
        'by_year': Counter(),
        'by_season': Counter(),
        'severity': Counter(),
        'outcomes': Counter(),
        'stories': []
    })
    
    for story in stories:
        theme = story.get('primary_theme')
        if not theme:
            continue
        
        theme_data[theme]['count'] += 1
        theme_data[theme]['by_year'][story.get('year')] += 1
        theme_data[theme]['by_season'][story.get('season', 'unknown')] += 1
        theme_data[theme]['severity'][story.get('severity_level', 'unknown')] += 1
        theme_data[theme]['outcomes'][story.get('outcome', 'unknown')] += 1
        theme_data[theme]['stories'].append(story)
    
    return dict(theme_data)

def detect_emerging_declining_themes(temporal_data):
    """Identify themes that are increasing or decreasing over time."""
    if len(temporal_data) < 2:
        return {'emerging': [], 'declining': [], 'stable': []}
    
    years = sorted(temporal_data.keys())
    early_years = years[:len(years)//2]
    recent_years = years[len(years)//2:]
    
    # Aggregate theme counts for early vs recent periods
    early_themes = Counter()
    recent_themes = Counter()
    
    for year in early_years:
        early_themes.update(temporal_data[year]['themes'])
    for year in recent_years:
        recent_themes.update(temporal_data[year]['themes'])
    
    # Normalize by number of years
    early_avg = {theme: count / len(early_years) for theme, count in early_themes.items()}
    recent_avg = {theme: count / len(recent_years) for theme, count in recent_themes.items()}
    
    emerging = []
    declining = []
    stable = []
    
    all_themes = set(early_avg.keys()) | set(recent_avg.keys())
    for theme in all_themes:
        if theme == 'unknown':
            continue
        early = early_avg.get(theme, 0)
        recent = recent_avg.get(theme, 0)
        
        if recent > early * 1.5:  # 50% increase
            emerging.append((theme, early, recent))
        elif early > recent * 1.5:  # 50% decrease
            declining.append((theme, early, recent))
        else:
            stable.append((theme, early, recent))
    
    return {
        'emerging': sorted(emerging, key=lambda x: x[2], reverse=True),
        'declining': sorted(declining, key=lambda x: x[1], reverse=True),
        'stable': sorted(stable, key=lambda x: x[2], reverse=True)
    }

def get_top_stories_for_theme_season(stories, theme, season, limit=3):
    """Get top stories for a specific theme and season."""
    filtered = [s for s in stories 
                if s.get('primary_theme') == theme and s.get('season') == season]
    # Prioritize major severity
    filtered.sort(key=lambda x: (x.get('severity_level') == 'major', x.get('date')), reverse=True)
    return filtered[:limit]

def generate_introduction(stories, model):
    """Generate a brief, casual introduction to the beat."""
    
    total = len(stories)
    themes = Counter(s.get('primary_theme') for s in stories if s.get('primary_theme'))
    top_themes = themes.most_common(5)
    
    years = sorted(set(s.get('year') for s in stories if s.get('year')))
    date_range = f"{years[0]} to {years[-1]}" if years else "recent years"
    
    prompt = f"""
Write a SHORT, friendly introduction (2-3 paragraphs max) for a public safety beatbook.

You're briefing a new reporter joining the public safety beat. Keep it conversational and welcoming—like you're talking to a colleague over coffee, not writing an academic paper.

Context:
- Time period: {date_range}
- Total stories analyzed: {total}
- Top issues covered: {', '.join(f'{theme} ({count})' for theme, count in top_themes)}

The introduction should:
- Welcome them to the beat in a friendly way
- Give a quick overview of what public safety coverage includes
- Mention that this analysis looks at how coverage has evolved over time—trends, patterns, changes
- Note that understanding these trends helps them know what to watch for and what's changing
- Set the tone: practical, approachable, focused on helping them succeed

Keep it short and get to the point. No fluff.
"""
    
    return call_llm(prompt, model)

def generate_coverage_narrative(stories, top_themes, geographic, model):
    """Generate a narrative overview of what this beat actually covers before trend analysis."""
    top_incidents = Counter(s.get('incident_type') for s in stories if s.get('incident_type')).most_common(6)
    top_locations = geographic[:6]

    sample_stories = sorted(
        stories,
        key=lambda s: (
            s.get('severity_level') == 'major',
            s.get('date', '')
        ),
        reverse=True
    )[:4]

    sample_lines = []
    for story in sample_stories:
        summary = summary_blurb(story.get('content', ''), max_chars=220)
        sample_lines.append(f"- {story.get('title', 'Untitled')} ({story.get('date', 'Unknown date')}): {summary}")

    prompt = f"""
Write a narrative section titled "What You're Covering" for a public safety beatbook.

Audience: a reporter new to this beat.
Tone: business casual, practical, colleague-to-colleague.

Context from the dataset:
- Top themes: {', '.join(f'{t.replace('_', ' ').title()} ({d['count']})' for t, d in top_themes[:5])}
- Common incident types: {', '.join(f'{i} ({c})' for i, c in top_incidents)}
- Common coverage locations: {', '.join(top_locations)}

Representative story snapshots:
{chr(10).join(sample_lines)}

Write 3-5 short paragraphs that:
1) Explain the types of stories this beat actually includes (not abstractly).
2) Mention recurring incident categories and the agencies/issues that keep showing up.
3) Briefly ground it in a few examples from the snapshot list.
4) Help the reporter understand where to focus attention day-to-day.

Do not use an academic tone. Keep it clear, direct, and practical.
"""

    narrative = call_llm(prompt, model)

    if narrative.startswith("[LLM Error:"):
        fallback = []
        fallback.append(
            "This beat is a mix of breaking incidents, accountability stories, and policy-driven coverage. "
            "On a typical week, you will bounce between law-enforcement operations, violent-crime updates, "
            "fire/rescue response, and community-safety efforts with direct public impact."
        )
        fallback.append(
            f"Recurring themes include {', '.join(t.replace('_', ' ').title() for t, _ in top_themes[:4])}. "
            f"Common incident types include {', '.join(i for i, _ in top_incidents[:4]) if top_incidents else 'a broad mix of incidents'} "
            "across both municipal and county jurisdictions."
        )
        if sample_stories:
            story_snippets = []
            for s in sample_stories[:3]:
                story_snippets.append(f"{s.get('title', 'Untitled')} ({s.get('date', 'Unknown date')})")
            fallback.append(
                "Story snapshots in this dataset show the range clearly: " + "; ".join(story_snippets) + "."
            )
        fallback.append(
            "For day-to-day reporting, track both immediate incidents and the follow-on policy, court, and agency-response angles. "
            "That combination is where the strongest enterprise stories usually come from."
        )
        return "\n\n".join(fallback)

    return narrative

def generate_temporal_overview(temporal_data, trend_analysis, model):
    """Generate overview of how coverage has evolved over time."""
    
    years = sorted(temporal_data.keys())
    
    # Build year-by-year summary
    year_summary = []
    for year in years:
        data = temporal_data[year]
        top_themes = data['themes'].most_common(3)
        year_summary.append(f"{year}: {data['count']} stories - top themes: {', '.join(f'{t}' for t, c in top_themes)}")
    
    year_summary_text = "\n".join(year_summary)
    
    emerging_themes = ', '.join(f"{t[0]}" for t in trend_analysis['emerging'][:3]) if trend_analysis['emerging'] else "none clearly emerging"
    declining_themes = ', '.join(f"{t[0]}" for t in trend_analysis['declining'][:3]) if trend_analysis['declining'] else "none clearly declining"
    
    prompt = f"""
Write a section about how public safety coverage has evolved over time.

You're helping a reporter understand the beat's trajectory—what's changed, what's new, what's fading.
Business casual tone—clear, direct, insightful.

Coverage breakdown by year:
{year_summary_text}

Key trends:
- Emerging issues (increasing coverage): {emerging_themes}
- Declining issues (decreasing coverage): {declining_themes}

Write 3-4 paragraphs that:
- Describe the overall arc of coverage over this time period
- Highlight what's changed—are certain issues getting more attention? Less?
- Note any clear shifts in the types of incidents being covered
- Help the reporter understand where the beat has been and where it might be going

Be specific. Reference the data. Make it useful for someone trying to understand this beat's evolution.
"""
    
    return call_llm(prompt, model)

def generate_seasonal_analysis(seasonal_data, model):
    """Generate analysis of seasonal patterns (only if significant patterns exist)."""
    
    # Check if there are meaningful seasonal differences
    if not seasonal_data or len(seasonal_data) < 3:
        return None
    
    # Calculate variance in seasonal coverage
    counts = [seasonal_data[s]['count'] for s in ['winter', 'spring', 'summer', 'fall'] if s in seasonal_data]
    if not counts or max(counts) < min(counts) * 1.3:  # Less than 30% variation
        return None  # Not significant enough to highlight
    
    seasonal_summary = []
    for season in ['winter', 'spring', 'summer', 'fall']:
        if season not in seasonal_data:
            continue
        data = seasonal_data[season]
        top_themes = data['themes'].most_common(3)
        seasonal_summary.append(f"{season.title()}: {data['count']} stories - {', '.join(f'{t} ({c})' for t, c in top_themes)}")
    
    seasonal_summary_text = "\n".join(seasonal_summary)
    
    prompt = f"""
Write a brief section about seasonal patterns in public safety coverage.

Data shows some meaningful variation by season. Help a reporter understand what to expect when.
Business casual tone—practical and clear.

Seasonal breakdown:
{seasonal_summary_text}

Write 2-3 paragraphs that:
- Highlight the clearest seasonal patterns (e.g., "summer sees more water-related incidents")
- Note which seasons are busier or have different types of coverage
- Give actionable advice—what should they watch for in each season?

Keep it focused on patterns that actually matter. Be specific.
"""
    
    return call_llm(prompt, model)

def generate_thematic_deep_dive(theme, data, all_stories, model):
    """Generate deep dive on a specific theme's evolution over time."""
    
    by_year = dict(data['by_year'])
    severity_breakdown = dict(data['severity'])
    outcomes = dict(data['outcomes'])
    
    # Check if there's temporal variation
    years = sorted(by_year.keys())
    year_breakdown = [f"{year}: {by_year[year]} stories" for year in years]
    
    # Get representative examples from different time periods
    early_stories = [s for s in data['stories'] if s.get('year') in years[:len(years)//2]][:2]
    recent_stories = [s for s in data['stories'] if s.get('year') in years[len(years)//2:]][:2]
    
    examples_text = "Early examples:\n" + "\n".join([
        f"- {s.get('title')} ({s.get('date')})"
        for s in early_stories
    ])
    if recent_stories:
        examples_text += "\n\nRecent examples:\n" + "\n".join([
            f"- {s.get('title')} ({s.get('date')})"
            for s in recent_stories
        ])
    
    # Check for seasonal patterns within this theme
    seasonal_note = ""
    if data['by_season']:
        seasonal_counts = dict(data['by_season'])
        seasonal_note = f"\nSeasonal variation: {', '.join(f'{s}: {c}' for s, c in sorted(seasonal_counts.items(), key=lambda x: x[1], reverse=True))}"
    
    prompt = f"""
Write an analysis of how {theme} coverage has evolved over time.

You're helping a reporter understand this specific issue area on the beat.
Business casual tone—insightful but not academic.

Data for {theme.upper()}:
- Total stories: {data['count']}
- By year: {', '.join(year_breakdown)}
- Severity levels: {severity_breakdown}
- Typical outcomes: {', '.join(f'{o} ({c})' for o, c in Counter(outcomes).most_common(3))}{seasonal_note}

{examples_text}

Write 2-3 paragraphs that:
- Describe how coverage of this issue has changed over time (increasing? decreasing? stable?)
- Note any patterns in severity or outcomes
- Mention seasonal patterns if they're significant for this theme
- Give practical insight—what should a reporter know about covering this issue?

Be specific and data-driven, but keep it conversational. If there's no clear trend, say so—that's useful too.
"""
    
    return call_llm(prompt, model)

def generate_followup_opportunities(stories, model):
    """Generate potential follow-up story ideas based on patterns."""
    
    themes = Counter(s.get('primary_theme') for s in stories if s.get('primary_theme'))
    temporal_data = analyze_temporal_periods(stories)
    trend_analysis = detect_emerging_declining_themes(temporal_data)
    
    # Get some recurring entities
    all_agencies = []
    all_locations = []
    for s in stories:
        agencies = s.get('response_agencies', [])
        if agencies:  # Only extend if not None
            all_agencies.extend(agencies)
        location_type = s.get('location_type')
        if location_type:  # Only append if not None
            all_locations.append(location_type)
    
    agency_counts = Counter(all_agencies).most_common(5)
    location_counts = Counter(all_locations).most_common(5)
    
    emerging = ', '.join(f"{t[0]}" for t in trend_analysis['emerging'][:3]) if trend_analysis['emerging'] else "none particularly"
    
    prompt = f"""
Based on this public safety data, suggest 4-6 potential follow-up story ideas.

You're brainstorming story angles with a colleague. Be creative but realistic.

Key patterns:
- Top themes: {', '.join(f'{t} ({c})' for t, c in themes.most_common(5))}
- Emerging issues (increasing coverage): {emerging}
- Most common response agencies: {', '.join(f'{a} ({c})' for a, c in agency_counts)}
- Most common location types: {', '.join(f'{loc} ({c})' for loc, c in location_counts)}
- Coverage spans multiple years with trends worth exploring

Suggest story ideas that:
- Explore WHY patterns exist or how issues are evolving
- Could help the community (prevention, awareness, resources, solutions)
- Go beyond breaking news to bigger questions about trends and changes
- Are specific and actionable—not vague
- Consider the temporal trends in the data

For each idea:
1. The angle (1-2 sentences)
2. Why it matters (what would readers learn?)
3. Who to talk to

Keep it practical. These should be stories a reporter could actually pursue.

IMPORTANT: End with a disclaimer noting that this data covers past years and reporters should verify current information, check for updates, and confirm details before pursuing any story ideas.
"""
    
    return call_llm(prompt, model)

def build_beatbook(stories, model):
    """Build the complete beatbook focused on temporal trends."""
    
    print("Generating beatbook sections...")
    
    # Extract key information
    print("  → Extracting key people and organizations...")
    key_people = extract_key_people(stories)
    key_orgs = extract_key_organizations(stories)
    geographic = extract_geographic_coverage(stories)
    
    # Introduction
    print("  → Writing introduction...")
    intro = generate_introduction(stories, model)
    
    # Temporal analysis - how has coverage evolved?
    print("  → Analyzing temporal trends...")
    temporal_data = analyze_temporal_periods(stories)
    trend_analysis = detect_emerging_declining_themes(temporal_data)
    
    print("  → Writing temporal overview...")
    temporal_overview = generate_temporal_overview(temporal_data, trend_analysis, model)
    
    # Theme deep dives - major issues and how they've changed
    print("  → Analyzing thematic trends...")
    theme_data = analyze_theme_trends(stories)
    top_themes = sorted(theme_data.items(), key=lambda x: x[1]['count'], reverse=True)[:5]

    # Narrative overview of beat coverage before trend analysis section
    print("  → Writing narrative coverage overview...")
    coverage_narrative = generate_coverage_narrative(stories, top_themes, geographic, model)
    
    theme_sections = {}
    theme_examples = {}
    for theme, data in top_themes:
        if theme and theme != 'unknown' and data['count'] >= 8:  # Only if enough stories
            print(f"  → Writing {theme} analysis...")
            theme_sections[theme] = generate_thematic_deep_dive(theme, data, stories, model)
            # Get story examples for this theme
            theme_examples[theme] = get_story_examples(stories, theme=theme, limit=2)
    
    # Seasonal patterns - only if significant
    print("  → Checking for seasonal patterns...")
    seasonal_data = analyze_seasonal_patterns(stories)
    seasonal_analysis = generate_seasonal_analysis(seasonal_data, model)
    
    # Weekend patterns
    print("  → Analyzing weekend vs weekday patterns...")
    weekend_data = analyze_weekend_patterns(stories)
    
    # Follow-up opportunities
    print("  → Generating follow-up story ideas...")
    followups = generate_followup_opportunities(stories, model)
    
    # Build final markdown
    beatbook = f"""# Public Safety Beat Book: Understanding the Beat Over Time

{intro}

---

## What You're Covering

{coverage_narrative}

**Coverage touchpoints that appear most often:**
{chr(10).join(f"- {t.replace('_', ' ').title()}" for t, _ in top_themes[:5])}

**Frequent places in the coverage footprint:**
{chr(10).join(f"- {loc}" for loc in geographic[:6])}

---

## How Coverage Has Evolved

Understanding how this beat has changed over time helps you see where it's been and where it might be going. Here's what the data shows about the evolution of public safety coverage in this area.

{temporal_overview}

"""
    
    # Add year-by-year story briefing (summary-driven, not count-driven)
    years = sorted(temporal_data.keys())
    if years:
        beatbook += "\n## Coverage by Year: What the Stories Were Actually About\n\n"
        beatbook += "This section is based on story summaries in the dataset, so you can see the substance of coverage year by year.\n\n"
        for year in years:
            beatbook += build_year_story_briefing(year, temporal_data[year])
    
    # Trend highlights
    if trend_analysis['emerging'] or trend_analysis['declining']:
        beatbook += "\n**Notable Trends:**\n\n"
        if trend_analysis['emerging']:
            beatbook += "*Emerging issues (increasing coverage):*\n"
            for theme, early_avg, recent_avg in trend_analysis['emerging'][:3]:
                change = ((recent_avg - early_avg) / early_avg * 100) if early_avg > 0 else 100
                beatbook += f"- {theme}: ↑ {change:.0f}% increase\n"
            beatbook += "\n"
        if trend_analysis['declining']:
            beatbook += "*Declining issues (decreasing coverage):*\n"
            for theme, early_avg, recent_avg in trend_analysis['declining'][:3]:
                change = ((early_avg - recent_avg) / early_avg * 100) if early_avg > 0 else 0
                beatbook += f"- {theme}: ↓ {change:.0f}% decrease\n"
            beatbook += "\n"
    
    beatbook += "---\n\n## Deep Dives: Major Issues on This Beat\n\n"
    beatbook += "Here's a closer look at the main issue areas you'll be covering and how they've evolved.\n\n"
    
    for theme, narrative in theme_sections.items():
        beatbook += f"### {theme.replace('_', ' ').title()}\n\n"
        beatbook += narrative + "\n\n"
        
        # Add stats and examples
        data = theme_data[theme]
        beatbook += f"**Quick stats:**\n"
        beatbook += f"- Total coverage: {data['count']} stories\n"
        
        # Year breakdown
        years_for_theme = sorted([y for y in data['by_year'].keys()])
        if len(years_for_theme) > 1:
            beatbook += f"- Timeline: {years_for_theme[0]} to {years_for_theme[-1]}\n"
            beatbook += f"- Coverage trend: "
            early = sum(data['by_year'][y] for y in years_for_theme[:len(years_for_theme)//2])
            recent = sum(data['by_year'][y] for y in years_for_theme[len(years_for_theme)//2:])
            if recent > early * 1.2:
                beatbook += "Increasing ↑\n"
            elif early > recent * 1.2:
                beatbook += "Decreasing ↓\n"
            else:
                beatbook += "Stable →\n"
        beatbook += "\n"
        
        # Add story examples
        if theme in theme_examples and theme_examples[theme]:
            beatbook += "**Story Examples:**\n\n"
            for example in theme_examples[theme]:
                beatbook += f"**\"{example['title']}\"** ({example['date']})\n"
                beatbook += f"- Type: {example['incident_type']}\n"
                beatbook += f"- Summary: {example['summary']}\n\n"
        
        beatbook += "\n"
    
    # Seasonal patterns (only if significant)
    if seasonal_analysis:
        beatbook += "---\n\n## Seasonal Patterns\n\n"
        beatbook += seasonal_analysis + "\n\n"
        
        # Add seasonal breakdown table
        beatbook += "**Seasonal breakdown:**\n\n"
        for season in ['winter', 'spring', 'summer', 'fall']:
            if season in seasonal_data:
                data = seasonal_data[season]
                top_theme = data['themes'].most_common(1)[0] if data['themes'] else ('varied', 0)
                beatbook += f"- **{season.title()}:** {data['count']} stories (most common: {top_theme[0]})\n"
        beatbook += "\n"
    
    # Weekend patterns
    beatbook += "---\n\n## Weekday vs Weekend Patterns\n\n"
    weekday_top = weekend_data['weekday']['themes'].most_common(3)
    weekend_top = weekend_data['weekend']['themes'].most_common(3)
    
    beatbook += f"**Weekday coverage** ({weekend_data['weekday']['count']} stories):\n"
    beatbook += f"- Top themes: {', '.join(f'{t} ({c})' for t, c in weekday_top)}\n\n"
    
    beatbook += f"**Weekend coverage** ({weekend_data['weekend']['count']} stories):\n"
    beatbook += f"- Top themes: {', '.join(f'{t} ({c})' for t, c in weekend_top)}\n\n"
    
    if weekend_data['weekend']['count'] > 0 and weekend_data['weekday']['count'] > 0:
        weekend_pct = weekend_data['weekend']['count'] / (weekend_data['weekend']['count'] + weekend_data['weekday']['count']) * 100
        beatbook += f"About {weekend_pct:.0f}% of coverage happens on weekends, which makes sense for breaking news and incidents that don't follow a 9-5 schedule.\n\n"
    
    # Key People section
    beatbook += "---\n\n## Key People to Know\n\n"
    beatbook += "These individuals appear frequently in public safety coverage and are important contacts:\n\n"
    for i, person in enumerate(key_people[:10], 1):
        beatbook += f"{i}. {person}\n"
    beatbook += "\n"
    
    # Key Organizations section
    beatbook += "---\n\n## Key Organizations\n\n"
    beatbook += "Main agencies and groups involved in public safety:\n\n"
    for i, org in enumerate(key_orgs[:10], 1):
        beatbook += f"- {org}\n"
    beatbook += "\n"
    
    # Follow-ups
    beatbook += "---\n\n## Potential Follow-Up Stories\n\n"
    beatbook += followups + "\n\n"
    
    # Footer
    beatbook += "---\n\n"
    beatbook += f"*Beatbook generated on {datetime.now().strftime('%Y-%m-%d')} from {len(stories)} stories*\n"
    
    return beatbook

def main():
    parser = argparse.ArgumentParser(description='Generate beatbook analyzing how public safety coverage has evolved over time')
    parser.add_argument('--input', default='thematic_entities_stories.json', help='Input JSON file with extracted entities (default: thematic_entities_stories.json)')
    parser.add_argument('--output', default='thematic_beatbook.md', help='Output markdown file (default: thematic_beatbook.md)')
    parser.add_argument('--model', default='groq/llama-3.3-70b-versatile', help='LLM model to use for narrative generation')
    
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    args = parser.parse_args()
    
    # Load pre-extracted data
    print(f"\n{'='*60}")
    print(f"TEMPORAL TRENDS BEATBOOK GENERATOR")
    print(f"{'='*60}")
    
    try:
        with open(args.input) as f:
            stories = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find input file '{args.input}'")
        return
    
    print(f"Loaded {len(stories)} stories from {args.input}")
    
    # Filter stories with entity extraction errors
    valid_stories = [s for s in stories if 'entity_extraction_error' not in s]
    print(f"Using {len(valid_stories)} stories with successful entity extraction")
    
    if len(valid_stories) == 0:
        print("Error: No valid stories found!")
        return
    
    print(f"Model: {args.model}")
    print(f"Output: {args.output}")
    print(f"{'='*60}\n")
    
    # Generate beatbook
    beatbook = build_beatbook(valid_stories, args.model)
    
    # Save
    with open(args.output, 'w') as f:
        f.write(beatbook)
    
    print(f"\n{'='*60}")
    print(f"✓ Beatbook generated successfully!")
    print(f"Saved to: {args.output}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
