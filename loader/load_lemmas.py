#!/usr/bin/env python3
import argparse
import csv
import io
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from lemma_corrections import apply_corrections, correction_files, read_corrections

GENDERS = ("*", "f", "m", "n")
IDS_HEADER = ["id_lemma", "lemma", "pos", "gen", "status", "replaced_by"]

def gen_for(pos, tsv_gender):
    if pos in ("NOUN", "PROPN"):
        return tsv_gender
    if pos == "ADJ":
        return "*"
    return None

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

def check_noun_genders(rows):
    missing = [(row_num, label, gender) for row_num, label, pos, gender in rows
               if pos in ("NOUN", "PROPN") and gender not in ("f", "m", "n")]
    assert not missing, f"nouns and proper nouns without gender f, m or n: {missing}"

def dedup(rows):
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

    if skipped:
        print("duplicate rows skipped (row_num, lemma, pos, gender, kept_row_num):")
        for row_num, label, pos, gender, kept_row_num in skipped:
            print(f"  {row_num}\t{label}\t{pos}\t{gender}\t{kept_row_num}")
    print(f"exact duplicates skipped: {len(skipped)}")

    return kept, skipped

def load_clusters(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header[1:] == ["lemma", "pos", "gender", "word_cluster", "TYPE"], (
            f"unexpected csv header: {header}"
        )

        clusters = {}
        for id_, label, pos, gender, cluster, row_type in reader:
            clusters.setdefault(cluster, []).append((int(id_), label, pos, gender, row_type))
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
            print(f"WARNING: WR group references rows not in ligre_lemmas.tsv, "
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
                  f"ligre_lemmas.tsv, skipping group: {missing}", file=sys.stderr)
            continue
        overlapping = [k for k in keys if k in absorbed]
        if overlapping:
            print(f"WARNING: LV group {cluster_id} overlaps with a WR merge, "
                  f"skipping group: {keys}", file=sys.stderr)
            continue
        variant_groups[cluster_id] = keys
    return variant_groups

def final_key(key):
    label, pos, gender = key
    return label, pos, gen_for(pos, gender)

def load_ids(ids_path):
    active, retired, seen = {}, {}, set()
    if not ids_path.exists():
        return active, retired
    with open(ids_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        assert reader.fieldnames == IDS_HEADER, f"unexpected header in {ids_path}: {reader.fieldnames}"
        for row in reader:
            id_lemma = int(row["id_lemma"])
            key = (row["lemma"], row["pos"], row["gen"] or None)
            assert id_lemma not in seen, f"duplicate id {id_lemma}"
            seen.add(id_lemma)
            if row["status"] == "active":
                assert key not in active, f"two active ids for {key}"
                active[key] = id_lemma
            elif row["status"] == "retired":
                retired[id_lemma] = (key, int(row["replaced_by"]) if row["replaced_by"] else None)
            else:
                raise AssertionError(f"unknown status {row['status']!r} for id {id_lemma}")
    return active, retired

def write_ids(ids_path, active, retired):
    rows = [(id_lemma, key, "active", None) for key, id_lemma in active.items()]
    rows += [(id_lemma, key, "retired", replaced_by) for id_lemma, (key, replaced_by) in retired.items()]
    with open(ids_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(IDS_HEADER)
        for id_lemma, (label, pos, gen), status, replaced_by in sorted(rows):
            writer.writerow([id_lemma, label, pos, gen or "", status, "" if replaced_by is None else replaced_by])

def assign_ids(final_lemmas, active, retired, moves):
    active, retired = dict(active), dict(retired)
    current = set(final_lemmas)
    changes = []

    for old, new in moves.items():
        if old in active and old not in current and new in current and new not in active:
            active[new] = active.pop(old)
            changes.append(f"kept id {active[new]}: {old} -> {new}")

    retired_by_key = {key: id_lemma for id_lemma, (key, _replaced_by) in retired.items()}
    for key in final_lemmas:
        if key not in active and key in retired_by_key:
            id_lemma = retired_by_key[key]
            del retired[id_lemma]
            active[key] = id_lemma
            changes.append(f"restored id {id_lemma}: {key}")

    next_id = max([*active.values(), *retired, 0]) + 1
    for key in final_lemmas:
        if key not in active:
            active[key] = next_id
            changes.append(f"new id {next_id}: {key}")
            next_id += 1

    for key in [key for key in active if key not in current]:
        id_lemma = active.pop(key)
        replacement = moves.get(key)
        replaced_by = active.get(replacement)
        retired[id_lemma] = (key, replaced_by)
        changes.append(f"retired id {id_lemma}: {key}" + (f", replaced by {replaced_by}" if replaced_by else ""))

    for id_lemma, (key, replaced_by) in retired.items():
        if replaced_by in retired:
            final = replaced_by
            while final in retired and retired[final][1] is not None:
                final = retired[final][1]
            retired[id_lemma] = (key, final if final in active.values() else None)
    return active, retired, changes

def check_ids(final_lemmas, active):
    current = set(final_lemmas)
    missing = [key for key in final_lemmas if key not in active]
    stale = [key for key in active if key not in current]
    if missing or stale:
        sys.exit(
            "the lemmas do not match data/lemma_ids.tsv: "
            f"{len(missing)} lemmas without an id (e.g. {missing[:3]}), "
            f"{len(stale)} active ids without a lemma (e.g. {stale[:3]}). "
            "Run `python loader/load_lemmas.py --assign-ids` and commit data/lemma_ids.tsv."
        )

def connect(retries=30, delay=2):
    import psycopg2

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

def copy_rows(cursor, table, columns, rows):
    buffer = io.StringIO()
    for row in rows:
        buffer.write("\t".join("\\N" if v is None else str(v).replace("\\", "\\\\").replace("\t", "\\t")
                               .replace("\n", "\\n").replace("\r", "\\r") for v in row) + "\n")
    buffer.seek(0)
    cursor.copy_expert(f"COPY {table} ({', '.join(columns)}) FROM STDIN", buffer)


def load_into_db(conn, final_lemmas, variants, lv_variant_groups, pos_tags, id_map, retired):
    wr_rows = [(id_map[key], key[0]) for key in final_lemmas]
    wr_rows += [(id_map[key], label) for key, labels in variants.items() for label in labels]
    variant_group_rows = [(id_map[key], str(int(cluster_id)))
                          for cluster_id, keys in lv_variant_groups.items() for key in keys]
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE lemma_replaced, variant_group, lemma_wr, lemma RESTART IDENTITY CASCADE")
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
        copy_rows(cur, "lemma", ["id_lemma", "label", "upostag", "gen"], [(id_map[key], *key) for key in final_lemmas])
        cur.execute("SELECT setval(pg_get_serial_sequence('lemma', 'id_lemma'), "
                    "GREATEST((SELECT MAX(id_lemma) FROM lemma), 1))")
        copy_rows(cur, "lemma_replaced", ["id_lemma", "replaced_by", "label"],
                  [(id_lemma, replaced_by, key[0]) for id_lemma, (key, replaced_by) in sorted(retired.items())])
        copy_rows(cur, "lemma_wr", ["id_lemma", "wr"], wr_rows)
        copy_rows(cur, "variant_group", ["id_lemma", "id_variant"], variant_group_rows)
    conn.commit()
    return len(wr_rows), len(variant_group_rows)


@dataclass
class LemmaData:
    final_lemmas: list
    variants: dict
    lv_groups: dict
    pos_tags: list
    id_moves: dict
    active: dict
    retired: dict
    corrections: object


def build_lemma_data(tsv, wr_lv_csv, ids, corrections_directory, verbose=True):
    say = print if verbose else (lambda *args, **kwargs: None)
    raw_rows = load_tsv_rows(tsv)
    check_noun_genders(raw_rows)
    pos_tags = sorted({pos for _rn, _label, pos, _gender in raw_rows})
    lemma_entries, skipped = dedup(raw_rows) if verbose else dedup_quietly(raw_rows)
    lemma_keys = {(label, pos, gender) for _rn, label, pos, gender in lemma_entries}

    clusters = load_clusters(wr_lv_csv)
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

    say(f"tsv data rows: {len(raw_rows)}")
    say(f"distinct POS tags found: {len(pos_tags)} -> {pos_tags}")
    say(f"WR merge groups applied: {len(variants)} "
        f"({sum(len(v) for v in variants.values())} lemmas absorbed as wr variants)")
    say(f"LV variant groups found: {len(lv_variant_groups_final)} "
        f"({sum(len(v) for v in lv_variant_groups_final.values())} lemmas linked as lemma variants)")

    active, retired = load_ids(ids)
    corrections, errors = read_corrections(corrections_directory)
    corrected = apply_corrections(final_lemmas, variants_by_final_key, lv_variant_groups_final, active, corrections)
    errors += corrected.errors
    if errors:
        sys.exit("the corrections in data/corrections/ cannot be applied:\n  " + "\n  ".join(errors))
    say(f"corrections applied: {len(corrected.applied)} from {len(correction_files(corrections_directory))} files")
    say(f"final lemma rows: {len(corrected.final_lemmas)}")

    id_moves = {}
    for canonical, variant_labels in variants.items():
        for label in variant_labels:
            id_moves[final_key((label, *canonical[1:]))] = final_key(canonical)
    id_moves.update(corrected.moves)
    id_moves.update(corrected.merges)
    return LemmaData(corrected.final_lemmas, corrected.variants, corrected.lv_groups,
                     sorted(set(pos_tags) | corrected.pos_tags), id_moves, active, retired, corrected)


def dedup_quietly(rows):
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        return dedup(rows)


def main():
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--tsv", type=Path, default=repo_root / "data" / "ligre_lemmas.tsv")
    parser.add_argument("--wr-lv-csv", type=Path,
                         default=repo_root / "data" / "ligre_wr_lv.csv")
    parser.add_argument("--ids", type=Path, default=repo_root / "data" / "lemma_ids.tsv")
    parser.add_argument("--corrections", type=Path, default=repo_root / "data" / "corrections")
    parser.add_argument("--assign-ids", action="store_true",
                        help="update the ids file for the current data, without loading the database")
    args = parser.parse_args()

    data = build_lemma_data(args.tsv, args.wr_lv_csv, args.ids, args.corrections)
    active, retired = data.active, data.retired
    if args.assign_ids:
        active, retired, changes = assign_ids(data.final_lemmas, active, retired, data.id_moves)
        for change in changes:
            print(change)
        write_ids(args.ids, active, retired)
        print(f"wrote {args.ids}: {len(active)} active and {len(retired)} retired ids, {len(changes)} changes")
        return
    check_ids(data.final_lemmas, active)

    print("connecting to Postgres...")
    conn = connect()
    try:
        wr_count, variant_count = load_into_db(
            conn, data.final_lemmas, data.variants, data.lv_groups, data.pos_tags,
            active, retired,
        )
        print(f"loaded {len(data.final_lemmas)} lemma rows, {wr_count} lemma_wr rows, "
              f"and {variant_count} variant_group rows")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
