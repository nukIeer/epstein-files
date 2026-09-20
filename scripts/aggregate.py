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


def torrent_meta(raw: bytes):
    """-> (infohash, name, total_length, trackers) for a .torrent blob."""
    d = bdecode(raw)
    info = d[b"info"]
    ih = hashlib.sha1(bencode(info)).hexdigest()
    name = info.get(b"name", b"").decode("utf-8", "replace")
    length = info.get(b"length")
    if length is None:
        length = sum(f[b"length"] for f in info.get(b"files", []))

    trackers = []
    for t in [d.get(b"announce")] + [u for tier in d.get(b"announce-list", []) for u in tier]:
        if isinstance(t, bytes):
            u = t.decode("utf-8", "replace")
            if u not in trackers:
                trackers.append(u)
    return ih, name, length, trackers


def build_magnet(ih: str, name: str, length, trackers=()) -> str:
    m = f"magnet:?xt=urn:btih:{ih}&dn={urllib.parse.quote(name)}"
    if isinstance(length, int) and length > 0:
        m += f"&xl={length}"
    for t in trackers:
        m += "&tr=" + urllib.parse.quote(t, safe="")
    return m


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
    # Seeded from the committed file so a failed upstream fetch never empties it.
    datasets = load_json(os.path.join(DATA, "datasets.json"), [])

    for s in src.get("sources", []):
        if not s.get("enabled"):
            continue
        try:
            if s["type"] == "dataset_sections":
                text = fetch(s["url"])
                datasets = parse_dataset_sections(text) or datasets
                # The same pointers also belong in the flat magnet/link lists.
                for ds in datasets:
                    for a in ds["artifacts"]:
                        if a["url"].startswith("magnet:"):
                            ih = magnet_infohash(a["url"])
                            if ih:
                                magnets[ih] = max(magnets.get(ih, ""), a["url"], key=len)
                        elif not LINK_DENY.search(a["url"]):
                            links.add(a["url"])
            else:
                handle_source(s, magnets, links, torrents)
            print(f"[ok] {s['id']}")
        except Exception as e:  # noqa: BLE001 - keep other sources alive
            print(f"[warn] {s['id']}: {e}", file=sys.stderr)

    write_outputs(magnets, links, torrents, datasets)
    print(f"magnets={len(magnets)} links={len(links)} torrents={len(torrents)} datasets={len(datasets)}")


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
                    ih, name, length, trackers = torrent_meta(fetch(url, binary=True))
                except Exception as e:  # noqa: BLE001
                    print(f"[warn] torrent {p}: {e}", file=sys.stderr)
                    continue
                ih = ih.lower()
                torrents.setdefault(
                    ih,
                    {"dataset": name, "infohash": ih, "size_bytes": length, "source": repo},
                )
                magnets.setdefault(ih, build_magnet(ih, name, length, trackers))
    elif t == "archive_org":
        handle_archive_org(s, magnets, links, torrents)
    elif t == "dataset_sections":
        pass  # handled separately in main(); needs its own output file
    else:
        raise ValueError(f"unknown source type: {t}")


# ---- per-dataset sections --------------------------------------------------
DS_HDR = re.compile(r'^### <a id="(data-set-[^"]*)"></a>\s*(.+?)\s*$', re.M)
SHA256_RE = re.compile(r"\*\*SHA-?256:?\*\*[:\s]*([0-9a-fA-F]{64})")
SIZE_IN_HDR = re.compile(r"\(([~\d][^)]*(?:B|b))\)")


def classify(u: str) -> str:
    if u.startswith("magnet:"):
        return "torrent"
    host = urllib.parse.urlparse(u).netloc.lower()
    if "justice.gov" in host:
        return "official"
    if "archive.org" in host:
        return "mirror:archive.org"
    return f"mirror:{host}"


def parse_dataset_sections(text: str):
    """Extract per-dataset artifacts (+ their SHA-256) from the upstream README.

    The upstream publishes every pointer twice: once as a markdown link and once
    inside a fenced ```text block for copy-paste. We read the fenced blocks — they
    are unambiguous — and attach each `**SHA256:**` line to the artifact above it.
    """
    out = []
    hdrs = list(DS_HDR.finditer(text))
    for i, h in enumerate(hdrs):
        body = text[h.end() : hdrs[i + 1].start() if i + 1 < len(hdrs) else len(text)]
        title = re.sub(r"\[\^\d+\]", "", h.group(2)).strip()

        size_m = SIZE_IN_HDR.search(title)
        name = re.sub(r"\s*\(.*", "", title).strip()
        entry = {
            "dataset": name,
            "slug": h.group(1),
            "size_label": size_m.group(1).strip() if size_m else None,
            "complete": "INCOMPLETE" not in title.upper(),
            "artifacts": [],
        }

        current = None
        in_fence = False
        fence_buf = []
        for line in body.splitlines():
            if line.strip().startswith("```"):
                if in_fence:
                    blob = "\n".join(fence_buf).strip()
                    # A fenced block is a pointer only if it is exactly one URL/magnet.
                    if "\n" not in blob and (blob.startswith("http") or blob.startswith("magnet:")):
                        current = {"kind": classify(blob), "url": blob}
                        entry["artifacts"].append(current)
                    in_fence, fence_buf = False, []
                else:
                    in_fence, fence_buf = True, []
                continue
            if in_fence:
                fence_buf.append(line)
                continue
            m = SHA256_RE.search(line)
            if m and current is not None and "sha256" not in current:
                current["sha256"] = m.group(1).lower()

        if entry["artifacts"]:
            out.append(entry)
    return out


# ---- Internet Archive ------------------------------------------------------
IA_SEARCH = "https://archive.org/advancedsearch.php"


def ia_search(query: str, min_size: int, rows: int):
    params = [
        ("q", f"({query}) AND item_size:[{min_size} TO 99999999999999]"),
        ("fl[]", "identifier"),
        ("fl[]", "title"),
        ("fl[]", "item_size"),
        ("fl[]", "mediatype"),
        ("fl[]", "publicdate"),
        ("sort[]", "item_size desc"),
        ("rows", str(rows)),
        ("output", "json"),
    ]
    resp = json.loads(fetch(IA_SEARCH + "?" + urllib.parse.urlencode(params)))
    return resp.get("response", {}).get("docs", [])


def handle_archive_org(s, magnets, links, torrents):
    """Index Internet Archive items that mirror the releases at collection scale.

    Every public IA item carries an auto-generated `<id>_archive.torrent`. We fetch
    it once per item, record the real infohash, and never fetch it again (items
    already present in torrents.json are skipped by their `ia_item` field).
    """
    docs = ia_search(s["query"], s.get("min_size_bytes", 1 << 30), s.get("max_items", 60))
    deny = re.compile(s["deny"], re.I) if s.get("deny") else None
    seen = {t["ia_item"] for t in torrents.values() if t.get("ia_item")}

    for d in docs:
        ident = d["identifier"]
        title = str(d.get("title", ""))
        if deny and deny.search(f"{ident} {title}"):
            continue

        links.add(f"https://archive.org/details/{ident}")
        if ident in seen:
            continue  # torrent already indexed — don't re-download it every run
        if d.get("mediatype") == "web":
            continue  # WARC crawls of justice.gov: browsable, but IA generates no torrent

        url = f"https://archive.org/download/{ident}/{urllib.parse.quote(ident)}_archive.torrent"
        try:
            ih, name, length, trackers = torrent_meta(fetch(url, binary=True))
        except Exception as e:  # noqa: BLE001 - item may be darkened or mid-derive
            print(f"[warn] ia {ident}: {e}", file=sys.stderr)
            continue

        ih = ih.lower()
        torrents.setdefault(
            ih,
            {
                "dataset": title or name,
                "infohash": ih,
                "size_bytes": length,
                "source": "archive.org",
                "ia_item": ident,
                "published": (d.get("publicdate") or "")[:10],
            },
        )
        magnets.setdefault(ih, build_magnet(ih, name, length, trackers))


def human(n):
    if not isinstance(n, int):
        return "?"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def write_outputs(magnets, links, torrents, datasets=()):
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

    # datasets.json
    dlist = sorted(datasets, key=lambda d: natural_key(d.get("dataset", "")))
    with open(os.path.join(DATA, "datasets.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(dlist, f, indent=2, ensure_ascii=False)
        f.write("\n")

    write_manifest(magnets, links, tlist, dlist)


def natural_key(s: str):
    """'Data Set 10' sorts after 'Data Set 9', not between 1 and 2."""
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", s)]


def write_manifest(magnets, links, tlist, dlist=()):
    total = sum(t.get("size_bytes", 0) or 0 for t in tlist)
    n_sha = sum(1 for d in dlist for a in d["artifacts"] if a.get("sha256"))
    lines = [
        "# MANIFEST — Epstein Files Aggregated Index",
        "",
        "> Generated by `scripts/aggregate.py`. Do not edit by hand.",
        "",
        f"- **Torrents indexed:** {len(tlist)}",
        f"- **Magnets:** {len(magnets)}",
        f"- **Direct/mirror links:** {len(links)}",
        f"- **Documented datasets:** {len(dlist)} ({n_sha} artifacts with a published SHA-256)",
        f"- **Sum of indexed torrent payloads:** {human(total)} ({total:,} bytes)",
        "",
        "> The payload sum counts every indexed torrent. Many are *mirrors of the same",
        "> release*, so it is an upper bound on transfer volume, not the size of the",
        "> underlying corpus. Use `data/datasets.json` for the deduplicated per-release view.",
        "",
    ]

    if dlist:
        lines += [
            "## Datasets",
            "",
            "Per-release view: the official DOJ URL, every known mirror, and published checksums.",
            "",
            "| Dataset | Size | Complete | Artifacts | Checksums |",
            "|---------|------|----------|-----------|-----------|",
        ]
        for d in dlist:
            arts = d["artifacts"]
            shas = sum(1 for a in arts if a.get("sha256"))
            lines.append(
                f"| {d['dataset']} | {d.get('size_label') or '?'} | "
                f"{'yes' if d.get('complete') else '**no**'} | {len(arts)} | {shas} |"
            )
        lines.append("")

    lines += [
        "## Torrents",
        "",
        "| Dataset | Infohash | Size | Source |",
        "|---------|----------|------|--------|",
    ]
    for t in tlist:
        src = t.get("ia_item") or t.get("source", "?")
        lines.append(
            f"| {t.get('dataset','?')} | `{t.get('infohash','?')}` | "
            f"{human(t.get('size_bytes'))} | {src} |"
        )
    lines += [
        "",
        "See [`data/magnets.txt`](data/magnets.txt), [`data/links.txt`](data/links.txt) and "
        "[`data/datasets.json`](data/datasets.json) for the full pointer lists.",
        "",
    ]
    with open(os.path.join(ROOT, "MANIFEST.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
