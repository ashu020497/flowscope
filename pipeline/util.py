import json
import math
import threading
import os
import time
from datetime import datetime, timezone

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "site", "data")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def session():
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    return s


def get(url, sess=None, tries=2, timeout=25, **kw):
    sess = sess or session()
    last = None
    for i in range(tries):
        try:
            r = sess.get(url, timeout=timeout, **kw)
            if r.status_code == 200 and r.content:
                return r
            last = RuntimeError(f"HTTP {r.status_code} from {url}")
        except Exception as e:  # network error
            last = e
        if i < tries - 1:
            time.sleep(2)
    raise last


def clean(o):
    """Make an object JSON-safe: NaN/inf -> None, numpy -> python, round floats."""
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if hasattr(o, "item") and not isinstance(o, (str, bytes)):
        try:
            o = o.item()
        except Exception:
            pass
    if isinstance(o, float):
        if math.isnan(o) or math.isinf(o):
            return None
        return round(o, 6)
    return o


def save_json(name, obj):
    path = os.path.join(DATA, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(clean(obj), f, ensure_ascii=False, separators=(",", ":"))


def load_json(name, default=None):
    path = os.path.join(DATA, name)
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


class SourceLog:
    """Records the status of every source so the site can show freshness honestly.
    Every source gets a time budget, and the whole run has a deadline, so one slow or
    blocked website can never make the job hit GitHub's time limit."""

    def __init__(self, deadline_min=None):
        prev = load_json("sources.json", {}) or {}
        self.prev = {s["id"]: s for s in prev.get("sources", [])}
        self.items = {}
        self.start = time.time()
        self.deadline = self.start + 60 * float(deadline_min or os.environ.get("FLOWSCOPE_DEADLINE_MIN", 40))

    def remaining(self):
        return self.deadline - time.time()

    def run(self, sid, meta, fn, fallback=None, budget=180):
        """Run fn() within `budget` seconds; on failure/timeout return fallback and mark stale."""
        entry = dict(id=sid, **meta)
        t0 = time.time()
        allowed = min(budget, self.remaining() - 30)
        box = {}

        def target():
            try:
                box["res"] = fn()
            except Exception as e:  # noqa
                box["err"] = e
        if allowed < 10:
            box["err"] = TimeoutError("skipped: overall time budget used up")
        else:
            th = threading.Thread(target=target, daemon=True)
            th.start()
            th.join(allowed)
            if th.is_alive():
                box["err"] = TimeoutError(f"took longer than {int(allowed)}s, skipped this run")
        took = time.time() - t0
        if "res" in box and "err" not in box:
            result, as_of = box["res"]
            entry.update(status="ok", as_of=as_of, checked=now_iso(), message="")
            self.items[sid] = entry
            print(f"[{sid}] ok in {took:.0f}s (as of {as_of})", flush=True)
            return result
        e = box["err"]
        msg = f"{type(e).__name__}: {e}"[:300]
        print(f"[{sid}] FAILED in {took:.0f}s: {msg}", flush=True)
        old = self.prev.get(sid, {})
        entry.update(status="stale" if fallback else "unavailable",
                     as_of=old.get("as_of"), checked=now_iso(), message=msg)
        self.items[sid] = entry
        return fallback

    def save(self):
        save_json("sources.json", {"generated": now_iso(), "sources": list(self.items.values())})


def merge_history(old, new, key="date"):
    """Merge two lists of dicts keyed by date; new values win. Sorted ascending."""
    d = {r[key]: r for r in (old or [])}
    for r in new or []:
        d[r[key]] = r
    return [d[k] for k in sorted(d)]
