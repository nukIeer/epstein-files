# Contributing

This repo indexes **pointers** to publicly released Epstein Files material — magnets,
torrent infohashes, and mirror URLs. **Never commit document blobs** (`.pdf`, `.zip`,
`.mp4`, …); CI rejects them. The whole point is that the repo stays a few kilobytes.

## Ways to contribute

### 1. Add a source (preferred)
Edit [`sources.json`](sources.json). Add an entry and the daily aggregator will pull it
in automatically:

```json
{ "id": "my-mirror", "enabled": true, "type": "readme_scan",
  "url": "https://raw.githubusercontent.com/OWNER/REPO/main/README.md" }
```

Supported `type` values:
- `readme_scan` — extract every magnet + URL from a raw text/markdown file.
- `torrents_json` — a JSON array of `{name, infohash, size, source}`.
- `github_tree` — scan a repo's tree for `*.torrent`; infohash is computed automatically.
- `archive_org` — run an Internet Archive search; each matching item's auto-generated
  `.torrent` is fetched once and its real infohash recorded.
- `dataset_sections` — parse a per-release README into `data/datasets.json`
  (official URL, mirrors, magnet, published SHA-256).
- `huggingface` — index derived corpora (OCR text, email sets, embeddings) into
  `data/derivatives.json`, gated on downloads/likes to keep re-uploads out.

### 2. Add a single magnet or link
Append to [`data/magnets.txt`](data/magnets.txt) or [`data/links.txt`](data/links.txt),
one per line. Don't worry about ordering or duplicates — the aggregator normalizes and
dedupes on the next run.

### 3. Add or correct a checksum
`data/datasets.json` is generated, so fix checksums at the upstream the entry came from
(see its `artifacts[].url`) — or open an issue here with the file, its SHA-256, and where
you got it, and we will add the upstream as a source.

## Rules
- **Public material only.** Court unsealings, Congressional/DOJ releases, FOIA
  productions, and public mirrors thereof.
- **Pointers, not payloads.** No blobs, ever.
- Prefer the **official DOJ URL** as tier-1, `archive.org` as tier-2, community mirrors
  as tier-3.
- Run `python scripts/aggregate.py` then `python scripts/verify.py selftest` locally
  before opening a PR — that is exactly what CI runs.

## Validation
Every PR runs [`.github/workflows/validate.yml`](.github/workflows/validate.yml): JSON
parses, magnets are well-formed, no blobs are committed, and the aggregator runs clean.
