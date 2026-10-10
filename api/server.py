#!/usr/bin/env python3
"""Plot Buddy server: standard library only. Serves web/index.html and POST /api/plan."""
import json, os, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import planner, guard  # noqa: E402

INDEX = os.path.join(os.path.dirname(HERE), "web", "index.html")
BACKEND = os.environ.get("LLM_BACKEND", "none")  # none | ollama


def build_response(req):
    plan = planner.make_plan(req)
    plan["phrased_by"] = "rules"
    if BACKEND == "ollama":
        try:
            import llm_ollama
            text = llm_ollama.phrase(plan)
            if guard.check(text, plan):
                plan["card_text"], plan["phrased_by"] = text, f"open model ({llm_ollama.MODEL})"
            else:
                plan["phrased_by"] = "rules (guard rejected the model text)"
        except Exception as e:  # model offline: the app still works
            plan["phrased_by"] = f"rules (model unavailable: {type(e).__name__})"
    return plan


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
    print(f"Plot Buddy on http://localhost:{port}  (LLM_BACKEND={BACKEND})")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
