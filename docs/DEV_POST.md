---
title: Plot Buddy: a weekly outdoor card that tells me to put the phone down
published: false
tags: devchallenge, hf26challenge, opensource, ai
---

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 1: Touch Grass](https://dev.to/challenges/hacktoberfest-week1-2026-10-05)*

## What I Built
Plot Buddy is a weekly outdoor coach for small home gardens (a bucket, a grow bag, a balcony or a backyard) in Lagos, Nigeria. You answer two questions, and it gives you a one-screen "outdoor card": two or three tasks, how many minutes they take, and when to check back. The card says "Put the phone down", you can print it or send it to WhatsApp, and then the real work happens outside. The screen is the shortest part of the experience.

It is for people who want to grow food in small spaces but don't know what to plant this week.

## Demo
- Live: [ADD YOUR RENDER LINK HERE]
- Screenshots: [ADD SCREENSHOTS: the form, the card, the printed card, your plants]

## Code
{% embed https://github.com/YOUR-USERNAME/plot-buddy %}

## How I Built It
- **Rules decide, the model phrases.** `planner.py` reads a sourced rules file (`crops_lagos.json`) and decides what to plant or check this week. It is plain code, with 19 tests.
- **Open-weight model for the wording.** `qwen2.5:1.5b` runs locally through Ollama and rewrites the card in simple English or Pidgin. It is switched on with `LLM_BACKEND=ollama`.
- **A guard checks the model.** `guard.py` throws the model's text away if it adds any number, price, link or crop that the rules did not produce, and the app falls back to the rules text. If Ollama is off, the app still works.
- **Standard library only.** No packages to install.
- **Sources for every crop window.** Each planting window links to its source, and every crop is marked `verified: false`.

Lesson from an earlier project: I tested a 1.5B model on real messages and it invented a street address and prices. Small models are good at wording and bad at deciding, so the decisions live in code.

### What my own tests caught
I saved the planner's output for six test cases (`tests/results-v1.txt`) and read them like a user would. They showed three bugs: "plant ... in your balcony" and "in your bag" read wrongly, a low-confidence note about leafy greens appeared on cards that never mentioned leafy greens, and the sources list included crops that were not on the card. I fixed all three, added tests, and saved the corrected output as `results-v2.txt`.

## Why Does Open Innovation Matter?
- The model runs on my own laptop, so it needs no internet, no API key, and costs nothing per card.
- I could read, test and change every piece, including the guard that stops the model from inventing facts, and I can swap models by changing one setting.
- Honest limits: the hosted site uses the rules only (the free Render plan is too small for a model); it covers Lagos and four crop groups; the planting dates come from public sources that disagree, so the app tells users to confirm with a local extension officer.

## Field Test
[WRITE THIS AFTER YOU GO OUTSIDE: what you planted, the time you spent, photos, what worked and what didn't. Use docs/field-test.md.]

## My Agent Session
[Optional: add your DevRelay link, or delete this section.]

## Prize Categories
[Only list a category you genuinely used and can show. Right now the project runs on Ollama and Render only. Delete this section if unsure.]
