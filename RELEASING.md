# Releasing

Each release is a `vMAJOR.MINOR.PATCH` tag on `main` with a GitHub release.
The tag builds the Ontop Docker image; the GitHub release is archived on
Zenodo with a DOI.

## One-time setup

1. Sign in to <https://zenodo.org> with GitHub, open
   *Settings → GitHub*, and switch on `ligre-lod/ligre_lemmabank`. This needs
   admin rights on the `ligre-lod` organisation.
2. Zenodo takes the metadata from `.zenodo.json` (title, creators, licence,
   keywords, related identifiers). The version is the tag name.

## Release steps

1. **Data.** Update the source tables (`data/`), update the lemma ids
   (`python data/generate_lemma_data.py --assign-ids`; check the new, kept
   and retired ids it prints, and commit `data/lemma_ids.tsv`), load them
   (`docker compose run --rm lemma-loader`), and export the dump from the
   running endpoint with `ttl/export_ttl.py` (set `ONTOP_SPARQL_URL`, e.g.
   `http://localhost:8081/sparql`, and `TTL_OUTPUT=ttl/ligre_lemmabank.ttl`).
2. **Version and date.** Set the new version and release date in
   - `ttl/lemmabank_description.ttl`: `dcat:version`, both `dcterms:issued`,
     and the tag in `void:dataDump`, `dcat:downloadURL` and `dcat:accessURL`;
   - `CITATION.cff`: `version` and `date-released`;
   - `CHANGELOG.md`: move the changes under the new version and date.
3. **Regenerate the descriptions** so that the dump and the VoID files carry
   the new metadata and statistics:

   ```bash
   TTL_INPUT=ttl/ligre_lemmabank.ttl TTL_OUTPUT=ttl/ligre_lemmabank.ttl VOID_OUTPUT=ttl/ligre_void.ttl \
     VOID_INCLUDE=ttl/knowledge_base_description.ttl:../../papygreek-to-ligre/ttl/PapyGreek_corpus.ttl \
     python ttl/export_ttl.py
   TTL_INPUT=ttl/ligre_lemmabank.ttl TTL_OUTPUT=ttl/ligre_lemmabank.ttl python ttl/export_ttl.py
   ```

   The first command writes the knowledge base description to
   `ttl/ligre_void.ttl`; the second rewrites `ttl/lemmabank_void.ttl`.
4. **Check** that the example queries still run, and update the statistics
   in the README if they changed.
5. **Commit, tag and push:**

   ```bash
   git tag -a v0.1.0 -m "LiGre Lemma Bank 0.1.0"
   git push origin main v0.1.0
   ```

6. **GitHub release.** Create a release from the tag (web UI or
   `gh release create v0.1.0 --notes-file …`) with the changelog entry as
   notes. Zenodo archives it and mints the DOIs.
7. **Deploy.** Redeploy the endpoint with the new image (it contains the new
   `ttl/ligre_void.ttl` as static facts, so the dataset IRIs show the new
   description), apply any schema changes listed in the changelog, and copy
   `ttl/ligre_void.ttl` to `ligre-lod/.well-known/void` and `void.ttl`.

## After the first Zenodo release

Zenodo mints the DOIs only when the first release is archived, so
release 0.1.0 cannot contain its own DOI. Afterwards:

1. Add the concept DOI (the one for all versions) to
   `ttl/lemmabank_description.ttl` as `dcterms:identifier`, to the README
   badge, and to `CITATION.cff` as `doi`.
2. Release these metadata changes as a patch release (0.1.1).
