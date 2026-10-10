"""Local open-weight model through Ollama. Standard library only."""
import json, os, urllib.request

URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")


def phrase(plan):
    lang = "simple Nigerian Pidgin" if plan["language"] == "pidgin" else "simple, friendly English"
    system = (f"Rewrite this outdoor garden card in {lang}. Keep every task, every number and the "
              "'put the phone down' message. Do NOT add tasks, crops, numbers, prices or advice. "
              "Maximum 120 words. Plain text only.")
    body = json.dumps({"model": MODEL, "stream": False, "options": {"temperature": 0.2},
                       "messages": [{"role": "system", "content": system},
                                    {"role": "user", "content": plan["card_text"]}]}).encode()
    req = urllib.request.Request(URL, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)["message"]["content"].strip()
