#!/usr/bin/env python3
import argparse
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, XSD

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "loader"))
import load_lemmas as loader
from lemma_corrections import (CORRECTIONS_DIRECTORY, FILE_NAME, RELEASES_FILE, correction_files,
                               read_releases)

LILA = Namespace("http://lila-erc.eu/ontologies/lila/")
ONTOLEX = Namespace("http://www.w3.org/ns/lemon/ontolex#")
LEMMA = "https://w3id.org/ligre/data/id/lemma/"
MAPPING = ROOT / "ontop" / "input" / "mapping.ttl.template"
SHAPES = ROOT / "shapes" / "lemma.shacl.ttl"
GENDERS = {"m": LILA.masculine, "f": LILA.feminine, "n": LILA.neuter}


def pos_iris():
    pairs = re.findall(r"upostag = '(\w+)'\"\"\" \] ;.*?rr:constant lila:(\w+)", MAPPING.read_text(), re.S)
    return {tag: LILA[name] for tag, name in pairs}


def lemma_graph(ids, data, active, retired):
    graph, pos_of = Graph(), pos_iris()
    graph.bind("lila", LILA)
    key_of = {id_lemma: key for key, id_lemma in active.items()}
    for id_lemma in sorted(ids):
        lemma = URIRef(f"{LEMMA}{id_lemma}")
        if id_lemma in key_of:
            key = key_of[id_lemma]
            label, pos, gen = key
            graph.add((lemma, RDF.type, LILA.Lemma))
            graph.add((lemma, RDFS.label, Literal(label, datatype=XSD.string)))
            for form in [label, *data.variants.get(key, [])]:
                graph.add((lemma, ONTOLEX.writtenRep, Literal(form, lang="grc")))
            graph.add((lemma, LILA.hasPOS, pos_of[pos]))
            if pos in ("NOUN", "PROPN") and gen in GENDERS:
                graph.add((lemma, LILA.hasGender, GENDERS[gen]))
            graph.add((lemma, DCTERMS.isPartOf, URIRef(f"{LEMMA}LemmaBank")))
        elif id_lemma in retired:
            graph.add((lemma, OWL.deprecated, Literal(True)))
            graph.add((lemma, RDFS.label, Literal(retired[id_lemma][0][0], datatype=XSD.string)))
            replaced_by = retired[id_lemma][1]
            if replaced_by is not None:
                graph.add((lemma, DCTERMS.isReplacedBy, URIRef(f"{LEMMA}{replaced_by}")))
                ids_to_add = {replaced_by} - set(ids)
                if ids_to_add:
                    graph += lemma_graph(ids_to_add, data, active, retired)
    return graph


def validate(graph):
    from pyshacl import validate as shacl_validate
    conforms, _report_graph, report = shacl_validate(graph, shacl_graph=Graph().parse(SHAPES), inference="none",
                                                     allow_warnings=True)
    return conforms, report


def git_show(ref, path):
    result = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=ROOT, capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else None


def check_history(base, directory):
    errors = []
    listed = subprocess.run(["git", "ls-tree", "--name-only", base, "data/corrections/"], cwd=ROOT,
                            capture_output=True, text=True, check=True).stdout.split()
    base_files = {Path(name).name for name in listed if FILE_NAME.match(Path(name).name)}
    current = {path.name for path in correction_files(directory)}
    for name in sorted(base_files - current):
        errors.append(f"{name} was removed; merged correction files stay (add a new file to undo a correction)")
    for name in sorted(base_files & current):
        if git_show(base, f"data/corrections/{name}") != (directory / name).read_text(encoding="utf-8"):
            errors.append(f"{name} was changed; merged correction files stay as they are (add a new file instead)")
    new_files = sorted(current - base_files)
    if base_files:
        for name in new_files:
            if name <= max(base_files):
                errors.append(f"{name} must sort after the last merged file, {max(base_files)}: corrections apply "
                              f"in the order of the file names, so rename it with today's date")
    base_releases = git_show(base, f"data/corrections/{RELEASES_FILE}")
    base_releases = dict(line.split("\t") for line in base_releases.splitlines()[1:]) if base_releases else {}
    releases = read_releases(directory)
    for name, release in base_releases.items():
        if releases.get(name) != release:
            errors.append(f"{RELEASES_FILE}: the release of {name} changed; it is recorded once, at the release")
    for name in new_files:
        if name in releases:
            errors.append(f"{RELEASES_FILE}: {name} is new; its release is recorded at the release, not in the "
                          f"pull request")
    return errors, new_files


def describe(key):
    if key is None:
        return "—"
    label, pos, gen = key
    return f"{label} {pos}" + (f" {gen}" if gen and gen != "*" else "")


def main():
    parser = argparse.ArgumentParser(description="Check the corrections in data/corrections/.")
    parser.add_argument("--base", help="git ref of the target branch, e.g. origin/main")
    parser.add_argument("--corrections", type=Path, default=CORRECTIONS_DIRECTORY, help=argparse.SUPPRESS)
    parser.add_argument("--dump", type=Path, help="validate this dump against the data and the shapes instead")
    parser.add_argument("--save-hashes", action="store_true", help="with --dump: record the validated lemmas")
    args = parser.parse_args()
    if args.dump:
        validate_dump(args.dump, args.save_hashes)

    lines, failed = ["## Corrections check", ""], False
    new_files = None
    if args.base:
        history_errors, new_files = check_history(args.base, args.corrections)
        if history_errors:
            failed = True
            lines += ["### ❌ Correction files", "", *[f"- {e}" for e in history_errors], ""]

    try:
        data = loader.build_lemma_data(ROOT / "data" / "ligre_lemmas.tsv", ROOT / "data" / "ligre_wr_lv.csv",
                                       ROOT / "data" / "lemma_ids.tsv", args.corrections, verbose=False)
    except SystemExit as error:
        lines += ["### ❌ The corrections cannot be applied", "", "```", str(error), "```"]
        finish(lines, failed=True)

    active, retired, changes = loader.assign_ids(data.final_lemmas, data.active, data.retired, data.id_moves)
    shown = [(c, old, new) for c, old, new in data.corrections.applied if new_files is None or c.file in new_files]
    lines += [f"{len(data.corrections.applied)} corrections in {len(correction_files(args.corrections))} files "
              f"apply cleanly"
              + (f"; {len(shown)} of them are new in this pull request." if new_files is not None else "."), ""]
    if shown:
        lines += ["| File | Action | Id | Now | After | Reason | Evidence | By |", "|---|---|---|---|---|---|---|---|"]
        for c, old, new in shown:
            after = {"retire": "retired", "merge": f"merged into {c['replaced_by']} ({describe(new)})",
                     "add-wr": f"{describe(new)}, also written {c['new_lemma']}",
                     "add-variant": f"lemma variant of {describe(new)}"}.get(c["action"], describe(new))
            lines.append(f"| {c.where} | {c['action']} | {c['ligre_id'] or 'new'} | {describe(old)} | {after} | "
                         f"{c['reason']} | {c['evidence']} | {c['submitted_by']} |")
        lines.append("")
    if changes:
        lines += ["<details><summary>Ids at the next release (<code>--assign-ids</code>)</summary>", "", "```",
                  *changes, "```", "</details>", ""]

    touched = {active.get(new) for _c, _old, new in data.corrections.applied if new is not None}
    touched |= {int(c["ligre_id"]) for c, _old, _new in data.corrections.applied if c["ligre_id"]}
    touched.discard(None)
    if touched:
        conforms, report = validate(lemma_graph(touched, data, active, retired))
        if conforms:
            lines += [f"✅ SHACL: the {len(touched)} lemmas these corrections touch conform to "
                      f"`shapes/lemma.shacl.ttl`.", ""]
        else:
            failed = True
            lines += ["### ❌ SHACL", "", "```", report.strip(), "```", ""]
    finish(lines, failed)


def lemmas_in_dump(graph):
    tag_of, gender_of = {iri: tag for tag, iri in pos_iris().items()}, {iri: g for g, iri in GENDERS.items()}
    number = re.compile(r"/data/id/lemma/(\d+)$")
    current, retired = {}, set()
    for lemma in graph.subjects(RDF.type, LILA.Lemma):
        match = number.search(str(lemma))
        if match:
            current[int(match.group(1))] = (str(graph.value(lemma, RDFS.label)),
                                            tag_of.get(graph.value(lemma, LILA.hasPOS)),
                                            gender_of.get(graph.value(lemma, LILA.hasGender)))
    for lemma in graph.subjects(OWL.deprecated, None):
        match = number.search(str(lemma))
        if match:
            retired.add(int(match.group(1)))
    return current, retired


def lemmas_in_data():
    data = loader.build_lemma_data(ROOT / "data" / "ligre_lemmas.tsv", ROOT / "data" / "ligre_wr_lv.csv",
                                   ROOT / "data" / "lemma_ids.tsv", CORRECTIONS_DIRECTORY, verbose=False)
    loader.check_ids(data.final_lemmas, data.active)
    current = {id_lemma: (label, pos, gen if pos in ("NOUN", "PROPN") else None)
               for (label, pos, gen), id_lemma in data.active.items()}
    return current, set(data.retired)


def compare_with_data(graph):
    (dump, dump_retired), (data, data_retired) = lemmas_in_dump(graph), lemmas_in_data()
    errors = []
    for name, ids in (("missing from the dump", data.keys() - dump.keys()),
                      ("in the dump but not in the data", dump.keys() - data.keys())):
        if ids:
            errors.append(f"{len(ids)} lemmas {name}, e.g. {sorted(ids)[:5]}")
    differ = sorted(i for i in data.keys() & dump.keys() if data[i] != dump[i])
    if differ:
        errors.append(f"{len(differ)} lemmas differ, e.g. " +
                      "; ".join(f"{i}: data {data[i]}, dump {dump[i]}" for i in differ[:3]))
    if dump_retired != data_retired:
        errors.append(f"retired lemmas differ: data {sorted(data_retired - dump_retired)[:5]} not retired in the "
                      f"dump, dump {sorted(dump_retired - data_retired)[:5]} not retired in the data")
    return errors, len(data), len(data_retired)


def lemma_hashes(graph):
    number = re.compile(r"/data/id/lemma/(\d+)$")
    lines = {}
    for subject, predicate, value in graph:
        match = number.search(str(subject))
        if match:
            lines.setdefault(int(match.group(1)), []).append(f"{subject.n3()} {predicate.n3()} {value.n3()}")
    return {i: hashlib.sha256("\n".join(sorted(l)).encode()).hexdigest()[:16] for i, l in lines.items()}


def read_hashes(path):
    if not path.exists():
        return None, {}
    rows = [line.split("\t") for line in path.read_text().splitlines() if line]
    return rows[0][1], {int(i): h for i, h in rows[1:]}


def write_hashes(path, shapes_hash, hashes):
    lines = [f"shapes\t{shapes_hash}", *(f"{i}\t{h}" for i, h in sorted(hashes.items()))]
    path.write_text("\n".join(lines) + "\n")


def changed_subgraph(graph, ids):
    wanted = {URIRef(f"{LEMMA}{i}") for i in ids}
    wanted |= {o for s in list(wanted) for o in graph.objects(s, DCTERMS.isReplacedBy)}
    subgraph = Graph()
    for subject in wanted:
        for triple in graph.triples((subject, None, None)):
            subgraph.add(triple)
    return subgraph


def validate_dump(path, save_hashes):
    graph = Graph().parse(path)
    errors, lemmas, retired = compare_with_data(graph)
    shapes_hash = hashlib.sha256(SHAPES.read_bytes()).hexdigest()
    hashes_path = path.with_suffix(".hashes.tsv")
    known_shapes, known = read_hashes(hashes_path)
    hashes = lemma_hashes(graph)
    changed = set(hashes) if known_shapes != shapes_hash else {i for i, h in hashes.items() if known.get(i) != h}
    conforms, report = validate(changed_subgraph(graph, changed)) if changed else (True, "")
    lines = ["## Validation of the dump", ""]
    lines += [f"✅ `{path.name}` has the {lemmas} lemmas and {retired} retired lemmas of `data/`."] if not errors else \
        ["❌ The dump does not have the lemmas of `data/` (load the lemmas and export the dump again):", "",
         *[f"- {e}" for e in errors], ""]
    scope = f"all {len(hashes)} lemmas conform" if len(changed) == len(hashes) else \
        f"the {len(changed)} lemmas changed since `{hashes_path.name}` conform"
    lines += [f"✅ SHACL: {scope} to `shapes/lemma.shacl.ttl`."] if conforms else \
        ["❌ The dump does not conform to `shapes/lemma.shacl.ttl`:", "", "```", report.strip()[:20000], "```"]
    failed = bool(errors) or not conforms
    if save_hashes and not failed:
        write_hashes(hashes_path, shapes_hash, hashes)
        lines.append(f"wrote `{hashes_path.name}`")
    finish(lines, failed)


def finish(lines, failed):
    text = "\n".join(lines) + "\n"
    print(text)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
            summary.write(text)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
