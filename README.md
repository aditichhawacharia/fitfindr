# FitFindr 🛍️

A multi-tool AI agent that helps users find secondhand clothing and figure out how to wear it. Give it a natural language query — it searches listings, suggests outfits, and generates a shareable fit card.

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
GROQ_API_KEY=your_key_here
```

Run the app:
```bash
python app.py
```

Open the URL shown in your terminal (usually `http://localhost:7860`).

---

## Tool Inventory

### `search_listings(description: str, size: Optional[str], max_price: Optional[float]) → list[dict]`
Searches the mock listings dataset for items matching the user's query. Filters by size and price if provided, then scores each remaining listing by keyword overlap with the description. Returns a list of matching listing dicts sorted by relevance score (highest first). Returns an empty list if nothing matches — does not raise an exception.

### `suggest_outfit(new_item: dict, wardrobe: dict) → str`
Given a thrifted item and the user's wardrobe, asks the LLM to suggest 1–2 complete outfit combinations using pieces from the wardrobe. If the wardrobe is empty, returns general styling advice for the item instead. Always returns a non-empty string.

### `create_fit_card(outfit: str, new_item: dict) → str`
Generates a short, casual Instagram/TikTok-style caption for the outfit. Uses a higher LLM temperature (0.8) so outputs vary across runs. If the outfit string is empty, returns a descriptive error message string instead of crashing.

---

## How the Planning Loop Works

The agent runs a linear planning loop with one conditional branch — whether search results came back or not.

```
User query
    │
    ▼
Parse query with LLM → extract description, size, max_price
    │
    ▼
search_listings(description, size, max_price)
    │
    ├── results == [] → set session["error"], return early
    │                   (suggest_outfit is never called)
    │
    └── results not empty → selected_item = results[0]
            │
            ▼
        suggest_outfit(selected_item, wardrobe)
            │
            ▼
        create_fit_card(outfit_suggestion, selected_item)
            │
            ▼
        return session
```

The key decision point is after `search_listings`. If nothing matched, the agent stops immediately and returns an error message. It does not call `suggest_outfit` with empty input. If results exist, it picks the top result and proceeds through the remaining two tools in sequence.

---

## State Management

All state is stored in a session dict initialized at the start of each interaction:

```python
session = {
    "query": query,               # original user query
    "parsed": {},                 # description, size, max_price extracted by LLM
    "search_results": [],         # full list returned by search_listings
    "selected_item": None,        # results[0] — passed into suggest_outfit
    "wardrobe": wardrobe,         # user's wardrobe dict
    "outfit_suggestion": None,    # string returned by suggest_outfit
    "fit_card": None,             # string returned by create_fit_card
    "error": None,                # set if the agent terminates early
}
```

Each tool writes its output into the session before the next tool runs. `suggest_outfit` reads from `session["selected_item"]` — the exact same dict that `search_listings` returned. `create_fit_card` reads from `session["outfit_suggestion"]` — the exact string `suggest_outfit` returned. No values are re-entered or hardcoded between steps.

---

## Error Handling

| Tool | Failure Mode | Agent Response |
|---|---|---|
| `search_listings` | No listings match | Sets `session["error"]` with a message telling the user to try different keywords, size, or price range. Returns early — `suggest_outfit` is never called. |
| `suggest_outfit` | Empty wardrobe | Calls the LLM with a general styling prompt instead of a wardrobe-specific one. Always returns a non-empty string. |
| `create_fit_card` | Empty outfit string | Returns `"Error: no outfit description was provided to generate a caption."` — does not call the LLM or raise an exception. |

**Concrete example from testing:**

Running `create_fit_card('', results[0])` returned:
```
Error: no outfit description was provided to generate a caption.
```
No exception was raised. The agent stayed alive and the error was surfaced as a string the UI could display.

---

## Spec Reflection

**One way the spec helped:** Writing the planning loop branch condition in `planning.md` before touching code made the implementation straightforward. The spec said "if results is empty, set session['error'] and return early" — that translated directly into three lines of code with no ambiguity.

**One way implementation diverged:** The spec didn't account for query parsing. The original plan assumed `description`, `size`, and `max_price` would be passed directly into the agent. In practice, users type natural language like "vintage tee under $30 size M" — so an LLM parsing step was added before `search_listings` to extract structured parameters from the raw query. This wasn't in the original spec but was necessary for the agent to work end-to-end.

---

## AI Usage

**Instance 1 — implementing `search_listings`:**
I gave Claude the Tool 1 spec block from `planning.md` (inputs, return value, scoring logic, failure mode) and asked it to implement the function using `load_listings()`. The generated code was mostly correct but had two bugs: `word is in listing_words` (invalid syntax — should be `word in listing_words`) and `listing["score"] = score` indented inside the inner loop instead of after it. I caught both by reading the code before running it and fixed them manually.

**Instance 2 — implementing `run_agent()`:**
I gave Claude the full agent diagram from `planning.md` and the Planning Loop section, and asked it to implement `run_agent()`. The generated code had the right structure but used `listings is None` instead of `listings == []` to check for empty results (search_listings returns `[]`, not `None`), used `User_query` instead of `user_query` (wrong capitalization), and didn't call `json.loads()` on the LLM's response before using it as a dict. I caught all three by reviewing the code against the spec before running it.