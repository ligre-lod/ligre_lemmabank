#!/usr/bin/env python3
"""Loads a CoNLL-U treebank into ligre_db: one row per document, sentence and token,
with each token linked to `lemma.id_lemma` (matched on the token's LEMMA+UPOS, and,
where the same label/pos maps to more than one lemma row, disambiguated with the
token's FEATS Gender).

Creates corpus_document/corpus_sentence/corpus_token if they don't exist yet, then
truncates and reloads them, so this is safe to re-run any time (e.g. on every
container start) and always leaves the DB matching the source .conllu file exactly.
"""

import argparse
import os
import sys
import time
from pathlib import Path

try:
    import pymysql
except ImportError:
    sys.exit("Missing dependency: pip install pymysql")

CHUNK_SIZE = 1000

CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS `corpus_document` (
  `id_document` INT NOT NULL AUTO_INCREMENT,
  `doc_id` VARCHAR(255) NOT NULL,
  `updatedAt` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_document`),
  UNIQUE KEY `doc_id` (`doc_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE IF NOT EXISTS `corpus_sentence` (
  `id_sentence` INT NOT NULL AUTO_INCREMENT,
  `id_document` INT NOT NULL,
  `sent_id` VARCHAR(255) NOT NULL,
  `sent_index` INT NOT NULL,
  `text` TEXT NOT NULL,
  `updatedAt` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_sentence`),
  UNIQUE KEY `sent_id` (`sent_id`),
  KEY `id_document` (`id_document`),
  CONSTRAINT `corpus_sentence_fk_document` FOREIGN KEY (`id_document`)
    REFERENCES `corpus_document` (`id_document`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE IF NOT EXISTS `corpus_token` (
  `id_token` INT NOT NULL AUTO_INCREMENT,
  `id_sentence` INT NOT NULL,
  `token_order` INT NOT NULL,
  `form` VARCHAR(191) NOT NULL,
  `lemma_label` VARCHAR(191) NOT NULL,
  `upostag` VARCHAR(10) NOT NULL,
  `xpos` VARCHAR(20) DEFAULT NULL,
  `feats` TEXT DEFAULT NULL,
  `head_order` INT DEFAULT NULL,
  `deprel` VARCHAR(40) DEFAULT NULL,
  `misc` TEXT DEFAULT NULL,
  `id_lemma` INT DEFAULT NULL,
  `id_head_token` INT DEFAULT NULL,
  `updatedAt` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_token`),
  UNIQUE KEY `id_sentence_order` (`id_sentence`, `token_order`),
  KEY `id_lemma` (`id_lemma`),
  KEY `id_head_token` (`id_head_token`),
  CONSTRAINT `corpus_token_fk_sentence` FOREIGN KEY (`id_sentence`)
    REFERENCES `corpus_sentence` (`id_sentence`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `corpus_token_fk_lemma` FOREIGN KEY (`id_lemma`)
    REFERENCES `lemma` (`id_lemma`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `corpus_token_fk_head` FOREIGN KEY (`id_head_token`)
    REFERENCES `corpus_token` (`id_token`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
"""

UD_GENDER_TO_GEN = {"Masc": "m", "Fem": "f", "Neut": "n"}


def parse_feats(raw):
    if raw == "_":
        return {}
    feats = {}
    for pair in raw.split("|"):
        k, _, v = pair.partition("=")
        feats[k] = v
    return feats


def parse_conllu(path):
    """Yields (doc_id, sent_id, sent_index, text, tokens) per sentence, where tokens
    is a list of dicts with keys: order, form, lemma, upos, xpos, feats, head, deprel,
    misc. Multi-word/empty-node rows (ids like "3-4" or "3.1") are skipped with a
    warning, since none are expected in this treebank."""
    doc_id = None
    sent_id = None
    text = None
    tokens = []
    sent_index_by_doc = {}
    skipped_special_ids = 0

    def flush():
        nonlocal sent_id, text, tokens
        if sent_id is not None:
            sent_index_by_doc[doc_id] = sent_index_by_doc.get(doc_id, 0) + 1
            yield doc_id, sent_id, sent_index_by_doc[doc_id], text or "", tokens
        sent_id = None
        text = None
        tokens = []

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("# newdoc id ="):
                yield from flush()
                doc_id = line.split("=", 1)[1].strip()
            elif line.startswith("# sent_id ="):
                yield from flush()
                sent_id = line.split("=", 1)[1].strip()
            elif line.startswith("# text ="):
                text = line.split("=", 1)[1].strip()
            elif line.startswith("#"):
                continue
            elif line == "":
                yield from flush()
            else:
                cols = line.split("\t")
                if len(cols) != 10:
                    continue
                tok_id, form, lemma, upos, xpos, feats, head, deprel, _deps, misc = cols
                if not tok_id.isdigit():
                    skipped_special_ids += 1
                    continue
                tokens.append({
                    "order": int(tok_id),
                    "form": form,
                    "lemma": lemma,
                    "upos": upos,
                    "xpos": None if xpos == "_" else xpos,
                    "feats": None if feats == "_" else feats,
                    "head": int(head) if head != "_" else None,
                    "deprel": None if deprel == "_" else deprel,
                    "misc": None if misc == "_" else misc,
                })
    yield from flush()
    if skipped_special_ids:
        print(f"WARNING: skipped {skipped_special_ids} multiword/empty-node rows "
              f"(unsupported)", file=sys.stderr)


def connect(retries=30, delay=2):
    last_err = None
    for _ in range(retries):
        try:
            return pymysql.connect(
                host=os.environ.get("MARIADB_HOST", "127.0.0.1"),
                port=int(os.environ.get("MARIADB_PORT", "3306")),
                user=os.environ.get("MARIADB_USER", "ligre"),
                password=os.environ.get("MARIADB_PASSWORD", "ligre"),
                database=os.environ.get("MARIADB_DATABASE", "ligre_db"),
                charset="utf8mb4",
            )
        except pymysql.err.OperationalError as e:
            last_err = e
            time.sleep(delay)
    raise last_err


def chunked(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def build_lemma_index(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT `id_lemma`, `label`, `upostag`, `gen` FROM `lemma`")
        index = {}
        for id_lemma, label, upostag, gen in cur.fetchall():
            index.setdefault((label, upostag), []).append((gen, id_lemma))
    return index


def resolve_id_lemma(lemma_index, label, upos, feats):
    candidates = lemma_index.get((label, upos))
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0][1]
    want_gen = UD_GENDER_TO_GEN.get((feats or {}).get("Gender"))
    matches = [id_lemma for gen, id_lemma in candidates if gen == want_gen]
    return matches[0] if len(matches) == 1 else None


def load_into_db(conn, sentences):
    with conn.cursor() as cur:
        for stmt in CREATE_TABLES.split(";"):
            stmt = stmt.strip()
            if stmt:
                cur.execute(stmt)

        cur.execute("SET FOREIGN_KEY_CHECKS=0")
        cur.execute("TRUNCATE TABLE `corpus_token`")
        cur.execute("TRUNCATE TABLE `corpus_sentence`")
        cur.execute("TRUNCATE TABLE `corpus_document`")
        cur.execute("SET FOREIGN_KEY_CHECKS=1")
    conn.commit()

    doc_ids = list(dict.fromkeys(doc_id for doc_id, *_ in sentences))
    with conn.cursor() as cur:
        cur.executemany("INSERT INTO `corpus_document` (`doc_id`) VALUES (%s)",
                         [(d,) for d in doc_ids])
    conn.commit()

    with conn.cursor() as cur:
        cur.execute("SELECT `id_document`, `doc_id` FROM `corpus_document`")
        doc_id_map = {doc_id: id_document for id_document, doc_id in cur.fetchall()}

    sentence_rows = [
        (doc_id_map[doc_id], sent_id, sent_index, text)
        for doc_id, sent_id, sent_index, text, _tokens in sentences
    ]
    with conn.cursor() as cur:
        for chunk in chunked(sentence_rows, CHUNK_SIZE):
            cur.executemany(
                "INSERT INTO `corpus_sentence` "
                "(`id_document`, `sent_id`, `sent_index`, `text`) VALUES (%s, %s, %s, %s)",
                chunk,
            )
    conn.commit()

    with conn.cursor() as cur:
        cur.execute("SELECT `id_sentence`, `sent_id` FROM `corpus_sentence`")
        sent_id_map = {sent_id: id_sentence for id_sentence, sent_id in cur.fetchall()}

    lemma_index = build_lemma_index(conn)
    matched, unmatched = 0, 0
    token_rows = []
    for _doc_id, sent_id, _sent_index, _text, tokens in sentences:
        id_sentence = sent_id_map[sent_id]
        for tok in tokens:
            feats = parse_feats(tok["feats"]) if tok["feats"] else {}
            id_lemma = resolve_id_lemma(lemma_index, tok["lemma"], tok["upos"], feats)
            if id_lemma is not None:
                matched += 1
            else:
                unmatched += 1
            token_rows.append((
                id_sentence, tok["order"], tok["form"], tok["lemma"], tok["upos"],
                tok["xpos"], tok["feats"], tok["head"], tok["deprel"], tok["misc"],
                id_lemma,
            ))

    with conn.cursor() as cur:
        for chunk in chunked(token_rows, CHUNK_SIZE):
            cur.executemany(
                "INSERT INTO `corpus_token` "
                "(`id_sentence`, `token_order`, `form`, `lemma_label`, `upostag`, `xpos`, "
                "`feats`, `head_order`, `deprel`, `misc`, `id_lemma`) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                chunk,
            )
    conn.commit()

    with conn.cursor() as cur:
        cur.execute("SELECT `id_token`, `id_sentence`, `token_order` FROM `corpus_token`")
        token_id_map = {(id_sentence, token_order): id_token
                         for id_token, id_sentence, token_order in cur.fetchall()}

    head_updates = []
    for _doc_id, sent_id, _sent_index, _text, tokens in sentences:
        id_sentence = sent_id_map[sent_id]
        for tok in tokens:
            if tok["head"]:
                head_key = (id_sentence, tok["head"])
                id_head_token = token_id_map.get(head_key)
                if id_head_token is not None:
                    head_updates.append((id_head_token, id_sentence, tok["order"]))

    with conn.cursor() as cur:
        cur.executemany(
            "UPDATE `corpus_token` SET `id_head_token` = %s "
            "WHERE `id_sentence` = %s AND `token_order` = %s",
            head_updates,
        )
    conn.commit()

    return len(doc_ids), len(sentence_rows), len(token_rows), matched, unmatched


def main():
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--conllu", type=Path,
                         default=repo_root / "data" / "grc_perseus_all.conllu")
    args = parser.parse_args()

    sentences = list(parse_conllu(args.conllu))
    print(f"parsed {len(sentences)} sentences")

    print("connecting to MariaDB...")
    conn = connect()
    try:
        n_docs, n_sents, n_toks, matched, unmatched = load_into_db(conn, sentences)
        print(f"loaded {n_docs} documents, {n_sents} sentences, {n_toks} tokens")
        print(f"tokens linked to a lemma: {matched} ({100 * matched / n_toks:.1f}%), "
              f"unlinked: {unmatched}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
