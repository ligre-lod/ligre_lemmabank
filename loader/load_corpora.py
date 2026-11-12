#!/usr/bin/env python3
import argparse
import gzip
import hashlib
import io
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DC, DCAT, DCTERMS, RDF, RDFS, XSD

POWLA = Namespace("http://purl.org/powla/powla.owl#")
LC = Namespace("http://lila-erc.eu/ontologies/lila_corpora/")
LILA = Namespace("http://lila-erc.eu/ontologies/lila/")
DCAT_VERSION = URIRef(str(DCAT) + "version")
BASE = "https://w3id.org/ligre/"
LEMMA = BASE + "data/id/lemma/"
REPO_ROOT = Path(__file__).resolve().parent.parent
DESCRIPTIONS = REPO_ROOT / "ttl" / "corpora"
TABLES = ["corpus", "document", "document_identifier", "document_see_also", "citation_structure", "citation_unit",
          "token", "unit_token", "token_structure"]
IRI_COLUMNS = {"corpus": [1], "document": [0], "document_identifier": [0], "document_see_also": [0],
               "citation_structure": [0, 2, 5], "citation_unit": [0, 2, 3, 8, 9, 10], "token": [0, 5],
               "unit_token": [0, 1], "token_structure": [0, 1]}
SUPPORTED = {
    POWLA.Document: {RDF.type, DC.title, DCTERMS.identifier, RDFS.seeAlso},
    LC.CitationStructure: {RDF.type, DC.title, DC.description, POWLA.hasDocument, LC.first, LC.isLayer},
    LC.citationUnit: {RDF.type, RDFS.label, LC.hasRefType, LC.hasCitLevel, LC.hasRefValue, LC.hasCitSubUnit,
                      POWLA.hasChild, LC.first, LC.last, POWLA.next, POWLA.previous},
    POWLA.Terminal: {RDF.type, POWLA.hasStringValue, RDFS.label, LILA.hasLemma, POWLA.next, POWLA.previous,
                     LC.hasCitStructure},
}


class Refused(Exception):
    pass


def path_of(iri):
    text = str(iri)
    if not text.startswith(BASE):
        raise Refused(f"{text} is not under {BASE}")
    return text[len(BASE):]


def iri_of(path):
    return None if path is None else URIRef(BASE + path)


def normalized(term):
    if isinstance(term, Literal) and term.datatype == XSD.string:
        return Literal(str(term))
    return term


def described_corpora():
    corpora = []
    for description_path in sorted(DESCRIPTIONS.glob("*.ttl")):
        description = Graph().parse(description_path, format="turtle")
        for corpus in description.subjects(RDF.type, POWLA.Corpus):
            urls = sorted({str(u) for d in description.objects(corpus, DCAT.distribution)
                           for u in description.objects(d, DCAT.downloadURL)})
            release = description.value(corpus, DCAT_VERSION)
            if len(urls) != 1 or release is None:
                raise Refused(f"{description_path.name}: {corpus} needs one dcat:downloadURL and a dcat:version")
            match = re.search(r"data/corpora/([^/]+)/", str(corpus))
            corpus_id = match.group(1) if match else description_path.stem
            corpora.append({"id": corpus_id, "iri": corpus, "url": urls[0], "release": str(release)})
    return corpora


def read_dump(corpus, local_path=None):
    if local_path is None:
        print(f"{corpus['id']}: downloading {corpus['url']}...", flush=True)
        with urllib.request.urlopen(corpus["url"], timeout=600) as response:
            data = response.read()
    else:
        data = Path(local_path).read_bytes()
    text = gzip.decompress(data).decode("utf-8") if data[:2] == b"\x1f\x8b" else data.decode("utf-8")
    corpus["sha256"] = hashlib.sha256(data).hexdigest()
    graph = Graph().parse(data=text, format="turtle")
    print(f"{corpus['id']}: parsed {len(graph)} triples", flush=True)
    return graph


def corpus_triples(graph, corpus):
    prefix = str(corpus["iri"]) + "/"
    return {(s, p, normalized(o)) for s, p, o in graph if isinstance(s, URIRef) and str(s).startswith(prefix)}


def one(graph, subject, predicate):
    values = list(graph.objects(subject, predicate))
    if len(values) > 1:
        raise Refused(f"{subject} has {len(values)} values for {predicate}; the tables hold one")
    return values[0] if values else None


def text(value):
    return None if value is None else str(value)


def build_rows(graph, corpus):
    prefix = str(corpus["iri"]) + "/"
    kinds = {}
    for subject in {s for s in graph.subjects() if isinstance(s, URIRef) and str(s).startswith(prefix)}:
        types = set(graph.objects(subject, RDF.type)) & set(SUPPORTED)
        if len(types) != 1:
            raise Refused(f"{subject} is not exactly one of {[str(t) for t in SUPPORTED]}")
        kind = types.pop()
        unsupported = set(graph.predicates(subject)) - SUPPORTED[kind]
        if unsupported:
            raise Refused(f"{subject}: the corpus tables do not hold {sorted(str(p) for p in unsupported)}")
        kinds[subject] = kind
    of_kind = {kind: sorted((s for s, k in kinds.items() if k == kind), key=str) for kind in SUPPORTED}
    corpus_id = corpus["id"]
    rows = {table: [] for table in TABLES}
    rows["corpus"].append((corpus_id, path_of(corpus["iri"]), corpus["release"], corpus["url"], corpus["sha256"]))

    for document in of_kind[POWLA.Document]:
        path = path_of(document)
        rows["document"].append((path, corpus_id, text(one(graph, document, DC.title))))
        rows["document_identifier"] += [(path, str(i)) for i in graph.objects(document, DCTERMS.identifier)]
        rows["document_see_also"] += [(path, str(u)) for u in graph.objects(document, RDFS.seeAlso)]

    layer_of = {}
    for structure in of_kind[LC.CitationStructure]:
        rows["citation_structure"].append((path_of(structure), corpus_id,
                                           path_of(one(graph, structure, POWLA.hasDocument)),
                                           text(one(graph, structure, DC.title)),
                                           text(one(graph, structure, DC.description)),
                                           path_of(one(graph, structure, LC.first)) if one(graph, structure, LC.first)
                                           else None))
        for unit in graph.objects(structure, LC.isLayer):
            layer_of[unit] = structure
    parent_of = {child: unit for unit in of_kind[LC.citationUnit] for child in graph.objects(unit, LC.hasCitSubUnit)}

    def structure_of(unit):
        seen = set()
        while unit in parent_of:
            if unit in seen:
                raise Refused(f"{unit} is part of a cycle of hasCitSubUnit")
            seen.add(unit)
            unit = parent_of[unit]
        if unit not in layer_of:
            raise Refused(f"{unit} is not in a layer (lila_corpus:isLayer) of a citation structure")
        return layer_of[unit]

    for unit in of_kind[LC.citationUnit]:
        level = one(graph, unit, LC.hasCitLevel)
        nodes = [one(graph, unit, p) for p in (LC.first, LC.last, POWLA.next)]
        rows["citation_unit"].append((path_of(unit), corpus_id, path_of(structure_of(unit)),
                                      path_of(parent_of[unit]) if unit in parent_of else None,
                                      text(one(graph, unit, RDFS.label)), text(one(graph, unit, LC.hasRefType)),
                                      None if level is None else int(level), text(one(graph, unit, LC.hasRefValue)),
                                      *[None if n is None else path_of(n) for n in nodes]))
        for child in graph.objects(unit, POWLA.hasChild):
            if kinds.get(child) != POWLA.Terminal:
                raise Refused(f"{unit} has a powla:hasChild that is not a token: {child}")
            rows["unit_token"].append((path_of(unit), path_of(child)))

    structure_of_unit = {row[0]: row[2] for row in rows["citation_unit"]}
    rows["token_structure"] = sorted({(token, structure_of_unit[unit]) for unit, token in rows["unit_token"]})
    for token in of_kind[POWLA.Terminal]:
        lemma, following = one(graph, token, LILA.hasLemma), one(graph, token, POWLA.next)
        if lemma is not None and not (str(lemma).startswith(LEMMA) and str(lemma)[len(LEMMA):].isdigit()):
            raise Refused(f"{token} links to {lemma}, which is not a LiGre lemma")
        rows["token"].append((path_of(token), corpus_id, text(one(graph, token, POWLA.hasStringValue)),
                              text(one(graph, token, RDFS.label)),
                              None if lemma is None else int(str(lemma)[len(LEMMA):]),
                              None if following is None else path_of(following)))
    return rows


def reproduce(rows):
    triples = set()

    def add(s, p, o):
        if o is not None:
            triples.add((iri_of(s), p, o))

    def lit(value, datatype=None):
        return None if value is None else Literal(value, datatype=datatype)

    for path, _corpus, title in rows["document"]:
        add(path, RDF.type, POWLA.Document)
        add(path, DC.title, lit(title))
    for path, identifier in rows["document_identifier"]:
        add(path, DCTERMS.identifier, Literal(identifier))
    for path, url in rows["document_see_also"]:
        add(path, RDFS.seeAlso, URIRef(url))
    for path, _corpus, document, title, description, first in rows["citation_structure"]:
        add(path, RDF.type, LC.CitationStructure)
        add(path, POWLA.hasDocument, iri_of(document))
        add(path, DC.title, lit(title))
        add(path, DC.description, lit(description))
        add(path, LC.first, iri_of(first))
    for path, _corpus, structure, parent, label, ref_type, level, ref_value, first, last, following in \
            rows["citation_unit"]:
        add(path, RDF.type, LC.citationUnit)
        add(path, RDFS.label, lit(label))
        add(path, LC.hasRefType, lit(ref_type))
        add(path, LC.hasCitLevel, lit(level, XSD.int))
        add(path, LC.hasRefValue, lit(ref_value))
        add(path, LC.first, iri_of(first))
        add(path, LC.last, iri_of(last))
        add(path, POWLA.next, iri_of(following))
        if following is not None:
            add(following, POWLA.previous, iri_of(path))
        if parent is None:
            add(structure, LC.isLayer, iri_of(path))
        else:
            add(parent, LC.hasCitSubUnit, iri_of(path))
    for path, _corpus, value, label, lemma, following in rows["token"]:
        add(path, RDF.type, POWLA.Terminal)
        add(path, POWLA.hasStringValue, lit(value))
        add(path, RDFS.label, lit(label))
        add(path, LILA.hasLemma, None if lemma is None else URIRef(f"{LEMMA}{lemma}"))
        add(path, POWLA.next, iri_of(following))
        if following is not None:
            add(following, POWLA.previous, iri_of(path))
    for unit, token in rows["unit_token"]:
        add(unit, POWLA.hasChild, iri_of(token))
    for token, structure in rows["token_structure"]:
        add(token, LC.hasCitStructure, iri_of(structure))
    return {(s, p, normalized(o)) for s, p, o in triples}


def check_reproduced(graph, corpus, rows):
    expected, reproduced = corpus_triples(graph, corpus), reproduce(rows)
    if expected != reproduced:
        missing, extra = sorted(expected - reproduced, key=str), sorted(reproduced - expected, key=str)
        raise Refused(f"the tables cannot reproduce the release: {len(missing)} triples missing "
                      f"(e.g. {[tuple(map(str, t)) for t in missing[:2]]}), {len(extra)} extra "
                      f"(e.g. {[tuple(map(str, t)) for t in extra[:2]]})")
    print(f"{corpus['id']}: the tables reproduce the {len(expected)} triples of its documents, structures, "
          f"units and tokens", flush=True)


def connect(retries=30, delay=2):
    import psycopg2
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


def copy_rows(cursor, table, rows, base):
    buffer = io.StringIO()
    for row in rows:
        row = [f"{base}/{v}" if i in IRI_COLUMNS[table] and v is not None else v for i, v in enumerate(row)]
        buffer.write("\t".join("\\N" if v is None else str(v).replace("\\", "\\\\").replace("\t", "\\t")
                               .replace("\n", "\\n").replace("\r", "\\r") for v in row) + "\n")
    buffer.seek(0)
    cursor.copy_expert(f"COPY corpus.{table} FROM STDIN", buffer)


def loaded_releases(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT corpus_id, release, source_url FROM corpus.corpus")
        return {corpus_id: (release, url) for corpus_id, release, url in cur.fetchall()}


def load(conn, loaded, described, base):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM corpus.corpus WHERE corpus_id <> ALL(%s)", (sorted(described),))
        for corpus_id, rows in loaded.items():
            cur.execute("DELETE FROM corpus.corpus WHERE corpus_id = %s", (corpus_id,))
            for table in TABLES:
                copy_rows(cur, table, rows[table], base)
        cur.execute("""
            SELECT t.corpus_id, t.id_lemma, r.id_lemma IS NOT NULL AS retired, count(*)
            FROM corpus.token t
            LEFT JOIN lemma l ON l.id_lemma = t.id_lemma
            LEFT JOIN lemma_replaced r ON r.id_lemma = t.id_lemma
            WHERE t.id_lemma IS NOT NULL AND l.id_lemma IS NULL
            GROUP BY t.corpus_id, t.id_lemma, r.id_lemma""")
        dangling = cur.fetchall()
    unknown = [(c, i) for c, i, retired, _n in dangling if not retired]
    if unknown:
        conn.rollback()
        raise Refused(f"{len(unknown)} linked lemmas are not in the lemma bank (load the lemma bank first), "
                      f"e.g. {unknown[:5]}")
    for corpus_id in sorted({c for c, _i, _r, _n in dangling}):
        tokens = sum(n for c, _i, _r, n in dangling if c == corpus_id)
        print(f"warning: {corpus_id} links {tokens} tokens to retired lemmas; they resolve as deprecated until the "
              f"corpus links to the lemmas that replace them", flush=True)
    conn.commit()


def main():
    parser = argparse.ArgumentParser(description="Load the corpora described in ttl/corpora/ into Postgres.")
    parser.add_argument("--input", action="append", default=[], metavar="CORPUS=PATH",
                        help="a local copy of a corpus dump instead of downloading it")
    parser.add_argument("--check-only", action="store_true", help="check the dumps without loading the database")
    parser.add_argument("--force", action="store_true", help="also reload corpora whose release is already loaded")
    args = parser.parse_args()
    inputs = dict(item.split("=", 1) for item in args.input)
    base = os.environ.get("LIGRE_BASE_URL", "https://w3id.org/ligre").rstrip("/")
    conn = None
    try:
        corpora = described_corpora()
        if not corpora:
            raise Refused(f"no corpus is described in {DESCRIPTIONS}; refusing to remove every corpus from the database")
        if not args.check_only:
            print(f"connecting to Postgres (IRIs under {base}, as LIGRE_BASE_URL of the endpoint)...", flush=True)
            conn = connect()
        present = {} if conn is None or args.force else loaded_releases(conn)
        loaded = {}
        for corpus in corpora:
            if present.get(corpus["id"]) == (corpus["release"], corpus["url"]):
                print(f"{corpus['id']} {corpus['release']}: already loaded, skipped (--force reloads it)", flush=True)
                continue
            graph = read_dump(corpus, inputs.get(corpus["id"]))
            rows = build_rows(graph, corpus)
            check_reproduced(graph, corpus, rows)
            print(f"{corpus['id']} {corpus['release']}: " + ", ".join(f"{len(rows[t])} {t}" for t in TABLES[1:]),
                  flush=True)
            loaded[corpus["id"]] = rows
            del graph
        if conn is not None:
            load(conn, loaded, [c["id"] for c in corpora], base)
            print(f"loaded {len(loaded)} corpora" + (f": {', '.join(loaded)}" if loaded else "") +
                  f"; {len(corpora) - len(loaded)} unchanged")
    except Refused as refusal:
        sys.exit(f"error: {refusal}")
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    main()
