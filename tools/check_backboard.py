#!/usr/bin/env python3
"""Send ONE real message to Backboard and show what came back. Run this BEFORE deploying."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api"))
import llm_backboard, planner, guard  # noqa: E402

plan = planner.make_plan({"space": "bucket", "language": "en"})
print(f"Provider: {llm_backboard.PROVIDER}    Model: {llm_backboard.MODEL}")
print("\n--- card written by the rules ---\n" + plan["card_text"])
try:
    text = llm_backboard.phrase(plan)
except Exception as e:
    print(f"\nFAILED: {e}")
    sys.exit(1)
print("\n--- reply from the open-weight model ---\n" + text)
ok = guard.check(text, plan)
print("\nGuard:", "ACCEPTED, the live site would show this text."
      if ok else "REJECTED (the model added or dropped facts), the live site would show the rules text.")

