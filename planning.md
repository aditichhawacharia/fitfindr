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
search_listings loads all listings from data/listings.json and filters them by size and max_price if provided. It then scores each remaining listing by counting how many words from the user's description appear in the listing's title and description. Returns a list of matching listing dicts sorted by score (highest first). Returns an empty list if nothing matches.

**Input parameters:**
- `description` (str): keywords describing what the user is looking for (e.g. "vintage graphic tee")
- `size` (Optional[str]): size to filter by, or None to skip size filtering. Matching is case-insensitive.
- `max_price` (Optional[float]): maximum price inclusive, or None to skip price filtering.

**What it returns:**
A list of listing dicts sorted by relevance score. Each dict contains:
- `id` (str): unique identifier for the listing
- `title` (str): name of the item
- `description` (str): full text description of the item
- `category` (str): garment type (e.g. tops, bottoms, outerwear)
- `style_tags` (list of str): style characteristics (e.g. ["vintage", "graphic", "oversized"])
- `size` (str): size of the item
- `condition` (str): condition of the item (e.g. "Good", "Like New")
- `price` (float): listed price
- `colors` (list of str): available colors
- `brand` (str): brand name
- `platform` (str): where it's listed (e.g. "Depop", "Poshmark")
- `score` (int): keyword overlap score added by search_listings

**What happens if it fails or returns nothing:**
If no listings match, search_listings returns an empty list `[]` without raising an exception. The agent checks for this, sets `session["error"]` to "Sorry, no listings matched your search. Try different keywords, size, or price range.", and returns the session early. It does not proceed to suggest_outfit with empty input.

---

### Tool 2: suggest_outfit

**What it does:**
Given a thrifted item and the user's existing wardrobe, calls the LLM to suggest 1–2 complete outfit combinations using pieces from the wardrobe. If the wardrobe is empty, calls the LLM with a general styling prompt instead and returns styling advice based only on the item itself.

**Input parameters:**
- `new_item` (dict): the listing dict returned by search_listings, containing fields like title, description, price, platform
- `wardrobe` (dict): the user's wardrobe with an `items` key containing a list of wardrobe item dicts. Each wardrobe item has fields: name, category, colors, style_tags, notes.

**What it returns:**
A non-empty string with outfit suggestions. If the wardrobe has items, the string references specific wardrobe pieces by name. If the wardrobe is empty, it returns general styling advice for the item.

**What happens if it fails or returns nothing:**
If `wardrobe["items"]` is empty, the agent calls the LLM with a general styling prompt rather than crashing or returning an empty string. The result is stored in `session["outfit_suggestion"]` and the agent proceeds to create_fit_card normally.

---

### Tool 3: create_fit_card

**What it does:**
Generates a short, casual Instagram/TikTok-style caption for a complete outfit. Uses LLM temperature 0.8 so outputs vary across runs. Mentions the item name, price, and platform naturally in the caption.

**Input parameters:**
- `outfit` (str): the outfit suggestion string returned by suggest_outfit
- `new_item` (dict): the listing dict from search_listings, used to pull title, price, and platform into the caption

**What it returns:**
A 2–4 sentence string in casual social-media voice. Example: "Just scored the Graphic Tee — 2003 Tour Bootleg Style on Depop for $24 and I'm obsessed. Paired it with baggy jeans and chunky sneakers for the perfect laid-back look. #ootd #thrifted"

**What happens if it fails or returns nothing:**
If the outfit string is empty or whitespace, create_fit_card returns the string `"Error: no outfit description was provided to generate a caption."` without calling the LLM or raising an exception. The agent surfaces this string to the user rather than crashing.

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**

1. Initialize the session dict with the query and wardrobe.
2. Call the LLM to parse the user's natural language query into structured fields: `description`, `size`, `max_price`. Store the result in `session["parsed"]`.
3. Call `search_listings(description, size, max_price)`. Store results in `session["search_results"]`.
4. Check if results is empty. If yes → set `session["error"]` = "Sorry, no listings matched your search. Try different keywords, size, or price range." and return the session early. Do NOT proceed.
5. If results is not empty → set `session["selected_item"]` = `results[0]` and call `suggest_outfit(new_item=selected_item, wardrobe=wardrobe)`.
6. Store the result in `session["outfit_suggestion"]`. Call `create_fit_card(outfit=session["outfit_suggestion"], new_item=session["selected_item"])`.
7. Store the result in `session["fit_card"]`. Return the session.

---

## State Management

**How does information from one tool get passed to the next?**

All state is stored in a session dict initialized at the start of each `run_agent()` call:

```python
session = {
    "query": query,              # original user query string
    "parsed": {},                # description, size, max_price extracted by LLM
    "search_results": [],        # full list returned by search_listings
    "selected_item": None,       # results[0] — passed into suggest_outfit
    "wardrobe": wardrobe,        # user's wardrobe dict passed into suggest_outfit
    "outfit_suggestion": None,   # string returned by suggest_outfit, passed into create_fit_card
    "fit_card": None,            # string returned by create_fit_card, shown to user
    "error": None,               # set if the agent terminates early
}
```

Initially only `query` and `wardrobe` are populated. Each tool writes its output into the session before the next tool runs. `suggest_outfit` receives `session["selected_item"]` — the exact same dict `search_listings` returned. `create_fit_card` receives `session["outfit_suggestion"]` — the exact string `suggest_outfit` returned. No values are re-entered or hardcoded between steps.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` | No listings match the query | Returns `[]`. Agent sets `session["error"]` = "Sorry, no listings matched your search. Try different keywords, size, or price range." and returns the session early. `suggest_outfit` is never called. |
| `suggest_outfit` | Wardrobe is empty (`wardrobe["items"] == []`) | Calls the LLM with a general styling prompt instead of a wardrobe-specific one. Always returns a non-empty string. Stores it in `session["outfit_suggestion"]` and proceeds to `create_fit_card` normally. |
| `create_fit_card` | Outfit string is empty or whitespace | Returns the string `"Error: no outfit description was provided to generate a caption."` without calling the LLM or raising an exception. Agent surfaces this to the user. |

---

## Architecture

```
User Input (natural language query)
        |
        v
  run_agent()
  - initializes session dict
  - calls LLM to parse query → description, size, max_price
  - stores in session["parsed"]
        |
        v
  search_listings(description, size, max_price)
        |
   results == []? --YES--> session["error"] = "no results..." → return session
        |
       NO
        |
   session["selected_item"] = results[0]
   session["search_results"] = results
        |
        v
  suggest_outfit(new_item=selected_item, wardrobe=wardrobe)
  - if wardrobe empty → general styling prompt
  - if wardrobe has items → specific outfit prompt
        |
   session["outfit_suggestion"] = result
        |
        v
  create_fit_card(outfit=outfit_suggestion, new_item=selected_item)
  - if outfit empty → return error string
  - else → LLM generates caption at temperature 0.8
        |
   session["fit_card"] = result
        |
        v
  return session
  {query, parsed, search_results, selected_item, wardrobe,
   outfit_suggestion, fit_card, error}
```

---

## AI Tool Plan

**Milestone 3 — Individual tool implementations:**
I'll use Claude for all three tools. For each one I'll paste in that tool's spec section from planning.md (inputs, return value, failure mode) and ask it to implement the function using `load_listings()` from `utils/data_loader.py`. I'll test each tool in isolation with at least 3 inputs before moving on — for `search_listings` I'll test a query that matches, a query that matches nothing, and a borderline price filter. For `suggest_outfit` I'll test with a full wardrobe and an empty wardrobe. For `create_fit_card` I'll test with a complete outfit string and an empty outfit string.

**Milestone 4 — Planning loop and state management:**
I'll give Claude the Architecture diagram above plus the Planning Loop section and ask it to implement `run_agent()` in `agent.py`. I'll verify it by running the full example query end to end and printing `session["selected_item"]` and `session["outfit_suggestion"]` to confirm state is flowing correctly between tools without re-entry.

---

## A Complete Interaction (Step by Step)

**Example user query:** "looking for a vintage graphic tee under $30"

**Step 1:**
The agent calls the LLM to parse the query. It extracts `description="vintage graphic tee"`, `size=None`, `max_price=30.0` and stores these in `session["parsed"]`. Then it calls `search_listings("vintage graphic tee", size=None, max_price=30.0)`. This returns a list of matching listings sorted by score. The top result is `{"title": "Graphic Tee — 2003 Tour Bootleg Style", "price": 24.0, "platform": "Depop", "condition": "Good", ...}`. This is stored in `session["selected_item"]`.

**Step 2:**
The agent calls `suggest_outfit(new_item=session["selected_item"], wardrobe=get_example_wardrobe())`. The wardrobe contains items like baggy jeans, chunky sneakers, and a denim jacket. The LLM returns a string like: "Pair the Graphic Tee with your baggy straight-leg jeans and chunky white sneakers for a casual weekend look. Add the vintage denim jacket for a layered effect." This is stored in `session["outfit_suggestion"]`.

**Step 3:**
The agent calls `create_fit_card(outfit=session["outfit_suggestion"], new_item=session["selected_item"])`. The LLM returns a caption like: "Just scored the Graphic Tee — 2003 Tour Bootleg Style on Depop for $24 and I'm obsessed 🖤 Styled it with my baggy jeans and chunky sneakers for the perfect laid-back OOTD. #thrifted #vintagevibes". This is stored in `session["fit_card"]`.

**Final output to user:**
The Gradio UI displays three panels: the listing details (title, size, price, platform, condition, description), the outfit suggestion from step 2, and the fit card caption from step 3.