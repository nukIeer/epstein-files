# Data dictionary

Everything in `data/` is a pointer to material held elsewhere — nothing here is a
document. Most of it is **generated** by `scripts/aggregate.py`; `viewers.json` is the
one hand-curated exception, and `health.json` comes from `scripts/healthcheck.py`.

Schemas are stable: fields are added, not renamed or removed, so a consumer pinned to an
older release keeps working.

If you are not writing code, you want [`START-HERE.md`](START-HERE.md) instead.

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

## `data/derivatives.json`

Third-party **processed** versions of the same records — OCR text, extracted email
sets, embeddings. For most text-analysis work these are what you want; the raw scans
are hundreds of gigabytes of images. Sorted by downloads, descending.

| Field | Type | Meaning |
|-------|------|---------|
| `id` | string | Platform identifier, e.g. `"ishumilin/epstein-files-ocr-complete"`. |
| `platform` | string | Currently always `"huggingface"`. |
| `url` | string | Landing page. |
| `kind` | string | `ocr-text`, `email-corpus`, `embeddings`, `media`, `index`, or `corpus`. Inferred from the name and tags. |
| `name_group` | string | Lowercased name without the owner. **Entries sharing one are probably the same corpus re-uploaded** — group by this before treating them as independent. |
| `downloads`, `likes` | int | Platform counters at last run. The quality gate is ≥50 downloads or ≥3 likes. |
| `license` | string \| null | As declared by the uploader. Frequently wrong or absent — verify before redistributing. |
| `formats`, `modalities` | array | From platform tags, e.g. `["parquet"]`, `["text"]`. |
| `size_category` | string \| null | Platform bucket, e.g. `"1M<n<10M"` rows. |
| `updated` | string | `YYYY-MM-DD` of last modification upstream. |

> **Not vetted.** These are other people's pipelines. OCR quality, coverage, dedup­lication
> and redaction handling vary widely and none of it is checked here. Anything load-bearing
> should be traced back to the source document via `datasets.json`.

## `data/viewers.json`

The one **hand-curated** file: websites where the documents can be read without
downloading anything. Whether a site is usable by a non-technical visitor is a
judgement call, so this list is maintained by people, not scraped. Rendered into
[`VIEWERS.md`](VIEWERS.md).

| Field | Type | Meaning |
|-------|------|---------|
| `name`, `url` | string | Display name and landing page. |
| `kind` | string | `official`, `browse`, `search`, `graph`, or `media`. |
| `operator` | string | Who runs it — government, a named person, a company, or "community". |
| `summary` | string | One or two sentences in plain language. |
| `needs_download` | bool | `true` means it must be run locally, so it is listed under "for researchers" rather than offered to general visitors. |
| `needs_account` | bool | Whether a login is required. |
| `source_repo` | string | *Optional.* Source code, when open. |
| `note` | string | *Optional.* Caveat about how it works. |
| `caution` | string | *Optional.* Rendered as a prominent warning. Used where a site's contents raise a concern — for example one advertising "unredacted" material that the DOJ withheld to protect victims. |

Reachability is **not** stored here. It comes from `health.json` at render time, so the
curated description and the live status never drift apart.

## `data/health.json`

Output of `scripts/healthcheck.py`, refreshed weekly in CI. Answers "does this pointer
still resolve, and if not, when did it last work?"

| Field | Type | Meaning |
|-------|------|---------|
| `checked` | string | `YYYY-MM-DD` of the probe run. |
| `total`, `ok` | int | Pointers probed / reachable. |
| `by_verdict` | object | Counts per verdict. |
| `results` | array | One entry per pointer. |

Each entry of `results`:

| Field | Type | Meaning |
|-------|------|---------|
| `url` | string | The probed pointer. |
| `status` | int \| null | HTTP status; `null` when the request never completed. |
| `ok` | bool | `true` for 2xx/3xx. |
| `verdict` | string | `ok`, `gone` (404/410), `blocked` (401/403/429), `unreachable` (DNS/TLS/timeout), `error` (other). |
| `last_ok` | string | *Optional.* Last date this pointer was seen working, carried forward across runs. |
| `cited_by` | array | Which releases or files reference it. |
| `redirect_to`, `size_hint`, `content_type`, `error` | | *Optional* probe details. |

> **`blocked` is not `gone`.** Bot protection, rate limiting and geo-blocking are
> indistinguishable from withdrawal at this level. `congress.gov` and `justice.gov`
> both refuse this probe while serving browsers normally. Treat `blocked` as "check by
> hand". Only `gone` means the host actively says the resource is not there.

Probes send `HEAD`, falling back to a one-byte ranged `GET` for hosts that reject it.
No response body is ever downloaded.

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
