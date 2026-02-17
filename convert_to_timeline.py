#!/usr/bin/env python3
"""
Convert stardem_nearly_final_talbot_beatbook_v6.md to KnightLab Timeline JSON format.
Enhanced version with introduction, coverage overview, and detailed story summaries.
"""

import json
import re
from datetime import datetime
from pathlib import Path


def parse_date(date_str):
    """Parse date string in format YYYY-MM-DD."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except:
        return None


def extract_introduction(md_content):
    """Extract and summarize the introduction section."""
    intro_match = re.search(r'### 1\. Introduction\s+(.*?)(?=---|\n###)', md_content, re.DOTALL)
    if intro_match:
        intro_text = intro_match.group(1).strip()
        # Remove blockquotes and clean up
        intro_text = re.sub(r'>\s*\*\*For additional context.*?\n\n', '', intro_text, flags=re.DOTALL)
        # Take first 2 paragraphs
        paragraphs = [p.strip() for p in intro_text.split('\n\n') if p.strip() and not p.strip().startswith('>')]
        summary = '\n\n'.join(paragraphs[:2]) if paragraphs else intro_text[:600]
        return f"<p>{summary}</p>"
    return None


def extract_coverage_overview(md_content):
    """Extract key points from 'What You'll Be Covering' section."""
    coverage_match = re.search(r'### 2\. What You.ll Be Covering\s+(.*?)(?=---|\n###)', md_content, re.DOTALL)
    if coverage_match:
        coverage_text = coverage_match.group(1).strip()
        # Extract bold headings as key points
        sections = re.findall(r'\*\*([^\*]+)\*\*\s+(.*?)(?=\n\*\*|\Z)', coverage_text, re.DOTALL)
        if sections:
            summary = "<strong>Key Coverage Areas:</strong><br><br>"
            summary += "<ul style='text-align: left;'>"
            for heading, text in sections[:5]:  # Limit to 5 main points
                heading = heading.strip()
                # Get first sentence of the description
                text_clean = re.sub(r'\s+', ' ', text.strip())
                first_sent = text_clean.split('.')[0] + '.' if text_clean else ''
                summary += f"<li><strong>{heading}:</strong> {first_sent[:150]}...</li>"
            summary += "</ul>"
            return summary
    return None


def extract_bottom_line(md_content):
    """Extract the 'Bottom Line for the New Reporter' section."""
    bottom_line_match = re.search(r'### Bottom Line for the New Reporter\s+(.*?)(?=##|\Z)', md_content, re.DOTALL)
    if bottom_line_match:
        text = bottom_line_match.group(1).strip()
        # Clean and format
        text = re.sub(r'\s+', ' ', text)
        return text
    return None


def extract_story_examples_detailed(md_content):
    """Extract story examples with full details."""
    events = []
    
    # Pattern to match story example sections with full content
    story_pattern = r'### ([^:]+): "([^"]+)"\s*\*(\d{4}-\d{2}-\d{2})\*\s*\*\*Why it\'s a good example:\*\* ([^\n]+(?:\n(?!###|\n##)[^\n]+)*)'
    
    matches = re.finditer(story_pattern, md_content, re.DOTALL)
    
    for match in matches:
        story_type = match.group(1).strip()
        title = match.group(2).strip()
        date_str = match.group(3).strip()
        description = match.group(4).strip()
        
        # Clean up description
        description = description.split('\n\n')[0]
        description = re.sub(r'\s+', ' ', description).strip()
        description = re.sub(r'##.*$', '', description).strip()
        
        date_obj = parse_date(date_str)
        if date_obj:
            events.append({
                "start_date": {
                    "year": str(date_obj.year),
                    "month": str(date_obj.month),
                    "day": str(date_obj.day)
                },
                "text": {
                    "headline": title,
                    "text": f"<strong>Story Type: {story_type}</strong><br><br>"
                           f"<strong>Why it's a good example:</strong> {description}<br><br>"
                           f"<em>This story exemplifies {story_type.lower()} coverage on the public safety beat.</em>"
                }
            })
    
    return events


def extract_followup_opportunities(md_content):
    """Extract potential follow-up story opportunities."""
    followup_match = re.search(r'## Potential Follow-Ups\s+(.*?)(?=\Z)', md_content, re.DOTALL)
    if followup_match:
        followup_text = followup_match.group(1).strip()
        # Extract numbered items
        items = re.findall(r'\d+\.\s+\*\*([^*]+)\*\*\s+-\s+Angle:\s+([^\n]+)\s+-\s+Why:\s+([^\n]+)', followup_text, re.DOTALL)
        
        if items:
            summary = "<strong>Potential Follow-Up Stories</strong><br><br>"
            summary += "<ol>"
            for title, angle, why in items[:5]:
                title = title.strip()
                angle = angle.strip()
                why = re.sub(r'\s+', ' ', why.strip())
                summary += f"<li><strong>{title}</strong><br>"
                summary += f"<em>Angle:</em> {angle}<br>"
                summary += f"<em>Why:</em> {why}</li><br>"
            summary += "</ol>"
            return summary
    return None


def extract_context_events(md_content):
    """Extract contextual events mentioned in the beat book."""
    events = []
    
    # Extract some key dates mentioned in the narrative
    date_mentions = [
        ('2024-02-01', 'Major Kidnapping Investigation',
         'Cambridge kidnapping case prompted joint task force of Cambridge PD, Easton PD, Maryland State Police, and Talbot Sheriff\'s Office. The case lasted months and involved multi-agency coordination across the Mid-Shore region.'),
        
        ('2024-04-01', 'Fake 911 Drug Bust',
         'Major drug bust uncovered "shoot-to-kill" ring using counterfeit 911 calls to mask fentanyl shipments. This sparked statewide conversation about how technology can be weaponized against public safety systems.'),
        
        ('2024-07-01', 'Vision Zero Grant Awarded',
         'MD DOT Vision Zero grant funded three-way stop on Brookletts Avenue in Easton, addressing deer-season crash hotspot. Part of ongoing traffic safety improvements for aging population.'),
        
        ('2024-08-01', 'Oxford Stop-Sign Installation',
         'Town of Oxford installed stop-sign at dangerous intersection after series of rear-end collisions. Demonstrates local response to traffic safety data.'),
        
        ('2024-09-01', 'County-Wide Emergency Drill',
         'Talbot County Department of Emergency Services ran joint shelter-opening drill during National Preparedness Month, bringing together fire, EMS, and Maryland Emergency Management Agency.'),
        
        ('2024-10-01', 'Route 662 Detour Begins',
         'Temporary closure began when new hospital wing construction forced detour, sparking multi-agency debate involving County Council, MD SHA, hospital system, and local farmers about economic impact versus safety.'),
        
        ('2024-11-01', 'County Burn-Ban Ordinance',
         'Talbot County rolled out burn-ban ordinance to curb wildfire risk during protracted drought, sparking lively town-hall debate over enforcement on private property.'),
        
        ('2024-12-01', 'Talbot CaRES AED Rollout',
         'County-wide AED network (Talbot CaRES) expanded with new installations at Bluepoint Hospitality restaurants, part of public-access cardiac arrest response program.'),
        
        ('2025-01-01', 'Citizens Police Academy Launch',
         'Sheriff Joe Gamble launched Citizens Police Academy, bringing high-school seniors into precinct for 10-week immersion program as part of community policing initiatives.'),
        
        ('2025-05-01', 'Sanctuary Jurisdiction Controversy',
         'Federal grant threatened unless counties signed pledge not to limit ICE cooperation. Sparked debate between federal funding needs and community trust.'),
    ]
    
    for date_str, headline, text in date_mentions:
        date_obj = parse_date(date_str)
        if date_obj:
            events.append({
                "start_date": {
                    "year": str(date_obj.year),
                    "month": str(date_obj.month),
                    "day": str(date_obj.day)
                },
                "text": {
                    "headline": headline,
                    "text": text
                }
            })
    
    return events


def create_timeline_json(md_file, output_file):
    """Create KnightLab Timeline JSON from markdown beatbook."""
    
    md_path = Path(md_file)
    if not md_path.exists():
        raise SystemExit(f"Input file not found: {md_file}")
    
    with md_path.open("r", encoding="utf-8") as f:
        content = f.read()
    
    all_events = []
    
    # 1. Add introduction slide (date: start of coverage period)
    intro_text = extract_introduction(content)
    if intro_text:
        all_events.append({
            "start_date": {"year": "2023", "month": "1", "day": "1"},
            "text": {
                "headline": "Welcome to the Beat",
                "text": intro_text
            }
        })
    
    # 2. Add coverage overview slide
    coverage_text = extract_coverage_overview(content)
    if coverage_text:
        all_events.append({
            "start_date": {"year": "2023", "month": "6", "day": "1"},
            "text": {
                "headline": "What You'll Be Covering",
                "text": coverage_text
            }
        })
    
    # 3. Extract story events with detailed summaries
    story_events = extract_story_examples_detailed(content)
    all_events.extend(story_events)
    
    # 4. Extract context events from the narrative
    context_events = extract_context_events(content)
    all_events.extend(context_events)
    
    # 5. Add bottom line slide (near end of timeline)
    bottom_line_text = extract_bottom_line(content)
    if bottom_line_text:
        all_events.append({
            "start_date": {"year": "2025", "month": "12", "day": "1"},
            "text": {
                "headline": "Bottom Line for the New Reporter",
                "text": bottom_line_text
            }
        })
    
    # 6. Add follow-up opportunities slide (at the end)
    followup_text = extract_followup_opportunities(content)
    if followup_text:
        all_events.append({
            "start_date": {"year": "2025", "month": "12", "day": "15"},
            "text": {
                "headline": "Potential Follow-Up Stories",
                "text": followup_text
            }
        })
    
    # Sort by date
    all_events.sort(key=lambda x: (
        int(x["start_date"]["year"]),
        int(x["start_date"]["month"]),
        int(x["start_date"]["day"])
    ))
    
    # Create timeline structure
    timeline = {
        "title": {
            "text": {
                "headline": "Talbot County Public Safety Beat Book",
                "text": "A comprehensive timeline guide for reporters covering public safety on the Eastern Shore"
            }
        },
        "events": all_events
    }
    
    # Write output
    output_path = Path(output_file)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(timeline, f, indent=2)
    
    print(f"Timeline JSON created: {output_path}")
    print(f"Total events: {len(all_events)}")
    print(f"\nTo use this timeline:")
    print(f"1. Go to https://timeline.knightlab.com/")
    print(f"2. Click 'Make a Timeline'")
    print(f"3. Choose 'JSON' option")
    print(f"4. Paste the contents of {output_file}")


def main():
    create_timeline_json(
        "stardem_nearly_final_talbot_beatbook_v6.md",
        "talbot_beatbook_timeline.json"
    )


if __name__ == "__main__":
    main()
