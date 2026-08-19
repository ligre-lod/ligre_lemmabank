#!/usr/bin/env python3
import argparse
import csv
import os
import sys
import time
from pathlib import Path

from numbers_parser import Document

try:
    import pymysql
except ImportError:
    sys.exit("Missing dependency: pip install pymysql")

INCLUDED_POS = {"ADJ", "ADP", "ADV", "CCONJ", "NOUN", "PART", "SCONJ", "VERB"}
GENDERS = ("*", "f", "m", "n")
CHUNK_SIZE = 1000

def gen_for(pos, tsv_gender):
    if pos == "NOUN":
        return tsv_gender
    if pos == "ADJ":
        return "*"
    return None

def chunked(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]

def load_tsv_rows(tsv_path):
    rows = []
    with open(tsv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        assert header == ["lemma", "pos", "gender"], f"unexpected header: {header}"
        for row_num, row in enumerate(reader, start=2):
            label, pos, gender = row
            rows.append((row_num, label, pos, gender))
    return rows

def dedup(rows, duplicates_out):
    seen = {}
    kept = []
    skipped = []
    for row_num, label, pos, gender in rows:
        if pos not in INCLUDED_POS:
            continue
        key = (label, pos, gender)
        if key in seen:
            skipped.append((row_num, label, pos, gender, seen[key]))
            continue
        seen[key] = row_num
        kept.append((row_num, label, pos, gender))

    if duplicates_out is not None:
        with open(duplicates_out, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(["row_num", "lemma", "pos", "gender", "kept_row_num"])
            for row_num, label, pos, gender, kept_row_num in skipped:
                writer.writerow([row_num, label, pos, gender, kept_row_num])

    return kept, skipped


def load_wr_clusters(numbers_path):
    doc = Document(numbers_path)
    table = doc.sheets[0].tables[0]
    all_rows = table.rows(values_only=True)
    header = all_rows[0]
    assert header[1:] == ["lemma", "pos", "gender", "word_cluster", "TYPE"], (
        f"unexpected numbers header: {header}"
    )

    clusters = {}
    for id_, label, pos, gender, cluster, wr_type in all_rows[1:]:
        clusters.setdefault(cluster, []).append((id_, label, pos, gender, wr_type))

    wr_groups = []
    for members in clusters.values():
        wr_members = [m for m in members if m[4] == "WR"]
        if len(wr_members) < 2:
            continue
        wr_members.sort(key=lambda m: m[0])
        wr_groups.append(wr_members)
    return wr_groups

def build_wr_variants(wr_groups, lemma_keys):
    variants = {}
    absorbed = set()
    for group in wr_groups:
        keys = [(label, pos, gender) for _id, label, pos, gender, _t in group]
        missing = [k for k in keys if k not in lemma_keys]
        if missing:
            print(f"WARNING: WR group references rows not in final_lemmaList.tsv, "
                  f"skipping group: {missing}", file=sys.stderr)
            continue
        if any(k[1:] != keys[0][1:] for k in keys):
            print(f"WARNING: WR group has inconsistent pos/gender, skipping: {keys}",
                  file=sys.stderr)
            continue
        canonical_key = keys[0]
        variant_keys = keys[1:]
        if canonical_key in absorbed or any(k in absorbed for k in variant_keys):
            print(f"WARNING: WR group overlaps with another merge, skipping: {keys}",
                  file=sys.stderr)
            continue
        variants[canonical_key] = [k[0] for k in variant_keys]
        absorbed.update(variant_keys)
    return variants, absorbed

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

def load_into_db(conn, final_lemmas, variants):
    with conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS=0")
        cur.execute("TRUNCATE TABLE `lemma_wr`")
        cur.execute("TRUNCATE TABLE `lemma`")
        cur.execute("SET FOREIGN_KEY_CHECKS=1")

        cur.executemany(
            "INSERT INTO `universal_pos_tag` (`upostag`) VALUES (%s) "
            "ON DUPLICATE KEY UPDATE `upostag` = VALUES(`upostag`)",
            [(p,) for p in sorted(INCLUDED_POS)],
        )
        cur.executemany(
            "INSERT INTO `gender` (`gen`) VALUES (%s) "
            "ON DUPLICATE KEY UPDATE `gen` = VALUES(`gen`)",
            [(g,) for g in GENDERS],
        )

        for chunk in chunked(final_lemmas, CHUNK_SIZE):
            cur.executemany(
                "INSERT INTO `lemma` (`label`, `upostag`, `gen`) VALUES (%s, %s, %s)",
                chunk,
            )
    conn.commit()

    with conn.cursor() as cur:
        cur.execute("SELECT `id_lemma`, `label`, `upostag`, `gen` FROM `lemma`")
        id_map = {(label, pos, gen): id_lemma for id_lemma, label, pos, gen in cur.fetchall()}

    wr_rows = []
    for label, pos, gen in final_lemmas:
        wr_rows.append((id_map[(label, pos, gen)], label))
    for (label, pos, gen), variant_labels in variants.items():
        id_lemma = id_map[(label, pos, gen)]
        for variant_label in variant_labels:
            wr_rows.append((id_lemma, variant_label))

    with conn.cursor() as cur:
        for chunk in chunked(wr_rows, CHUNK_SIZE):
            cur.executemany(
                "INSERT INTO `lemma_wr` (`id_lemma`, `wr`) VALUES (%s, %s)", chunk
            )
    conn.commit()

    return len(wr_rows)


def main():
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tsv", type=Path, default=repo_root / "data" / "final_lemmaList.tsv")
    parser.add_argument("--numbers", type=Path,
                         default=repo_root / "data" / "lemma_annotations.numbers")
    parser.add_argument("--duplicates-out", type=Path, default=None,
                         help="optional path to write skipped exact duplicates as CSV")
    args = parser.parse_args()

    raw_rows = load_tsv_rows(args.tsv)
    lemma_entries, skipped = dedup(raw_rows, args.duplicates_out)
    lemma_keys = {(label, pos, gender) for _rn, label, pos, gender in lemma_entries}

    wr_groups = load_wr_clusters(args.numbers)
    variants, absorbed = build_wr_variants(wr_groups, lemma_keys)

    final_lemmas = [
        (label, pos, gen_for(pos, gender))
        for _row_num, label, pos, gender in lemma_entries
        if (label, pos, gender) not in absorbed
    ]
    variants_by_final_key = {(l, p, gen_for(p, g)): v for (l, p, g), v in variants.items()}

    print(f"tsv data rows: {len(raw_rows)}")
    print(f"excluded (unsupported pos): {sum(1 for r in raw_rows if r[2] not in INCLUDED_POS)}")
    print(f"exact duplicates skipped: {len(skipped)}")
    print(f"WR merge groups applied: {len(variants)} "
          f"({sum(len(v) for v in variants.values())} lemmas absorbed as wr variants)")
    print(f"final lemma rows: {len(final_lemmas)}")

    print("connecting to MariaDB...")
    conn = connect()
    try:
        wr_count = load_into_db(conn, final_lemmas, variants_by_final_key)
        print(f"loaded {len(final_lemmas)} lemma rows and {wr_count} lemma_wr rows")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
