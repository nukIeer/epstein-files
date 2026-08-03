# Epstein Files — Aggregated Index

A **tiny, pointer-only** archive index for publicly released Epstein-related documents.

This repository contains **no document blobs**. It stores only *pointers*: magnet links,
torrent infohashes, direct URLs, and a document manifest. That keeps the repo a few
kilobytes while indexing terabytes of public material held elsewhere (torrents, IPFS,
mirrors, court/FOIA releases).

The index is **auto-updated daily** by aggregating a curated list of upstream sources,
**community-editable** via pull requests, and **archived to Zenodo with a citable DOI** on
every release.

## What's here

| Path | Contents |
|------|----------|
| [`data/magnets.txt`](data/magnets.txt) | Deduped magnet links |
| [`data/torrents.json`](data/torrents.json) | Torrents: name, infohash, size, source |
| [`data/links.txt`](data/links.txt) | Direct / mirror / IPFS URLs |
| [`data/documents.json`](data/documents.json) | Document-level index (title, source, hash) |
| [`sources.json`](sources.json) | Upstream repos & files the aggregator pulls from |
| [`MANIFEST.md`](MANIFEST.md) | Generated human-readable index (do not edit by hand) |

## How it works

```
sources.json ──► scripts/aggregate.py ──► data/*  +  MANIFEST.md
                        ▲
                        │ daily cron (GitHub Actions)
                        │ + on push + manual dispatch
```

1. `aggregate.py` reads `sources.json`.
2. For each source it fetches the referenced raw files (magnet lists, link lists,
   torrent JSON), plus optionally scans a GitHub repo tree for `*.torrent` / magnet files.
3. Everything is parsed, normalized, **deduped by infohash / URL**, and written back to
   `data/`.
4. `MANIFEST.md` is regenerated.
5. The workflow commits any diff.

## Use the index

Download everything referenced by a torrent client that accepts magnet lists:

```bash
# feed all magnets to your client (example: aria2)
aria2c -i data/magnets.txt
```

Or import `data/torrents.json` into your own tooling.

## Contribute

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Short version: add a magnet/link/source, open a PR.
The CI validates and dedupes automatically.

## Provenance & scope

Only **publicly released** material (court unsealings, Congressional releases, FOIA
productions, and public mirrors thereof). This project indexes pointers to that material;
it does not host it. See [`LICENSE`](LICENSE) — index data is dedicated to the public
domain under CC0.

## Citation

Each GitHub Release is archived to Zenodo. Cite via the DOI badge (added after first
release).
