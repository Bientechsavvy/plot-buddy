"""Reject model text that contains facts the rules did not produce."""
import re

OTHER_CROPS = ["maize", "cassava", "yam", "rice", "beans", "cowpea", "cucumber", "onion",
               "carrot", "cabbage", "watermelon", "plantain", "cocoa", "sorghum"]
MONEY = re.compile(r"https?://|[$\u20a6\u20b5]|\b(naira|cedis?|usd|ghs|ngn|dollars?)\b", re.I)


def _nums(text):
    return set(re.findall(r"\d+", text))


def check(model_text, plan):
    """True only if the model text adds no new numbers, money, links or crops."""
    t = (model_text or "").strip()
    if not t or len(t) > 900:
        return False
    if MONEY.search(t):
        return False
    base = plan["card_text"].lower()
    low = t.lower()
    if any(c in low and c not in base for c in OTHER_CROPS):
        return False
    return _nums(t) <= _nums(plan["card_text"])
