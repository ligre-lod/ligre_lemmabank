import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

COLUMNS = ["action", "ligre_id", "lemma", "pos", "gender", "new_lemma", "new_pos", "new_gender", "replaced_by",
           "reason", "evidence", "submitted_by"]
ACTIONS = ("correct", "add", "merge", "retire", "add-wr", "add-variant")
POS_TAGS = ("ADJ", "ADP", "ADV", "AUX", "CCONJ", "DET", "INTJ", "NOUN", "NUM", "PART", "PRON", "PROPN", "PUNCT",
            "SCONJ", "SYM", "VERB", "X")
NOUN_GENDERS = ("m", "f", "n")
CORRECTIONS_DIRECTORY = Path(__file__).resolve().parent.parent / "data" / "corrections"
FILE_NAME = re.compile(r"^\d{4}-\d{2}-\d{2}_[a-z0-9][a-z0-9-]*\.tsv$")
RELEASES_FILE = "RELEASES.tsv"
OTHER_FILES = {"README.md", RELEASES_FILE}


@dataclass
class Correction:
    file: str
    line: int
    values: dict

    def __getitem__(self, column):
        return self.values[column].strip()

    @property
    def where(self):
        return f"{self.file}:{self.line}"


@dataclass
class Result:
    final_lemmas: list
    variants: dict
    lv_groups: dict
    moves: dict = field(default_factory=dict)
    merges: dict = field(default_factory=dict)
    pos_tags: set = field(default_factory=set)
    applied: list = field(default_factory=list)
    errors: list = field(default_factory=list)


def gen_for(pos, gender):
    if pos in ("NOUN", "PROPN"):
        return gender
    if pos == "ADJ":
        return "*"
    return None


def correction_files(directory=CORRECTIONS_DIRECTORY):
    return sorted(p for p in Path(directory).iterdir() if FILE_NAME.match(p.name))


def misnamed_files(directory=CORRECTIONS_DIRECTORY):
    return sorted(p.name for p in Path(directory).iterdir() if not FILE_NAME.match(p.name) and p.name not in OTHER_FILES)


def read_releases(directory=CORRECTIONS_DIRECTORY):
    path = Path(directory) / RELEASES_FILE
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as stream:
        return {row["file"]: row["release"] for row in csv.DictReader(stream, delimiter="\t")}


def write_releases(releases, directory=CORRECTIONS_DIRECTORY):
    lines = ["file\trelease", *(f"{name}\t{release}" for name, release in releases.items())]
    (Path(directory) / RELEASES_FILE).write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_corrections(directory=CORRECTIONS_DIRECTORY):
    corrections, errors = [], []
    for name in misnamed_files(directory):
        errors.append(f"{name}: a correction file is named YYYY-MM-DD_short-description.tsv (lowercase, hyphens)")
    for path in correction_files(directory):
        with path.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            if reader.fieldnames != COLUMNS:
                errors.append(f"{path.name}: the columns must be {COLUMNS}, found {reader.fieldnames}")
                continue
            for line, row in enumerate(reader, start=2):
                if any(value is None for value in row.values()) or None in row:
                    errors.append(f"{path.name}:{line}: the row does not have {len(COLUMNS)} tab-separated columns")
                    continue
                corrections.append(Correction(path.name, line, row))
    return corrections, errors


def key_of(correction, prefix=""):
    pos = correction[f"{prefix}pos"]
    return correction[f"{prefix}lemma"], pos, gen_for(pos, correction[f"{prefix}gender"] or None)


def check_values(correction, prefix, errors):
    lemma, pos, gender = correction[f"{prefix}lemma"], correction[f"{prefix}pos"], correction[f"{prefix}gender"]
    ok = True
    if not lemma or lemma != lemma.strip() or any(c.isspace() for c in lemma):
        errors.append(f"{correction.where}: {prefix}lemma must be one word without spaces")
        ok = False
    if pos not in POS_TAGS:
        errors.append(f"{correction.where}: {prefix}pos {pos!r} is not a Universal Dependencies tag {POS_TAGS}")
        ok = False
    if pos in ("NOUN", "PROPN") and gender not in NOUN_GENDERS:
        errors.append(f"{correction.where}: a {pos} needs {prefix}gender m, f or n")
        ok = False
    if pos not in ("NOUN", "PROPN") and gender:
        errors.append(f"{correction.where}: only NOUN and PROPN have a gender; leave {prefix}gender empty")
        ok = False
    return ok


def check_row(correction, errors):
    action = correction["action"]
    if action not in ACTIONS:
        errors.append(f"{correction.where}: action {action!r} must be one of {ACTIONS}")
        return False
    for column in ("reason", "evidence", "submitted_by"):
        if not correction[column]:
            errors.append(f"{correction.where}: {column} is required")
    ok = True
    if action == "add":
        for column in ("ligre_id", "lemma", "pos", "gender", "replaced_by"):
            if correction[column]:
                errors.append(f"{correction.where}: an add has only new_lemma, new_pos and new_gender; "
                              f"leave {column} empty")
                ok = False
        return check_values(correction, "new_", errors) and ok
    if not correction["ligre_id"].isdigit():
        errors.append(f"{correction.where}: ligre_id must be the id of the lemma (the number in its IRI)")
        ok = False
    ok = check_values(correction, "", errors) and ok
    if action in ("correct", "add-variant"):
        ok = check_values(correction, "new_", errors) and ok
        if ok and key_of(correction) == key_of(correction, "new_"):
            errors.append(f"{correction.where}: the new values are the same as the current ones")
            ok = False
    elif action == "add-wr":
        written_form = correction["new_lemma"]
        if not written_form or any(c.isspace() for c in written_form):
            errors.append(f"{correction.where}: an add-wr needs the written form in new_lemma, one word without spaces")
            ok = False
        if correction["new_pos"] or correction["new_gender"]:
            errors.append(f"{correction.where}: an add-wr keeps the part of speech and gender; leave new_pos and "
                          f"new_gender empty")
            ok = False
    elif any(correction[c] for c in ("new_lemma", "new_pos", "new_gender")):
        errors.append(f"{correction.where}: a {action} has no new values; leave new_lemma, new_pos and new_gender empty")
        ok = False
    if action == "merge" and not correction["replaced_by"].isdigit():
        errors.append(f"{correction.where}: a merge needs replaced_by, the id of the lemma that replaces it")
        ok = False
    if action != "merge" and correction["replaced_by"]:
        errors.append(f"{correction.where}: only a merge has replaced_by")
        ok = False
    return ok


def apply_corrections(final_lemmas, variants, lv_groups, active, corrections):
    result = Result(list(final_lemmas), {k: list(v) for k, v in variants.items()},
                    {g: list(keys) for g, keys in lv_groups.items()})
    current = set(result.final_lemmas)
    position = {key: i for i, key in enumerate(result.final_lemmas)}
    groups_of = {}
    for group, keys in result.lv_groups.items():
        for key in keys:
            groups_of.setdefault(key, []).append(group)
    ids_key = {id_lemma: key for key, id_lemma in active.items()}
    next_group = max((int(group) for group in result.lv_groups), default=0) + 1
    first_key, state = {}, {}

    def key_of_id(id_lemma):
        return state[id_lemma] if id_lemma in state else ids_key.get(id_lemma)

    def rekey(old, new):
        result.final_lemmas[position[old]] = new
        position[new] = position.pop(old)
        current.discard(old)
        current.add(new)
        if old in result.variants:
            result.variants[new] = result.variants.pop(old)
        for group in groups_of.pop(old, []):
            keys = result.lv_groups[group]
            keys[:] = [new if k == old else k for k in keys]
            groups_of.setdefault(new, []).append(group)

    def remove(old):
        result.final_lemmas[position.pop(old)] = None
        current.discard(old)
        result.variants.pop(old, None)
        for group in groups_of.pop(old, []):
            keys = result.lv_groups[group]
            keys[:] = [k for k in keys if k != old]

    def link_variants(old, other):
        nonlocal next_group
        old_groups, other_groups = groups_of.get(old, []), groups_of.get(other, [])
        if set(old_groups) & set(other_groups):
            return False
        if old_groups:
            group = old_groups[0]
        elif other_groups:
            group = other_groups[0]
        else:
            group = str(next_group)
            next_group += 1
            result.lv_groups[group] = []
        members = [old, other]
        for absorbed in {*old_groups, *other_groups} - {group}:
            members += result.lv_groups.pop(absorbed)
        for key in members:
            if key not in result.lv_groups[group]:
                result.lv_groups[group].append(key)
            groups_of[key] = [group]
        return True

    for correction in corrections:
        if not check_row(correction, result.errors):
            continue
        action = correction["action"]
        if action == "add":
            new = key_of(correction, "new_")
            if new in current:
                result.errors.append(f"{correction.where}: the lemma {new} already exists")
                continue
            position[new] = len(result.final_lemmas)
            result.final_lemmas.append(new)
            current.add(new)
            result.pos_tags.add(new[1])
            result.applied.append((correction, None, new))
            continue
        id_lemma, old = int(correction["ligre_id"]), key_of(correction)
        if id_lemma in state and state[id_lemma] != old:
            result.errors.append(f"{correction.where}: after the earlier corrections, lemma {id_lemma} is "
                                 f"{state[id_lemma]}, not {old}")
            continue
        if old not in current:
            result.errors.append(f"{correction.where}: there is no lemma {old} (lemma, pos and gender must be its "
                                 f"current values)")
            continue
        if active.get(old) not in (None, id_lemma):
            result.errors.append(f"{correction.where}: {old} has id {active[old]}, not {id_lemma}")
            continue
        first_key.setdefault(id_lemma, old)
        state.setdefault(id_lemma, old)
        if action == "correct":
            new = key_of(correction, "new_")
            if new in current:
                result.errors.append(f"{correction.where}: the lemma {new} already exists (id {active.get(new)}); "
                                     f"use a merge to make one lemma of the two")
                continue
            rekey(old, new)
            result.moves[old] = new
            state[id_lemma] = new
            result.pos_tags.add(new[1])
            result.applied.append((correction, old, new))
        elif action == "add-wr":
            written_form = correction["new_lemma"]
            if written_form == old[0] or written_form in result.variants.get(old, []):
                result.errors.append(f"{correction.where}: lemma {id_lemma} already has the written form {written_form}")
                continue
            result.variants.setdefault(old, []).append(written_form)
            result.applied.append((correction, old, old))
        elif action == "add-variant":
            other = key_of(correction, "new_")
            if other not in current:
                result.errors.append(f"{correction.where}: there is no lemma {other} to link as lemma variant (add it "
                                     f"in an earlier row)")
                continue
            if not link_variants(old, other):
                result.errors.append(f"{correction.where}: {old} and {other} are already lemma variants")
                continue
            result.applied.append((correction, old, other))
        elif action == "merge":
            target_id = int(correction["replaced_by"])
            target = key_of_id(target_id)
            if target is None or target not in current or target_id == id_lemma:
                result.errors.append(f"{correction.where}: replaced_by {target_id} is not another current lemma")
                continue
            written_forms = [old[0], *result.variants.get(old, [])]
            remove(old)
            result.variants.setdefault(target, [])
            result.variants[target] += [f for f in written_forms if f != target[0] and f not in result.variants[target]]
            result.merges[old] = target
            state[id_lemma] = None
            result.applied.append((correction, old, target))
        else:
            remove(old)
            state[id_lemma] = None
            result.applied.append((correction, old, None))
    for id_lemma, first in first_key.items():
        before, after = ids_key.get(id_lemma) == first, ids_key.get(id_lemma) == state[id_lemma]
        if not before and not after:
            result.errors.append(f"ligre_id {id_lemma}: data/lemma_ids.tsv has {ids_key.get(id_lemma)}, but the "
                                 f"corrections start from {first}")
    for mapping in (result.moves, result.merges):
        for old in list(mapping):
            target = mapping[old]
            while target in result.moves and target not in current:
                target = result.moves[target]
            mapping[old] = target
    result.final_lemmas = [key for key in result.final_lemmas if key is not None]
    for keys in result.lv_groups.values():
        keys[:] = list(dict.fromkeys(keys))
    result.lv_groups = {g: keys for g, keys in result.lv_groups.items() if len(keys) >= 2}
    return result
