# Changelog

All notable changes to the LiGre Lemma Bank are listed here. Releases follow
[semantic versioning](https://semver.org/).

The tags v0.0.1 to v0.0.6 were development versions, not published releases:
they have no GitHub release and no DOI. Since v0.0.5 the deployed endpoint has
minted lemma IRIs under `https://w3id.org/ligre`.

## [Unreleased]

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

[Unreleased]: https://github.com/ligre-lod/ligre_lemmabank/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ligre-lod/ligre_lemmabank/compare/v0.0.6...v0.1.0
