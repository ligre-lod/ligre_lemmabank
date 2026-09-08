# LiGre Lemmabank

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

The project has several components:

- **`data/`** — a Postgres schema and a loader script that populate the
  lemma bank from source TSV data.
- **`ontop/`** — an [Ontop](https://ontop-vkg.org/) configuration that maps
  the Postgres database to RDF on the fly and exposes it as an endpoint 
- **`ttl/` - A .ttl file containing the live data deployed from /data and exposed via /ontop, formatted based on the Lila ontology
- A [LodView](https://github.com/dati-semantic/lodview)
  instance for visualizing individual resources, launched via the docker-compose file 
- **`query-interface/`** —  (https://github.com/ligre-lod/query-interface) a React frontend that lets users search and
  browse the lemma bank through the SPARQL endpoint, deployed at
  [ligre-lod.github.io/query-interface](https://ligre-lod.github.io/query-interface/). This repository was forked from the Linking Italian project (https://github.com/LiITA-LOD/query-interface)

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
and LodView at `http://localhost:8082`. Launch the query-interface from https://github.com/ligre-lod/query-interface  for running the full local stack.
