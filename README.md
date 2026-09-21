# The Epstein Files Collection

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22865745.svg)](https://doi.org/10.5281/zenodo.22865745)
[![Links checked weekly](https://img.shields.io/badge/links-checked%20weekly-brightgreen)](data/health.json)
[![CC0-1.0](https://img.shields.io/badge/license-CC0--1.0-lightgrey)](LICENSE)

Where to read the Epstein files, where to download them, and how to check what you got.

**No documents are stored here.** This is the index of where they all are.

## What do you want to do?

|  | |
|---|---|
| 📖 **Read them** — in your browser, nothing to install | **[Read online →](docs/VIEWERS.md)** |
| ⬇️ **Download the files** — every release, smallest first | **[Downloads →](docs/DOWNLOADS.md)** |
| ⚖️ **Find one court record or FOIA file** | **[Official library →](docs/OFFICIAL-LIBRARY.md)** |
| 🔬 **Analyse the text** — OCR corpora, email sets | **[Datasets →](data/derivatives.json)** |
| 🤔 **Not sure** | **[Start here →](docs/START-HERE.md)** |

Most people want the first row.

> [!WARNING]
> These records concern the sexual abuse of children, and the redactions protecting
> victims are inconsistent. **Being named in an investigative file is not evidence of
> wrongdoing.** → [What to know before reading](docs/START-HERE.md#before-you-read-them)

## What's in the index

<!-- stats:start -->
| | |
|---|---|
| Official DOJ library entries | **76** |
| Torrents (by infohash) | **57** |
| Releases with published checksums | **12** |
| Processed text corpora | **24** |
| Browser viewers | **11** |
| Links re-checked weekly | **243** |
<!-- stats:end -->

## For developers

<details>
<summary>Machine-readable data, CLI tools, and how it is built</summary>

### Data

| File | Contents |
|------|----------|
| [`datasets.json`](data/datasets.json) | Per release: official URL, mirrors, magnet, SHA-256 |
| [`official_library.json`](data/official_library.json) | Snapshot of the DOJ library's own structure |
| [`torrents.json`](data/torrents.json) | Every torrent, keyed by infohash |
| [`derivatives.json`](data/derivatives.json) | OCR text, email sets, embeddings |
| [`viewers.json`](data/viewers.json) | Browser readers and search interfaces |
| [`health.json`](data/health.json) | Which links still resolve, and when each last worked |
| [`magnets.txt`](data/magnets.txt) · [`links.txt`](data/links.txt) | Flat lists for tooling |

Schemas: [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md)

### CLI

```bash
python scripts/verify.py list                # every documented release
python scripts/verify.py show "Data Set 9"   # all pointers for one release
python scripts/verify.py check DataSet9.zip  # identify a file you downloaded
python scripts/healthcheck.py --report       # what is still reachable
```

### Build

```
sources.json ──► aggregate.py ──► data/ ──► render_docs.py ──► docs/
                                     └────► verify.py selftest
              healthcheck.py ──► data/health.json
```

Stdlib only, no dependencies. Daily aggregation, weekly link probe, self-tested before
anything is committed. A source going down degrades to "no change", never data loss.

Contributions: [`CONTRIBUTING.md`](CONTRIBUTING.md)

</details>

<details>
<summary>Known limits — read before relying on the data</summary>

**Checksums are claims, not proofs.** They are transcribed from whoever published each
mirror; nobody here re-downloads terabytes to re-verify them. A match is strong evidence
of provenance. A mismatch usually means a repackaged mirror, not tampering.

**`blocked` is not `gone`.** In `health.json`, `gone` means the host says the file is not
there. `blocked` means the host refused *our probe* — bot protection looks identical to
withdrawal from the outside. congress.gov and justice.gov both do it.

**Data Set 9 is incomplete at the source.** Files were removed from justice.gov after
publication. Volunteer reconstructions cover more of it than the official ZIP. No single
copy is the complete record.

**Derivative corpora are unvetted.** Other people's OCR pipelines. Quality, coverage and
redaction handling vary. Trace anything load-bearing back to the source document.

</details>

## Citation

```
https://doi.org/10.5281/zenodo.22865745
```

Always resolves to the latest version. BibTeX and per-version DOIs:
[`CITATION.cff`](CITATION.cff).

## Scope & license

Publicly released material only — court unsealings, DOJ and Congressional releases, FOIA
productions, and public mirrors. Index data is [CC0](LICENSE); the underlying documents
are U.S. government records.
