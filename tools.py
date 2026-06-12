"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
from typing import Optional

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: Optional[str] = None,
    max_price: Optional[float] = None,
) -> list[dict]:
    # Step 1: load the listings
    listings = load_listings()
    filtered_listings = []

    # Step 2: filter by max_price and size (if provided)
    for listing in listings:
        if max_price is not None and listing["price"] > max_price:
            continue
        if size is not None and listing["size"].lower() != size.lower():
            continue
        filtered_listings.append(listing)

    # Step 3: score each listing by keyword overlap with description
    query_words = description.lower().split()
    for listing in filtered_listings:
        text = (listing["title"] + " " + listing["description"]).lower()
        listing_words = text.split()
        score = 0
        for word in query_words:
            if word in listing_words:
                score += 1
        listing["score"] = score

    # Step 4: drop any listings with a score of 0
    filtered_listings = [
        listing
        for listing in filtered_listings
        if listing["score"] > 0
    ]

    # Step 5: sort by score, highest first, and return
    filtered_listings.sort(key=lambda x: x["score"], reverse=True)
    return filtered_listings


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.
    """
    client = _get_groq_client()

    # Step 1: check whether wardrobe is empty
    if wardrobe['items'] == []:
        # Step 2: general styling prompt
        prompt = f"Please give me general styling ideas, what kinds of items pair well, what vibe it suits, etc. The item is a {new_item['title']}. To describe it: {new_item['description']}. Give me general styling advice."
    else:
        # Step 3: specific outfit prompt using wardrobe
        wardrobe_text = "\n".join(f"- {item['name']}" for item in wardrobe['items'])
        prompt = f"I'm considering buying: {new_item['title']}. {new_item['description']}.\n\nMy wardrobe includes:\n{wardrobe_text}\n\nSuggest 1-2 outfits."

    # Step 4: call the LLM and return the response
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.
    """
    client = _get_groq_client()

    # Step 1: guard against empty outfit string
    if outfit.strip() == '':
        return "Error: no outfit description was provided to generate a caption."

    # Step 2: build the prompt
    prompt = (
        f"I'm wearing this outfit: {outfit}\n\n"
        f"The thrifted item I just bought is called '{new_item['title']}', "
        f"priced at ${new_item['price']}, found on {new_item['platform']}.\n\n"
        f"Write a 2-4 sentence Instagram/TikTok caption. "
        f"Keep it casual and authentic like a real OOTD post. "
        f"Mention the item name, price, and platform naturally (once each). "
        f"Capture the outfit vibe in specific terms."
    )

    # Step 3: call the LLM and return the response
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8
    )
    return response.choices[0].message.content