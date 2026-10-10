"""Rules decide WHAT to do this week. The model only phrases it (see guard.py)."""
import json, os
from datetime import date, datetime

RULES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules", "crops_lagos.json")
SPACES = ("bucket", "bag", "balcony", "backyard")
MAX_PLANT_TASKS = 2  # keep outdoor time small and the card short
WHERE = {"bucket": "in a bucket", "bag": "in a grow bag", "balcony": "in a container on your balcony",
         "backyard": "in your backyard"}


def load_rules(path=RULES_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _parse(text):
    try:
        return datetime.strptime(str(text), "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Bad date '{text}'. Use YYYY-MM-DD.")


def make_plan(req, rules=None, today=None):
    rules = rules or load_rules()
    today = today or (_parse(req["today"]) if req.get("today") else date.today())
    space = req.get("space") if req.get("space") in SPACES else "bucket"
    language = "pidgin" if req.get("language") == "pidgin" else "en"
    crops = {c["id"]: c for c in rules["crops"]}

    plant_now = []
    for c in rules["crops"]:
        if space not in c["container_ok"]:
            continue
        for w in c["windows"]:
            if today.month in w["months"]:
                plant_now.append({"id": c["id"], "name": c["name"], "window": w["label"],
                                  "confidence": w["confidence"], "source": w["source"]})
                break

    shown = plant_now[:MAX_PLANT_TASKS]
    tasks = []
    for p in shown:
        tasks.append({"when": "today", "minutes": 20, "action":
                      f"Plant {p['name']} {WHERE[space]}." + ("" if space == "backyard" else " Make sure the container has drainage holes.")})

    for item in req.get("already_planted") or []:
        crop = crops.get(item.get("crop"))
        if not crop:
            continue
        days = (today - _parse(item.get("date"))).days
        if days < 0:
            continue
        lo, hi = crop["harvest_weeks"]
        if days >= lo * 7:
            action = (f"Check your {crop['name']}: it is {days} days old and may be ready to harvest "
                      f"(sources say {lo} to {hi} weeks after planting).")
        else:
            action = f"Check your {crop['name']}: day {days}. Water if the soil is dry and look for pests."
        tasks.append({"when": "today", "minutes": 10, "action": action})

    if not tasks:
        tasks.append({"when": "today", "minutes": 20, "action":
                      "No strong planting window for your space this week. Clean a container, "
                      "check the drainage holes and add compost."})

    total = sum(t["minutes"] for t in tasks)
    low = [p["name"] for p in shown if p["confidence"] == "low"]
    note = (f"The timing for {', '.join(low)} comes from a low-confidence source. " if low else "") + \
           "Please check with a local extension officer."
    lines = [f"OUTDOOR CARD | Week of {today.isoformat()} | {rules['region']}",
             f"Put the phone down. Go outside for about {total} minutes.", ""]
    lines += [f"{i}. {t['action']} (~{t['minutes']} min)" for i, t in enumerate(tasks, 1)]
    lines += ["", "Check back in 7 days.", f"Note: {note}"]

    return {"week_of": today.isoformat(), "space": space, "language": language,
            "plant_now": [p["id"] for p in plant_now], "tasks": tasks, "total_minutes": total,
            "check_back_in_days": 7, "confidence_note": note,
            "sources": sorted({p["source"] for p in shown}), "card_text": "\n".join(lines)}
