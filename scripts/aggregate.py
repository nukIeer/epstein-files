#!/usr/bin/env python3
"""Aggregate Epstein-file pointers from upstream sources into data/*.

Pointer-only: fetches magnets, links, and torrent metadata. Never downloads
document blobs. Dedupes by infohash (magnets/torrents) and by normalized URL
(links). Rebuilds MANIFEST.md.

Stdlib only. Runs in CI (see .github/workflows/update.yml) and locally:

    python scripts/aggregate.py
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import sys
import urllib.request
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SOURCES = os.path.join(ROOT, "sources.json")

MAGNET_RE = re.compile(r"magnet:\?[^\s)\"'<>\]]+")
BTIH_RE = re.compile(r"urn:btih:([0-9a-fA-F]{40}|[2-7A-Za-z]{32})")
URL_RE = re.compile(r"https?://[^\s)\"'<>\]]+")
UA = {"User-Agent": "epstein-files-aggregator/1.0"}

# Links we never want to index (badges, the tooling itself, generic homepages).
LINK_DENY = re.compile(
    r"(shields\.io|img\.shields|badge|komarev\.com|ghpvc|/blob/|/issues/|/pull/|/commit/|"
    r"user-attachments|favicon|\.ico($|\?)|YOUR_QUERY|"
    r"transmissionbt\.com/?$|qbittorrent\.org/?$|githubusercontent\.com/.+README)",
    re.I,
)


def fetch(url: str, binary: bool = False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")


# ---- bencode (for infohash from .torrent) ---------------------------------
def bdecode(data: bytes):
    def parse(i):
        c = data[i : i + 1]
        if c == b"i":
            j = data.index(b"e", i)
            return int(data[i + 1 : j]), j + 1
        if c == b"l":
            i += 1
            out = []
            while data[i : i + 1] != b"e":
                v, i = parse(i)
                out.append(v)
            return out, i + 1
        if c == b"d":
            i += 1
            out = {}
            while data[i : i + 1] != b"e":
                k, i = parse(i)
                v, i = parse(i)
                out[k] = v
            return out, i + 1
        j = data.index(b":", i)
        n = int(data[i:j])
        return data[j + 1 : j + 1 + n], j + 1 + n

    v, _ = parse(0)
    return v


def bencode(x) -> bytes:
    if isinstance(x, bool):
        raise TypeError("bool not bencodable")
    if isinstance(x, int):
        return b"i" + str(x).encode() + b"e"
    if isinstance(x, bytes):
        return str(len(x)).encode() + b":" + x
    if isinstance(x, list):
        return b"l" + b"".join(bencode(e) for e in x) + b"e"
    if isinstance(x, dict):
        return b"d" + b"".join(bencode(k) + bencode(v) for k, v in sorted(x.items())) + b"e"
    raise TypeError(type(x))


def torrent_infohash(raw: bytes):
    d = bdecode(raw)
    info = d[b"info"]
    ih = hashlib.sha1(bencode(info)).hexdigest()
    name = info.get(b"name", b"").decode("utf-8", "replace")
    length = info.get(b"length")
    if length is None:
        length = sum(f[b"length"] for f in info.get(b"files", []))
    return ih, name, length


# ---- extraction -----------------------------------------------------------
def magnet_infohash(magnet: str):
    m = BTIH_RE.search(magnet)
    return m.group(1).lower() if m else None


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def read_lines(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().splitlines()
    except FileNotFoundError:
        return []


def main():
    src = load_json(SOURCES, {"sources": []})

    # Seed with what's already committed (community + prior runs).
    magnets = {}  # infohash -> magnet string (prefer richer/longer one)
    for line in read_lines(os.path.join(DATA, "magnets.txt")):
        line = line.strip()
        if line.startswith("magnet:"):
            ih = magnet_infohash(line)
            if ih:
                magnets[ih] = max(magnets.get(ih, ""), line, key=len)

    links = set()
    header_links = []
    for line in read_lines(os.path.join(DATA, "links.txt")):
        s = line.strip()
        if s.startswith("http") and not LINK_DENY.search(s):
            links.add(s)

    torrents = {t["infohash"].lower(): t for t in load_json(os.path.join(DATA, "torrents.json"), []) if t.get("infohash")}

    for s in src.get("sources", []):
        if not s.get("enabled"):
            continue
        try:
            handle_source(s, magnets, links, torrents)
            print(f"[ok] {s['id']}")
        except Exception as e:  # noqa: BLE001 - keep other sources alive
            print(f"[warn] {s['id']}: {e}", file=sys.stderr)

    write_outputs(magnets, links, torrents)
    print(f"magnets={len(magnets)} links={len(links)} torrents={len(torrents)}")


def handle_source(s, magnets, links, torrents):
    t = s["type"]
    if t == "readme_scan":
        text = fetch(s["url"])
        for m in MAGNET_RE.findall(text):
            ih = magnet_infohash(m)
            if ih:
                magnets[ih] = max(magnets.get(ih, ""), m, key=len)
        for u in URL_RE.findall(text):
            u = u.rstrip(".,`>]*")
            if not LINK_DENY.search(u):
                links.add(u)
    elif t == "torrents_json":
        for t2 in json.loads(fetch(s["url"])):
            ih = (t2.get("infohash") or "").lower()
            if ih:
                torrents.setdefault(ih, t2)
    elif t == "github_tree":
        repo, ref = s["repo"], s.get("ref", "main")
        prefix = s.get("path_prefix", "")
        tree = json.loads(fetch(f"https://api.github.com/repos/{repo}/git/trees/{ref}?recursive=1"))
        for node in tree.get("tree", []):
            p = node["path"]
            if p.lower().endswith(".torrent") and p.startswith(prefix):
                url = f"https://raw.githubusercontent.com/{repo}/{ref}/" + urllib.parse.quote(p)
                try:
                    ih, name, length = torrent_infohash(fetch(url, binary=True))
                except Exception as e:  # noqa: BLE001
                    print(f"[warn] torrent {p}: {e}", file=sys.stderr)
                    continue
                ih = ih.lower()
                torrents.setdefault(
                    ih,
                    {"dataset": name, "infohash": ih, "size_bytes": length, "source": repo},
                )
                if ih not in magnets:
                    dn = urllib.parse.quote(name)
                    magnets[ih] = f"magnet:?xt=urn:btih:{ih}&dn={dn}&xl={length}"
    else:
        raise ValueError(f"unknown source type: {t}")


def human(n):
    if not isinstance(n, int):
        return "?"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def write_outputs(magnets, links, torrents):
    # magnets.txt
    header = [
        "# Magnet links — one per line. Auto-managed by scripts/aggregate.py (deduped by infohash).",
        "# Source: DOJ Epstein Files Transparency Act (EFTA) releases + community mirrors.",
    ]
    body = sorted(magnets.values(), key=lambda m: (magnet_infohash(m) or ""))
    with open(os.path.join(DATA, "magnets.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(header + body) + "\n")

    # links.txt
    with open(os.path.join(DATA, "links.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# Direct / mirror / archive URLs — one per line. Auto-managed (deduped).\n")
        f.write("\n".join(sorted(links)) + "\n")

    # torrents.json
    tlist = sorted(torrents.values(), key=lambda t: str(t.get("dataset", "")))
    with open(os.path.join(DATA, "torrents.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(tlist, f, indent=2, ensure_ascii=False)
        f.write("\n")

    write_manifest(magnets, links, tlist)


def write_manifest(magnets, links, tlist):
    total = sum(t.get("size_bytes", 0) or 0 for t in tlist)
    lines = [
        "# MANIFEST — Epstein Files Aggregated Index",
        "",
        "> Generated by `scripts/aggregate.py`. Do not edit by hand.",
        "",
        f"- **Torrents indexed:** {len(tlist)}",
        f"- **Magnets:** {len(magnets)}",
        f"- **Direct/mirror links:** {len(links)}",
        f"- **Total indexed payload:** {human(total)} ({total:,} bytes)",
        "",
        "## Torrents",
        "",
        "| Dataset | Infohash | Size |",
        "|---------|----------|------|",
    ]
    for t in tlist:
        lines.append(f"| {t.get('dataset','?')} | `{t.get('infohash','?')}` | {human(t.get('size_bytes'))} |")
    lines += ["", "See [`data/magnets.txt`](data/magnets.txt) and [`data/links.txt`](data/links.txt) for the full pointer lists.", ""]
    with open(os.path.join(ROOT, "MANIFEST.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
