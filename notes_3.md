## From news archives to beatbook

### 1) Prerequisites
- Story samples in a JSON file
- GitHub account
- Access to a terminal/Codespace

### 2) Quick Setup for Beginners
- We will be using this repository for this workshop: https://github.com/NewsAppsUMD/nicar2026

- Open Codespace or local terminal in project folder
	- In GitHub, open the repo and click **Code → Codespaces → Create codespace**. This takes you into the terminal where we will be working out of for most of this session.
	A codespace environment is typically divided into three sections: the explorer on the left, your text editor in the upper part of the right and the terminal right below.
    -  ## A terminal lets you type commands directky into your system, rather than pushing buttone explain better...
	You can include Github Copilot at the extreme right of your codespace and for this session we shall, because we will be writing python codes that will best be writtes using copilot. Copilot is an AI assistant that helps you write code, explain your codes or other issues that might come up in your terminal as you work in your codespace.
	- To do this, click on the chat icon at the top right. This gives you options in a drop-down. Click on Open Chat. Your codespaces appears at the right. To be able to use Copilot in codespaces, complete set up by clicking on "Finish setup" below the chat box. Click on Use AI Features. Now you can use copilot for your work.
	- If you already see the chat box open at the right, then click on "Finish setup" directly under the chat box and follow the same steps above.
	- To confirm that copilot is working, type a simple message like: “hello”.
	   - If you get a response, setup is complete.

- To begin our process with our open models, we need to install the packages required for this process:
- Install `uv`:
	- Run: `pip install uv`
- Initialize your project (optional but helpful):
	- Run: `uv init --python 3.12`

- Next, we'll install `llm` and model plugins (Groq, Gemini, Anthropic, etc.)
	- Plugins are tools you add to a bigger app to give it new features (like Chrome extensions). Together with llm models, we can access the weights of the AI tools on our own machines through API keys. [We can download these models on our own machines without API keys, but that would require us to have adequate storage, GPUs, etc. Using the API keys for these models reduces such challenges.]
	- Run: `uv add llm`
	- Run: `uv add llm-groq`
	- You can also add other providers (for example run  `uv add llm-gemini`, `uv add llm-anthropic`) if you have keys for those
- For this process, we use **Groq**:
	- Groq is an API provider that hosts multiple **open-weight models**, meaning that these models are publiclly available.

- Get a Groq API key:
	- Go to `https://console.groq.com`
	- Create an account and API key.
	- Set key locally: `uv run llm keys set groq`

Now you are ready to use open-weight models via API.

### 3) First: Extract Metadata!

# Step 1
- The first step from JSON archives to beatbook is metadata extraction.
- Metadata is data about the stories (themes, locations, outcomes, etc.).
- We generate metadata so that later interactions with commercial models (for example Claude) can use those lighter derived fields and summaries, instead of full raw article text. We want to avoid repeatedly sending full article text into commercial models, and we also want to reduce token costs later.

- We use a Python script (generated with Copilot) to extract metadata and summaries from the archive JSON.
- Your prompt should be specific to the beatbook you want.

For a thematic beatbook over time, ask for fields like:
- **Temporal:** names, season, year
- **Content classification:** primary/secondary themes, incident type, severity
- **Geographic:** location, location type
- **Contextual:** incident time, weather, agencies, outcomes

For a narrative beatbook, include fields like:
- **People:** names, titles
- **Places:** county/town/place names

- Regardless of beatbook type, request quote retention and summary replacement of full story content in output.
- Also request exclusions: bylines, photographer names, and news organization names.

In response to your prompt, Copilot generates a `.py` script. Review prompt text inside that script and verify it matches your editorial goals.

# Step 2
Run extraction:

```bash
uv run python metadata.py --model YOUR_MODEL --input story_sample.json
```

- Replace `metadata.py` with your script filename.
- Replace `YOUR_MODEL` with your selected model.

If unsure what models are available:

`uv run llm models`

Example:

`uv run python metadata.py --model groq/qwen/qwen3-32b --input story_sample.json`

### Possible problems with extraction

You may encounter errors during large runs. The most common is **rate limiting**.

- Rate limits cap how fast/how often you can call an API.
- If processing hundreds of stories, requests can exceed provider limits.

When this happens, avoid losing progress by using **incremental saves** in your extraction script:
- Save output after each processed story.
- On failure, rerun and continue from existing output rather than restarting.

Example workflow when limits hit:
1. Stop run (`Ctrl/Cmd + C`)
2. Switch model
3. Rerun command using same output file

### 4) Verification

Even local/open-model workflows require verification.

- Check whether extracted fields match source stories.
- Look for false names, wrong organizations, missed outcomes, and parse failures.

An easy workflow is SQLite + Datasette.

Before inserting data, install tools:

```bash
uv add sqlite-utils
uv add datasette
```

Load JSON into SQLite:

```bash
uv run sqlite-utils insert entities.db stories your_json_file_name --pk docref
```

Open Datasette:

```bash
uv run datasette entities.db
```

If the popup is missed, open via **PORTS** and select the Datasette port.

Use Datasette to:
- Inspect extraction quality
- Check false positives / failed parses
- Compare extracted fields against summaries and source stories

If quality is low, refine the extraction prompt/script and rerun.

### 6) Generate the Beatbook

This is another iterative step. Here, you can use commercial models more safely because you are working from extracted metadata/summaries.

Prompt Copilot to create a second script that:
- Produces a narrative, reporter-friendly beatbook from `metadata_stories.json`
- Uses summaries in the file rather than fetching full stories again
- Uses business-casual tone
- Includes short intro and follow-up ideas
- Includes disclaimer that data may be outdated
- Focuses on thematic evolution over time (seasonal patterns optional, not dominant)

Run beatbook generation:

```bash
uv run python generate_beatbook.py --model "claude-sonnet-4.5" --input metadata_stories.json --output my_narrative_beatbook.md
```

Refine repeatedly until narrative quality and factual grounding are strong.
