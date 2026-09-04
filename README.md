# ligre lemmabank

LiGre (Lemma Bank for Ancient Greek) is a linked open data resource that
publishes lemmatized Ancient Greek vocabulary as structured, interlinked
RDF data. Each lemma is modeled using the [OntoLex-Lemon](https://www.w3.org/community/ontolex/)
vocabulary and the [LiLa](https://lila-erc.eu/) `Lemma` class, so that
Ancient Greek lemmas can be published, queried, and linked following the
same conventions as the broader Linked Data knowledge base for the
Latin language built by the [LiLa project](https://lila-erc.eu/).

The design and rationale behind the resource are described in the paper
*"From Lemmas to Links: A Lemma Bank for Ancient Greek"*. If you use LiGre
in your research, please cite:

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

The project has three parts:

- **`data/`** — a Postgres schema and a loader script that populate the
  lemma bank from source TSV data.
- **`ontop/`** — an [Ontop](https://ontop-vkg.org/) configuration that maps
  the Postgres database to RDF on the fly and exposes it as a SPARQL
  endpoint, plus a [LodView](https://github.com/dati-semantic/lodview)
  instance for browsing individual resources.
- **`query-interface/`** — a React frontend that lets users search and
  browse the lemma bank through the SPARQL endpoint, deployed at
  [ligre-lod.github.io/query-interface](https://ligre-lod.github.io/query-interface/).

## Local setup

For local development, everything runs through the top-level
`docker-compose.yml`:

```bash
docker compose up
```

This starts:

- `postgres` — a local Postgres instance, initialized with `data/schema.sql`
- `lemma-loader` — a one-shot job that populates the database from the
  source data (re-run with `docker compose run --rm lemma-loader`)
- `ontop` — the SPARQL endpoint, backed by the local Postgres instance
- `lodview` — a browsable UI for individual RDF resources, backed by `ontop`

Once it's up, the SPARQL endpoint is available at `http://localhost:8081`
and LodView at `http://localhost:8082`.

## Remote setup

The remote deployment doesn't run the full compose stack — the database is
managed separately from the RDF backend:

- **Database** — the schema is created manually on the remote Postgres
  server (using `data/schema.sql`), and populated from a `pg_dump` data
  dump produced locally and transferred to the server, rather than by
  running `lemma-loader` against the remote database directly.
- **Backend** — only the `ontop` container (and `lodview`) run on the
  server, pointed at that remote Postgres instance, serving the SPARQL
  endpoint and resource pages.
- **Frontend** — the [query-interface](https://ligre-lod.github.io/query-interface/)
  is a static React app, built and served through GitHub Pages, which
  talks to the remote `ontop` SPARQL endpoint.
