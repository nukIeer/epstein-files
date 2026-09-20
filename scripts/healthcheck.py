#!/usr/bin/env python3
"""Probe every HTTP pointer in the index and record whether it still resolves.

Link rot is the failure this index exists to survive: justice.gov reorganizes,
community mirrors lapse, hosts start throttling. Knowing *which* pointer died,
and when, is what lets a researcher reach for the next one.

    python scripts/healthcheck.py              # probe everything -> data/health.json
    python scripts/healthcheck.py --limit 20   # quick sample
    python scripts/healthcheck.py --report     # print the last run, probe nothing

Sends HEAD, falling back to a one-byte ranged GET for hosts that reject it. Never
downloads a body. Stdlib only.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
HEALTH = os.path.join(DATA, "health.json")

UA = {"User-Agent": "epstein-files-aggregator/1.0 (+https://github.com/nukIeer/epstein-files)"}
TIMEOUT = 25


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def targets():
    """Every distinct http(s) pointer the index publishes, with what cites it."""
    cites = {}

    try:
        with open(os.path.join(DATA, "links.txt"), encoding="utf-8") as f:
            for line in f:
                u = line.strip()
                if u.startswith(("http://", "https://")):
                    cites.setdefault(u, set()).add("links.txt")
    except FileNotFoundError:
        pass

    for d in load_json(os.path.join(DATA, "datasets.json"), []):
        for a in d.get("artifacts", []):
            u = a.get("url", "")
            if u.startswith(("http://", "https://")):
                cites.setdefault(u, set()).add(d["dataset"])

    for d in load_json(os.path.join(DATA, "derivatives.json"), []):
        u = d.get("url", "")
        if u.startswith(("http://", "https://")):
            cites.setdefault(u, set()).add(d["id"])

    return {u: sorted(c) for u, c in cites.items()}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """We want to *record* redirects, not silently follow them."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def probe_once(url, method):
    opener = urllib.request.build_opener(NoRedirect)
    headers = dict(UA)
    if method == "GET":
        headers["Range"] = "bytes=0-0"
    req = urllib.request.Request(url, method=method, headers=headers)
    try:
        with opener.open(req, timeout=TIMEOUT) as r:
            return r.status, dict(r.headers), None
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), None
    except Exception as e:  # noqa: BLE001 - DNS, TLS, timeouts all land here
        return None, {}, f"{type(e).__name__}: {e}".strip()[:160]


def probe(url):
    status, headers, err = probe_once(url, "HEAD")
    # Plenty of static hosts answer HEAD with 403/405 but serve GET fine.
    if status in (403, 405, 501) or status is None:
        s2, h2, e2 = probe_once(url, "GET")
        if s2 is not None and (status is None or s2 < 400):
            status, headers, err = s2, h2, e2

    out = {"url": url, "status": status}
    if err:
        out["error"] = err
    if status is None:
        out["verdict"] = "unreachable"
    elif 200 <= status < 400:
        out["verdict"] = "ok"
    elif status in (401, 403, 429):
        # Not necessarily removed. Bot protection and rate limiting look identical
        # to withdrawal from here, and congress.gov / justice.gov both do it.
        out["verdict"] = "blocked"
    elif status in (404, 410):
        out["verdict"] = "gone"
    else:
        out["verdict"] = "error"

    if status is not None:
        out["ok"] = 200 <= status < 400
        loc = headers.get("Location")
        if loc:
            out["redirect_to"] = urllib.parse.urljoin(url, loc)
        clen = headers.get("Content-Range") or headers.get("Content-Length")
        if clen:
            out["size_hint"] = clen
        ctype = headers.get("Content-Type")
        if ctype:
            out["content_type"] = ctype.split(";")[0].strip()
    else:
        out["ok"] = False
    return out


def run(limit, workers):
    tg = targets()
    urls = sorted(tg)[:limit] if limit else sorted(tg)
    print(f"probing {len(urls)} pointers with {workers} workers…", file=sys.stderr)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(probe, urls))

    previous = {r["url"]: r for r in load_json(HEALTH, {}).get("results", [])}
    for r in results:
        prev = previous.get(r["url"])
        if r["ok"]:
            r["last_ok"] = datetime.date.today().isoformat()
        elif prev and prev.get("last_ok"):
            r["last_ok"] = prev["last_ok"]  # carry forward: when did it last work?
        r["cited_by"] = tg[r["url"]]

    results.sort(key=lambda r: (r["ok"], r["url"]))
    by_verdict = {}
    for r in results:
        by_verdict[r["verdict"]] = by_verdict.get(r["verdict"], 0) + 1
    payload = {
        "checked": datetime.date.today().isoformat(),
        "total": len(results),
        "ok": sum(1 for r in results if r["ok"]),
        "by_verdict": dict(sorted(by_verdict.items())),
        "results": results,
    }
    with open(HEALTH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return payload


def report(payload):
    print(f"\nchecked {payload['checked']}: {payload['ok']}/{payload['total']} reachable")
    if payload.get("by_verdict"):
        print("  " + "  ".join(f"{k}={v}" for k, v in payload["by_verdict"].items()))
    dead = [r for r in payload["results"] if not r["ok"]]
    if not dead:
        print("every pointer resolved.")
        return 0

    print(
        "\n'blocked' means the host refused us (401/403/429). Bot protection looks exactly"
        "\nlike withdrawal from here, so read it as 'check by hand', not 'gone'.\n"
    )
    for verdict in ("gone", "unreachable", "error", "blocked"):
        group = [r for r in dead if r.get("verdict") == verdict]
        if not group:
            continue
        print(f"{verdict} ({len(group)}):")
        for r in group:
            why = r.get("error") or f"HTTP {r['status']}"
            seen = f"   last ok {r['last_ok']}" if r.get("last_ok") else ""
            print(f"  {why:24} {r['url'][:82]}{seen}")
            print(f"      cited by: {', '.join(r['cited_by'][:4])}")
        print()
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=0, help="probe only the first N pointers")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--report", action="store_true", help="print the last run without probing")
    args = ap.parse_args()

    if args.report:
        payload = load_json(HEALTH, None)
        if not payload:
            print("No health.json yet — run without --report first.", file=sys.stderr)
            return 1
        return report(payload)

    return report(run(args.limit, args.workers))


if __name__ == "__main__":
    sys.exit(main())
