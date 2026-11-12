# Contributing

## Correcting the lemmas

Corrections to LiGre (a wrong part of speech or gender, a missing lemma, two lemmas that are the same, a lemma that
should not be there) are welcome, from anyone. They go into a new release, which credits who submitted them.

**With a pull request:**

1. Fork the repository and create a branch.
2. Add one file to `data/corrections/`, named `YYYY-MM-DD_short-description.tsv` with today's date, with one row
   per change. The columns and actions are explained in [data/corrections/README.md](data/corrections/README.md). Do
   not change other files, and do not change correction files that are already merged.
3. Optionally check it locally:

   ```bash
   pip install rdflib pyshacl
   python scripts/check_corrections.py
   ```

4. Open a pull request. The check runs automatically and shows every change; a maintainer then reviews the content.

**Without git:** open an issue with the *Correction* form, and a maintainer turns it into a correction file.

## What happens next

A merged correction goes into the next release of LiGre: the data dump, the SPARQL endpoint and Zenodo. The
release is then recorded for your file in `data/corrections/RELEASES.tsv`. Corrected lemmas keep their IRI; merged and
retired lemmas keep resolving as deprecated.

## Other contributions

For the code, the mapping or the documentation, open an issue or a pull request.
