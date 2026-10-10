# Plot Buddy

A weekly outdoor coach for small home gardens (bucket, bag, balcony, backyard) in Lagos, Nigeria.
You spend about one minute on the screen, then 20 to 30 minutes outside. Hacktoberfest 2026, Week 1: Touch Grass.

## How it works
- `api/planner.py` decides what to do this week from a sourced rules file (`api/rules/crops_lagos.json`). Plain code, no AI.
- An open-weight model (`qwen2.5:1.5b` via Ollama) only rewrites the card in friendly English or Pidgin.
- `api/guard.py` throws the model text away if it adds numbers, money, links or crops the rules did not produce.
- Standard library only. No packages to install.

## Run it (Git Bash)
```bash
python -m unittest discover -s tests -v          # run tests
python api/server.py                              # rules only, http://localhost:8000
LLM_BACKEND=ollama python api/server.py           # with the local open model
```

## Honest limits
- Every crop window is marked `verified: false`. Sources disagree and some are low confidence. Check with a local extension officer.
- Covers Lagos only, 4 crop groups.
- The hosted Render site uses the rules only. The open model runs locally (the free Render plan is too small for it).
