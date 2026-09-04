#!/usr/bin/env python3
import argparse
import csv
import os
import sys
import time
from pathlib import Path
from numbers_parser import Document
import psycopg2

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

def load_clusters(numbers_path):
    doc = Document(numbers_path)
    table = doc.sheets[0].tables[0]
    all_rows = table.rows(values_only=True)
    header = all_rows[0]
    assert header[1:] == ["lemma", "pos", "gender", "word_cluster", "TYPE"], (
        f"unexpected numbers header: {header}"
    )

    clusters = {}
    for id_, label, pos, gender, cluster, row_type in all_rows[1:]:
        clusters.setdefault(cluster, []).append((id_, label, pos, gender, row_type))
    return clusters

def type_groups(clusters, row_type):
    groups = {}
    for cluster_id, members in clusters.items():
        matching = [m for m in members if m[4] == row_type]
        if len(matching) < 2:
            continue
        matching.sort(key=lambda m: m[0])
        groups[cluster_id] = matching
    return groups

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

def build_lv_variant_groups(lv_groups, lemma_keys, absorbed):
    variant_groups = {}
    for cluster_id, members in lv_groups.items():
        keys = [(label, pos, gender) for _id, label, pos, gender, _t in members]
        missing = [k for k in keys if k not in lemma_keys]
        if missing:
            print(f"WARNING: LV group {cluster_id} references rows not in "
                  f"final_lemmaList.tsv, skipping group: {missing}", file=sys.stderr)
            continue
        overlapping = [k for k in keys if k in absorbed]
        if overlapping:
            print(f"WARNING: LV group {cluster_id} overlaps with a WR merge, "
                  f"skipping group: {keys}", file=sys.stderr)
            continue
        variant_groups[cluster_id] = keys
    return variant_groups

def connect(retries=30, delay=2):
    last_err = None
    for _ in range(retries):
        try:
            return psycopg2.connect(
                host=os.environ.get("POSTGRES_HOST", "127.0.0.1"),
                port=int(os.environ.get("POSTGRES_PORT", "5432")),
                user=os.environ.get("POSTGRES_USER", "ligre"),
                password=os.environ.get("POSTGRES_PASSWORD", "ligre"),
                dbname=os.environ.get("POSTGRES_DATABASE", "ligre_db"),
            )
        except psycopg2.OperationalError as e:
            last_err = e
            time.sleep(delay)
    raise last_err

def load_into_db(conn, final_lemmas, variants, lv_variant_groups, pos_tags):
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE variant_group, lemma_wr, lemma RESTART IDENTITY CASCADE")

        cur.executemany(
            "INSERT INTO universal_pos_tag (upostag) VALUES (%s) "
            "ON CONFLICT (upostag) DO UPDATE SET upostag = EXCLUDED.upostag",
            [(p,) for p in pos_tags],
        )
        cur.executemany(
            "INSERT INTO gender (gen) VALUES (%s) "
            "ON CONFLICT (gen) DO UPDATE SET gen = EXCLUDED.gen",
            [(g,) for g in GENDERS],
        )

        for chunk in chunked(final_lemmas, CHUNK_SIZE):
            cur.executemany(
                "INSERT INTO lemma (label, upostag, gen) VALUES (%s, %s, %s)",
                chunk,
            )
    conn.commit()

    with conn.cursor() as cur:
        cur.execute("SELECT id_lemma, label, upostag, gen FROM lemma")
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
                "INSERT INTO lemma_wr (id_lemma, wr) VALUES (%s, %s)", chunk
            )
    conn.commit()

    variant_group_rows = []
    for cluster_id, keys in lv_variant_groups.items():
        group_key = str(int(cluster_id))
        for key in keys:
            variant_group_rows.append((id_map[key], group_key))

    with conn.cursor() as cur:
        for chunk in chunked(variant_group_rows, CHUNK_SIZE):
            cur.executemany(
                "INSERT INTO variant_group (id_lemma, id_variant) VALUES (%s, %s)",
                chunk,
            )
    conn.commit()

    return len(wr_rows), len(variant_group_rows)


def main():
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tsv", type=Path, default=repo_root / "input_data" / "final_lemmaList.tsv")
    parser.add_argument("--numbers", type=Path,
                         default=repo_root / "input_data" / "lemma_annotations.numbers")
    parser.add_argument("--duplicates-out", type=Path, default=None,
                         help="optional path to write skipped exact duplicates as CSV")
    args = parser.parse_args()

    raw_rows = load_tsv_rows(args.tsv)
    pos_tags = sorted({pos for _rn, _label, pos, _gender in raw_rows})
    lemma_entries, skipped = dedup(raw_rows, args.duplicates_out)
    lemma_keys = {(label, pos, gender) for _rn, label, pos, gender in lemma_entries}

    clusters = load_clusters(args.numbers)
    wr_groups = list(type_groups(clusters, "WR").values())
    variants, absorbed = build_wr_variants(wr_groups, lemma_keys)

    lv_groups = type_groups(clusters, "LV")
    lv_variant_groups = build_lv_variant_groups(lv_groups, lemma_keys, absorbed)

    final_lemmas = [
        (label, pos, gen_for(pos, gender))
        for _row_num, label, pos, gender in lemma_entries
        if (label, pos, gender) not in absorbed
    ]
    variants_by_final_key = {(l, p, gen_for(p, g)): v for (l, p, g), v in variants.items()}
    lv_variant_groups_final = {
        cluster_id: [(l, p, gen_for(p, g)) for l, p, g in keys]
        for cluster_id, keys in lv_variant_groups.items()
    }

    print(f"tsv data rows: {len(raw_rows)}")
    print(f"distinct POS tags found: {len(pos_tags)} -> {pos_tags}")
    print(f"exact duplicates skipped: {len(skipped)}")
    print(f"WR merge groups applied: {len(variants)} "
          f"({sum(len(v) for v in variants.values())} lemmas absorbed as wr variants)")
    print(f"LV variant groups found: {len(lv_variant_groups_final)} "
          f"({sum(len(v) for v in lv_variant_groups_final.values())} lemmas linked as lemma variants)")
    print(f"final lemma rows: {len(final_lemmas)}")

    print("connecting to Postgres...")
    conn = connect()
    try:
        wr_count, variant_count = load_into_db(
            conn, final_lemmas, variants_by_final_key, lv_variant_groups_final, pos_tags
        )
        print(f"loaded {len(final_lemmas)} lemma rows, {wr_count} lemma_wr rows, "
              f"and {variant_count} variant_group rows")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
