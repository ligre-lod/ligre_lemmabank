# LiGre Lemma Bank

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24085996.svg)](https://doi.org/10.5281/zenodo.24085996)
[![Data: CC BY-SA 4.0](https://img.shields.io/badge/data-CC%20BY--SA%204.0-lightgrey.svg)](LICENSE-DATA.md)
[![Code: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)

LiGre (Lemma Bank for Ancient Greek) is a linked open data resource that
publishes lemmatized Ancient Greek vocabulary as structured, interlinked
RDF data. Each lemma is modeled using the [OntoLex-Lemon](https://www.w3.org/community/ontolex/)
vocabulary and the [LiLa](https://lila-erc.eu/) `Lemma` class, so that
Ancient Greek lemmas can be published, queried, and linked following the
same conventions as the broader Linked Data knowledge base for the
Latin language built by the [LiLa project](https://lila-erc.eu/).

The design and rationale behind the resource are described in the paper
*"From Lemmas to Links: A Lemma Bank for Ancient Greek"* (see [Citation](#citation)).

## At a glance

| | |
|---|---|
| Dataset IRI | <https://w3id.org/ligre/data/id/lemma/LemmaBank> |
| Lemma IRIs | `https://w3id.org/ligre/data/id/lemma/{id}`, e.g. <https://w3id.org/ligre/data/id/lemma/15308> |
| SPARQL endpoint | <https://ligre.ugent.be/sparql> ([query UI](https://ligre.ugent.be/sparql-ui/)) |
| Search interface | <https://ligre-lod.github.io/query-interface/> |
| Data dump | [`ttl/ligre_lemmabank.ttl`](ttl/ligre_lemmabank.ttl) (Turtle) |
| VoID/DCAT description | [`ttl/lemmabank_void.ttl`](ttl/lemmabank_void.ttl); whole knowledge base: <https://ligre-lod.github.io/.well-known/void> |
| Vocabularies | LiLa ontology, OntoLex-Lemon, Dublin Core terms, RDFS |
| Licence | Data [CC BY-SA 4.0](LICENSE-DATA.md); code [MIT](LICENSE) |
| Archived releases | Zenodo: <https://doi.org/10.5281/zenodo.24085996> (all versions), with a DOI per release (see [Versioning and releases](#versioning-and-releases)) |

The lemma bank is part of the LiGre Knowledge Base
(<https://w3id.org/ligre/data/id/KnowledgeBase>), together with the corpora
linked to its lemmas: so far
[PapyGreek–LiGre](https://github.com/ligre-lod/papygreek), the PapyGreek
Treebanks linked to LiGre (<https://doi.org/10.5281/zenodo.24089052>).
The endpoint serves the corpus as well, so its tokens can be queried together
with the lemmas they are linked to (see [Corpora in the endpoint](#corpora-in-the-endpoint)).

## Data files

| File | Content                                                                                                                                                                                                                         |
|---|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `ttl/ligre_lemmabank.ttl` | The complete lemma bank in Turtle, with its dataset description and VoID statistics. This is the canonical data dump.                                                                                                           |
| `ttl/lemmabank_void.ttl` | The VoID/DCAT description of the lemma bank on its own, with statistics (triples, entities, class and property partitions).                                                                                                     |
| `ttl/ligre_void.ttl` | The VoID/DCAT description of the whole LiGre Knowledge Base (lemma bank and linked corpora), published at <https://ligre-lod.github.io/.well-known/void>.                                                                       |
| `ttl/corpora/` | The dataset descriptions of the released corpora of the knowledge base, copied from their releases, which are included in `ttl/ligre_void.ttl`. |
| `ttl/lemmabank_description.ttl`, `ttl/knowledge_base_description.ttl` | Dataset descriptions (Dublin Core, DCAT, VoID) that `scripts/export_ttl.py` merges into the files above.                                                                                                                            |
| `data/ligre_lemmas.tsv` | Source list of lemmas: `lemma`, `pos` (Universal Dependencies tag) and `gender` (`m`, `f`, `n`).                                                                                                                                |
| `data/ligre_wr_lv.csv` | Clusters of lemma entries. Clusters of type WR are spellings of the same lemma and become extra `ontolex:writtenRep` values of one lemma; clusters of type LV are distinct but related lemmas, linked with `lila:lemmaVariant`. |
| `data/lemma_ids.tsv` | The fixed id of every lemma, and so its IRI (see [IRIs](#iris)), including retired ids and the lemma that replaces them.                                                                                                        |
| `data/corrections/` | The corrections to the source list, one file per pull request (see [Corrections](#corrections)). |
| `database/schema.sql`, `database/schema_corpora.sql` | The Postgres schema of the lemma bank and of the corpora. |
| `loader/` | The loaders that fill Postgres: `load_lemmas.py` (the lemma bank, with the corrections) and `load_corpora.py` (the corpora in `ttl/corpora/`), with their Docker image. |
| `ontop/input/mapping.ttl.template` | The R2RML mapping from Postgres to RDF used by Ontop.                                                                                                                                                                           |
| `queries/*.rq` | Example SPARQL queries (see [Example queries](#example-queries)).                                                                                                                                                               |

The list of lemmas in `data/ligre_lemmas.tsv` was compiled by Colin Swaelens,
Francesco Mambrini and Marco Passarotti, and is described in Swaelens,
Mambrini & Passarotti (2026) (see [Citation](#citation)). This repository publishes
that list, and its clusters in `data/ligre_wr_lv.csv`, as linked open data as
they are: the loader does not correct lemmas, parts of speech or genders (see
[Quality and known limitations](#quality-and-known-limitations)).

## Data model

Every lemma is a `lila:Lemma` with:

| Property | Value | Lemmas |
|---|---|---|
| `rdfs:label` | the citation form, as a plain string | all |
| `ontolex:writtenRep` | the citation form and any spelling variants, tagged `@grc` | all |
| `lila:hasPOS` | a LiLa part-of-speech individual (`lila:noun`, `lila:verb`, …) | all |
| `lila:hasGender` | `lila:masculine`, `lila:feminine` or `lila:neuter` | nouns and proper nouns |
| `lila:lemmaVariant` | another LiGre lemma that is a variant of this one | some |
| `dcterms:isPartOf` | the lemma bank, <https://w3id.org/ligre/data/id/lemma/LemmaBank> | all |

```turtle
<https://w3id.org/ligre/data/id/lemma/15308> a lila:Lemma ;
    rdfs:label "αὐτοκράτωρ" ;
    ontolex:writtenRep "αὐτοκράτωρ"@grc ;
    lila:hasPOS lila:noun ;
    lila:hasGender lila:masculine ;
    dcterms:isPartOf <https://w3id.org/ligre/data/id/lemma/LemmaBank> .
```

## Statistics

The statistics of each release are part of its VoID description, which
`scripts/export_ttl.py` counts on the exported lemmas: the number of triples and
lemmas, and the number of triples per property (for example how many lemmas
have a gender, or how many written representations there are). They are in
[`ttl/lemmabank_void.ttl`](ttl/lemmabank_void.ttl), in the data dump, and on
the SPARQL endpoint;
[`06_dataset_statistics.rq`](queries/06_dataset_statistics.rq) reads them.
The other example queries count lemmas per part of speech and per gender,
homographs and spelling variants (see [Example queries](#example-queries)).

## Example queries

The [`queries/`](queries) directory contains example SPARQL queries. They run
on the public endpoint and on a local copy of the data dump:

| Query | What it returns |
|---|---|
| [`01_lemma_by_written_form.rq`](queries/01_lemma_by_written_form.rq) | The lemma for a written form (λόγος), with part of speech and gender. |
| [`02_lemmas_per_pos.rq`](queries/02_lemmas_per_pos.rq) | The number of lemmas per part of speech. |
| [`03_nouns_per_gender.rq`](queries/03_nouns_per_gender.rq) | The number of noun lemmas per gender. |
| [`04_homographs.rq`](queries/04_homographs.rq) | Citation forms shared by more than one lemma, with the analyses that tell them apart. |
| [`05_spelling_variants.rq`](queries/05_spelling_variants.rq) | Lemmas with more than one written representation. |
| [`06_dataset_statistics.rq`](queries/06_dataset_statistics.rq) | The VoID statistics of the lemma bank: version, triples, lemmas and triples per property. |

Run a query against the endpoint:

```bash
curl -H 'Accept: text/csv' --data-urlencode query@queries/02_lemmas_per_pos.rq \
  https://ligre.ugent.be/sparql
```

## Quality and known limitations

- The lemma list is based on the Ancient Greek WordNet (AGWN), whose lemmas
  were partly generated automatically. It therefore contains errors, such as
  wrong parts of speech or genders and lemmas that occur more than once.
- This release publishes the list as compiled by Swaelens, Mambrini &
  Passarotti (2026), without corrections.
- Proper nouns are not distinguished from common nouns: personal and place
  names are tagged `lila:noun`.
- Every noun has a gender: the loader (`loader/load_lemmas.py`) refuses
  to load nouns without one.

### Corrections

Anyone can correct LiGre: with a pull request that adds a correction file,
or with the *Correction* form in the
[issue tracker](https://github.com/ligre-lod/ligre_lemmabank/issues) (see
[CONTRIBUTING.md](CONTRIBUTING.md)). Corrections are handled as follows:

- **Only in new releases.** A published release is never changed. Corrections
  are published in a new release and listed in [CHANGELOG.md](CHANGELOG.md),
  and every release stays available on Zenodo with its own DOI.
- **The source list is not edited.** `data/ligre_lemmas.tsv` stays as its
  authors published it. Corrections are files in `data/corrections/`, one per
  merged pull request with one row per change (correct, add, merge or
  retire a lemma, add a written representation or a lemma variant), each with its reason, evidence and author;
  `data/corrections/RELEASES.tsv` records the release that first contains
  each file. The loader applies them on top of the source list.
  The folder is the complete history of changes to LiGre (see
  [data/corrections/README.md](data/corrections/README.md)).
- **Checked automatically.** On every pull request,
  `scripts/check_corrections.py` checks that every correction applies, shows
  each change (now → after) and the ids it will get, and validates the
  lemmas it touches against the SHACL shapes in `shapes/lemma.shacl.ttl`.
  Reviewers only judge the content.
- **IRIs stay stable.** A corrected lemma keeps its IRI. A lemma that is
  merged into another one or removed is not deleted: its IRI keeps resolving,
  marked `owl:deprecated true` and, if it was merged, `dcterms:isReplacedBy`
  the lemma that replaces it. Ids are never reused (see [IRIs](#iris)).

## Project components

- **`data/`**: the source data of the lemma bank and its corrections.
- **`database/`** and **`loader/`**: the Postgres schema and the loaders that
  fill it with the lemma bank and the corpora served by the endpoint (see
  [Corpora in the endpoint](#corpora-in-the-endpoint)).
- **`ontop/`**: an [Ontop](https://ontop-vkg.org/) configuration that maps
  the Postgres database to RDF on the fly and exposes it as a SPARQL endpoint.
  The endpoint also serves `ttl/ligre_void.ttl` as static facts, so that the
  IRIs of the knowledge base, the lemma bank and the corpora resolve to their
  descriptions and the VoID statistics can be queried with SPARQL. The image
  is built from the repository root (`docker build -f ontop/Dockerfile .`).
- **`ttl/`**: the data dump, exported from the endpoint, and the dataset
  descriptions.
- A [LodView](https://github.com/dati-semantic/lodview) instance for
  browsing individual resources, launched via the docker-compose file.
- **[query-interface](https://github.com/ligre-lod/query-interface)**: a
  React frontend, in its own repository, to search and browse the lemma bank
  through the SPARQL endpoint, deployed at
  [ligre-lod.github.io/query-interface](https://ligre-lod.github.io/query-interface/).
  It was forked from the [Linking Italian](https://github.com/LiITA-LOD/query-interface) project.

## Corpora in the endpoint

Like the [LiLa Knowledge Base](https://lila-erc.eu/sparql/), the endpoint
serves the corpora linked to the lemma bank, so a query can combine the
tokens of a corpus with the lemmas they are linked to. A corpus is published
in its own repository, as a Turtle dump; the endpoint serves one of its
releases. So far this is PapyGreek–LiGre.

### Which releases are served

`ttl/corpora/` holds the description of each corpus release the endpoint
serves, copied from the release (e.g. `PapyGreek_corpus.ttl`). Each
`powla:Corpus` in it needs one `dcat:downloadURL` (the dump, plain or
gzipped Turtle) and a `dcat:version`. The corpus id is the name after
`data/corpora/` in its IRI (`PapyGreek`). The corpus itself, its description
and its `powla:hasSubDocument` links are not loaded into Postgres: the
endpoint serves them from `ttl/ligre_void.ttl`, which includes these
descriptions.

### From the dump to the tables

`loader/load_corpora.py` converts each dump into the tables of the `corpus`
schema (`database/schema_corpora.sql`), shared by all corpora. It knows no
corpus by name: it reads every resource under the corpus IRI by its type in
the LiLa corpus model.

| Type in the dump | Tables | Properties |
|---|---|---|
| `powla:Document` | `document`, `document_identifier`, `document_see_also` | `dc:title`; `dcterms:identifier` and `rdfs:seeAlso` (any number) |
| `lila_corpus:CitationStructure` | `citation_structure` | `dc:title`, `dc:description`, `powla:hasDocument`, `lila_corpus:first`; `lila_corpus:isLayer` is the units without a parent |
| `lila_corpus:citationUnit` | `citation_unit`, `unit_token` | `rdfs:label`, `lila_corpus:hasRefType`, `lila_corpus:hasCitLevel`, `lila_corpus:hasRefValue`, `lila_corpus:first`, `lila_corpus:last`, `powla:next`; `lila_corpus:hasCitSubUnit` becomes the parent of the sub-unit, `powla:hasChild` a row in `unit_token` |
| `powla:Terminal` | `token`, `token_lemma`, `token_structure` | `powla:hasStringValue`, `rdfs:label`, `powla:next`; `lila:hasLemma` from `token_lemma`, one row per lemma, so a token can link to several lemmas (a crasis such as κοὐκ: καί and οὐ); `lila_corpus:hasCitStructure` is the structures of the units that contain the token |

`powla:previous` is not stored: the mapping derives it from `powla:next`. The
conversion refuses a dump it cannot store without loss:

- a resource with none or more than one of these types, or with a property
  not in the table;
- more than one value for a property the tables hold once (all except
  `dcterms:identifier`, `rdfs:seeAlso`, `powla:hasChild` and
  `lila_corpus:hasCitSubUnit`);
- an IRI that is not under `https://w3id.org/ligre/`, a unit that is in no
  citation structure, or a `lila:hasLemma` that is not a LiGre lemma IRI.

It then rebuilds the triples from the rows, as the mapping will serve them,
and compares them with the triples of the dump under the corpus IRI. If they
differ in a single triple, nothing is loaded. So the endpoint serves exactly
the triples of the release.

### IRIs

The tables store the IRIs of the release with `https://w3id.org/ligre`
replaced by `LIGRE_BASE_URL` (as for Ontop), so in production they are the
IRIs of the release and locally they open in the local LodView. Lemma links
are stored as the lemma id, and the mapping mints the lemma IRI under the
same base URL.

### Loading

All corpora are loaded in one transaction:

- a corpus whose release and download URL are already loaded is skipped, so
  only new releases are downloaded (`--force` reloads them);
- a corpus that is loaded but no longer described in `ttl/corpora/` is
  removed, and the loader refuses to run if no corpus is described;
- tokens linked to a lemma id that is not in the lemma bank roll back the
  whole load (load the lemma bank first); tokens linked to a retired lemma
  are loaded with a warning, and resolve as deprecated until the corpus
  links to the lemma that replaces it.

The SHA-256 of each dump is recorded in `corpus.corpus`. To check a dump
without a database, or to use a local copy instead of downloading it:

```bash
python loader/load_corpora.py --check-only --input PapyGreek=path/to/PapyGreek.ttl.gz
```

`ontop/input/mapping.ttl.template` maps the tables of all corpora back to
their triples, so a new corpus needs no code. To serve a new release, copy
its description into `ttl/corpora/` and run the loader again.

### Querying

For example, the most frequent lemmas of PapyGreek–LiGre with their written
form:

```sparql
PREFIX lila: <http://lila-erc.eu/ontologies/lila/>
PREFIX powla: <http://purl.org/powla/powla.owl#>
PREFIX ontolex: <http://www.w3.org/ns/lemon/ontolex#>
SELECT ?lemma ?writtenRep (COUNT(?token) AS ?tokens) WHERE {
  ?token a powla:Terminal ; lila:hasLemma ?lemma .
  ?lemma ontolex:writtenRep ?writtenRep .
} GROUP BY ?lemma ?writtenRep ORDER BY DESC(?tokens) LIMIT 10
```

## Dataset description

`ttl/lemmabank_description.ttl` describes the Lemma Bank
(`https://w3id.org/ligre/data/id/lemma/LemmaBank`) in Dublin Core, DCAT and
VoID. `scripts/export_ttl.py` merges it into `ligre_lemmabank.ttl` and adds VoID
statistics (triples, entities, class and property partitions) counted on the
exported lemmas. It also writes the description with those statistics on its
own to `ttl/lemmabank_void.ttl` (or `VOID_OUTPUT`). `VOID_INCLUDE` adds other
descriptions to that file (paths separated by `:`). The VoID file of the whole
knowledge base, published at https://ligre-lod.github.io/.well-known/void,
combines `ttl/knowledge_base_description.ttl` (the LiGre Knowledge Base, with
the lemma bank and the corpora as subsets) and the description of each
released corpus in `ttl/corpora/`:

```bash
TTL_INPUT=ttl/ligre_lemmabank.ttl TTL_OUTPUT=ttl/ligre_lemmabank.ttl VOID_OUTPUT=ttl/ligre_void.ttl \
  VOID_INCLUDE=ttl/knowledge_base_description.ttl:ttl/corpora/PapyGreek_corpus.ttl \
  python scripts/export_ttl.py
cp ttl/ligre_void.ttl ../ligre-lod/.well-known/void
cp ttl/ligre_void.ttl ../ligre-lod/.well-known/void.ttl
```

To add or refresh the description of an exported file without the endpoint:

```bash
TTL_INPUT=ttl/ligre_lemmabank.ttl TTL_OUTPUT=ttl/ligre_lemmabank.ttl python scripts/export_ttl.py
```

## Local setup

For local development, everything runs through the top-level
`docker-compose.yml`:

```bash
docker compose up
```

This starts:

- `postgres`: a local Postgres instance, initialized with
  `database/schema.sql` and `database/schema_corpora.sql`
- `lemma-loader`: a one-shot job that populates the database from the
  source data (re-run with `docker compose run --rm lemma-loader`)
- `corpus-loader`: a one-shot job, after `lemma-loader`, that loads the
  corpora described in `ttl/corpora/` (re-run with
  `docker compose run --rm --no-deps corpus-loader`)
- `ontop`: the SPARQL endpoint, backed by the local Postgres instance, with
  `ttl/ligre_void.ttl` mounted as static facts (minted under `LIGRE_BASE_URL`,
  like the lemmas)
- `lodview`: a browsable UI for individual RDF resources, backed by `ontop`

Once it's up, the SPARQL endpoint is available at `http://localhost:8081`
and LodView at `http://localhost:8082`.

The schema files only run on an empty database volume. To add the corpora to an
existing local database, recreate `postgres` (`docker compose up -d postgres`)
and run
`docker compose exec postgres psql -U ligre -d ligre_db -f /docker-entrypoint-initdb.d/02_schema_corpora.sql`
before loading them. Launch the
[query-interface](https://github.com/ligre-lod/query-interface) for the full
local stack.

## IRIs

Resources are minted under the base URL in `LIGRE_BASE_URL`. The published
`ligre-ontop` image defaults to the persistent namespace
`https://w3id.org/ligre`, which redirects to the deployed LodView, so dev and
production publish the same IRIs. The local `docker-compose.yml` defaults to
`http://localhost:8082` instead, so that local IRIs open in the local LodView.
Set `LIGRE_BASE_URL` to override either.

Lemma IRIs are persistent. The id of every lemma is fixed in
`data/lemma_ids.tsv`, and the loader only uses those ids, so lemma IRIs do not
change between releases. After changing the source data, run

```bash
python loader/load_lemmas.py --assign-ids
```

to update the file (the loader refuses to load data that does not match it):

- new lemmas get new ids;
- a lemma that is removed, or merged into another one, is retired: its id is
  never reused, and its IRI stays available with `owl:deprecated true` and,
  if it was merged, `dcterms:isReplacedBy` the lemma that replaces it.

## Versioning and releases

Releases follow [semantic versioning](https://semver.org/) and are tagged
`vMAJOR.MINOR.PATCH`. Each tag

- builds and publishes the `ghcr.io/ligre-lod/ligre-ontop` Docker image
  (`.github/workflows/docker.yaml`), and
- is archived on Zenodo through the GitHub integration, with a DOI for the
  release and a concept DOI for all releases (metadata in `.zenodo.json`).

Changes per release are listed in [CHANGELOG.md](CHANGELOG.md); the release
procedure is in [RELEASING.md](RELEASING.md).

## Sustainability

LiGre is maintained by Paulien Lemay (Ghent Centre for Digital Humanities,
Ghent University) at least until the end of the maintainer's PhD, expected
in 2030. Maintenance is then planned to pass to the Ghent Centre for Digital
Humanities; this plan is not yet final.
The endpoint and LodView are hosted at Ghent University. The IRIs use the
[w3id.org](https://w3id.org/) persistent namespace, so they can be redirected
if hosting changes, and every release is archived on Zenodo, so the data stays
available independently of the live services. Issues and corrections can be
reported through the
[GitHub issue tracker](https://github.com/ligre-lod/ligre_lemmabank/issues).

## Citation

If you use LiGre in your research, please cite the paper:

```bibtex
@inproceedings{swaelens2026lemmas,
  title={From Lemmas to Links: A Lemma Bank for Ancient Greek},
  author={Swaelens, Colin and Mambrini, Francesco and Passarotti, Marco},
  booktitle={Language Technology for Historical and Ancient Languages (LT4HALA)},
  pages={106--111},
  year={2026},
  organization={ELRA Language Resources Association}
}
```

To cite the data, use the Zenodo DOI. The concept DOI always resolves to the
latest release; to cite the exact version you used, take the DOI of that
release from the Zenodo record:

> Lemay, P., Swaelens, C., & Passarotti, M. (2026). *LiGre Lemma Bank: a Lemma
> Bank for Ancient Greek as Linked Open Data* [Data set]. Zenodo.
> https://doi.org/10.5281/zenodo.24085996

| Version | DOI                                       |
|---|-------------------------------------------|
| All versions (concept DOI) | <https://doi.org/10.5281/zenodo.24085996> |
| 0.4.0 | <https://doi.org/10.5281/zenodo.24160509> |
| 0.3.0 | <https://doi.org/10.5281/zenodo.24153619> |
| 0.2.0 | <https://doi.org/10.5281/zenodo.24101759> |
| 0.1.1 | <https://doi.org/10.5281/zenodo.24099796> |
| 0.1.0 | <https://doi.org/10.5281/zenodo.24085997> |

Citation metadata is also in [CITATION.cff](CITATION.cff).

## Licence

The data is licensed under [CC BY-SA 4.0](LICENSE-DATA.md); the code under
the [MIT License](LICENSE).
