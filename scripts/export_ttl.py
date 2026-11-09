#!/usr/bin/env python3
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from collections import Counter

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF, XSD

CONSTRUCT_QUERY = "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }"

LEMMA_BANK = URIRef("https://w3id.org/ligre/data/id/lemma/LemmaBank")
ROOT = Path(__file__).resolve().parent.parent
DESCRIPTION_PATH = ROOT / "ttl" / "lemmabank_description.ttl"
CITATION_PATH = ROOT / "CITATION.cff"
REPOSITORY = "ligre-lod/ligre_lemmabank"
VOID = Namespace("http://rdfs.org/ns/void#")
DCAT = Namespace("http://www.w3.org/ns/dcat#")

PREFIXES = {
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "dcterms": "http://purl.org/dc/terms/",
    "ontolex": "http://www.w3.org/ns/lemon/ontolex#",
    "lila": "http://lila-erc.eu/ontologies/lila/",
    "void": str(VOID),
    "dcat": str(DCAT),
    "foaf": "http://xmlns.com/foaf/0.1/",
}
VOID_PREFIXES = {
    **PREFIXES,
    "powla": "http://purl.org/powla/powla.owl#",
    "lila_corpus": "http://lila-erc.eu/ontologies/lila_corpora/",
}


def keep_lemmas(graph):
    for subject in set(graph.subjects()):
        if not (isinstance(subject, URIRef) and "/data/id/lemma/" in str(subject)):
            graph.remove((subject, None, None))


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
    return statistics


def release():
    fields = dict(re.findall(r"^(version|date-released|doi):\s*\"?([^\s\"]+)\"?\s*$", CITATION_PATH.read_text(), re.M))
    return fields["version"], fields["date-released"], fields.get("doi")


def add_release(description):
    version, date, doi = release()
    tag = f"v{version}"
    dump = URIRef(f"https://raw.githubusercontent.com/{REPOSITORY}/{tag}/ttl/ligre_lemmabank.ttl")
    issued = Literal(date, datatype=XSD.date)
    distribution = BNode()
    for triple in [
        (LEMMA_BANK, DCAT.version, Literal(version)),
        (LEMMA_BANK, DCTERMS.issued, issued),
        (LEMMA_BANK, VOID.dataDump, dump),
        (LEMMA_BANK, DCAT.distribution, distribution),
        (distribution, RDF.type, DCAT.Distribution),
        (distribution, DCTERMS.title, Literal("All lemmas in Turtle", lang="en")),
        (distribution, DCTERMS.issued, issued),
        (distribution, DCTERMS.license, URIRef("https://creativecommons.org/licenses/by-sa/4.0/")),
        (distribution, DCAT.accessURL, URIRef(f"https://github.com/{REPOSITORY}/releases/tag/{tag}")),
        (distribution, DCAT.downloadURL, dump),
        (distribution, DCAT.mediaType, URIRef("https://www.iana.org/assignments/media-types/text/turtle")),
    ]:
        description.add(triple)
    if doi:
        description.add((LEMMA_BANK, DCTERMS.identifier, Literal(f"https://doi.org/{doi}")))


def describe(graph):
    description = Graph().parse(DESCRIPTION_PATH, format="turtle")
    add_release(description)
    remove_description(graph, description)
    statistics = add_void_statistics(graph, LEMMA_BANK)
    graph += description
    for triple in statistics:
        description.add(triple)
    return description


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
    out_path = Path(os.environ.get("TTL_OUTPUT", ROOT / "ttl" / "ligre_lemmabank.ttl"))
    void_path = Path(os.environ.get("VOID_OUTPUT", out_path.with_name("lemmabank_void.ttl")))

    graph = Graph()
    input_path = os.environ.get("TTL_INPUT")
    if input_path:
        graph.parse(input_path, format="turtle")
    else:
        print(f"fetching triples from {sparql_url}...")
        nt_data = fetch_construct(sparql_url)
        print(f"fetched {len(nt_data)} bytes of N-Triples")
        graph.parse(data=nt_data, format="nt")
        keep_lemmas(graph)
    print(f"parsed {len(graph)} triples")
    void_graph = describe(graph)
    print(f"added the dataset description from {DESCRIPTION_PATH.name}")
    for include_path in filter(None, os.environ.get("VOID_INCLUDE", "").split(os.pathsep)):
        void_graph.parse(include_path, format="turtle")
        print(f"added {include_path} to the VoID description")

    for output_graph, path, prefixes in ((graph, out_path, PREFIXES), (void_graph, void_path, VOID_PREFIXES)):
        for prefix, uri in prefixes.items():
            output_graph.bind(prefix, Namespace(uri))
        path.parent.mkdir(parents=True, exist_ok=True)
        output_graph.serialize(destination=str(path), format="turtle")
        print(f"wrote {path} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
