# tests/test_tools.py
from tools import search_listings, suggest_outfit, create_fit_card

# ── search_listings tests ──────────────────────────────────────────────────

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0

def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []

def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)

# ── suggest_outfit tests ───────────────────────────────────────────────────

def test_suggest_outfit_empty_wardrobe():
    item = {"title": "Vintage tee", "description": "Cool graphic tee"}
    wardrobe = {"items": []}
    result = suggest_outfit(item, wardrobe)
    assert isinstance(result, str)
    assert len(result) > 0

# ── create_fit_card tests ──────────────────────────────────────────────────

def test_fit_card_empty_outfit():
    result = create_fit_card("", {"title": "Tee", "price": 12, "platform": "Depop"})
    assert isinstance(result, str)
    assert len(result) > 0

def test_fit_card_varies():
    item = {"title": "Vintage tee", "price": 12, "platform": "Depop"}
    outfit = "baggy jeans and white sneakers"
    result1 = create_fit_card(outfit, item)
    result2 = create_fit_card(outfit, item)
    assert result1 != result2   # outputs should vary due to temperature