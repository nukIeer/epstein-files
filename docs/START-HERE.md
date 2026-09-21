# Start here

You have heard about the Epstein files and want to see them for yourself. This page
tells you where to go, in plain language. You do not need to understand torrents,
checksums or the command line to use any of this.

## What these documents are

In 2025 the U.S. Congress passed the **Epstein Files Transparency Act**
([H.R.4405](https://www.congress.gov/bill/119th-congress/house-bill/4405)), which
required the Department of Justice to publish its records on the Jeffrey Epstein
investigation. The DOJ published them on [justice.gov/epstein](https://www.justice.gov/epstein/)
in batches called **Data Set 1** through **Data Set 12**, alongside earlier court
unsealings and material released by the House Oversight Committee.

They are mostly scanned documents — court filings, emails, flight and financial
records, photographs, video — released as large ZIP files with no index inside. The
full set runs to hundreds of gigabytes.

## What this repository is

**A catalogue, not the documents.** Think of it as a library card index: it records
where every copy lives, how big it is, whether the link still works, and what its
fingerprint should be. The whole thing is a few hundred kilobytes.

It exists because the documents keep moving. Government sites reorganize, files have
been removed after publication, and volunteer mirrors lapse. A catalogue that is
checked weekly outlives any single copy.

## What do you want to do?

### "I just want to read them"

→ **[VIEWERS.md](VIEWERS.md)**

Other people have already put the documents online in searchable form. You read them
like any website — nothing to install, no account, no download. **This is the right
answer for almost everyone.** Downloading hundreds of gigabytes of scanned PDFs will
not help you find anything; the search interfaces will.

### "I'm writing something and need the text"

→ **[`data/derivatives.json`](../data/derivatives.json)**

Researchers have published processed versions: OCR'd text, extracted email sets, and
prepared datasets you can load in Python or R in one line. Far more tractable than the
page images. They are other people's pipelines, so OCR quality and coverage vary —
trace anything important back to the original document before you cite it.

For how to cite this index itself, see [Citing this](#citing-this) below.

### "I want the original files"

→ **[DOWNLOADS.md](DOWNLOADS.md)**

Every release, smallest first, with the easy browser links before the technical ones.
Data Set 5 is 61 MB. Start there rather than with the 180 GB one.

### "I want to help keep this available"

→ **[DOWNLOADS.md](DOWNLOADS.md)**, torrent section

Download a release over BitTorrent and leave your client running. While it is open you
are serving the files to everyone else. This is the single most useful thing a
non-technical person can do here, and it costs nothing but disk space.

## Before you read them

**These documents concern the sexual abuse of children.** Much of the material is
distressing, and some of it is graphic. Decide deliberately whether you want to look.

**Being named is not evidence of wrongdoing.** These are investigative files. They
contain witnesses, investigators, household staff, hotel and travel records, business
correspondence and people who appear once in someone else's address book. Names have
already circulated online as "revelations" on the strength of a single filename. If
you are about to accuse someone based on a document, read the whole document, work out
what kind of record it is, and check whether anyone with access to the full context
has reported on it.

**The redactions are inconsistent.** Material was withheld to protect victims, but not
uniformly — victim names and identifying details survive in places. Some sites
advertise "unredacted" versions assembled by volunteers. Those redactions protect real
people who did not choose to be in these files. Do not republish anything that
identifies a victim.

**Data Set 9 is incomplete.** Files were removed from the government site after
publication. Volunteer reconstructions cover more of it than the official download
does, and no single copy is the complete record. If something appears to be missing,
that may be why.

## Citing this

This index is archived on Zenodo with a permanent DOI, so a citation keeps working
even if the repository moves:

> https://doi.org/10.5281/zenodo.22865745

That DOI always resolves to the latest version. To pin one exact snapshot, use the
individual release's DOI from the Zenodo record. GitHub also renders a **"Cite this
repository"** button from [`CITATION.cff`](../CITATION.cff).

Cite the index when you used it to *locate* material. Cite the underlying records
themselves by their production numbers (`EFTA…`, `DOJ-OGR-…`) and the release they
came from, and say which copy you worked from — official, archive.org, or a specific
torrent infohash — since the copies are not all byte-identical.

## Still stuck?

[Open an issue](https://github.com/nukIeer/epstein-files/issues). A question about
where to find something is a perfectly good issue, and the answer probably belongs in
this page.
