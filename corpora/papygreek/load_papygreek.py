#!/usr/bin/env python3
import os
from pathlib import Path

from papygreek_to_ligre import settings
from papygreek_to_ligre.document_layout import build_document_layout
from papygreek_to_ligre.downloads import fetch_papygreek_treebanks, find_treebank_files
from papygreek_to_ligre.graph_builder import is_linkable
from papygreek_to_ligre.lemma_bank import normalize_lemma
from papygreek_to_ligre.treebank_reader import read_treebank_document

from shared.database import connect, insert_rows, truncate_tables
from shared.lemma_linking import NOT_LINKABLE_LINK, LemmaIndex

PAPYGREEK_TABLES = (
    "papygreek_token_candidate",
    "papygreek_token",
    "papygreek_sentence",
    "papygreek_line",
    "papygreek_part",
    "papygreek_document_hgv",
    "papygreek_document_tm",
    "papygreek_document",
    "papygreek_corpus",
)

TOKEN_COLUMNS = [
    "id_document",
    "token_index",
    "form",
    "source_lemma",
    "postag",
    "link_status",
    "id_lemma",
    "id_sentence",
    "part_number",
    "line",
]


def corpus_rows():
    return [(
        settings.CORPUS_TITLE,
        settings.PAPYGREEK_LICENSE_URL,
        settings.PAPYGREEK_REPOSITORY_URL,
        settings.PAPYGREEK_PORTAL_URL,
    )]


def trismegistos_rows(document):
    return [(document.identifier, tm_id) for tm_id in document.metadata.trismegistos_ids]


def hgv_rows(document):
    return [(document.identifier, hgv_id) for hgv_id in document.metadata.hgv_ids]


def part_rows(document, layout):
    return [(document.identifier, part.number) for part in layout.parts]


def line_rows(document, layout):
    return [
        (document.identifier, part.number, line, position)
        for part in layout.parts
        for position, line in enumerate(part.tokens_by_line, start=1)
    ]


def sentence_rows(document, layout):
    return [
        (document.identifier, sentence.sentence_id, position)
        for position, sentence in enumerate(layout.sentences, start=1)
    ]


def link_word(word, lemma_index):
    if not is_linkable(word):
        return NOT_LINKABLE_LINK
    return lemma_index.link(word.lemma)


def token_row(document, token, link):
    word = token.word
    return (
        document.identifier,
        token.index,
        word.form,
        word.lemma,
        word.postag,
        link.status,
        link.id_lemma,
        token.sentence_id,
        token.part_number,
        word.line or None,
    )


def candidate_rows(document, token, link):
    if link.id_lemma is not None:
        return []
    return [(document.identifier, token.index, id_lemma) for id_lemma in link.candidates]


def insert_tokens(cursor, document, layout, lemma_index):
    tokens = []
    candidates = []
    for token in layout.tokens:
        link = link_word(token.word, lemma_index)
        tokens.append(token_row(document, token, link))
        candidates.extend(candidate_rows(document, token, link))
    insert_rows(cursor, "papygreek_token", TOKEN_COLUMNS, tokens)
    insert_rows(cursor, "papygreek_token_candidate", ["id_document", "token_index", "id_lemma"], candidates)


def insert_document(cursor, document, lemma_index):
    layout = build_document_layout(document)
    insert_rows(cursor, "papygreek_document", ["id_document"], [(document.identifier,)])
    insert_rows(cursor, "papygreek_document_tm", ["id_document", "tm_id"], trismegistos_rows(document))
    insert_rows(cursor, "papygreek_document_hgv", ["id_document", "hgv_id"], hgv_rows(document))
    insert_rows(cursor, "papygreek_part", ["id_document", "part_number"], part_rows(document, layout))
    insert_rows(cursor, "papygreek_line", ["id_document", "part_number", "line", "position"], line_rows(document, layout))
    insert_rows(cursor, "papygreek_sentence", ["id_document", "id_sentence", "position"], sentence_rows(document, layout))
    insert_tokens(cursor, document, layout, lemma_index)


def load_papygreek(connection, treebank_files):
    with connection.cursor() as cursor:
        lemma_index = LemmaIndex.load(cursor, normalize_lemma)
        truncate_tables(cursor, PAPYGREEK_TABLES)
        insert_rows(cursor, "papygreek_corpus", ["title", "license", "source", "see_also"], corpus_rows())
        for treebank_file in treebank_files:
            insert_document(cursor, read_treebank_document(treebank_file), lemma_index)
    connection.commit()


def report_link_statuses(connection):
    with connection.cursor() as cursor:
        cursor.execute("SELECT link_status, count(*) FROM papygreek_token GROUP BY link_status")
        counts = dict(cursor.fetchall())
    print(f"loaded {sum(counts.values())} tokens")
    for status, count in sorted(counts.items()):
        print(f"  {status}: {count}")


def main():
    data_directory = Path(os.environ.get("PAPYGREEK_DATA_DIR", "/tmp/papygreek"))
    treebank_files = find_treebank_files(fetch_papygreek_treebanks(data_directory))
    print(f"found {len(treebank_files)} PapyGreek treebanks")

    connection = connect()
    try:
        load_papygreek(connection, treebank_files)
        report_link_statuses(connection)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
