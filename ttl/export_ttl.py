#!/usr/bin/env python3
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from collections import Counter

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD

CONSTRUCT_QUERY = "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }"

LEMMA_BANK = URIRef("https://w3id.org/ligre/data/id/lemma/LemmaBank")
DESCRIPTION_PATH = Path(__file__).with_name("lemmabank_description.ttl")
VOID = Namespace("http://rdfs.org/ns/void#")

PREFIXES = {
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "dcterms": "http://purl.org/dc/terms/",
    "ontolex": "http://www.w3.org/ns/lemon/ontolex#",
    "lila": "http://lila-erc.eu/ontologies/lila/",
    "void": str(VOID),
    "dcat": "http://www.w3.org/ns/dcat#",
    "foaf": "http://xmlns.com/foaf/0.1/",
}


def remove_description(graph, description):
    for subject in set(description.subjects()):
        if isinstance(subject, BNode):
            continue
        graph.remove((subject, None, None))
    for subject in [subject for subject in set(graph.subjects()) if isinstance(subject, BNode)]:
        graph.remove((subject, None, None))


def add_void_statistics(graph, dataset):
    def integer(value):
        return Literal(value, datatype=XSD.integer)

    instances = Counter(rdf_class for rdf_class in graph.objects(None, RDF.type))
    properties = Counter(predicate for predicate in graph.predicates())
    statistics = [
        (dataset, VOID.triples, integer(len(graph))),
        (dataset, VOID.entities, integer(len({subject for subject in graph.subjects() if isinstance(subject, URIRef)}))),
        (dataset, VOID.classes, integer(len(instances))),
        (dataset, VOID.properties, integer(len(properties))),
    ]
    for rdf_class, count in sorted(instances.items()):
        partition = BNode()
        statistics += [(dataset, VOID.classPartition, partition), (partition, VOID["class"], rdf_class),
                       (partition, VOID.entities, integer(count))]
    for rdf_property, count in sorted(properties.items()):
        partition = BNode()
        statistics += [(dataset, VOID.propertyPartition, partition), (partition, VOID.property, rdf_property),
                       (partition, VOID.triples, integer(count))]
    for triple in statistics:
        graph.add(triple)


def describe(graph):
    description = Graph().parse(DESCRIPTION_PATH, format="turtle")
    remove_description(graph, description)
    add_void_statistics(graph, LEMMA_BANK)
    graph += description


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
    out_path = Path(os.environ.get("TTL_OUTPUT", "/app/ttl/ligre_lemmabank.ttl"))

    graph = Graph()
    input_path = os.environ.get("TTL_INPUT")
    if input_path:
        graph.parse(input_path, format="turtle")
    else:
        print(f"fetching triples from {sparql_url}...")
        nt_data = fetch_construct(sparql_url)
        print(f"fetched {len(nt_data)} bytes of N-Triples")
        graph.parse(data=nt_data, format="nt")
    print(f"parsed {len(graph)} triples")
    describe(graph)
    print(f"added the dataset description from {DESCRIPTION_PATH.name}")

    for prefix, uri in PREFIXES.items():
        graph.bind(prefix, Namespace(uri))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(destination=str(out_path), format="turtle")
    print(f"wrote {out_path} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
