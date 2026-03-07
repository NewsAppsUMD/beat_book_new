import json

# Load the output file - it's a list of stories
with open('data/local_government_stories_top_issues.json', 'r') as f:
    stories = json.load(f)

original_count = len(stories)
print(f"Original story count: {original_count}")

# From the terminal output, we processed 240 stories and kept 233 (7 were excluded)
processed_kept = 233

# Keep only the processed stories
stories = stories[:processed_kept]

# Save back
with open('data/local_government_stories_top_issues.json', 'w') as f:
    json.dump(stories, f, indent=2)

print(f"Kept {len(stories)} stories, removed {original_count - len(stories)} unprocessed stories")
