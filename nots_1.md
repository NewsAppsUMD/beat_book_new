## Beat Book Process for Beginners (Outline)

### 1) Prerequisites
- Story samples in a JSON file
- GitHub account
- Access to a terminal/Codespace

### 2) Environment Setup
- Create a GitHub repository
- Open Codespace or local terminal in project folder
- Install `uv`
- (Optional) Initialize project with Python 3.12
- Install `llm` and model plugins (Groq, Gemini, Anthropic, etc.)
- Set API key (`uv run llm keys set groq`)

### 3) Extract Metadata First
- Generate a Python script to extract metadata from original stories
- Metadata should support whatever type of beat book you intend to create.
For a thematic-over-time beatbook
- Key field groups:
  - **Temporal:** names, season, year, is_weekend
  - **Content classification:** primary/secondary themes, incident type, severity
  - **Geographic:** location, location type
  - **Contextual:** incident time, weather, agencies, outcome
For a narrative beatbook
- Key field groups:
  - **People:** names,title
  - **Places:** Maryland, Talbot, St Michael's
- Regardless of the type, you might want to keep quotes; replace full story content with summaries in output
- Exclude bylines, photographer names, and org names

### 4) Why This Step Is Critical
- Metadata quality strongly affects beatbook quality
- Extract from full stories before summarization for richer signals
- Summaries reduce token usage while preserving context

### 5) Reliability Practices
- Save output incrementally after each story
- Handle API rate limits and interruptions
- Process large corpora in batches
- Resume from where processing stopped

### 6) Validate Extraction in SQLite + Datasette
- Load JSON into SQLite:
  - `uv run sqlite-utils insert entities.db stories your_json_file_name --pk docref`
- Install/run Datasette:
  - `uv add datasette`
  - `uv run datasette entities.db`
- Use Datasette to:
  - Inspect extraction quality
  - Check false positives/failed parses
  - Compare extracted fields against summaries and actual stories.

### 7) Iteration Loop
- Review extracted output
- Refine prompts/scripts
- Re-run extraction and validation
- Repeat until metadata quality is acceptable

### 8) Generate the Beatbook
- Use a dedicated script (e.g., `generate_thematic_beatbook.py`)
- Example run:
  - `uv run python generate_thematic_beatbook.py --model "anthropic/claude-sonnet-4-" --input thematic_entities_stories.json --output my_narrative_beatbook_v2.md`

### 9) Beatbook Writing Requirements may include
- Reporter-friendly, business-casual tone
- Short, approachable introduction
- Use pre-extracted data and summaries only
- Include follow-up story ideas + disclaimer that data may be outdated.