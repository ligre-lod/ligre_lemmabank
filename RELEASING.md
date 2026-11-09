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
   (`docker compose run --rm lemma-loader`), and export the dump from the
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
   statistics. The PapyGreek corpus description is read from
   `../../papygreek-to-ligre/ttl/PapyGreek_corpus.ttl`; set
   `PAPYGREEK_CORPUS` if it is elsewhere.
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
6. **Deploy.** Redeploy the endpoint with the new image (it contains the new
   `ttl/ligre_void.ttl` as static facts), apply any schema changes listed in
   the changelog, and copy `ttl/ligre_void.ttl` to `ligre-lod/.well-known/void`
   and `void.ttl`.
