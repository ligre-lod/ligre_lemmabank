#!/usr/bin/env python3
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from rdflib import Graph, Namespace

CONSTRUCT_QUERY = "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }"

# Only the ontology vocabulary gets a bound prefix (so terms like lila:hasGender /
# lila:feminine get abbreviated), matching liitaTTLRDF.ttl's style. Data-identifier
# namespaces (lemma/hypolemma/prefix/suffix/base ids) are deliberately left unbound
# so their IRIs stay fully expanded, exactly as liitaTTLRDF.ttl does.
PREFIXES = {
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "dcterms": "http://purl.org/dc/terms/",
    "ontolex": "http://www.w3.org/ns/lemon/ontolex#",
    "lila": "http://lila-erc.eu/ontologies/lila/",
}


def fetch_construct(sparql_url, retries=30, delay=2, timeout=300):
    url = f"{sparql_url}?{urllib.parse.urlencode({'query': CONSTRUCT_QUERY})}"
    req = urllib.request.Request(url, headers={"Accept": "application/n-triples"})
    last_err = None
    for _ in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            last_err = e
            time.sleep(delay)
    raise last_err


def main():
    sparql_url = os.environ.get("ONTOP_SPARQL_URL", "http://ontop:8080/sparql")
    out_path = Path(os.environ.get("TTL_OUTPUT", "/app/ttl/ligreTTLRDF.ttl"))

    print(f"fetching triples from {sparql_url}...")
    nt_data = fetch_construct(sparql_url)
    print(f"fetched {len(nt_data)} bytes of N-Triples")

    graph = Graph()
    graph.parse(data=nt_data, format="nt")
    print(f"parsed {len(graph)} triples")

    for prefix, uri in PREFIXES.items():
        graph.bind(prefix, Namespace(uri))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(out_path), format="turtle")
    print(f"wrote {out_path} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
