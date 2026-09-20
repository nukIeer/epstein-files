# Epstein Files — Aggregated Index

A **tiny, pointer-only** research index for publicly released Epstein-related documents.

This repository contains **no document blobs**. It stores *pointers*: magnet URIs,
torrent infohashes, official and mirror URLs, and the SHA-256 checksums published
alongside them. That keeps the repo a few hundred kilobytes while indexing terabytes of
public material held elsewhere — on justice.gov, the Internet Archive, and in BitTorrent
swarms.

The index is **rebuilt daily** from a curated source list, **community-editable** via
pull requests, and **archived to Zenodo with a citable DOI** on every release.

## What's here

| Path | Contents |
|------|----------|
| [`data/datasets.json`](data/datasets.json) | **Start here.** Per-release: official URL, every mirror, magnet, published SHA-256 |
| [`data/torrents.json`](data/torrents.json) | Every distinct torrent: name, infohash, size, source |
| [`data/magnets.txt`](data/magnets.txt) | Deduped magnet URIs, one per line |
| [`data/derivatives.json`](data/derivatives.json) | Processed corpora built from the releases: OCR text, email sets, embeddings |
| [`data/health.json`](data/health.json) | Weekly probe: which pointers still resolve, and when each last worked |
| [`data/links.txt`](data/links.txt) | Direct / mirror / archive URLs |
| [`MANIFEST.md`](MANIFEST.md) | Generated human-readable rollup |
| [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md) | Field-by-field schema and provenance model |
| [`sources.json`](sources.json) | Upstreams the aggregator pulls from |

## Use the index

Find every way to obtain one release, with checksums:

```bash
python scripts/verify.py list
python scripts/verify.py show "Data Set 9"
```

Identify a file you already downloaded — from any mirror — against the recorded
checksums:

```bash
python scripts/verify.py check ~/Downloads/DataSet9.zip
```

Or fetch everything the index points at:

```bash
aria2c -i data/magnets.txt
```

Check what is still alive before planning a download:

```bash
python scripts/healthcheck.py --report
```

**Working with the text rather than the scans?** Start from
[`data/derivatives.json`](data/derivatives.json) instead. It indexes third-party OCR
corpora, extracted email sets and embeddings — far easier to analyse than hundreds of
gigabytes of page images. They are other people's pipelines and are not vetted here, so
trace anything load-bearing back to the source document.

Consuming it from your own code: `data/datasets.json` is the deduplicated per-release
view; `data/torrents.json` is keyed by infohash. Schemas and stability guarantees are in
[`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md).

## How it works

```
sources.json ──► scripts/aggregate.py ──► data/*  +  MANIFEST.md
                        ▲                      │
                        │ daily cron           └──► scripts/verify.py selftest
                        │ + on push + manual
```

1. `aggregate.py` reads `sources.json`.
2. Each source is fetched by type: raw README scans, torrent JSON, GitHub tree scans for
   `*.torrent`, Internet Archive searches, and a per-release parser that extracts
   checksums.
3. Everything is normalized and **deduped by infohash / URL**, then written to `data/`.
4. `MANIFEST.md` is regenerated and the index is self-tested before anything is committed.
5. Weekly, `healthcheck.py` probes every HTTP pointer and records what still resolves.

The aggregator is stdlib-only, seeds from what is already committed, and keeps other
sources alive when one fails — so an upstream going down degrades to "no change" rather
than data loss.

## Verification and its limits

Checksums in this index are **transcribed from the upstream that published each mirror**.
This project does not re-download terabytes to independently re-verify them. A matching
hash is strong evidence of provenance; a mismatch is a reason to investigate, not proof
of tampering — mirrors legitimately repackage the archives. Data Set 9 is known to be
**incomplete at the source**: files were removed from justice.gov after publication, and
community reconstructions cover more of it than the official ZIP.

Pointers rot, and the index records it rather than hiding it. `health.json` distinguishes
`gone` (the host says it is not there) from `blocked` (the host refused *us* — bot
protection is indistinguishable from withdrawal at this level, and `congress.gov` and
`justice.gov` both do it). Read `blocked` as "check by hand". See
[`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md) for the full model.

## Scope and responsible use

Only **publicly released** material is indexed: court unsealings, Congressional and DOJ
releases, FOIA productions, and public mirrors thereof. This project indexes pointers to
that material; it does not host it.

These records concern the sexual abuse of minors and contain information about victims,
some of it identifying, in productions that were redacted inconsistently. Appearance in
these files is not evidence of wrongdoing, and many named people are witnesses, staff, or
unrelated correspondents. Use the material for research, journalism and accountability —
not to identify, contact or expose victims.

## Contribute

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Short version: add a source or a magnet, open a
PR. CI validates, dedupes and rejects blobs automatically.

## Citation

Each GitHub Release is archived to Zenodo. Cite via the DOI badge (added after first
release), or see [`CITATION.cff`](CITATION.cff).

## License

Index data and metadata are dedicated to the public domain under
[CC0 1.0](LICENSE). The underlying documents are U.S. government records and are not
covered by this repository's license.
