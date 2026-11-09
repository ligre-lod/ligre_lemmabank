# Changelog

All notable changes to the LiGre Lemma Bank are listed here. Releases follow
[semantic versioning](https://semver.org/).

## [Unreleased]

This release publishes the lemma list of Swaelens, Mambrini & Passarotti
(2026) as it is, without corrections: the lemmas, parts of speech and genders
are the same as in release 0.0.5. Known errors are listed in the README.

### Added
- Persistent lemma ids: the id of every lemma, and so its IRI, is fixed in
  `data/lemma_ids.tsv` instead of depending on the order of the source data.
  The ids of release 0.0.5 are kept. Retired lemmas keep their IRI, with
  `owl:deprecated` and `dcterms:isReplacedBy` (new table `lemma_replaced`).
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

## [0.0.5] - 2026-10-28

### Changed
- Lemma IRIs are minted under the persistent namespace
  `https://w3id.org/ligre` in deployments, and under `localhost` locally.

## [0.0.4] - 2026-09-08

### Changed
- The base URL of the IRIs is configurable (`LIGRE_BASE_URL`).

[Unreleased]: https://github.com/ligre-lod/ligre_lemmabank/compare/v0.0.5...HEAD
[0.0.5]: https://github.com/ligre-lod/ligre_lemmabank/compare/v0.0.4...v0.0.5
[0.0.4]: https://github.com/ligre-lod/ligre_lemmabank/compare/v0.0.3...v0.0.4
