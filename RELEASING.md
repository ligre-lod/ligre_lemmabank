# Releasing

Each release is a `vMAJOR.MINOR.PATCH` tag on `main`. Pushing the tag builds
the Ontop Docker image and creates the GitHub release, which is archived on
Zenodo with a DOI.

The version and release date are set in one place, `CITATION.cff`, by
`scripts/generate_release.py`; the dataset descriptions take them from there.

## Release steps

1. **Changelog.** List the changes under `## [Unreleased]` in `CHANGELOG.md`.
2. **Data** (only if the source data changed). Update the source tables
   (`data/`); the loader publishes them as they are, without corrections.
   Update the lemma ids (`python data/generate_lemma_data.py --assign-ids`;
   check the new, kept and retired ids it prints), load them
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
   python scripts/generate_release.py prepare 0.1.0
   ```

   This moves the unreleased changes in `CHANGELOG.md` under the new version
   and today's date, sets both in `CITATION.cff`, and regenerates the dump,
   `ttl/lemmabank_void.ttl` and `ttl/ligre_void.ttl` with the new metadata and
   statistics. `ttl/ligre_void.ttl` also includes the descriptions of the
   released corpora in `ttl/corpora/`. When a corpus is released, copy its
   description from that release into `ttl/corpora/` (for PapyGreek–LiGre,
   `ttl/PapyGreek_corpus.ttl`); a new corpus also goes into `dcat:dataset`
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
   `data/schema.sql` or `data/schema_papygreek.sql` changed since the previous
   release (`git diff vPREVIOUS vNEW -- data/schema*.sql`). `schema.sql` only runs when
   Postgres starts on an empty volume, so it never reaches an existing
   database: apply each change by hand, taking the statements for the
   changed tables from `data/schema.sql` (list schema changes in the
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

   `data/schema_papygreek.sql` creates its tables with `IF NOT EXISTS`, so run
   it as a whole (`psql ... -f data/schema_papygreek.sql`).

   **Load the corpora** if a corpus release changed (its description in
   `ttl/corpora/`) or the corpus tables were created. The loader downloads
   the dump of the release that `ttl/corpora/PapyGreek_corpus.ttl` describes,
   checks it, and replaces the contents of the `papygreek` tables; it needs the
   lemmas to be loaded already:

   ```bash
   POSTGRES_HOST=<host> POSTGRES_USER=<user> POSTGRES_PASSWORD=<password> POSTGRES_DATABASE=<database> \
     python data/load_papygreek.py
   ```
7. **Deploy.** Redeploy the endpoint with the new image (it contains the new
   `ttl/ligre_void.ttl` as static facts) and check that a lemma IRI, e.g.
   <https://w3id.org/ligre/data/id/lemma/15308>, and the SPARQL UI load.
   Copy `ttl/ligre_void.ttl` of the release to `.well-known/void` and
   `.well-known/void.ttl` in the
   [ligre-lod](https://github.com/ligre-lod/ligre-lod) repository.
