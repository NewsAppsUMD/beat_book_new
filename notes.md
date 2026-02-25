## From news archives to beatbook

### 1) Prerequisites
- Story samples in a JSON file
- GitHub account
- Access to a terminal/Codespace

### 2) Quick Setup for Beginners
- Create a GitHub repository:
  Go to github.com -> Log into your account
	- Click the + icon in the top-right, choose New repository.
	- Name it, set Public or Private, then click Create repository.

- Open Codespace or local terminal in project folder
  - Click Code -> Codespaces -> Create codespace.
	- We'll work locally, so open a terminal in your project folder. [explain this like they have never used a terminal, explain parts of the terminal. keep it concise but detailed. Let the user know how to install copilot]
- Install `uv`:
  Run: `pip install uv`
- Initialize your project (optional but helpful):
	- Run: uv init --python 3.12)

- Install `llm` and model plugins (Groq, Gemini, Anthropic, etc.)
  Plugins are tools you add into bigger apps that help perform new functions. Think Chrome extension and how it helps give Chrome extra features.
  - Run: `uv add llm install llm-groq` (Here, you can include other models in addition to groq: llm-gemini, llm-anthropic, especially if you have access to their API keys).
  - For this presentation, we'll work with groq.
- Get a Groq API key:
	- Go to https://console.groq.com
	- Create an account and an API key (click on Create API at the top right corner when you log in to Groq).
  - To set up your Groq API key which should help you access the models, run: uv run llm keys set groq. You'll be prompted to enter your API keys. Bear in mind that you wont see the key, but when you click 'enter/return' it should work.
- Set API key (`uv run llm keys set groq`)
Now you are ready to use open source models on your local computers.

### 3) First: Extract Metadata!
# Step 1
- The first step to taking our archives from json file to beatbook is to extract metadata. Metadata is simply data about the stories we have. This step is crucial because: we do not want to dump all of our sensitive data into commercial models. We also want to reduce the number of tokens we use to generate our beatbook.
- The open models we use for this task allow us use llms locally on our computers. So we are able to download the weights (or brains) of the models onto our devices and use them like we would use Word or Excel.
(Include how to access their APIs?)
- To extract metadata, we need a python script, and this is where copilot comes in. Go into the copilot chat box by the right side of your screen, and craft a prompt asking it to generate a Python script that extracts metadata from your original json file. Your prompt must be detailed, and put into perspective the kind of beatbook you'd like to create.
 For instance, consider prompting copilot to create a beatbook that looks at the following, if your aim is to generate a thematic beatbook that looks at how occurrences have changed over time:
- Key field groups: 
  - **Temporal:** names, season, year, is_weekend
  - **Content classification:** primary/secondary themes, incident type, severity
  - **Geographic:** location, location type
  - **Contextual:** incident time, weather, agencies, outcomes.
- For a narrative beatbook, key field groups:
  - **People:** names,title
  - **Places:** Maryland, Talbot, St Michael's
- Regardless of the type of beatbook, you want to keep quotes and replace full story content with summaries in output. We want to generate metadata from our json file directly on our devices without pushing it to the internet. So our json files are not exposed, and we have extracted summaries of our stories, which can now serve as the raw materials for our beatbook.
- Remember that your prompt should exclude bylines, photographer names, and name of news organization.

# PRO TIP: When unsure about what prompts/directions to give your AI tool, ask AI!
# [SAMPLE PROMPT: I'd like to generate metadata from articles that will help me create a beat book that looks at public safety issues thematically over time. For example, common issues that occur in the summer vs. the winter. What would the structure of that metadata need to look like?]

In response to your prompt, copilot will generate the script and save it in your directory, in a file that will end in .py (since it is a python script). While the script will mostly not be easy to understand given that it is written in code, you need to look over it and read through the prompts contained in the script, which, more likely than not, will be written in plain text within the script. Check for things that might not align with your intial intention for the beatbook; a step you should not skip, given AI's affinity for halluciantions.

# Step 2
Now that the script for the extraction is ready, run this command in the terminal to carry out the extraction:
```bash
uv run python metadata.py --model YOUR MODEL --input story_sample.json
```
In the command above, metadata.py will be replaced with the name of the script copilot generated for you. 'YOUR MODEL' should be replaced with whatever AI open source model you will be using for your extraction.
- NOTE: it is very important to use OPEN SOURCE MODELS here. This is the part of beatbook generation that requires extra care and attention. You want to be conscious so that you are not running this prompt with a commercial model.
NOTE ALSO: earlier, we installed Groq llm. If you are unsure what open source model to use, run:
`uv run llm models`

You will get results in your terminal similar to this:
 
LLMGroq: groq/groq/compound-mini
LLMGroqWhisper: groq/whisper-large-v3
LLMGroq: groq/qwen/qwen3-32b
LLMGroq: groq/llama-3.1-8b-instant (aliases: groq-llama3.1-8b)
LLMGroq: groq/meta-llama/llama-4-scout-17b-16e-instruct
LLMGroq: groq/canopylabs/orpheus-arabic-saudi
LLMGroq: groq/moonshotai/kimi-k2-instruct-0905
LLMGroq: groq/groq/compound
LLMGroq: groq/openai/gpt-oss-120b
LLMGroq: groq/openai/gpt-oss-safeguard-20b
[substitutee list above with screenshot]

Any of the models that show up should be fine to run the extraction with. So if you choose to use `groq/qwen/qwen3-32b` and your python script and json file are called metada,py and story_sample.json like mine is in the example above, you should run this command in the terminal: 

`uv run python metadata.py --model groq/qwen/qwen3-32b --input story_sample.json`

# Possible problems with extraction
Although it sounds quite straight forward, many things can go wrong with extraction, and you should not be surprised if you run into errors while carrying out your extraction.
One common reason why you might get an error with this process is rate limits. Rate limits are limits on how many API requests you can make at a given time to the AI model. So if you are working with hundreds of stories you are making hundreds of calls to the AI model. You are likely to run into limits at some point, escpecially if you are using free open source models.
[Image of rate limits error]
When you run into rate limits, the metadata already extracted can be lost.
You can fix rate limits by going again to our friend copilot and asking it to modify your script so that it saves output incrementally. So what happens here is that as your python script extracts the metadata. it saves it directly to a new document. Whenever you encounter rate limits, you can move on immediately to a new miodel. The new model continues from where the older model stopped, instead of starting afresh. So say use used this model: `groq/qwen/qwen3-32b`  and extracted 80 stories out of 500 before reaching your rate limits, you can switch to `groq/meta-llama/llama-4-scout-17b-16e-instruct` simply by interrupting the error messages you are receiving using Cntrl/Cmd + C
The you rerun this command with your new model: `uv run python metadata.py --model groq/meta-llama/llama-4-scout-17b-16e-instruct --input story_sample.json`
Replace your model as many times as possible to complete the process, if using free open source models.
This step is critical to the outcome of your beatbook, because it replaces the raw materials i.e. the story archives, and serves as the bases upon which we build our beatbook. Consider spending enough time here and not rushing through the process. You should also repeat the process if you notice that something seems off during verification, as it most likely will.

### 4) Verification
We are still working with llms, even if locally and one thing to always do, is verify. Now you have your metadata in a json file. You might want to go through the json file to ensure that names, organizaions, everything extracted were actually extracted from the stories you fed into the llm, rather than manufactured from thin air by your llm. A smooth way to look through your metadata is loading the json file into a simple tool: Datasette. Datasette is a tool that allows you load your unstructued data into a database and view it in structured format.[###Get_better_desc_from_Derek]
[Image of Datasette]
To view your metadata in Datasette, first push your metadata into the tool using this bash: 
```bash
uv run sqlite-utils insert entities.db stories your_json_file_name --pk docref
```
To view your document on datasette you first have to install it in your environment: 
`uv add datasette`
You know you added it correctly when your output says: "Installed 15 packages in 58ms" and goes ahead to list the packages installed.
Then you can run this to view your data in Datasette:
`uv run datasette entities.db`
What the command above does is take you to Datasette on you browser. Running this command prompts a pop up that asks you if you want to open datasette in a browser. If, somehow, you miss the pop up or close it, you can access datasette by clicking on 'PORTS' locted at the top of your terminal. You should look for Port 8001, and you know this is what you are looking for because in your terminal, the last line there says: Uvicorn running on http://127.0.0.1:8001
The last four figures there tells you what port to look for.
CLick on the link. A globe icon pops up by the side. Click on that and look through your data. Your data is linked to "stories" under entities [we know this how?]
Looking at your work in datasette lets you see how well your extraction worked. It also helps you with factchecking: are there false names in the extracted data? You are able to compare the extractions with the summary you have. You also get to see how many cases your llm failed to parse or extract your data, which gives a sense of how reliable the data is.

- Use Datasette to:
  - Inspect extraction quality
  - Check false positives/failed parses
  - Compare extracted fields against summaries and actual stories.
Notice something off? Now is the time to repeat the metadata extraction process until metadata quality is acceptable.

### 6) Generate the Beatbook
This is another iterative process similar to the process for metadata extraction, only, this time, you are not really dealing with sensitive materials (your main stories data/archives) and can use commercial models for parts of this process.
To create a beatbook out of the metadata you have, you need a second python script. Prompt copilot to create that.
You should be very specific in writing the prompt for this script. The type of beatbook you hope to create should come to bear on your prompt.
Sample prompt:
Create a script that will:
Produce a narrative, reporter-friendly beatbook leveraging on pre-extracted data in metadata_stories.json (assuming this is where you saved your metadata).
Rely on the summaries in the document, rather than calling the the stories afresh.
Have a business casual tone. Write like you're briefing a colleague, not writing an academic paper.
Short, approachable introduction .
Include potential follow up stories with a disclaimer that data may be outdated.
MOST IMPORTANTLY, LOOKS AT PUBLIC SAFETY ISSUES THEMATICALLY OVER TIME. FOR EXAMPLE, COMMON ISSUES THAT HAPPEN IN THE SUMMER VS. WINTER. I  do not want the beat book to be strictly limited to seasons. What are trends in the story over time? Seasonal issues are only an example, and if there are seasonal trends, include them. But how has coverage of the stories and incidents in the coverage area evolved over time?
When the beatbook generator script is ready, use that to create the first draft of your beatbook by running the bash below:
```bash
uv run python generate_beatbook.py --model "anthropic/claude-sonnet-4-" --input metadata_stories.json --output my_narrative_beatbook_v2.md
```
In the bash above, `generate_beatbook.py` represents the second python script copilot produced and you should replace that what whatever you have named your script.
`"anthropic/claude-sonnet-4-"` refers to whatever model you decide to use for your beatbook.
`metadata_stories.json` refers to the json file containing your metadata.
`my_narrative_beatbook_v2.md` refers to whatever you would like to save your beatbook as.
As with metadata generation, consider refining your beatbook until you get a sophisticated copy. Read through to ensure that the information included is accurate and always remember to cross-check this with your raw data.

Other things you may include in refining the beatbook:
- Display contact ninformation of courses if mentioned (like a cource directory))
- Include follow-up story ideas + disclaimer that data may be outdated.
- Whatever else comes to mind as you refine.

### 7) Expore other formats
After you have generated a beatbook that's good enough, you may consider displaying it in a format different from just text.
Assuming you generated a beatbook that looks at stories contained in the archives to show how things have changed with a newsroom's coverage over time, you can decided to reproduce this as a timeline even if you are not familiar with using [#timeline_tool]
To convert a thematic beatbook into a timeline, you might need a final python script and you certainly need copilot. Write a prompt to copilot asking it to reformat your beatbook into a timeline. Or a mind map. Or a html page. When copilot is done, it presents your beatbook in a new format as a server and you see the pop up at the lower right side of your screen. Click on the pop up or follow the same steps as we did when viewing Datasette in "PORTS."