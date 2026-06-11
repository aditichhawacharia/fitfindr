# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
Search_listings looks through the json file of listings and returns 3 matches sorted by relevance based on the user. Using search_listings, it essentially based on the clothing the user is looking for, search_listings will pick the top
3 matches to what the user wants. 

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
     description: str -  describes the clothing they are looking for gives more information of it
     size: str - the size preference on whether it's small, medium, or large
     max_price: float -  this is the max amount/cost of the item they'd pay

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
it returns a list of listing dictionaries.

- 'id' (str): this is to basically give each item a unique id for reference
- 'title' (str): this is to basically name the product and give a name for it like a product NAME
- 'description' (str): describes the clothing and gives more information of it
- 'category' (str): whether it's a shirt, jeans, skirt, jacket, etc, it gives a category on what type of garment and assigns it
- 'style_tags' (list): list in strings of different style tags/characteristics that suit each garment
- 'size' (str): the size on whether it's small, medium, or large
- 'condition' (str): describes condition of the clothing and the quality
- 'price' (float): this is the total amount/cost of the item 
- 'colors' (list): list of the different colors available
- 'brand' (str): brand of the clothing
- 'platform' (str): where the clothing is offered


**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
If no listings match, the agent tells the user no results were found and suggests adjusting the description, size, or price. It does not proceed to suggest_outfit with empty input.


---

### Tool 2: suggest_outfit

**What it does:**
Given a newly found thrifted item and the user's existing wardrobe, suggests one or more complete outfit combinations that incorporate the new piece. Uses the wardrobe item fields (category, style_tags, colors) to find complementary pairings.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- 'new_item' (dict): the listing dict returned by search_listings: contains fields like title, category, style_tags, colors, size, condition, price, platform
- `wardrobe` (dict): the user's existing wardrobe, each item following wardrobe_schema.json: contains fields like name, category, colors, style_tags

**What it returns:**
A string describing one or more outfit combinations. Example: "Pair the faded band tee with your wide-leg jeans and chunky sneakers for a 90s grunge look. Tuck the front corner slightly for shape."

**What happens if it fails or returns nothing:**
If the wardrobe is empty (get_empty_wardrobe()), the agent still returns a generic styling suggestion based only on the new item's style_tags and category, and notes that no wardrobe items were available to pair with. It does not crash or skip to create_fit_card with empty input.

---

### Tool 3: create_fit_card

**What it does:**
Generates a short, shareable caption for a complete outfit: written in the style of an Instagram or Depop post. Output should sound like a real person captioning a fit, not a product description, and should be different for different inputs.

**Input parameters:**
outfit (str): the outfit suggestion string returned by suggest_outfit
new_item (dict): the listing dict from search_listings, used to pull in specific details like price, platform, and title for the caption

**What it returns:**
A short string (1–3 sentences) written in casual, social-media-style voice. Example: "thrifted this faded band tee off depop for $22 and it was made for my wide-legs 🖤 full look in my stories"

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
1. The agent receives the user's natural language query and extracts description, size, and max_price, then calls search_listings.
2. Check if results is empty. If yes → set an error message ("no listings found, try adjusting your search") in the session and return early. Do not proceed.
3. If results is not empty → set selected_item = results[0] and call suggest_outfit(new_item=selected_item, wardrobe=session["wardrobe"]).
4. Check if suggest_outfit returns an empty or None response. If yes → set an error message ("couldn't generate an outfit suggestion") and return early. Do not proceed to create_fit_card.
5. If suggest_outfit returns a valid string → set session["outfit"] = suggestion and call create_fit_card(outfit=session["outfit"], new_item=selected_item).
6. Check if create_fit_card returns an empty or None response. If yes → return a fallback message to the user noting the fit card couldn't be generated, but still show the outfit suggestion from step 5.
7. If create_fit_card returns a valid caption → display both the outfit suggestion and the fit card to the user. Agent is done.

---

## State Management

**How does information from one tool get passed to the next?**
So we initially have sessions, sessions is a dictionary that has everything the agent NEEDS to know. So this would be the user query, size and max prize of desires, then the results which is what the search listings returned, then the selected item which is results[0] and the top relevant listing which will be passed to suggest outfit, wardrobe which is a list of the user's clothes and it's passed to suggest outfit.  Then "outfit" which is the string of what suggest_outfit returned and then fit card, which is what create_fit_card returned and shown to user. Initially, only query size and amx_price are stored and the rest get filled throughout the program. This is how we do state management.

Through sessions, each tool can read from this dictionary and write back to it.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Tells the user no listings were found and suggests adjusting the description, size, or max price. Sets an error in the session and returns early, does not pass empty results to suggest_outfit. |
| suggest_outfit | Wardrobe is empty | Still returns a generic styling suggestion based only on the new item's style_tags and category. Stores that suggestion in session["outfit"] and proceeds to create_fit_card normally.|
| create_fit_card | Outfit input is missing or incomplete |Returns a fallback caption using whatever fields are available from new_item. Flags to the user that the fit card may be incomplete. Still shows the outfit suggestion from suggest_outfit so the user gets something useful. |

---

## Architecture

User Input (natural language query)
        |
        v
  Planning Loop
  - extracts description, size, max_price from query
        |
        v
  search_listings(description, size, max_price)
        |
   results empty? --YES--> error message → return early
        |
       NO
        |
   session["selected_item"] = results[0]
        |
        v
  suggest_outfit(new_item=selected_item, wardrobe=session["wardrobe"])
        |
   outfit empty? --YES--> error message → return early
        |
       NO
        |
   session["outfit"] = suggestion
        |
        v
  create_fit_card(outfit=session["outfit"], new_item=selected_item)
        |
   card empty? --YES--> fallback caption + show outfit suggestion → return
        |
       NO
        |
        v
  Final Output to User
  (fit card caption + outfit suggestion)
        |
        v
  Session State (persists across all tool calls)
  {query, size, max_price, results, selected_item, wardrobe, outfit, fit_card}

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**
I'll use Claude for all three tools. For each one I'll paste in that tool's spec section from planning.md (inputs, return value, failure mode) and ask it to implement the function using load_listings() from utils/data_loader.py. I'll test each tool in isolation with at least 3 inputs before moving on — for search_listings I'll test a query that matches, a query that matches nothing, and a borderline price filter. For suggest_outfit I'll test with a full wardrobe, an empty wardrobe, and a wardrobe with only one item. For create_fit_card I'll test with a complete outfit string, a missing platform field, and an empty outfit string.


**Milestone 4 — Planning loop and state management:**
I'll give Claude the Architecture diagram above plus the Planning Loop section and ask it to implement the main agent loop that initializes the session dict, calls each tool in order, checks the conditions at each step, and handles early returns. I'll verify it by running the full example query from "A Complete Interaction" end to end and checking that the session dict contains the right values after each tool call.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
The agent calls search_listings("vintage graphic tee", size="M", max_price=30.0). It returns 3 matching listings sorted by relevance. The agent picks the top result: {title: "Faded Band Tee", price: 22.0, platform: "Depop", condition: "Good", style_tags: ["vintage", "graphic", "oversized"]}.

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? --> 
 The agent calls suggest_outfit(new_item=<faded band tee dict>, wardrobe=get_example_wardrobe()). The wardrobe contains baggy jeans and chunky sneakers. It returns: "Pair the faded band tee with your wide-leg jeans and chunky sneakers for a 90s grunge look. Tuck the front corner slightly for shape."

**Step 3:**
The agent calls create_fit_card(outfit=<suggestion string>, new_item=<faded band tee dict>). It returns: "thrifted this faded band tee off depop for $22 and it was made for my wide-legs 🖤 full look in my stories"

**Final output to user:**
<!-- What does the user actually see at the end? -->
The fit card caption above, plus the outfit suggestion from step 2 so they know how to actually style it.