## Beat book process for beginners		02/14/2026

Before we proceed with this task, users should:
    -Have story samples in a json file
    -Have a Github account
If these requirements are met, the next thing is to set up our environment. Note: we will be using Groq models for this process, but users can feel free to install other models.
## Quick setup for beginners
First create a repository: 
1. Go to github.com -> Log into your account
	- Click the + icon in the top-right, choose New repository.
	- Name it, set Public or Private, then click Create repository.
2. Open your codespace or terminal:
	- Click Code -> Codespaces -> Create codespace.
	- We'll work locally, so open a terminal in your project folder. [explain this like they have never used a terminal, explain parts of the terminal. keep it concise but detailed. Let the user know how to install copilot]
3. Install uv (Python tool runner):
	- Run: curl -LsSf https://astral.sh/uv/install.sh | sh
	- Then run: export PATH="$HOME/.local/bin:$PATH"
4. Initialize your project (optional but helpful):
	- Run: uv init --python 3.12
5. Install llm:
	- Run: uv add llm
    - Run: uv add llm install llm-groq (Here, you can include other models: llm-gemini, llm-anthropic, especially if you have access to their API keys).
6. Get a Groq API key:
	- Go to https://console.groq.com
	- Create an account, then create an API key (click on Create API at the top right corner when you log in to Groq).
    - To set up your Groq API key which should help you access the models, run: uv run llm keys set groq. You'll be prompted to enter your API keys. Bear in mind that you wont see the key, but when you click 'enter/return' it should work.

## Next steps: Extract entities
Now that we are all set up, our next step is to begin gathering/extracting entities: metadata from the stories we have. We do this One reason for extracting entities is [because ...? Why do we not use the json file we have?]
We can use any of the models we have access to to extract metadata. We also need a python script for this process, but since many people are not versed in Pythong, we'll write a prompt in copilot asking the agent to generate a script that extracts our metadata.
But while metadata can provide [what ?] it is not enough context for a beatbook.
To get more context for a beatbook, we need to have some parts of our story included in the beatbook script. We can choose to include entire stories as they appear in our original data, or just summaries.
I crafted my prompt to generate a script prioritize the following requirements:
Summarize each story (keeps quotes), then extract entities from the summary. I did this because [what benefit?] I also included that metadata be extracted from the original stories first, before they are summarized. I did this because I did not want to be limited to only the metadat found in the summaries, and yet, I wanted to maximize my tokens by given as much information as was necessary but not excessive.
	- Output: replace full story content with the summary text in the saved JSON.
	 Default output file: stories_entities_3.json (or whatever name you want your json file containing your entities to be)
	Exclusions in metadata extraction:
	- Do not include author/byline names.
	- Do not include photographer names.
	- Do not include news organization names (Star Democrat, Chesapeake Publishing, APG Media).
	Incremental saves:
	- The script writes the output file after each story is processed.
[talk about rate limits: you are likely to hit rate limits because of ??]
[to get through this, one needs to update the .py script that extract the eentities to save incrementally. That way, when you run into a problem, you can continue saving from where you stopped. Sometimes you have too many stories. It's best to process them in batches. Or how best to deal with this?]
[It's usually best to use closed models: why?]
[after generating entities, you might want to study it to see what your extracted values look like. SQLite database is a good way to do that because?]
First you laod your json file into a sqlite database using this command: 
`uv run sqlite-utils insert entities.db stories your_json_file_name --pk docref`

Replace your_json_file_name with the name of the json file where you have the entities. The command above converts your json file into a database table that lives in entities.db. Now you can filter, analyze the data using datasette.
What is datasette? Datasette is [ ??]
To view your document on datasette you first have to install it in your environment: 
`uv add datasette`
You know you added it correctly when your output says: "Installed 15 packages in 58ms" and goes ahead to list the packages installed.
Then you can run this to view your data in Datasette:
`uv run datasette entities.db`
What the command above does is take you to Datasette on you browser. Running this command prompts a pop up that asks you if you want to open datasette in a browser. If, somehow, you miss the pop up or close it, you can access datasette by clicking on 'PORTS' locted at the top of your terminal. You should look for Port 8001, and you know this is what you are looking for because in your terminal, the last line there says: Uvicorn running on http://127.0.0.1:8001
The last four figures there tells you what port to look for.
CLick on the link. A globe icon pops up by the side. Click on that and look through your data. Your data is linked to "stories" under entities [we know this how?]
Looking at your work in datasette lets you see how well your extraction worked. It also helps you with factchecking: are there false names in the extracted data? You are able to compare the extractions with the summary you have. You also get to see how many cases your llm failed to parse or extract your data, which gives a sense of how reliable the data is.
If you are not content with your extracted entities, you can review the process afresh, prompting copilot to update the script so that it reflects whatever you wish to include or take out.
For me, by the third try, I was comfortable enough to generate my beatbook.
You may choose to create your beatbook in a way that focuses on the most important people mentioned, or the most significant issues covered in one beat. ANYTHING can infuence the angle from which you may choose to create your beatbook. I have decided to create a beatbook that gives a chronological narrative? This helps a new reporter not only understand the beat, but see how that has evolved over time.
One other significant factor to consider when creating a beatbook is the format. Will this be in text? A table? A webpage?

## Writing the beat book
This process will largely be handled by your AI tool. Again, what this means is that we need a Python script to [do what?]
To generate this, we go again to copilot and ask it to generate a script.
I saved mine as create_beatbook.py. You can call yours whatever.
To generate a first draft, I ran this bash (or code):
`python create_beatbook.py`
You should replace create_beatbook.py with whatever you call your script.
While you may not have all the knowledge of Python, you have to pay attention to this script, especially whatever prompts/directives you might have given to your AI tool. The reason for this is, it helps you provide directions for your script so that even when you are unsure how the code works, you have you can direct the AI throught the prompts you provide in plain language.
Without really editing my prompt, I generated a beatbook to have a glimpse of what might need some improvement. But I had given copilot some instructions for the script: make it narrative, but also chronological. I want to see trends in story coverage over time. Not trends in bylines, trends in stories. Remember, this is targetted at a reporter new in the beat.
I ran the first prototype with this bash:
`uv run python create_beatbook.py --input stories_entities_3.json --output beatbook_narrative_chronological.md --model groq/llama-3.3-70b-versatile`