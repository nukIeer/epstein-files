# Data dictionary

Every file in `data/` is **generated** by `scripts/aggregate.py`. Nothing here is a
document; everything is a pointer to material held elsewhere. Schemas are stable —
fields are added, not renamed or removed, so a consumer pinned to an older release keeps
working.

## `data/datasets.json`

The per-release view, and the file most research code should start from. One object per
DOJ release, in natural order (Data Set 1 … 12).

| Field | Type | Meaning |
|-------|------|---------|
| `dataset` | string | Release name as published, e.g. `"Data Set 9"`. |
| `slug` | string | Stable anchor id from the upstream, e.g. `"data-set-9-incomplete"`. |
| `size_label` | string \| null | Size as published upstream (`"78.65 GB"`). Human-facing; not a byte count. |
| `complete` | bool | `false` when the release is known to be incomplete **at the source**. See note below. |
| `artifacts` | array | Every known way to obtain this release. |

Each entry of `artifacts`:

| Field | Type | Meaning |
|-------|------|---------|
| `kind` | string | `official` (justice.gov), `torrent` (magnet URI), or `mirror:<host>`. |
| `url` | string | Absolute URL or `magnet:?…` URI. |
| `sha256` | string | *Optional.* Lowercase hex SHA-256 **as published by the upstream**. |

> **`sha256` is a claim, not a guarantee.** It is transcribed from the upstream that
> published the mirror; this project does not re-download terabytes to re-verify it.
> Two artifacts of the same release can legitimately differ, because mirrors repackage
> the archives. Treat a match as strong evidence of provenance and a mismatch as a
> reason to investigate, not as proof of tampering.

> **`complete: false`** currently applies to Data Set 9 only, where files were removed
> from the DOJ website after initial publication. The reconstructed torrents cover more
> of it than the official ZIP does. Do not treat any single Data Set 9 artifact as the
> canonical corpus.

## `data/torrents.json`

One object per distinct torrent infohash. Many are **mirrors of the same release** —
deduplicate on content before summing sizes.

| Field | Type | Meaning |
|-------|------|---------|
| `dataset` | string | Torrent or item name. Free-form; from the torrent or IA title. |
| `infohash` | string | Lowercase 40-hex BitTorrent v1 infohash. Primary key. |
| `size_bytes` | int | Total payload length in bytes, from the torrent itself. |
| `source` | string | Where the pointer came from: a GitHub repo, or `archive.org`. |
| `ia_item` | string | *Optional.* Internet Archive identifier; present iff `source` is `archive.org`. Also the cache key that stops the aggregator re-downloading the torrent. |
| `published` | string | *Optional.* `YYYY-MM-DD` the IA item went public. |

## `data/magnets.txt`

One magnet URI per line; `#` comments. Deduplicated by infohash, sorted by infohash.
Includes `dn`, `xl` and — for torrents we parsed ourselves — the announce URLs as `tr`.
Feed it straight to a client:

```bash
aria2c -i data/magnets.txt
```

## `data/links.txt`

One absolute URL per line; `#` comments; sorted and deduplicated. Direct downloads,
mirrors, IPFS gateways and Internet Archive item pages. Badges, issue links and other
noise are filtered by `LINK_DENY` in the aggregator.

## `MANIFEST.md`

Human-readable rollup of all of the above. Regenerated on every run; never edit it.

## Provenance chain

```
DOJ / House Oversight release
        │
        ├── official ZIP on justice.gov          ← artifacts[kind=official]
        ├── Internet Archive item                ← artifacts[kind=mirror:archive.org], torrents[ia_item]
        ├── community mirror host                ← artifacts[kind=mirror:*]
        └── community torrent                    ← artifacts[kind=torrent], magnets.txt
                                                     ▲
                      this repository indexes ────────┘  (pointers only)
```

## Reproducing the index

```bash
python scripts/aggregate.py        # rebuild data/* + MANIFEST.md from sources.json
python scripts/verify.py selftest  # structural check of what was produced
```

The aggregator is stdlib-only and deterministic given the same upstream state: outputs
are sorted, deduplicated, and seeded from what is already committed, so a failed source
degrades to "no change" rather than data loss.
