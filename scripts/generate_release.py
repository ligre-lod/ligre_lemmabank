#!/usr/bin/env python3
"""Prepare or check a release.

    python scripts/generate_release.py prepare 0.1.0   # set version and date, regenerate the descriptions
    python scripts/generate_release.py check 0.1.0     # check that everything says 0.1.0, print the release notes
"""
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = ROOT / "CHANGELOG.md"
CITATION = ROOT / "CITATION.cff"
COMPARE = "https://github.com/ligre-lod/ligre_lemmabank/compare"
VOID_FILES = [ROOT / "ttl" / "lemmabank_void.ttl", ROOT / "ttl" / "ligre_void.ttl"]
CORPORA = [str(path.relative_to(ROOT)) for path in sorted((ROOT / "ttl" / "corpora").glob("*.ttl"))]


def fail(message):
    sys.exit(f"error: {message}")


def citation_field(name):
    match = re.search(rf"^{name}:\s*(\S+)\s*$", CITATION.read_text(), re.M)
    return match and match.group(1)


def changelog_section(version):
    match = re.search(rf"^## \[{re.escape(version)}\] - (\S+)\n(.*?)(?=^## |^\[)", CHANGELOG.read_text(), re.M | re.S)
    return match and (match.group(1), match.group(2).strip())


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
    changelog = changelog.replace("## [Unreleased]", f"## [Unreleased]\n\n## [{version}] - {date}", 1)
    changelog = changelog.replace(link.group(0), f"[Unreleased]: {COMPARE}/v{version}...HEAD\n"
                                                 f"[{version}]: {COMPARE}/{link.group(1)}...v{version}")
    CHANGELOG.write_text(changelog)

    citation = CITATION.read_text()
    citation = re.sub(r"^version: .*$", f"version: {version}", citation, flags=re.M)
    citation = re.sub(r"^date-released: .*$", f"date-released: {date}", citation, flags=re.M)
    CITATION.write_text(citation)
    print(f"set version {version} and date {date} in CHANGELOG.md and CITATION.cff")

    dump = "ttl/ligre_lemmabank.ttl"
    export = [sys.executable, "scripts/export_ttl.py"]
    env = {**os.environ, "TTL_INPUT": dump, "TTL_OUTPUT": dump}
    subprocess.run(export, cwd=ROOT, check=True, env={
        **env, "VOID_OUTPUT": "ttl/ligre_void.ttl",
        "VOID_INCLUDE": os.pathsep.join(["ttl/knowledge_base_description.ttl", *CORPORA])})
    subprocess.run(export, cwd=ROOT, check=True, env=env)


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
    if errors:
        fail("release metadata does not match v" + version + ":\n  " + "\n  ".join(errors))
    print(section[1])


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("prepare", "check"):
        fail(__doc__.strip())
    command, version = sys.argv[1], sys.argv[2].removeprefix("v")
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        fail(f"'{version}' is not MAJOR.MINOR.PATCH")
    {"prepare": prepare, "check": check}[command](version)
