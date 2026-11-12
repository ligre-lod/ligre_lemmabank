# Corrections

Every change to the lemmas of LiGre is a row in a file in this folder. The source list
(`data/ligre_lemmas.tsv`) stays as its authors published it; the loader applies the corrections on top of it, in
the order of the file names and then of the rows.

- **One file per pull request**, named `YYYY-MM-DD_short-description.tsv` (lowercase, words joined by hyphens),
  e.g. `2026-11-20_papygreek-pos.tsv`. Corrections apply in the order of the file names, so a new file must sort
  after every merged one: if another correction was merged in the meantime, rename yours with today's date.
- **One row per change.**
- **A merged file is never changed.** To undo or change a correction, add a new file with a new row.
- **`RELEASES.tsv`** records, for every file, the LiGre release that first contains it. It is written at the
  release (`scripts/generate_release.py prepare`), never in a pull request.

Together, the files and `RELEASES.tsv` are the history of every change to LiGre: who changed what, when, why, and
in which release.

## Columns

Tab-separated, with this header:

```
action	ligre_id	lemma	pos	gender	new_lemma	new_pos	new_gender	replaced_by	reason	evidence	submitted_by
```

| Column | Content |
|---|---|
| `action` | `correct`, `add`, `merge` or `retire` (see below) |
| `ligre_id` | the id of the lemma: the number in its IRI, e.g. `61173` for <https://w3id.org/ligre/data/id/lemma/61173>; empty for `add` |
| `lemma`, `pos`, `gender` | the lemma as it is in LiGre now (after earlier corrections); empty for `add` |
| `new_lemma`, `new_pos`, `new_gender` | the lemma as it should be; only for `correct` and `add` |
| `replaced_by` | only for `merge`: the id of the lemma that replaces this one |
| `reason` | why: one sentence |
| `evidence` | where this can be checked: a URL (an issue, a dictionary entry such as LSJ, a corpus passage) or a reference |
| `submitted_by` | your name, ORCID or GitHub handle |

`pos` and `new_pos` are Universal Dependencies tags (`ADJ`, `ADP`, `ADV`, `AUX`, `CCONJ`, `DET`, `INTJ`, `NOUN`,
`NUM`, `PART`, `PRON`, `PROPN`, `PUNCT`, `SCONJ`, `SYM`, `VERB`, `X`). `gender` and `new_gender` are `m`, `f` or `n`
for `NOUN` and `PROPN`, and empty for every other part of speech.

## Actions

- **`correct`**: change the written form, part of speech or gender of a lemma. It keeps its id and IRI. If the
  corrected lemma would be identical to another one, use `merge`.
- **`add`**: a lemma that is missing from LiGre. It gets a new id at the next release.
- **`merge`**: two lemmas are the same; this one is merged into `replaced_by`. Its IRI keeps resolving, with its
  label, as `owl:deprecated` with `dcterms:isReplacedBy`, and its written forms become written forms of
  `replaced_by`.
- **`retire`**: a lemma that should not be in LiGre. Its IRI keeps resolving, with its label, as `owl:deprecated`.

Ids are never reused and IRIs never disappear.

## Example

```
action	ligre_id	lemma	pos	gender	new_lemma	new_pos	new_gender	replaced_by	reason	evidence	submitted_by
correct	61173	ὁ	NOUN	m	ὁ	DET			the article is a determiner	https://github.com/ligre-lod/ligre_lemmabank/issues/1	Paulien Lemay
add					α	NUM			letter numeral α (1), distinct from the letter name	PapyGreek–LiGre review	Paulien Lemay
```

## Checks

Every pull request is checked automatically (`scripts/check_corrections.py`, also to run locally): every row must
apply to the current lemmas, the lemmas it changes must conform to `shapes/lemma.shacl.ttl`, merged files must be
unchanged and new files must sort after them. At every release, the whole exported lemma bank is validated against
the same shapes. The check posts a summary with every change (now → after) and the ids at the next release, so that
the reviewer only has to judge the content.
