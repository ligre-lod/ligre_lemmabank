#!/usr/bin/env python3
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF

ROOT = Path(__file__).resolve().parent.parent
USAGE = """usage:
    python scripts/generate_release.py prepare X.Y.Z
    python scripts/generate_release.py check X.Y.Z"""
CHANGELOG = ROOT / "CHANGELOG.md"
CITATION = ROOT / "CITATION.cff"
COMPARE = "https://github.com/ligre-lod/ligre_lemmabank/compare"
CORRECTIONS = ROOT / "data" / "corrections"
sys.path.insert(0, str(ROOT / "loader"))
from lemma_corrections import correction_files, read_releases, write_releases
VOID_FILES = [ROOT / "ttl" / "lemmabank_void.ttl", ROOT / "ttl" / "ligre_void.ttl"]
DUMP = "ttl/ligre_lemmabank.ttl"
CORPORA = [str(path.relative_to(ROOT)) for path in sorted((ROOT / "ttl" / "corpora").glob("*.ttl"))]
LINKSET_DIRECTORY = ROOT / "ttl" / "linksets"
LINKSET_DESCRIPTIONS = [str(path.relative_to(ROOT)) for path in sorted(LINKSET_DIRECTORY.glob("*_description.ttl"))]
LINKSETS = [path for path in sorted(LINKSET_DIRECTORY.glob("*.ttl")) if not path.name.endswith("_description.ttl")]
LEMMA = "https://w3id.org/ligre/data/id/lemma/"
LILA = Namespace("http://lila-erc.eu/ontologies/lila/")


def fail(message):
    sys.exit(f"error: {message}")


def citation_field(name):
    match = re.search(rf"^{name}:\s*(\S+)\s*$", CITATION.read_text(), re.M)
    return match and match.group(1)


def changelog_section(version):
    match = re.search(rf"^## \[{re.escape(version)}\] - (\S+)\n(.*?)(?=^## |^\[)", CHANGELOG.read_text(), re.M | re.S)
    return match and (match.group(1), match.group(2).strip())


def linkset_errors():
    dump = Graph().parse(ROOT / DUMP, format="turtle")
    lemmas = set(dump.subjects(RDF.type, LILA.Lemma))
    deprecated = set(dump.subjects(OWL.deprecated, Literal(True)))
    errors = []
    for path in LINKSETS:
        linked = {term for term in Graph().parse(path, format="turtle").objects()
                  if isinstance(term, URIRef) and str(term).startswith(LEMMA) and str(term)[len(LEMMA):].isdigit()}
        missing, retired = sorted(linked - lemmas - deprecated, key=str), sorted(linked & deprecated, key=str)
        if missing:
            errors.append(f"{path.relative_to(ROOT)} links to {len(missing)} lemmas that are not in {DUMP}, "
                          f"e.g. {[str(lemma) for lemma in missing[:3]]}")
        if retired:
            errors.append(f"{path.relative_to(ROOT)} links to {len(retired)} deprecated lemmas, e.g. "
                          f"{[str(lemma) for lemma in retired[:3]]}; link to the lemmas that replace them")
    return errors


def mark_corrections(version):
    releases = read_releases(CORRECTIONS)
    new = [path.name for path in correction_files(CORRECTIONS) if path.name not in releases]
    releases.update({name: version for name in new})
    write_releases(releases, CORRECTIONS)
    return len(new)


def prepare(version):
    date = datetime.date.today().isoformat()
    changelog = CHANGELOG.read_text()
    if "## [Unreleased]" not in changelog:
        fail("CHANGELOG.md has no '## [Unreleased]' section")
    if f"## [{version}]" in changelog:
        fail(f"CHANGELOG.md already has a section for {version}")
    link = re.search(rf"^\[Unreleased\]: {re.escape(COMPARE)}/(v\S+)\.\.\.HEAD$", changelog, re.M)
    if not link:
        fail("CHANGELOG.md has no '[Unreleased]: .../compare/vX.Y.Z...HEAD' link")
    changed = [CHANGELOG, CITATION, CORRECTIONS / "RELEASES.tsv", *VOID_FILES, ROOT / DUMP,
               (ROOT / DUMP).with_suffix(".hashes.tsv")]
    snapshot = {path: path.read_bytes() if path.exists() else None for path in changed}
    try:
        write_release(version, date, changelog, link)
    except BaseException as error:
        for path, content in snapshot.items():
            if content is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(content)
        fail(f"prepare stopped ({error}); every file is back as it was, so you can run it again")


def write_release(version, date, changelog, link):
    changelog = changelog.replace("## [Unreleased]", f"## [Unreleased]\n\n## [{version}] - {date}", 1)
    changelog = changelog.replace(link.group(0), f"[Unreleased]: {COMPARE}/v{version}...HEAD\n"
                                                 f"[{version}]: {COMPARE}/{link.group(1)}...v{version}")
    CHANGELOG.write_text(changelog)

    citation = CITATION.read_text()
    citation = re.sub(r"^version: .*$", f"version: {version}", citation, flags=re.M)
    citation = re.sub(r"^date-released: .*$", f"date-released: {date}", citation, flags=re.M)
    CITATION.write_text(citation)
    print(f"set version {version} and date {date} in CHANGELOG.md and CITATION.cff")
    print(f"recorded release {version} for {mark_corrections(version)} new correction files in "
          f"data/corrections/RELEASES.tsv")

    export = [sys.executable, "scripts/export_ttl.py"]
    env = {**os.environ, "TTL_INPUT": DUMP, "TTL_OUTPUT": DUMP}
    subprocess.run(export, cwd=ROOT, check=True, env={
        **env, "VOID_OUTPUT": "ttl/ligre_void.ttl",
        "VOID_INCLUDE": os.pathsep.join(["ttl/knowledge_base_description.ttl", *CORPORA, *LINKSET_DESCRIPTIONS])})
    subprocess.run(export, cwd=ROOT, check=True, env=env)
    print("validating the dump against data/ and the changed lemmas against shapes/lemma.shacl.ttl...")
    subprocess.run([sys.executable, "scripts/check_corrections.py", "--dump", DUMP, "--save-hashes"], cwd=ROOT,
                   check=True)
    print("checking that the linksets in ttl/linksets/ link to lemmas of the dump...")
    errors = linkset_errors()
    if errors:
        raise RuntimeError("; ".join(errors))


def check(version):
    errors = []
    if citation_field("version") != version:
        errors.append(f"CITATION.cff has version {citation_field('version')}")
    section = changelog_section(version)
    if not section:
        errors.append(f"CHANGELOG.md has no '## [{version}] - <date>' section")
    elif section[0] != citation_field("date-released"):
        errors.append(f"CHANGELOG.md date {section[0]} differs from CITATION.cff date {citation_field('date-released')}")
    for path in VOID_FILES:
        if f'dcat:version "{version}"' not in path.read_text():
            errors.append(f"{path.relative_to(ROOT)} does not describe version {version}; run 'prepare'")
    releases = read_releases(CORRECTIONS)
    for path in correction_files(CORRECTIONS):
        if path.name not in releases:
            errors.append(f"data/corrections/{path.name} is not in data/corrections/RELEASES.tsv; run 'prepare'")
    errors += linkset_errors()
    if errors:
        fail("release metadata does not match v" + version + ":\n  " + "\n  ".join(errors))
    print(section[1])


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("prepare", "check"):
        fail(USAGE)
    command, version = sys.argv[1], sys.argv[2].removeprefix("v")
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        fail(f"'{version}' is not MAJOR.MINOR.PATCH")
    {"prepare": prepare, "check": check}[command](version)
