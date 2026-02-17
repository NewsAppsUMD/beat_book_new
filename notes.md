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
	- We'll work locally, so open a terminal in your project folder.
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
Next, we use any of the models we have access to to extract metadata. We also need a python script for this process, but we'll write a prompt in copilot asking it to generate a script that extracts our metadata.
To give our metadata some context for a beatbook, we need to have some parts of our story included in the beatbook script. We can choose to include the entire content or just summaries.
 Same of my requirements for the script:
Summarize each story (keeps quotes), then extracts entities from the summary.
	- Output: replace full story content with the summary text in the saved JSON.
	 Default output file: stories_and_entities_new.json
	Exclusions in metadata extraction:
	- Do not include author/byline names.
	- Do not include photographer names.
	- Do not include news organization names (Star Democrat, Chesapeake Publishing, APG Media).
	Incremental saves:
	- The script writes the output file after each story is processed.
[talk about rate limits: you are likely to hit rate limits because of ??]
[to get through this, one needs to update the .py script that extract the eentities to save incrementally. That way, when you run into a problem, you can continue saving from where you stopped. Sometimes you have too many stories. It's best to process them in batches. Or how best to deal with this?]
[It's usually best to use closed models: why?]
[after generating entities, you might want to study it to see what your extracted vallues look like. SQLite database is a good way to do that because?]
First you laod your json file into a sqlite database using this command: 
`uv run sqlite-utils insert entities.db stories your_json_file_name --pk docref`

Replace your_json_file_name with the name of the json file where you have the entities. The command above converts your json file into a database table that lives in entities.db. Now you can filter, analyze the data using datasette.
What is datasette? Datasette is [ ??]
To view your document on datasette you first have to install it in your environment: 
`uv add datasette`
You know you added it correctly when your output says: "Installed 15 packages in 58ms" and goes ahead to list the packages installed.
Then you can run this to view your data in Datasette:
`uv run datasette entities.db`
