#!/usr/bin/env python3
"""Plot Buddy server: standard library only. Serves web/index.html and POST /api/plan.

LLM_BACKEND = none      rules only (default)
              ollama    local open-weight model through Ollama
              backboard hosted open-weight model through Backboard (needs BACKBOARD_API_KEY)
"""
import json, os, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import planner, guard  # noqa: E402

INDEX = os.path.join(os.path.dirname(HERE), "web", "index.html")
BACKEND = os.environ.get("LLM_BACKEND", "none").lower()
MAX_CALLS_PER_HOUR = int(os.environ.get("MODEL_MAX_PER_HOUR", "60"))  # protects your Backboard credit
CACHE_MAX = 200

_LOCK = threading.Lock()
_CALLS = []   # timestamps of hosted-model calls in the last hour
_CACHE = {}   # (backend, language, card_text) -> (text, label)


def _allow_call():
    now = time.time()
    with _LOCK:
        while _CALLS and now - _CALLS[0] > 3600:
            _CALLS.pop(0)
        if len(_CALLS) >= MAX_CALLS_PER_HOUR:
            return False
        _CALLS.append(now)
        return True


def _call_model(plan):
    if BACKEND == "ollama":
        import llm_ollama
        return llm_ollama.phrase(plan), f"open model ({llm_ollama.MODEL})"
    if BACKEND == "backboard":
        import llm_backboard
        return llm_backboard.phrase(plan), f"open-weight model via Backboard ({llm_backboard.MODEL})"
    raise RuntimeError("no model backend")


def build_response(req):
    plan = planner.make_plan(req)
    plan["phrased_by"] = "rules"
    if BACKEND not in ("ollama", "backboard"):
        return plan
    key = (BACKEND, plan["language"], plan["card_text"])
    with _LOCK:
        hit = _CACHE.get(key)
    if hit:
        plan["card_text"], plan["phrased_by"] = hit[0], hit[1] + " (cached)"
        return plan
    if BACKEND == "backboard" and not _allow_call():
        plan["phrased_by"] = "rules (hourly model limit reached)"
        return plan
    try:
        text, label = _call_model(plan)
        if guard.check(text, plan):
            with _LOCK:
                if len(_CACHE) >= CACHE_MAX:
                    _CACHE.clear()
                _CACHE[key] = (text, label)
            plan["card_text"], plan["phrased_by"] = text, label
        else:
            plan["phrased_by"] = "rules (guard rejected the model text)"
    except Exception as e:  # the app must keep working when the model is down
        print(f"model error: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        plan["phrased_by"] = f"rules (model unavailable: {type(e).__name__})"
    return plan


def status_info():
    """Safe diagnostics: never includes the API key."""
    info = {"backend": BACKEND, "hourly_model_limit": MAX_CALLS_PER_HOUR}
    if BACKEND == "backboard":
        import llm_backboard
        info.update(provider=llm_backboard.PROVIDER, model=llm_backboard.MODEL,
                    key_set=bool(os.environ.get("BACKBOARD_API_KEY")))
    elif BACKEND == "ollama":
        import llm_ollama
        info.update(model=llm_ollama.MODEL)
    return info


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/healthz":
            return self._send(200, {"ok": True})
        if self.path == "/api/status":
            return self._send(200, status_info())
        if self.path in ("/", "/index.html"):
            with open(INDEX, "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/plan":
            return self._send(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length") or 0)
        if n > 10000:
            return self._send(413, {"error": "request too large"})
        try:
            req = json.loads(self.rfile.read(n) or b"{}")
            if not isinstance(req, dict):
                raise ValueError("Send a JSON object.")
            self._send(200, build_response(req))
        except (ValueError, TypeError, AttributeError) as e:
            self._send(400, {"error": str(e)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"Plot Buddy on http://localhost:{port}  (LLM_BACKEND={BACKEND})", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()