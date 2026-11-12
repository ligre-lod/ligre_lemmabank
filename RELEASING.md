# Releasing

Each release is a `vMAJOR.MINOR.PATCH` tag on `main`. Pushing the tag builds
the Ontop Docker image and creates the GitHub release, which is archived on
Zenodo with a DOI.

The version and release date are set in one place, `CITATION.cff`, by
`scripts/generate_release.py`; the dataset descriptions take them from there.

## Release steps

1. **Changelog.** List the changes under `## [Unreleased]` in `CHANGELOG.md`.
2. **Data** (only if the source data changed or corrections were merged in
   `data/corrections/`). The source tables in `data/` stay as published; the
   loader applies the corrections on top of them. Update the lemma ids
   (`python loader/load_lemmas.py --assign-ids`; check the new, kept and
   retired ids it prints, which `scripts/check_corrections.py` also previews), load them
   (`docker compose run --rm lemma-loader`), start Ontop with the published
   base URL (`LIGRE_BASE_URL=https://w3id.org/ligre docker compose up -d ontop`;
   with the default `localhost` the dump gets the wrong IRIs and the
   statistics count the dataset description), and export the dump from the
   running endpoint:

   ```bash
   ONTOP_SPARQL_URL=http://localhost:8081/sparql TTL_OUTPUT=ttl/ligre_lemmabank.ttl python scripts/export_ttl.py
   ```

3. **Prepare the release:**

   ```bash
   uv run --with rdflib --with pyshacl python scripts/generate_release.py prepare 0.1.0
   ```

   This moves the unreleased changes in `CHANGELOG.md` under the new version
   and today's date, sets both in `CITATION.cff`, records the release of the
   new correction files in `data/corrections/RELEASES.tsv`, regenerates the
   dump, `ttl/lemmabank_void.ttl` and `ttl/ligre_void.ttl` with the new
   metadata and statistics, and validates the dump: its lemmas must be exactly
   those that `loader/load_lemmas.py` builds from `data/` (so a dump exported
   before the last corrections is refused), and the lemmas that changed since
   the previous release must conform to `shapes/lemma.shacl.ttl`. It then
   writes `ttl/ligre_lemmabank.hashes.tsv` (a hash per lemma), which is
   committed with the release and tells the next release which lemmas
   changed; the release workflow checks the dump the same way. If any step
   fails, `prepare` puts every file back as it was, so it can simply be run
   again. `ttl/ligre_void.ttl` also includes the descriptions of the
   released corpora in `ttl/corpora/`. When a corpus is released, copy its
   description from that release into `ttl/corpora/` (for PapyGreek–LiGre,
   `ttl/corpora/PapyGreek_corpus.ttl`); a new corpus also goes into `dcat:dataset`
   and `void:subset` in `ttl/knowledge_base_description.ttl`.
4. **Check** that the example queries in `queries/` still run.
5. **Commit, tag and push:**

   ```bash
   git commit -am "Release 0.1.0"
   git tag -a v0.1.0 -m "LiGre Lemma Bank 0.1.0"
   git push origin main v0.1.0
   ```

   The release workflow (`.github/workflows/release.yaml`) checks that
   `CHANGELOG.md`, `CITATION.cff` and the VoID files all describe the tagged
   version, and creates the GitHub release with the changelog entry as notes.
   If they do not match, no release is made: fix the metadata, move the tag,
   and push again.
6. **Upgrade the production database** before deploying, if
   `database/schema.sql` or `database/schema_corpora.sql` changed since the
   previous release (`git diff vPREVIOUS vNEW -- database/`). `schema.sql` only runs when
   Postgres starts on an empty volume, so it never reaches an existing
   database: apply each change by hand, taking the statements for the
   changed tables from `database/schema.sql` (list schema changes in the
   changelog, so this step is not missed). Otherwise the new Ontop image fails to start
   (`Cannot find relation ...`) and the endpoint returns 503. Connect with
   the `ONTOP_DB_URL` and `ONTOP_DB_USER` of the deployment (UGent network
   or VPN):

   ```bash
   psql -h <host> -p 5432 -U <user> -d <database>
   ```

   Run the SQL from the changelog (`CREATE TABLE IF NOT EXISTS ...`, so it is
   safe to run twice), check it with `\d <table>`, and if Ontop connects as
   another user, grant it `SELECT` on the new tables. Tables and columns that
   were removed from `schema.sql` can stay; nothing reads them.

   `database/schema_corpora.sql` creates its tables with `IF NOT EXISTS`, so
   run it as a whole (`psql ... -f database/schema_corpora.sql`).

   **Load the corpora** if a corpus release changed (its description in
   `ttl/corpora/`) or the corpus tables were created. The loader downloads
   the dump of every corpus release described in `ttl/corpora/`, checks it,
   and replaces that corpus in the `corpus` tables (corpora no longer in
   `ttl/corpora/` are removed); it needs the lemmas to be loaded already:

   ```bash
   POSTGRES_HOST=<host> POSTGRES_USER=<user> POSTGRES_PASSWORD=<password> POSTGRES_DATABASE=<database> \
     python loader/load_corpora.py
   ```

   It stores the corpus IRIs under `LIGRE_BASE_URL` (default
   `https://w3id.org/ligre`), which must be the base URL of the endpoint. A
   corpus whose release is already loaded is skipped (`--force` reloads it).
   It refuses to run without any description in `ttl/corpora/`, and warns
   when a corpus links tokens to lemmas that were merged or retired.
7. **Deploy.** Redeploy the endpoint with the new image (it contains the new
   `ttl/ligre_void.ttl` as static facts) and check that a lemma IRI, e.g.
   <https://w3id.org/ligre/data/id/lemma/15308>, and the SPARQL UI load.
   Copy `ttl/ligre_void.ttl` of the release to `.well-known/void` and
   `.well-known/void.ttl` in the
   [ligre-lod](https://github.com/ligre-lod/ligre-lod) repository.
