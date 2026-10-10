"""Hosted open-weight model through Backboard (one API key, many models).
Standard library only. Endpoint, header and fields are from Backboard's API docs:
POST {BASE}/threads/messages, header X-API-Key, JSON body, reply text in "content".
A new thread and a default assistant are created automatically by Backboard.
"""
import json, os, ssl, urllib.error, urllib.request

BASE = os.environ.get("BACKBOARD_URL", "https://app.backboard.io/api").rstrip("/")
PROVIDER = os.environ.get("BACKBOARD_PROVIDER", "openrouter")
MODEL = os.environ.get("BACKBOARD_MODEL", "moonshotai/kimi-k2.6")
TIMEOUT = int(os.environ.get("BACKBOARD_TIMEOUT", "60"))

_CTX = None


def _ssl_context():
    """Normal certificate checking, never turned off. On Windows it also trusts the
    certificates in the Windows store, which fixes 'unable to get local issuer certificate'
    for Python installed under MSYS2 / Git Bash."""
    global _CTX
    if _CTX is None:
        ctx = ssl.create_default_context()
        if hasattr(ssl, "enum_certificates"):  # only exists on Windows builds of Python
            for store in ("ROOT", "CA"):
                try:
                    for cert, enc, _trust in ssl.enum_certificates(store):
                        if enc == "x509_asn":
                            try:
                                ctx.load_verify_locations(cadata=ssl.DER_cert_to_PEM_cert(cert))
                            except ssl.SSLError:
                                pass
                except OSError:
                    pass
        _CTX = ctx
    return _CTX

def _system(plan):
    lang = "simple Nigerian Pidgin" if plan["language"] == "pidgin" else "simple, friendly English"
    return (f"Rewrite this outdoor garden card in {lang}. Keep every task, every number "
            "(including the total minutes and 'check back in 7 days') and the 'put the phone down' "
            "message. Do NOT add tasks, crops, numbers, prices, links or advice. "
            "Maximum 120 words. Plain text only, no markdown.")


def phrase(plan):
    key = os.environ.get("BACKBOARD_API_KEY", "")
    if not key:
        raise RuntimeError("BACKBOARD_API_KEY is not set")
    body = {"content": plan["card_text"], "system_prompt": _system(plan),
            "llm_provider": PROVIDER, "model_name": MODEL, "stream": False}
    req = urllib.request.Request(
        BASE + "/threads/messages", json.dumps(body).encode(),
        {"Content-Type": "application/json", "X-API-Key": key, "User-Agent": "plot-buddy/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=_ssl_context()) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Backboard HTTP {e.code}") from None
    if str(data.get("status", "COMPLETED")).upper() == "FAILED":
        raise RuntimeError("Backboard run failed")
    text = data.get("content")
    if not isinstance(text, str) or not text.strip():
        raise RuntimeError(f"Backboard returned no text (fields: {sorted(data)[:12]})")
    return text.replace("**", "").replace("__", "").strip()