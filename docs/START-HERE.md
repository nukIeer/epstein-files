# Start here

Plain language, no jargon. You do not need to understand torrents or checksums.

## What these documents are

In 2025 Congress passed the **Epstein Files Transparency Act**
([H.R.4405](https://www.congress.gov/bill/119th-congress/house-bill/4405)), requiring
the Justice Department to publish its records on the Jeffrey Epstein investigation.

The DOJ published them at [justice.gov/epstein](https://www.justice.gov/epstein/) as
**Data Set 1** through **12**, plus court records and FOIA productions released
separately. Mostly scanned documents — filings, emails, flight and financial records,
photos, video. Hundreds of gigabytes, with no index inside.

## What this repository is

A **catalogue, not the documents** — a library card index. It records where every copy
lives, how big it is, whether the link still works, and what its fingerprint should be.
A few hundred kilobytes.

It exists because the documents keep moving. Sites reorganize, files get removed after
publication, volunteer mirrors lapse. A catalogue checked weekly outlives any one copy.

## Where to go

| You want to… | Go to | Why |
|---|---|---|
| **Read them** | [VIEWERS.md](VIEWERS.md) | Others already put the documents online, searchable. Nothing to install. **Right answer for almost everyone.** |
| **Get the original files** | [DOWNLOADS.md](DOWNLOADS.md) | Every release, smallest first. Data Set 5 is 61 MB — start there, not the 180 GB one. |
| **Find one specific case** | [OFFICIAL-LIBRARY.md](OFFICIAL-LIBRARY.md) | 51 named court records and FOIA productions that no mirror or torrent covers. |
| **Analyse the text** | [`derivatives.json`](../data/derivatives.json) | OCR'd text and email sets you can load in one line of Python or R. |
| **Help keep it online** | [DOWNLOADS.md](DOWNLOADS.md) | Seed a torrent. Costs only disk space, and it is the most useful thing a non-technical person can do here. |

Downloading hundreds of gigabytes of scanned PDFs will not help you find anything. The
search interfaces will.

## Before you read them

> [!WARNING]
> **These documents describe the sexual abuse of children.** Much of it is distressing
> and some is graphic. Decide deliberately whether you want to look.

**Being named is not evidence of wrongdoing.** These are investigative files. They
contain witnesses, investigators, staff, hotel and travel records, business letters, and
people who appear once in someone else's address book. Names have already circulated
online as "revelations" on the strength of a single filename. Before you accuse anyone:
read the whole document, work out what kind of record it is, and check whether anyone
with the full context has reported on it.

**The redactions are inconsistent.** Victim names and identifying details survive in
places. Some sites advertise "unredacted" versions assembled by volunteers — those
redactions protect real people who did not choose to be in these files. Do not republish
anything that identifies a victim. The DOJ asks that it be reported to **EFTA@usdoj.gov**.

**Data Set 9 is incomplete.** Files were removed from the government site after
publication. Volunteer reconstructions cover more of it than the official download does.
If something seems missing, that may be why.

## Citing this

```
https://doi.org/10.5281/zenodo.22865745
```

Always resolves to the latest version; see [`CITATION.cff`](../CITATION.cff) for BibTeX.

Cite the index when you used it to *locate* something. Cite the records themselves by
production number (`EFTA…`, `DOJ-OGR-…`) and say which copy you used — official,
archive.org, or a torrent infohash — because the copies are not all byte-identical.

## Stuck?

[Open an issue](https://github.com/nukIeer/epstein-files/issues). "Where do I find X" is
a perfectly good issue, and the answer probably belongs on this page.
