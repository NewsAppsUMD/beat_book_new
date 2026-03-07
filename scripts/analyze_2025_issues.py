import json
from collections import Counter
import re

# Load the stories
with open("data/local_government_stories.json", "r") as f:
    stories = json.load(f)

# Filter for 2025 stories only
stories_2025 = [s for s in stories if s.get("year") == 2025]

print(f"Total stories from 2025: {len(stories_2025)}")
print(f"Stories from 2025 with Local Government score >= 0.7: {sum(1 for s in stories_2025 if s.get('llm_classification', {}).get('topic') == 'Local Government' and s.get('llm_classification', {}).get('score', 0) >= 0.7)}\n")

# Extract key themes from titles and explanations
issues = []

for story in stories_2025:
    title = story.get("title", "").lower()
    explanation = story.get("llm_classification", {}).get("explanation", "").lower()
    
    # Common local government issues to look for
    patterns = {
        "zoning/rezoning": r"\b(zoning|rezoning|rezone)\b",
        "town/city council": r"\b(town council|city council|council meeting|commissioners)\b",
        "development/housing": r"\b(development|housing|apartment|residential)\b",
        "budget/finance": r"\b(budget|finance|funding|bond|tax|revenue)\b",
        "elections/candidates": r"\b(election|candidate|vote|voting|mayor|campaign)\b",
        "planning/zoning board": r"\b(planning|planning commission|zoning board)\b",
        "infrastructure": r"\b(infrastructure|road|bridge|water|sewer|utilities)\b",
        "parks/recreation": r"\b(park|recreation|playground|trail)\b",
        "ordinance/regulation": r"\b(ordinance|regulation|moratorium|law|policy)\b",
        "public hearing/meeting": r"\b(public hearing|public meeting|listening session)\b",
        "county government": r"\b(county commission|county council|county government)\b",
        "school board": r"\b(school board|board of education)\b",
        "economic development": r"\b(economic development|business|tourism|job)\b",
        "environmental": r"\b(environment|landfill|pollution|wildlife|water quality)\b",
        "veterans": r"\b(veteran|military)\b",
        "healthcare": r"\b(health|hospital|medical)\b",
        "transportation": r"\b(traffic|transportation|road)\b",
        "historic preservation": r"\b(historic|preservation|armory|heritage)\b",
        "cannabis": r"\b(cannabis|marijuana)\b",
        "ward realignment": r"\b(ward|redistricting)\b",
        "committee formation": r"\b(committee|advisory|task force)\b",
        "emergency services": r"\b(fire|police|sheriff|emergency)\b",
        "land use": r"\b(land use|property|real estate)\b",
        "community engagement": r"\b(community|resident|public input)\b",
        "state/local relations": r"\b(general assembly|governor|state|legislature)\b"
    }
    
    text = title + " " + explanation
    for issue, pattern in patterns.items():
        if re.search(pattern, text):
            issues.append(issue)

# Count frequency
issue_counts = Counter(issues)

# Get top 25
print("Top 25 Issues in 2025 Local Government Stories:\n")
print(f"{'Rank':<5} {'Issue':<30} {'Count':<10}")
print("=" * 50)

for i, (issue, count) in enumerate(issue_counts.most_common(25), 1):
    print(f"{i:<5} {issue:<30} {count:<10}")

# Also show monthly breakdown
print("\n\n2025 Stories by Month:")
print(f"{'Month':<15} {'Count':<10}")
print("=" * 30)
month_counts = Counter(s.get("month") for s in stories_2025 if s.get("month"))
for month in sorted(month_counts.keys()):
    month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    print(f"{month_names[month]:<15} {month_counts[month]:<10}")
