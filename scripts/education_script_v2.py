import json
import subprocess
import sys
from pathlib import Path
from subprocess import TimeoutExpired

# Load content_type_list and maryland_counties_list from this script (copy-paste or import as needed)
content_type_list = [
    {
        "content_type": "News",
        "definition": "Full articles, excluding calendars, obituaries, legal notices, opinion pieces and other listings, meant to inform, not persuade, readers on news topics such as politics, elections, government, agriculture, education, housing, economy and budget, transportation, infrastructure, public works, public safety, crime, environment, arts, society, community and sports.",
        "examples": "Police investigating Easton homicide; Robbins YMCA opening reading hub to tackle childhood illiteracy"
    },
    {
        "content_type": "Calendars",
        "definition": "Calendars.",
        "examples": "Mid-Shore Calendar; RELIGION CALENDAR"
    },
    {
        "content_type": "Obituaries",
        "definition": "Obituaries.",
        "examples": "Rhonda Lynn Fearins Thomas; Mary Beth Adams"
    },
    {
        "content_type": "Legal Notices",
        "definition": "Legal notices.",
        "examples": "Legal Notices"
    },
    {
        "content_type": "Opinion",
        "definition": "Columns, editorials, letters to the editor and any other opinion-based pieces for which the primary purpose is to persuade, not necessarily inform, readers.",
        "examples": "Biden must go; EDITORIAL: 10-cent paper bag fee should be optional"
    },
    {
        "content_type": "Miscellaneous",
        "definition": "TV listings, Today in History articles and other non-news and non-opinion content.",
        "examples": "SPRING TRAINING GLANCE 3-10-24; TV LISTINGS 1-11-24; TODAY IN HISTORY/Aug. 4; Web links; Tonight's top picks"
    }
]

maryland_county_list = [
    {"county": "Dorchester County", "municipalities": "Brookview, Cambridge, Church Creek, Crapo, Crocheron, East New Market, Eldorado, Fishing Creek, Galestown, Hurlock, Linkwood, Madison, Rhodesdale, Secretary, Taylors Island, Toddville, Vienna, Wingate, Woolford"},
    {"county": "Caroline County", "municipalities": "Denton, Federalsburg, Goldsboro, Greensboro, Henderson, Hillsboro, Marydel, Preston, Ridgely, Templeville, Choptank, West Denton, Williston, American Corner, Andersontown, Baltimore Corner, Bethlehem, Brick Wall Landing, Burrsville, Gilpin Point, Harmony, Hickman, Hobbs, Jumptown, Linchester, Oakland, Oil City, Tanyard, Two Johns, Reliance, Whiteleysburg"},
    {"county": "Kent County", "municipalities": "Betterton, Chestertown, Galena, Millington, Rock Hall, Butlertown, Chesapeake Landing, Edesville, Fairlee, Georgetown, Kennedyville, Still Pond, Tolchester, Worton, Chesterville, Golts, Hassengers Corner, Langford, Lynch, Massey, Pomona, Sassafras, Sharpstown, Tolchester Beach"},
    {"county": "Queen Anne's County", "municipalities": "Barclay, Centreville, Church Hill, Millington, Queen Anne, Queenstown, Sudlersville, Templeville, Chester, Grasonville, Kent Narrows, Kingstown, Romancoke, Stevensville, Crumpton, Dominion, Ingleside, Love Point, Matapeake, Price, Ruthsburg"},
    {"county": "Talbot County", "municipalities": "Easton, Oxford, Queen Anne, Saint Michaels, Trappe, Cordova, Tilghman Island, Anchorage, Bellevue, Bozman, Claiborne, Copperville, Doncaster, Fairbanks, Lewistown, Lloyd Landing, Matthews, McDaniel, Neavitt, Newcomb, Royal Oak, Sherwood, Tunis Mills, Unionville, Wittman, Windy Hill, Woodland, Wye Mills, Dover, York, Wyetown"},
    {"county": "Prince George's County", "municipalities": "Bowie, College Park, District Heights, Glenarden, Greenbelt, Hyattsville, Laurel, Mount Rainier, New Carrollton, Seat Pleasant, Berwyn Heights, Bladensburg, Brentwood, Capitol Heights, Cheverly, Colmar Manor, Cottage City, Eagle Harbor, Edmonston, Fairmount Heights, Forest Heights, Landover Hills, Morningside, North Brentwood, Riverdale Park, University Park, Upper Marlboro"},
    {"county": "Calvert County", "municipalities": "Adelina, Barstow, Bowens, Chaneyville, Dares Beach, Dowell, Johnstown, Lower Marlboro, Mutual, Parran, Pleasant Valley, Port Republic, Scientists Cliffs, Stoakley, Sunderland, Wallville, Wilson, Chesapeake Beach, North Beach, Broomes Island, Calvert Beach, Chesapeake Ranch Estates, Drum Point, Dunkirk, Huntingtown, Long Beach, Lusby, Owings, Prince Frederick, St. Leonard, Solomons"},
    {"county": "Anne Arundel County", "municipalities": "Annapolis, Highland Beach, Annapolis Neck, Arden on the Severn, Arnold, Brooklyn Park, Cape Saint Claire, Crofton, Crownsville, Deale, Edgewater, Ferndale, Fort Meade, Friendship, Galesville, Gambrills, Glen Burnie, Herald Harbor, Jessup, Lake Shore, Linthicum, Maryland City, Mayo, Naval Academy, Odenton, Parole, Pasadena, Riva, Riviera Beach, Selby-on-the-Bay, Severn, Severna Park, Shady Side, Beverly Beach, Bristol, Chestnut Hill Cove, Churchton, Davidsonville, Fairhaven, Germantown, Gibson Island, Green Haven, Hanover, Harmans, Harundale, Harwood, Hillsmere Shores, Jacobsville, Londontowne, Lothian, Millersville, Orchard Beach, Owensville, Pumphrey, Riverdale, Rose Haven, Russett, Sherwood Forest, South Gate, Sudley, Tracys Landing, Waysons Corner, West River, Winchester-on-the-Severn, Woodland Beach"},
    {"county": "Baltimore County", "municipalities": "Arbutus, Baltimore Highlands, Bowleys Quarters, Carney, Catonsville, Cockeysville, Dundalk, Edgemere, Essex, Garrison, Hampton, Honeygo, Kingsville, Lansdowne, Lochearn, Lutherville, Mays Chapel, Middle River, Milford Mill, Overlea, Owings Mills, Parkville, Perry Hall, Pikesville, Randallstown, Reisterstown, Rosedale, Rossville, Timonium, Towson, White Marsh, Woodlawn, Baldwin, Boring, Bradshaw, Brooklandville, Butler, Chase, Fork, Fort Howard, Germantown, Glen Arm, Glencoe, Glyndon, Halethorpe, Hereford, Hunt Valley, Hydes, Jacksonville, Long Green, Maryland Line, Monkton, Nottingham, Oella, Parkton, Phoenix, Ruxton, Sparks, Sparrows Point, Stevenson, Trump, Turners Station, Upper Falls, Upperco, White Hall"},
    {"county": "Baltimore City", "municipalities": "Baltimore City"},
    {"county": "Howard County", "municipalities": "Columbia, Elkridge, Ellicott City, Fulton, Highland, Ilchester, Jessup, Lisbon, North Laurel, Savage, Scaggsville, Clarksville, Cooksville, Daniels, Dayton, Dorsey, Glenelg, Glenwood, Granite, Guilford, Hanover, Isaacsville, Marriottsville, Simpsonville, West Friendship, Woodbine, Woodstock"},
    {"county": "Carroll County", "municipalities": "Westminster, Taneytown, Manchester, Mount Airy, New Windsor, Union Bridge, Hampstead, Sykesville, Eldersburg, Alesia, Carrollton, Carrolltowne, Detour, Finksburg, Frizzelburg, Gamber, Gaither, Greenmount, Harney, Henryton, Jasontown, Keymar, Lineboro, Linwood, Marriottsville, Mayberry, Middleburg, Millers, Patapsco, Pleasant Valley, Silver Run, Union Mills, Uniontown, Woodbine, Woodstock"},
    {"county": "Montgomery County", "municipalities": "Gaithersburg, Rockville, Takoma Park, Barnesville, Brookeville, Chevy Chase, Chevy Chase View, Chevy Chase Village, Garrett Park, Glen Echo, Kensington, Laytonsville, Poolesville, Somerset, Washington Grove, Martin's Additions, North Chevy Chase, Drummond, Oakmont"},
    {"county": "Frederick County", "municipalities": "Brunswick, Frederick, Burkittsville, Emmitsburg, Middletown, Mount Airy, Myersville, New Market, Thurmont, Walkersville, Woodsboro, Rosemont, Adamstown, Ballenger Creek, Bartonsville, Braddock Heights, Buckeystown, Graceham, Green Valley, Jefferson, Lewistown, Libertytown, Linganore, Monrovia, Point of Rocks, Sabillasville, Spring Ridge, Urbana, Charlesville, Clover Hill, Creagerstown, Discovery, Garfield, Ijamsville, Knoxville, Ladiesburg, Lake Linganore, Linganore, Mountaindale, Mount Pleasant, New Midway, Petersville, Rocky Ridge, Spring Garden, Sunny Side, Tuscarora, Unionville, Utica, Wolfsville"},
    {"county": "St. Mary's County", "municipalities": "Leonardtown, California, Callaway, Charlotte Hall, Golden Beach, Lexington Park, Mechanicsville, Piney Point, St. George Island, Tall Timbers, Wildewood, Abell, Avenue, Beachville-St. Inigoes, Beauvue, Bushwood, Chaptico, Clements, Coltons Point, Compton, Dameron, Drayden, Great Mills, Helen, Hollywood, Hopewell, Huntersville, Hurry, Loveville, Maddox, Morganza, Oakley, Oakville, Oraville, Park Hall, Ridge, St. Inigoes, St. Mary's City, Scotland, Spencers Wharf, Valley Lee"},
    {"county": "Charles County", "municipalities": "Indian Head, La Plata, Port Tobacco Village, Benedict, Bensville, Bryans Road, Bryantown, Charlotte Hall, Cobb Island, Hughesville, Pomfret, Potomac Heights, Rock Point, Waldorf, Bel Alton, Dentsville, Faulkner, Glymont, Grayton, Ironsides, Issue, Malcolm, Marbury, Morgantown, Mount Victoria, Nanjemoy, Newburg, Pisgah, Popes Creek, Port Tobacco, Pomonkey, Ripley, Rison, Saint Charles, Swan Point, Welcome, White Plains"},
    {"county": "Washington County", "municipalities": "Hagerstown, Boonsboro, Clear Spring, Funkstown, Hancock, Keedysville, Sharpsburg, Smithsburg, Williamsport, Antietam, Bagtown, Bakersville, Beaver Creek, Big Pool, Big Spring, Breathedsville, Brownsville, Cavetown, Cearfoss, Charlton, Chewsville, Dargan, Downsville, Eakles Mill, Edgemont, Ernstville, Fairplay, Fairview, Fort Ritchie, Fountainhead-Orchard Hills, Gapland, Garretts Mill, Greensburg, Halfway, Highfield-Cascade, Indian Springs, Jugtown, Kemps Mill, Leitersburg, Mapleville, Maugansville, Mercersville, Middleburg, Mount Aetna, Mount Briar, Mount Lena, Paramount-Long Meadow, Pecktonville, Pinesburg, Pondsville, Reid, Ringgold, Robinwood, Rohrersville, Saint James, San Mar, Sandy Hook, Tilghmanton, Trego-Rohrersville Station, Wilson-Conococheague, Yarrowsburg, Appletown, Benevola, Broadfording, Burtner, Huyett, Pen Mar, Samples Manor, Spielman, Trego, Van Lear, Weverton, Woodmont, Zittlestown"},
    {"county": "Somerset County", "municipalities": "Crisfield, Princess Anne, Chance, Dames Quarter, Deal Island, Eden, Fairmount, Frenchtown-Rumbly, Mount Vernon, Smith Island, West Pocomoke, Ewell, Kingston, Manokin, Marion Station, Oriole, Rehobeth, Rhodes Point, Shelltown, Tylerton, Upper Fairmount, Upper Falls, Wenona, Westover"},
    {"county": "Allegany County", "municipalities": "Cumberland, Frostburg, Barton, Lonaconing, Luke, Midland, Westernport, Bel Air, Bowling Green, Cresaptown, Ellerslie, LaVale, McCoole, Mount Savage, Potomac Park, Barrelville, Bier, Borden Shaft, Bowmans Addition, Carlos, Clarysville, Corriganville, Danville, Dawson, Detmold, Eckhart Mines, Flintstone, Franklin, Gilmore, Grahamtown, Klondike, Little Orleans, Midlothian, Moscow, National, Nikep, Ocean, Oldtown, Pleasant Grove, Rawlings, Shaft, Spring Gap, Vale Summit, Woodland, Zihlman, Amcelle, Dickens, Evitts Creek, George's Creek, Loartown, McKenzie, Narrows Park, Pinto, Town Creek"},
    {"county": "Cecil County", "municipalities": "Cecilton, Charlestown, Chesapeake City, Elkton, North East, Perryville, Port Deposit, Rising Sun, Appleton, Bay View, Blue Ball Village, Calvert, Carpenter Point, Cherry Hill, Childs, Colora, Conowingo, Crystal Beach, Earleville, Elk Mills, Elk Neck, Fair Hill, Fredericktown, Frenchtown, Hack's Point, Harrisville, Hopewell Manor, Liberty Grove, Oakwood, Perry Point, Providence, Red Point, St. Augustine, Warwick, Westminister, White Crystal Beach, White Hall, Zion"},
    {"county": "Worcester County", "municipalities": "Pocomoke City, Berlin, Ocean City, Snow Hill, Bishopville, Girdletree, Newark, Ocean Pines, Stockton, West Ocean City, Whaleyville, Boxiron, Cedartown, Friendship, Germantown, Goodwill, Ironshire, Klej Grange, Nassawango Hills, Public Landing, Showell, Sinepuxent, South Point, Taylorville, Whiton"},
    {"county": "Wicomico County", "municipalities": "Fruitland, Salisbury, Delmar, Hebron, Mardela Springs, Pittsville, Sharptown, Willards, Allen, Bivalve, Jesterville, Nanticoke, Nanticoke Acres, Parsonsburg, Powellville, Quantico, Tyaskin, Waterview, Whitehaven, Doe Run, Silver Run, Wetipquin, Whiton"},
    {"county": "Garrett County", "municipalities": "Accident, Deer Park, Friendsville, Grantsville, Kitzmiller, Loch Lynn Heights, Mountain Lake Park, Oakland, Bloomington, Crellin, Finzel, Gorman, Hutton, Jennings, Swanton, Altamont, Asher Glade, Avilton, Bethel, Bevansville, Bittinger, Blooming Rose, Casselman, Cove, East Vindex, Elder Hill, Engle Mill, Fairview, Floyd, Fort Pendleton, Foxtown, Fricks Crossing, Gortner, Gravel Hill, Green Glade, Hazelhurst, Herrington Manor, Hi-Point, High Point, Hoyes, Hoyes Run, Kaese Mill, Kearney, Keeler Glade, Kempton, Kendall, Keysers Ridge, Lake Ford, Locust Grove, McComas Beach, McHenry, Merrill, Mineral Spring, Mitchell Manor, New Germany, North Glade, Piney Grove, Redhouse, Ryan's Glade, Sand Spring, Sang Run, Schell, Selbysport, Shallmar, Standard, Stanton Mill, Steyer, Strawn, Strecker, Sunnyside, Table Rock, Tasker Corners, Thayerville, Wallman, West Vindex, Wilson, Winding Ridge"},
    {"county": "Harford County", "municipalities": "Aberdeen, Havre de Grace, Bel Air, Aldino, Benson, Berkley, Cardiff, Castleton, Churchville, Clayton, Constant Friendship, Creswell, Dublin, Darlington, Emmorton, Fairview, Forest Hill, Fountain Green, Glenwood, Hess, Hickory, Hopewell Village, Joppa, Kalmia, Level, Madonna, Norrisville, Shawsville, Street, Taylor, Whiteford, Aberdeen Proving Ground, Abingdon, Bel Air North, Bel Air South, Darlington, Edgewood, Fallston, Jarrettsville, Joppatowne, Perryman, Pleasant Hills, Pylesville, Riverside, Glenville"}
]

INPUT_FILE = "education_stories_merged.json"
OUTPUT_FILE = "education_stories_with_entities_v2.json"
LLM_MODEL = "groq/meta-llama/llama-4-maverick-17b-128e-instruct"

# Helper to call LLM

def call_llm(prompt, story_json):
    # Combine the prompt and story into a single prompt
    full_prompt = f"{prompt}\n\nStory to process:\n{json.dumps(story_json, indent=2)}"
    
    try:
        result = subprocess.run(
            ["llm", "-m", LLM_MODEL],
            input=full_prompt.encode(),
            capture_output=True,
            check=True,
            timeout=120
        )
        
        # Parse the JSON response
        response_text = result.stdout.decode()
        
        # Try to extract JSON from the response (in case there's extra text)
        # Look for JSON object starting with { and ending with }
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            json_str = response_text[start_idx:end_idx+1]
            return json.loads(json_str)
        else:
            print(f"No JSON found in response", file=sys.stderr)
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"LLM call failed: {e.stderr.decode()}", file=sys.stderr)
        return None
    except subprocess.TimeoutExpired:
        print(f"LLM call timed out", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}", file=sys.stderr)
        print(f"Response was: {response_text[:200]}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return None

def save_progress(updated_stories, output_file):
    """Save progress to output file"""
    with open(output_file, "w") as f:
        json.dump(updated_stories, f, indent=2)
    print(f"💾 Saved progress: {len(updated_stories)} stories to {output_file}")



def main():
    import argparse
    parser = argparse.ArgumentParser(description='Process education stories to add entity fields (v2).')
    parser.add_argument('--limit', type=int, help='Limit the number of stories to process (testing)')
    parser.add_argument('--batch-size', type=int, default=10, help='Number of stories per batch (default: 10)')
    parser.add_argument('--single-batch', action='store_true', help='Only process one batch then exit')
    parser.add_argument('--dry-run', action='store_true', help='Skip LLM calls; just copy stories forward for testing')
    parser.add_argument('--continuous', action='store_true', help='Process all remaining stories in batches automatically')
    args = parser.parse_args()
    
    if not Path(INPUT_FILE).exists():
        print(f"Input file {INPUT_FILE} not found.", file=sys.stderr)
        sys.exit(1)
    
    # Load existing progress if output file exists
    if Path(OUTPUT_FILE).exists():
        print(f"Found existing output file {OUTPUT_FILE}, loading progress...")
        with open(OUTPUT_FILE, "r") as f:
            updated_stories = json.load(f)
        # Count how many stories actually have the new fields
        processed_count = sum(1 for s in updated_stories if "content_type" in s)
        print(f"Found {len(updated_stories)} stories in output file, {processed_count} have new fields")
        # Keep only the processed stories
        updated_stories = updated_stories[:processed_count]
        print(f"Resuming from story {len(updated_stories) + 1}")
    else:
        updated_stories = []
    
    with open(INPUT_FILE, "r") as f:
        stories = json.load(f)
    
    # Apply limit if specified (for testing)
    if args.limit:
        stories = stories[:args.limit]
        print(f"Limiting to {args.limit} stories")
    
    # Skip already processed stories / resume
    start_idx = len(updated_stories)
    remaining_total = len(stories) - start_idx
    if remaining_total <= 0:
        print("Nothing left to process.")
        save_progress(updated_stories, OUTPUT_FILE)
        print(f"✅ ALL DONE! Processed all {len(updated_stories)} stories")
        return

    batch_size = args.batch_size
    batch_num = 1
    from time import perf_counter
    
    if args.continuous:
        print(f"🚀 CONTINUOUS MODE: Processing all {remaining_total} remaining stories in batches of {batch_size}")
    else:
        print(f"🚀 Starting batch at story {start_idx+1}. Remaining: {remaining_total}. This batch size: {batch_size}")

    # Loop over batches
    while start_idx < len(stories):
        stories_to_process = stories[start_idx : start_idx + batch_size]
        if not stories_to_process:
            break
            
        print(f"\n🔄 Batch {batch_num}: Processing {len(stories_to_process)} stories (stories {start_idx + 1}-{start_idx + len(stories_to_process)})")
        
        for idx, story in enumerate(stories_to_process):
            actual_idx = start_idx + idx
            print(f"\n[{idx+1}/{len(stories_to_process)}] Processing story {actual_idx+1}/{len(stories)}: {story.get('title', '')[:60]}")
            story_start = perf_counter()
            
            prompt = f"""
You are an expert news data annotator specializing in EDUCATION stories. Analyze the story and return a JSON object with ALL the original story fields plus these NEW fields.

CRITICAL: ALL entities must be EXPLICITLY education-related. This is an education beat book.

NEW FIELDS TO ADD:
- content_type: single best from: {json.dumps([ct["content_type"] for ct in content_type_list])}
- regions: array of general regions (Maryland, Virginia, D.C., or other country/state/region; 'U.S.' for national)
- municipalities: array of Maryland municipalities mentioned or central to story
- counties: array of Maryland counties where those municipalities are located. ALWAYS include "County" in the name (e.g., "Talbot County", "Caroline County", not just "Talbot" or "Caroline")
- key_people: array of ALL public officials, politicians, board members, council members, superintendents, principals, teachers, education officials, etc. Format MUST be: "Name — Title, Organization/Body/Institution" (use em dash —, not hyphen). Examples: "John Smith — Superintendent, Talbot County Public Schools", "Jane Doe — President, Talbot County Board of Education", "Robert Johnson — Principal, Easton High School". STANDARDIZE all names (consistent capitalization), titles, and organizations. If a person appears in the known people list below, use their EXACT format.
- key_events: array of EDUCATION-RELATED events. ONLY include: named, recurring or significant education events. Examples: "Back to School Resource Fair", "Chrome City Ride", "Kent County Fair" (if it's a 4-H/education event). DO NOT include: generic ceremonies (ribbon-cuttings, grand openings, dedications), board meetings, or general community events unless they are major education-focused events with a specific name.
- key_initiatives: array of SPECIFIC NAMED education initiatives/legislation/policies with proper names. ONLY include actual named initiatives. Examples: "Blueprint for Maryland's Future", "No Child Left Behind Act". DO NOT include: general course types (e.g., "Career and Technical Education", "Advanced Placement"), general programs, curriculum types, or activities mentioned in passing. Must be an actual initiative with a specific name.
- key_establishments: array of EDUCATION-RELATED establishments in Maryland. ONLY include: Maryland schools, colleges, universities, education centers, tutoring centers that are central to the story. Examples: "Easton High School", "Talbot County Public Schools", "Chesapeake College". DO NOT include: out-of-state universities mentioned only in people's backgrounds, general businesses, restaurants, stores, or companies that provide services to schools.
- key_organizations: array of EDUCATION-RELATED organizations AND government bodies. ONLY include: education nonprofits, parent-teacher organizations, educational advocacy groups, school foundations, major 4-H organizations, school boards, boards of education, school districts, departments of education, education committees. Examples: "Talbot County Board of Education", "National 4-H Council", "Parent Teacher Association", "Maryland State Department of Education". Standardize "4-H" (not "4H" or variations). DO NOT include: individual local 4-H clubs mentioned only as historical background, general nonprofits or community organizations unless they have an explicit education mission central to the story. DO NOT include district numbers or subdivisions - only the main body name (e.g., "Talbot County Board of Education", not "Talbot County Board of Education District 5"). Avoid duplicates and variations of the same body.

KEY_PEOPLE EXTRACTION RULES:
1. Extract ALL public officials, politicians, board members, council members, superintendents, principals, teachers, education board members, school officials, college/university administrators, education program directors
2. Use the EXACT standardized format: "Name — Title, Organization/Body/Institution"
3. STANDARDIZE all elements: consistent name capitalization, standardized titles, standardized organization names
4. Use em dash (—) not hyphen (-) between name and title
5. CRITICAL: When a person is mentioned with incomplete information (e.g., "board member" without specifying which board, or "superintendent" without the district name), you MUST use context clues from the story to determine the full title and organization. Look at the story's location, topic, and surrounding context to infer the correct board/organization. For example, if the story is about Talbot County schools and mentions "board member John Smith", infer this refers to the "Talbot County Board of Education".

RULES:
- Use title case when original is capitalized
- NEVER include 'Star-Democrat', 'Chesapeake Publishing Group', or 'Adams Publishing/APGMedia'
- Leave arrays empty [] if no education-related items exist
- State legislature = 'Maryland General Assembly'
- When in doubt about non-people entities, EXCLUDE - only include if it's clearly education-related
- For key_people, be INCLUSIVE - extract all public officials and education-related people
- Return ONLY valid JSON with all original fields plus new fields"""
            
            if args.dry_run:
                updated_stories.append(story)
            else:
                print("  ⏳ Calling LLM...", end="", flush=True)
                llm_result = call_llm(prompt, story)
                elapsed = perf_counter() - story_start
                if llm_result:
                    print(f" ✓ Done in {elapsed:.1f}s")
                    updated_stories.append(llm_result)
                else:
                    print(f" ✗ Failed after {elapsed:.1f}s", file=sys.stderr)
                    updated_stories.append(story)

        # Save after each batch
        save_progress(updated_stories, OUTPUT_FILE)
        remaining = len(stories) - len(updated_stories)
        
        if remaining <= 0:
            print(f"\n✅ ALL DONE! Processed all {len(updated_stories)} stories")
            break
        else:
            est_batches = (remaining + batch_size - 1) // batch_size
            print(f"📊 Batch {batch_num} complete. Progress: {len(updated_stories)}/{len(stories)}. Remaining: {remaining} (~{est_batches} more batches)")
            
        if args.single_batch:
            print(f"⏹ Single batch mode: stopping. Run again to continue.")
            break
            
        # Move to next batch
        start_idx += len(stories_to_process)
        batch_num += 1

if __name__ == "__main__":
    main()
