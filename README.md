# LiGre Lemma Bank

<!-- After the first Zenodo release, add the concept DOI badge here:
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX) -->
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
| Archived releases | Zenodo, with a DOI per release (see [Versioning and releases](#versioning-and-releases)) |

The lemma bank is part of the LiGre Knowledge Base
(<https://w3id.org/ligre/data/id/KnowledgeBase>), together with the corpora
linked to its lemmas, such as
[PapyGreek–LiGre](https://github.com/ligre-lod/papygreek).

## Data files

| File | Content |
|---|---|
| `ttl/ligre_lemmabank.ttl` | The complete lemma bank in Turtle, with its dataset description and VoID statistics. This is the canonical data dump. |
| `ttl/lemmabank_void.ttl` | The VoID/DCAT description of the lemma bank on its own, with statistics (triples, entities, class and property partitions). |
| `ttl/ligre_void.ttl` | The VoID/DCAT description of the whole LiGre Knowledge Base (lemma bank and linked corpora), published at <https://ligre-lod.github.io/.well-known/void>. |
| `ttl/lemmabank_description.ttl`, `ttl/knowledge_base_description.ttl` | Hand-written dataset descriptions (Dublin Core, DCAT, VoID) that `ttl/export_ttl.py` merges into the files above. |
| `data/ligre_lemmas.tsv` | Source list of lemmas: `lemma`, `pos` (Universal Dependencies tag) and `gender` (`m`, `f`, `n`). |
| `data/ligre_wr_lv.csv` | Clusters of lemma entries. Clusters of type WR are spellings of the same lemma and become extra `ontolex:writtenRep` values of one lemma; clusters of type LV are distinct but related lemmas, linked with `lila:lemmaVariant`. |
| `data/ligre_corrections.tsv` | Manual corrections of lemma, part of speech or gender, applied when the database is loaded. |
| `data/lemma_ids.tsv` | The fixed id of every lemma, and so its IRI (see [IRIs](#iris)), including retired ids and the lemma that replaces them. |
| `data/schema.sql` | The Postgres schema. |
| `ontop/input/mapping.ttl.template` | The R2RML mapping from Postgres to RDF used by Ontop. |
| `queries/*.rq` | Example SPARQL queries (see [Example queries](#example-queries)). |

The list of lemmas in `data/ligre_lemmas.tsv` was compiled by Colin Swaelens,
Francesco Mambrini and Marco Passarotti, and is described in Swaelens,
Mambrini & Passarotti (2026) (see [Citation](#citation)). This repository publishes it as linked open data;
changes to the list are made through `data/ligre_corrections.tsv`, not in the
list itself.

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

Release 0.1.0, counted on `ttl/ligre_lemmabank.ttl`:

| | |
|---|---|
| Triples (lemma data, as in VoID; the dump adds the dataset description) | 541,269 |
| Lemmas (`lila:Lemma`) | 100,046 |
| Distinct citation forms | 99,950 |
| Citation forms shared by more than one lemma (homographs) | 93 |
| Lemmas with spelling variants (more than one `ontolex:writtenRep`) | 67 |
| Lemmas with a gender | 40,969 |
| Manual corrections applied | 7 |

| Part of speech | Lemmas |
|---|---|
| noun | 40,968 |
| adjective | 28,811 |
| verb | 27,552 |
| adverb | 2,505 |
| pronoun | 63 |
| adposition | 51 |
| subordinating conjunction | 39 |
| particle | 33 |
| numeral | 14 |
| coordinating conjunction | 4 |
| interjection | 4 |
| determiner | 1 |
| proper noun | 1 |

Nouns by gender: 16,891 feminine, 14,336 masculine, 9,741 neuter.

The full statistics in VoID (class and property partitions) are in
[`ttl/lemmabank_void.ttl`](ttl/lemmabank_void.ttl).

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

Run a query against the endpoint:

```bash
curl -H 'Accept: text/csv' --data-urlencode query@queries/02_lemmas_per_pos.rq \
  https://ligre.ugent.be/sparql
```

## Quality and known limitations

- Every noun and proper noun must have a gender: the loader
  (`data/generate_lemma_data.py`) refuses to load the data otherwise.
- Errors found in the source list, for example while linking corpora to the
  lemma bank, are fixed in `data/ligre_corrections.tsv` rather than in the
  source list, so that every change to the source data is documented.
- Some parts of speech are wrong. Six of the seven corrections so far fix
  function words that the source list tagged as nouns (`ὁ`, `ἐν`, `οὗτος`,
  `ὅς`, `ὡς`), and similar errors remain: the negations `οὐ` and `οὔτι` each
  occur as three lemmas, a verb, an adverb and an adjective, of which only
  the adverb is correct (see `queries/04_homographs.rq`).
- Proper nouns are not distinguished from common nouns: personal and place
  names (e.g. `Ἀγαμέμνων`, `Ζεύς`, `Αἴγυπτος`; about 1,400 capitalised
  lemmas) are tagged `lila:noun`, and only one lemma is a `lila:proper_noun`.

## Project components

- **`data/`**: a Postgres schema and a loader script that populate the
  lemma bank from the source tables.
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

## Dataset description

`ttl/lemmabank_description.ttl` describes the Lemma Bank
(`https://w3id.org/ligre/data/id/lemma/LemmaBank`) in Dublin Core, DCAT and
VoID. `ttl/export_ttl.py` merges it into `ligre_lemmabank.ttl` and adds VoID
statistics (triples, entities, class and property partitions) counted on the
exported lemmas. It also writes the description with those statistics on its
own to `ttl/lemmabank_void.ttl` (or `VOID_OUTPUT`). `VOID_INCLUDE` adds other
descriptions to that file (paths separated by `:`). The VoID file of the whole
knowledge base, published at https://ligre-lod.github.io/.well-known/void,
combines `ttl/knowledge_base_description.ttl` (the LiGre Knowledge Base, with
the lemma bank and the corpora as subsets) and the description of each corpus:

```bash
TTL_INPUT=ttl/ligre_lemmabank.ttl TTL_OUTPUT=ttl/ligre_lemmabank.ttl VOID_OUTPUT=ttl/ligre_void.ttl \
  VOID_INCLUDE=ttl/knowledge_base_description.ttl:../../papygreek-to-ligre/ttl/PapyGreek_corpus.ttl \
  python ttl/export_ttl.py
cp ttl/ligre_void.ttl ../ligre-lod/.well-known/void
cp ttl/ligre_void.ttl ../ligre-lod/.well-known/void.ttl
```

To add or refresh the description of an exported file without the endpoint:

```bash
TTL_INPUT=ttl/ligre_lemmabank.ttl TTL_OUTPUT=ttl/ligre_lemmabank.ttl python ttl/export_ttl.py
```

## Local setup

For local development, everything runs through the top-level
`docker-compose.yml`:

```bash
docker compose up
```

This starts:

- `postgres`: a local Postgres instance, initialized with `data/schema.sql`
- `lemma-loader`: a one-shot job that populates the database from the
  source data (re-run with `docker compose run --rm lemma-loader`)
- `ontop`: the SPARQL endpoint, backed by the local Postgres instance, with
  `ttl/ligre_void.ttl` mounted as static facts (their IRIs are always the
  `https://w3id.org/ligre` ones, whatever `LIGRE_BASE_URL` is)
- `lodview`: a browsable UI for individual RDF resources, backed by `ontop`

Once it's up, the SPARQL endpoint is available at `http://localhost:8081`
and LodView at `http://localhost:8082`. Launch the
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
python data/generate_lemma_data.py --assign-ids
```

to update the file (the loader refuses to load data that does not match it):

- new lemmas get new ids;
- a lemma whose lemma, part of speech or gender is corrected in
  `data/ligre_corrections.tsv` keeps its id;
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

To cite a specific version of the data, use the DOI of that release on
Zenodo. Citation metadata is also in [CITATION.cff](CITATION.cff).

## Licence

The data is licensed under [CC BY-SA 4.0](LICENSE-DATA.md); the code under
the [MIT License](LICENSE).
