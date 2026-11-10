#!/usr/bin/env python3
"""Load a PapyGreek–LiGre release into the papygreek schema (data/schema_papygreek.sql).

The release is the one described in ttl/corpora/PapyGreek_corpus.ttl: its data dump
(dcat:downloadURL) is downloaded, or read from --input. The Ontop mapping publishes the
tables again as the same triples; the loader refuses a dump that the tables cannot
reproduce (see check_derived).
"""
import argparse
import gzip
import io
import os
import time
import urllib.request
from pathlib import Path
from urllib.parse import unquote

import psycopg2
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import DC, DCAT, DCTERMS, RDF, RDFS

POWLA = Namespace("http://purl.org/powla/powla.owl#")
CORPUS_ONTOLOGY = Namespace("http://lila-erc.eu/ontologies/lila_corpora/")
LILA = Namespace("http://lila-erc.eu/ontologies/lila/")
CORPUS = "https://w3id.org/ligre/data/corpora/PapyGreek/id/corpus"
LEMMA = "https://w3id.org/ligre/data/id/lemma/"
REPO_ROOT = Path(__file__).resolve().parent.parent
DESCRIPTION = REPO_ROOT / "ttl" / "corpora" / "PapyGreek_corpus.ttl"
TABLES = ["token", "sentence", "linea", "pars", "citation_structure", "document_see_also",
          "document_identifier", "document"]


class Dump:
    """The triples of the dump, with the IRIs split into document, layer, part, line and token."""

    def __init__(self, graph):
        self.graph = graph

    @staticmethod
    def path(iri):
        text = str(iri)
        if not text.startswith(CORPUS + "/"):
            raise ValueError(f"not a PapyGreek IRI: {text}")
        return [unquote(part) for part in text[len(CORPUS) + 1:].split("/")]

    @staticmethod
    def position(iri):
        doc_id, local = Dump.path(iri)
        if not local.startswith(f"{doc_id}_t_") or len(local) != len(doc_id) + 10:
            raise ValueError(f"not a token IRI: {iri}")
        return doc_id, int(local[-7:])

    def value(self, subject, predicate):
        value = self.graph.value(subject, predicate)
        return None if value is None else str(value)

    def last(self, subject, predicate):
        value = self.graph.value(subject, predicate)
        return None if value is None else self.path(value)[-1]

    def of_type(self, rdf_class):
        return sorted(self.graph.subjects(RDF.type, rdf_class), key=str)


def read_dump(input_path):
    if input_path is None:
        description = Graph().parse(DESCRIPTION, format="turtle")
        urls = [str(url) for url in description.objects(None, DCAT.downloadURL)]
        if len(urls) != 1:
            raise SystemExit(f"{DESCRIPTION} should have one dcat:downloadURL, found {urls}")
        print(f"downloading {urls[0]}...")
        with urllib.request.urlopen(urls[0], timeout=300) as response:
            data = response.read()
    else:
        data = Path(input_path).read_bytes()
    text = gzip.decompress(data).decode("utf-8") if data[:2] == b"\x1f\x8b" else data.decode("utf-8")
    graph = Graph().parse(data=text, format="turtle")
    print(f"parsed {len(graph)} triples")
    return Dump(graph)


def build_rows(dump):
    g = dump.graph
    rows = {table: [] for table in TABLES}
    for document in dump.of_type(POWLA.Document):
        (doc_id,) = dump.path(document)
        rows["document"].append((doc_id, dump.value(document, DC.title)))
        rows["document_identifier"] += [(doc_id, str(i)) for i in g.objects(document, DCTERMS.identifier)]
        rows["document_see_also"] += [(doc_id, str(u)) for u in g.objects(document, RDFS.seeAlso)]
    for structure in dump.of_type(CORPUS_ONTOLOGY.CitationStructure):
        doc_id, layer = dump.path(structure)
        rows["citation_structure"].append((doc_id, layer, dump.value(structure, DC.title),
                                           dump.value(structure, DC.description),
                                           dump.last(structure, CORPUS_ONTOLOGY.first)))
    for unit in dump.of_type(CORPUS_ONTOLOGY.citationUnit):
        path = dump.path(unit)
        label = dump.value(unit, RDFS.label)
        if path[-1] != dump.value(unit, CORPUS_ONTOLOGY.hasRefValue):
            raise ValueError(f"the citation value of {unit} differs from its IRI")
        first, last = g.value(unit, CORPUS_ONTOLOGY.first), g.value(unit, CORPUS_ONTOLOGY.last)
        if path[1] == "CiteStructure" and len(path) == 3:
            rows["pars"].append((path[0], path[2], label, dump.path(first)[-1], dump.path(last)[-1],
                                 dump.last(unit, POWLA.next)))
        elif path[1] == "CiteStructure" and len(path) == 4:
            rows["linea"].append((path[0], path[2], path[3], label, dump.position(first)[1],
                                  dump.position(last)[1], dump.last(unit, POWLA.next)))
        elif path[1] == "SentenceLayer" and len(path) == 3:
            rows["sentence"].append((path[0], path[2], label, dump.position(first)[1],
                                     dump.position(last)[1], dump.last(unit, POWLA.next)))
        else:
            raise ValueError(f"unknown citation unit: {unit}")
    parents = {}
    for unit, token in g.subject_objects(POWLA.hasChild):
        parents.setdefault(token, []).append(dump.path(unit))
    for token in dump.of_type(POWLA.Terminal):
        doc_id, position = dump.position(token)
        lemma = g.value(token, LILA.hasLemma)
        if lemma is not None and not str(lemma).startswith(LEMMA):
            raise ValueError(f"{token} links to a lemma outside LiGre: {lemma}")
        following = g.value(token, POWLA.next)
        pars = linea = sentence = None
        for path in parents.get(token, []):
            if path[1] == "CiteStructure":
                pars, linea = path[2], path[3]
            else:
                sentence = path[2]
        rows["token"].append((doc_id, position, dump.value(token, POWLA.hasStringValue),
                              dump.value(token, RDFS.label),
                              None if lemma is None else int(str(lemma)[len(LEMMA):]),
                              None if following is None else dump.position(following)[1],
                              pars, linea, sentence))
    return rows


def check_derived(dump, rows):
    """The mapping derives these triples from the tables; check that they are the ones in the dump."""
    g = dump.graph
    expected = {
        "previous": {(s, o) for s, o in g.subject_objects(POWLA.previous)},
        "hasCitSubUnit": {(s, o) for s, o in g.subject_objects(CORPUS_ONTOLOGY.hasCitSubUnit)},
        "isLayer": {(s, o) for s, o in g.subject_objects(CORPUS_ONTOLOGY.isLayer)},
        "hasChild": {(s, o) for s, o in g.subject_objects(POWLA.hasChild)},
        "hasCitStructure": {(s, o) for s, o in g.subject_objects(CORPUS_ONTOLOGY.hasCitStructure)},
        "hasDocument": {(s, o) for s, o in g.subject_objects(POWLA.hasDocument)},
    }
    iri = lambda *parts: URIRef("/".join([CORPUS, *(p.replace("%", "%25").replace("/", "%2F").replace(",", "%2C") for p in parts)]))
    token_iri = lambda doc_id, position: iri(doc_id, f"{doc_id}_t_{position:07d}")
    derived = {key: set() for key in expected}
    for doc_id, pars, _label, _first, _last, following in rows["pars"]:
        derived["isLayer"].add((iri(doc_id, "CiteStructure"), iri(doc_id, "CiteStructure", pars)))
        if following:
            derived["previous"].add((iri(doc_id, "CiteStructure", following), iri(doc_id, "CiteStructure", pars)))
    for doc_id, pars, linea, _label, _first, _last, following in rows["linea"]:
        derived["hasCitSubUnit"].add((iri(doc_id, "CiteStructure", pars), iri(doc_id, "CiteStructure", pars, linea)))
        if following:
            derived["previous"].add((iri(doc_id, "CiteStructure", pars, following),
                                     iri(doc_id, "CiteStructure", pars, linea)))
    for doc_id, sentence, _label, _first, _last, following in rows["sentence"]:
        derived["isLayer"].add((iri(doc_id, "SentenceLayer"), iri(doc_id, "SentenceLayer", sentence)))
        if following:
            derived["previous"].add((iri(doc_id, "SentenceLayer", following), iri(doc_id, "SentenceLayer", sentence)))
    for doc_id, layer, *_rest in rows["citation_structure"]:
        derived["hasDocument"].add((iri(doc_id, layer), iri(doc_id)))
    for doc_id, position, _value, _label, _lemma, following, pars, linea, sentence in rows["token"]:
        token = token_iri(doc_id, position)
        if following:
            derived["previous"].add((token_iri(doc_id, following), token))
        derived["hasChild"].add((iri(doc_id, "SentenceLayer", sentence), token))
        derived["hasCitStructure"].add((token, iri(doc_id, "SentenceLayer")))
        if linea is not None:
            derived["hasChild"].add((iri(doc_id, "CiteStructure", pars, linea), token))
            derived["hasCitStructure"].add((token, iri(doc_id, "CiteStructure")))
    errors = [f"{key}: {len(expected[key] ^ derived[key])} triples differ" for key in expected
              if expected[key] != derived[key]]
    for unit in dump.of_type(CORPUS_ONTOLOGY.citationUnit):
        path = dump.path(unit)
        level, ref_type = int(g.value(unit, CORPUS_ONTOLOGY.hasCitLevel)), dump.value(unit, CORPUS_ONTOLOGY.hasRefType)
        if (level, ref_type) != (len(path) - 2, path[-1].split("_")[0]):
            errors.append(f"{unit}: level {level} and type {ref_type} do not follow from its IRI")
            break
    if errors:
        raise SystemExit("the tables cannot reproduce this release:\n  " + "\n  ".join(errors))
    print("checked: the relations derived by the mapping are the ones in the dump")


def connect(retries=30, delay=2):
    for attempt in range(retries):
        try:
            return psycopg2.connect(
                host=os.environ.get("POSTGRES_HOST", "127.0.0.1"),
                port=int(os.environ.get("POSTGRES_PORT", "5432")),
                user=os.environ.get("POSTGRES_USER", "ligre"),
                password=os.environ.get("POSTGRES_PASSWORD", "ligre"),
                dbname=os.environ.get("POSTGRES_DATABASE", "ligre_db"),
            )
        except psycopg2.OperationalError:
            if attempt == retries - 1:
                raise
            time.sleep(delay)


def copy_rows(cursor, table, rows):
    buffer = io.StringIO()
    for row in rows:
        buffer.write("\t".join("\\N" if v is None else str(v).replace("\\", "\\\\").replace("\t", "\\t")
                               .replace("\n", "\\n") for v in row) + "\n")
    buffer.seek(0)
    cursor.copy_expert(f"COPY papygreek.{table} FROM STDIN", buffer)


def load(conn, rows):
    lemma_ids = {row[4] for row in rows["token"] if row[4] is not None}
    with conn.cursor() as cur:
        cur.execute("SELECT id_lemma FROM lemma WHERE id_lemma = ANY(%s)", (sorted(lemma_ids),))
        missing = lemma_ids - {row[0] for row in cur.fetchall()}
        if missing:
            raise SystemExit(f"{len(missing)} linked lemmas are not in the lemma table (load the lemma bank "
                             f"first), e.g. {sorted(missing)[:5]}")
        cur.execute("TRUNCATE " + ", ".join(f"papygreek.{t}" for t in TABLES))
        for table in reversed(TABLES):
            copy_rows(cur, table, rows[table])
    conn.commit()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", help="a local copy of the dump (complete_papygreek.ttl.gz) instead of downloading it")
    parser.add_argument("--check-only", action="store_true", help="check the dump without loading the database")
    args = parser.parse_args()
    dump = read_dump(args.input)
    rows = build_rows(dump)
    check_derived(dump, rows)
    print(", ".join(f"{len(rows[t])} {t}" for t in reversed(TABLES)))
    if args.check_only:
        return
    print("connecting to Postgres...")
    conn = connect()
    try:
        load(conn, rows)
    finally:
        conn.close()
    print("loaded the PapyGreek–LiGre corpus")


if __name__ == "__main__":
    main()
