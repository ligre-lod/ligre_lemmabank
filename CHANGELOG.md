# Changelog

All notable changes to the LiGre Lemma Bank are listed here. Releases follow
[semantic versioning](https://semver.org/).

The tags v0.0.1 to v0.0.6 were development versions, not published releases:
they have no GitHub release and no DOI. Since v0.0.5 the deployed endpoint has
minted lemma IRIs under `https://w3id.org/ligre`.

## [Unreleased]

### Added
- Linksets from other lexical resources to the lemmas, served by the endpoint
  as static facts next to `ttl/ligre_void.ttl` (see *Linksets in the endpoint*
  in the README): `ttl/linksets/` holds each released linkset and its
  description, `ontop/entrypoint.sh` joins them into the facts of Ontop, and
  `scripts/generate_release.py` adds their descriptions to
  `ttl/ligre_void.ttl` and refuses links to lemmas that are not in the dump or
  are deprecated.
- The IGVLL–LiGre linkset 0.1.0: the Greek words of the Index Graecorum
  Vocabulorum in Linguam Latinam linked to their LiGre lemma
  (`ontolex:canonicalForm`), 1,381 links, a subset of the LiGre Knowledge Base,
  licensed under CC BY-NC-SA 4.0 like IGVLL.
- No database change: deploying the new image is enough.

## [0.5.0] - 2026-11-12

### Changed
- A corpus token can link to several lemmas, as a crasis does in
  PapyGreek–LiGre 0.2.0 (κοὐκ: καί and οὐ): the links are in the new table
  `corpus.token_lemma` (one row per token and lemma) instead of the column
  `corpus.token.id_lemma`, and the loader and the Ontop mapping use it. The
  loader names the columns it copies.
- Schema change for existing databases, in two steps, so that the endpoint
  keeps working in between:
  1. **before** deploying the new Ontop image:
     ```sql
     BEGIN;
     CREATE TABLE IF NOT EXISTS corpus.token_lemma (
       token_iri text NOT NULL REFERENCES corpus.token (iri) ON DELETE CASCADE,
       id_lemma int NOT NULL,
       PRIMARY KEY (token_iri, id_lemma)
     );
     CREATE INDEX IF NOT EXISTS ix_token_lemma_lemma ON corpus.token_lemma (id_lemma);
     INSERT INTO corpus.token_lemma (token_iri, id_lemma)
       SELECT iri, id_lemma FROM corpus.token WHERE id_lemma IS NOT NULL
       ON CONFLICT DO NOTHING;
     COMMIT;
     ```
     (grant `SELECT` on `corpus.token_lemma` if Ontop connects as another user);
  2. deploy the new image, load the corpora (`loader/load_corpora.py`), and
     then drop the old column: `ALTER TABLE corpus.token DROP COLUMN IF EXISTS id_lemma;`

## [0.4.0] - 2026-11-12
### Added
- Two correction actions: `add-wr` gives a lemma another written
  representation, `add-variant` links two lemmas as lemma variants
  (`lila:lemmaVariant`), following the definitions of Swaelens, Mambrini &
  Passarotti (2026). See `data/corrections/README.md`.
- The initial set of correction based upon PapyGreek linking

## [0.3.0] - 2026-11-12

### Added
- Corrections: anyone can correct the lemmas with a pull request that adds a
  file to `data/corrections/` (one row per change: correct, add, merge or
  retire), with its reason, evidence and author. The loader applies them on
  top of the unchanged source list; corrected lemmas keep their id, merged
  and retired lemmas stay as deprecated. See `CONTRIBUTING.md` and
  `data/corrections/README.md`.
- `scripts/check_corrections.py` and the *Check corrections* workflow check
  every correction pull request, with SHACL shapes for the lemmas
  (`shapes/lemma.shacl.ttl`). An issue form for corrections and a pull
  request template.
- `generate_release.py prepare` records the release of every new correction
  file in `data/corrections/RELEASES.tsv`.
- Retired and merged lemmas keep their `rdfs:label`, so that their IRI still
  shows which lemma it was.

### Changed
- Corpora are loaded generically: `loader/load_corpora.py` loads every corpus
  described in `ttl/corpora/` into one `corpus` schema
  (`database/schema_corpora.sql`), and one part of the mapping serves them
  all, so a new corpus needs no code. It replaces `data/load_papygreek.py` and
  the `papygreek` schema. The endpoint serves the same PapyGreek–LiGre triples.
- The repository is organised by role: `data/` holds only data, `database/`
  the Postgres schema and `loader/` the loaders with their Docker image
  (`data/generate_lemma_data.py` is now `loader/load_lemmas.py`). The Compose
  service `papygreek-loader` is now `corpus-loader`.
- The release check compares the dump with the data in `data/` (lemmas,
  ids, retired lemmas), and validates with SHACL only the lemmas that changed
  since the previous release, using a hash per lemma in
  `ttl/ligre_lemmabank.hashes.tsv`. `prepare` restores every file when a step
  fails.
- The loaders load in one transaction with `COPY`; reading `lemma_ids.tsv` is
  no longer quadratic (43 s to 0.3 s for 100,000 lemmas). The corpus loader
  skips corpora whose release is already loaded, records the SHA-256 of each
  dump, and refuses to run without corpus descriptions.
- Database changes for existing databases, **before** deploying the new Ontop
  image (without them Ontop does not start):
  `ALTER TABLE lemma_replaced ADD COLUMN IF NOT EXISTS label varchar(64);`,
  then `psql -f database/schema_corpora.sql` and `python loader/load_corpora.py`.
  Afterwards the old schema can be dropped: `DROP SCHEMA papygreek CASCADE;`

## [0.2.0] - 2026-11-10

### Added
- The PapyGreek–LiGre corpus in the SPARQL endpoint: its documents, citation
  structures, parts, lines, sentences and tokens, with their links to the
  lemmas, are stored in Postgres (schema `papygreek`, `data/schema_papygreek.sql`)
  and mapped to RDF by Ontop, so the corpus can be queried together with the
  lemma bank and its IRIs resolve. `data/load_papygreek.py` loads the release
  described in `ttl/corpora/PapyGreek_corpus.ttl`; the endpoint serves the same
  triples as that release's dump.

### Changed
- `scripts/export_ttl.py` exports only the lemma bank from the endpoint
  (subjects under `/data/id/lemma/`), now that the endpoint also serves the
  corpus.
- Schema change for existing databases: run `data/schema_papygreek.sql` and
  load the corpus (`data/load_papygreek.py`) **before** deploying the new
  Ontop image; without the `papygreek` tables Ontop does not start.

## [0.1.1] - 2026-11-09

### Added
- The Zenodo concept DOI (10.5281/zenodo.24085996) in the README, `CITATION.cff` and, from this
  release on, as `dcterms:identifier` of the lemma bank in the VoID
  description.
- The PapyGreek–LiGre corpus (release 0.1.1) in the description of the LiGre
  Knowledge Base (`ttl/ligre_void.ttl`), from its release description in
  `ttl/corpora/PapyGreek_corpus.ttl`.

## [0.1.0] - 2026-11-09

This release publishes the lemma list of Swaelens, Mambrini & Passarotti
(2026) as it is, without corrections: the lemmas, parts of speech and genders
are the same as served by the deployed endpoint since v0.0.5. Known errors are
listed in the README.

### Added
- Persistent lemma ids: the id of every lemma, and so its IRI, is fixed in
  `data/lemma_ids.tsv` instead of depending on the order of the source data.
  The ids used by the deployed endpoint since v0.0.5 are kept. Retired
  lemmas keep their IRI, with `owl:deprecated` and `dcterms:isReplacedBy`
  (new table `lemma_replaced`).
- Dataset descriptions in Dublin Core, DCAT and VoID for the lemma bank
  (`ttl/lemmabank_description.ttl`) and for the LiGre Knowledge Base
  (`ttl/knowledge_base_description.ttl`), with VoID statistics written by
  `scripts/export_ttl.py` to `ttl/lemmabank_void.ttl` and `ttl/ligre_void.ttl`.
- Example SPARQL queries in `queries/`.
- Licences (data CC BY-SA 4.0, code MIT), `CITATION.cff` and `.zenodo.json`
  for archiving releases on Zenodo.

### Changed
- The endpoint serves `ttl/ligre_void.ttl` as static facts, so the IRIs of the
  knowledge base, the lemma bank and the corpora resolve to their descriptions.
  The Ontop image is now built from the repository root.
- Schema change for existing databases: create the table `lemma_replaced`
  (see `data/schema.sql`).
- The data dump is renamed from `ttl/ligreTTLRDF.ttl` to
  `ttl/ligre_lemmabank.ttl`.

### Removed
- The tables and columns of `data/schema.sql` that were never loaded or
  mapped to RDF (bases, hypolemmas, prefixes, suffixes, phonetic
  representations, `ligre_lu`, and the `lemma` columns `infl_cat`, `p` and
  `grad`). Existing databases keep working; the tables can be dropped.

[Unreleased]: https://github.com/ligre-lod/ligre_lemmabank/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/ligre-lod/ligre_lemmabank/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/ligre-lod/ligre_lemmabank/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/ligre-lod/ligre_lemmabank/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/ligre-lod/ligre_lemmabank/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/ligre-lod/ligre_lemmabank/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/ligre-lod/ligre_lemmabank/compare/v0.0.6...v0.1.0
