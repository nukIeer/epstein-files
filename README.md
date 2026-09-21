# The Epstein Files: Complete Archive Index

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22865745.svg)](https://doi.org/10.5281/zenodo.22865745)
[![Link health](https://img.shields.io/badge/pointers-re--probed%20weekly-brightgreen)](data/health.json)
[![License: CC0-1.0](https://img.shields.io/badge/license-CC0--1.0-lightgrey)](LICENSE)

**Where to read the Epstein files online, where to download every DOJ release, and how
to check that what you got is genuine.**

One catalogue covering the whole public record: the twelve EFTA Data Sets, the
individually published court records and FOIA productions most mirrors miss, every
known mirror and torrent, the SHA-256 checksums to verify them, and a weekly check of
which links still work.

**This repository does not host the documents.** It is a card index — a few hundred
kilobytes describing terabytes of material on justice.gov, the Internet Archive and in
BitTorrent swarms. That is deliberate: the copies keep moving, and a small catalogue
re-checked every week outlives any one of them.

## 👉 New here? Read [**docs/START-HERE.md**](docs/START-HERE.md)

Plain language, no jargon. In short:

| If you want to… | Go to |
|---|---|
| **Read the documents** — searchable, in your browser, nothing to install | [**docs/VIEWERS.md**](docs/VIEWERS.md) |
| **Download the original files** — every release, easiest route first | [**docs/DOWNLOADS.md**](docs/DOWNLOADS.md) |
| **Find a specific court record or FOIA production** — the official library, mapped | [**docs/OFFICIAL-LIBRARY.md**](docs/OFFICIAL-LIBRARY.md) |
| **Analyse the text** — OCR'd corpora, email sets, ready-made datasets | [`data/derivatives.json`](data/derivatives.json) |
| **Help keep it online** — seed a torrent, costs nothing but disk | [docs/DOWNLOADS.md](docs/DOWNLOADS.md#three-ways-to-download-easiest-first) |

Most people want the first row. Hundreds of gigabytes of scanned PDFs will not help
you find anything; the search interfaces will.

> **Before you read:** these records concern the sexual abuse of children, the
> redactions protecting victims were applied inconsistently, and **being named in an
> investigative file is not evidence of wrongdoing**. [START-HERE](docs/START-HERE.md#before-you-read-them)
> explains what that means in practice.

## For developers and researchers

The machine-readable index lives in `data/`. Schemas, stability guarantees and the
provenance model are in [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md).

| Path | Contents |
|------|----------|
| [`data/datasets.json`](data/datasets.json) | Per-release: official URL, every mirror, magnet, published SHA-256 |
| [`data/torrents.json`](data/torrents.json) | Every distinct torrent, keyed by infohash |
| [`data/derivatives.json`](data/derivatives.json) | Processed corpora: OCR text, email sets, embeddings |
| [`data/viewers.json`](data/viewers.json) | Browser-based readers and search interfaces |
| [`data/official_library.json`](data/official_library.json) | Dated snapshot of the DOJ Epstein Library's own structure |
| [`data/health.json`](data/health.json) | Weekly probe: which pointers still resolve, and when each last worked |
| [`data/magnets.txt`](data/magnets.txt) · [`data/links.txt`](data/links.txt) | Flat pointer lists for tooling |
| [`MANIFEST.md`](MANIFEST.md) | Generated rollup of everything above |

Command line:

```bash
python scripts/verify.py list                  # every documented release
python scripts/verify.py show "Data Set 9"     # all pointers for one release
python scripts/verify.py check DataSet9.zip    # identify a file you downloaded
python scripts/healthcheck.py --report         # what is still reachable
aria2c -i data/magnets.txt                     # fetch everything at once
```

## How it works

```
sources.json ──► aggregate.py ──► data/*  ──► render_docs.py ──► docs/VIEWERS.md
                      ▲                 │                        docs/DOWNLOADS.md
   daily cron ────────┘                 ├──► verify.py selftest
   weekly ──► healthcheck.py ───────────┘
```

`aggregate.py` pulls from a curated source list: README scans, GitHub tree scans for
`*.torrent`, Internet Archive searches, a per-release parser that extracts checksums,
and Hugging Face for derived corpora. Everything is deduplicated by infohash and URL.
`healthcheck.py` probes every HTTP pointer weekly. `render_docs.py` regenerates the
human-facing pages. All stdlib, no dependencies, and the index is self-tested before
anything is committed.

An upstream going down degrades to "no change" rather than data loss: every output is
seeded from what is already committed.

## Verification and its limits

Checksums here are **transcribed from the upstream that published each mirror**. This
project does not re-download terabytes to independently re-verify them. A matching hash
is strong evidence of provenance; a mismatch means *this is not the exact file that
checksum describes*, which is often just a repackaged mirror rather than tampering.

Link health separates `gone` (the host says it is not there) from `blocked` (the host
refused **us** — bot protection is indistinguishable from withdrawal at probe level,
and both congress.gov and justice.gov do it). Read `blocked` as "check by hand".

Data Set 9 is **incomplete at the source**; see
[`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md).

## Scope

Only **publicly released** material is indexed: court unsealings, Congressional and DOJ
releases, FOIA productions, and public mirrors thereof. This project indexes pointers
to that material; it does not host it.

## Contribute

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Add a source or a magnet and open a PR — CI
validates, dedupes and rejects blobs automatically. Questions about where to find
something are also welcome as issues.

## Citation

Archived on Zenodo with a permanent DOI. Cite the concept DOI — it always resolves to
the latest version:

> Epstein Files Aggregated Index contributors. *Epstein Files — Aggregated Pointer Index
> (magnets, torrents, mirrors)*. Zenodo. https://doi.org/10.5281/zenodo.22865745

```bibtex
@dataset{epstein_files_index,
  title     = {Epstein Files --- Aggregated Pointer Index (magnets, torrents, mirrors)},
  author    = {{Epstein Files Aggregated Index contributors}},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.22865745},
  url       = {https://doi.org/10.5281/zenodo.22865745}
}
```

To cite one exact snapshot instead, use that release's own DOI from the
[Zenodo record](https://doi.org/10.5281/zenodo.22865745). See also [`CITATION.cff`](CITATION.cff) —
GitHub renders a **Cite this repository** button from it.

## License

Index data and metadata are dedicated to the public domain under [CC0 1.0](LICENSE).
The underlying documents are U.S. government records and are not covered by this
repository's license.
