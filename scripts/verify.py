#!/usr/bin/env python3
"""Researcher-side tool for the Epstein Files aggregated index.

The index is pointers only. This script is what turns those pointers into
something you can act on and trust:

    python scripts/verify.py list                 # every documented release
    python scripts/verify.py show "Data Set 9"    # all pointers for one release
    python scripts/verify.py check DataSet9.zip   # hash a local file, identify it
    python scripts/verify.py selftest             # index self-consistency check

`check` is the important one: it computes the SHA-256 of a file you downloaded
from any mirror and tells you which release — if any — it actually matches. A
mirror you have never heard of is fine as long as the bytes hash correctly.

Stdlib only; no network access except `--resolve`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

BTIH = re.compile(r"urn:btih:([0-9a-fA-F]{40}|[2-7A-Za-z]{32})")


def load(name, default):
    try:
        with open(os.path.join(DATA, name), encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def read_lines(name):
    try:
        with open(os.path.join(DATA, name), encoding="utf-8") as f:
            return [l.strip() for l in f if l.strip() and not l.startswith("#")]
    except FileNotFoundError:
        return []


def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    size = os.path.getsize(path)
    done = 0
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
            done += len(b)
            if size and sys.stderr.isatty():
                print(f"\r  hashing… {100 * done // size}%", end="", file=sys.stderr)
    if sys.stderr.isatty():
        print("\r" + " " * 24 + "\r", end="", file=sys.stderr)
    return h.hexdigest()


# ---- commands --------------------------------------------------------------
def cmd_list(args):
    datasets = load("datasets.json", [])
    if not datasets:
        print("No datasets indexed. Run scripts/aggregate.py first.", file=sys.stderr)
        return 1
    print(f"{'Dataset':14} {'Size':10} {'Complete':9} Artifacts (checksummed)")
    for d in datasets:
        arts = d.get("artifacts", [])
        n = sum(1 for a in arts if a.get("sha256"))
        print(
            f"{d['dataset']:14} {str(d.get('size_label') or '?'):10} "
            f"{'yes' if d.get('complete') else 'NO':9} {len(arts)} ({n})"
        )
    print(f"\n{len(datasets)} releases. `show <name>` for pointers.")
    return 0


def find_dataset(datasets, needle):
    n = needle.lower().replace(" ", "")
    exact = [d for d in datasets if d["dataset"].lower().replace(" ", "") == n]
    return exact or [d for d in datasets if n in d["dataset"].lower().replace(" ", "")]


def cmd_show(args):
    datasets = load("datasets.json", [])
    hits = find_dataset(datasets, args.dataset)
    if not hits:
        print(f"No release matches {args.dataset!r}. Try `list`.", file=sys.stderr)
        return 1
    for d in hits:
        flag = "" if d.get("complete") else "   ** INCOMPLETE AT SOURCE **"
        print(f"\n=== {d['dataset']} ({d.get('size_label') or '?'}){flag}")
        for a in d.get("artifacts", []):
            print(f"  [{a['kind']}]")
            print(f"    {a['url']}")
            if a.get("sha256"):
                print(f"    sha256: {a['sha256']}")
    print()
    return 0


def cmd_check(args):
    datasets = load("datasets.json", [])
    index = {}
    for d in datasets:
        for a in d.get("artifacts", []):
            if a.get("sha256"):
                index.setdefault(a["sha256"], []).append((d["dataset"], a["kind"], a["url"]))

    if not index:
        print("No checksums in the index — nothing to check against.", file=sys.stderr)
        return 1

    rc = 0
    for path in args.files:
        if not os.path.isfile(path):
            print(f"{path}: not a file", file=sys.stderr)
            rc = 1
            continue
        digest = sha256_file(path)
        hits = index.get(digest)
        print(f"\n{os.path.basename(path)}")
        print(f"  sha256 {digest}")
        if hits:
            print("  MATCH")
            for name, kind, url in hits:
                print(f"    {name}  [{kind}]  {url}")
        else:
            print("  NO MATCH in the index.")
            print("  This does not prove the file is bad: most mirrors repackage the")
            print("  archives, and only some artifacts have a published checksum.")
            rc = 2
    print()
    return rc


def cmd_selftest(args):
    """Structural checks. Exits non-zero on anything an index consumer would trip over."""
    problems = []

    magnets = read_lines("magnets.txt")
    torrents = load("torrents.json", [])
    datasets = load("datasets.json", [])
    links = read_lines("links.txt")

    # 1. every magnet parses and carries an infohash
    m_hashes = {}
    for m in magnets:
        if not m.startswith("magnet:?"):
            problems.append(f"not a magnet URI: {m[:60]}")
            continue
        hit = BTIH.search(m)
        if not hit:
            problems.append(f"magnet without btih: {m[:60]}")
            continue
        ih = hit.group(1).lower()
        if ih in m_hashes:
            problems.append(f"duplicate infohash in magnets.txt: {ih}")
        m_hashes[ih] = m

    # 2. torrents.json is well formed and agrees with magnets.txt
    t_hashes = set()
    for t in torrents:
        ih = (t.get("infohash") or "").lower()
        if not re.fullmatch(r"[0-9a-f]{40}", ih):
            problems.append(f"bad infohash in torrents.json: {t.get('infohash')!r}")
            continue
        if ih in t_hashes:
            problems.append(f"duplicate infohash in torrents.json: {ih}")
        t_hashes.add(ih)
        if not isinstance(t.get("size_bytes"), int):
            problems.append(f"{ih}: size_bytes is not an integer")

    for ih in t_hashes - set(m_hashes):
        problems.append(f"torrent has no magnet: {ih}")

    # 3. checksums are real SHA-256 hex
    for d in datasets:
        if not d.get("artifacts"):
            problems.append(f"{d.get('dataset')}: no artifacts")
        for a in d.get("artifacts", []):
            s = a.get("sha256")
            if s is not None and not re.fullmatch(r"[0-9a-f]{64}", s):
                problems.append(f"{d['dataset']}: malformed sha256 {s!r}")
            if not a.get("url"):
                problems.append(f"{d['dataset']}: artifact without url")

    # 4. links are absolute URLs
    for u in links:
        if not u.startswith(("http://", "https://")):
            problems.append(f"not an absolute URL in links.txt: {u[:60]}")

    # 5. derivatives point somewhere and are classified
    derivatives = load("derivatives.json", [])
    for d in derivatives:
        if not d.get("url", "").startswith("http"):
            problems.append(f"derivative without a URL: {d.get('id')!r}")
        if not d.get("kind"):
            problems.append(f"derivative without a kind: {d.get('id')!r}")

    print(
        f"magnets={len(magnets)} torrents={len(torrents)} datasets={len(datasets)} "
        f"derivatives={len(derivatives)} links={len(links)}"
    )

    # Advisory only — a dead mirror is a fact about the world, not a broken index.
    health = load("health.json", {})
    if health.get("results"):
        counts = health.get("by_verdict") or {}
        print(
            f"link health as of {health.get('checked')}: "
            f"{health.get('ok')}/{health.get('total')} reachable"
            + (f"  ({', '.join(f'{k}={v}' for k, v in counts.items())})" if counts else "")
        )
    if problems:
        print(f"\n{len(problems)} problem(s):", file=sys.stderr)
        for p in problems[:50]:
            print(f"  - {p}", file=sys.stderr)
        if len(problems) > 50:
            print(f"  … and {len(problems) - 50} more", file=sys.stderr)
        return 1
    print("index OK")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="list documented releases").set_defaults(fn=cmd_list)

    p = sub.add_parser("show", help="show every pointer for one release")
    p.add_argument("dataset", help='e.g. "Data Set 9" or just 9')
    p.set_defaults(fn=cmd_show)

    p = sub.add_parser("check", help="hash local files and identify them against the index")
    p.add_argument("files", nargs="+")
    p.set_defaults(fn=cmd_check)

    sub.add_parser("selftest", help="check the index for internal consistency").set_defaults(fn=cmd_selftest)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
