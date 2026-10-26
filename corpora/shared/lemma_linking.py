from collections import defaultdict
from dataclasses import dataclass

LINKED = "linked"
AMBIGUOUS = "ambiguous"
UNMATCHED = "unmatched"
NOT_LINKABLE = "not_linkable"

WRITTEN_REPRESENTATIONS_QUERY = "SELECT id_lemma, wr FROM lemma_wr"


@dataclass(frozen=True)
class LemmaLink:
    status: str
    candidates: tuple = ()

    @property
    def id_lemma(self):
        return self.candidates[0] if self.status == LINKED else None


NOT_LINKABLE_LINK = LemmaLink(NOT_LINKABLE)


def link_for_candidates(candidates):
    if not candidates:
        return LemmaLink(UNMATCHED)
    if len(candidates) == 1:
        return LemmaLink(LINKED, candidates)
    return LemmaLink(AMBIGUOUS, candidates)


class LemmaIndex:
    def __init__(self, lemma_ids_by_form, normalize):
        self.lemma_ids_by_form = lemma_ids_by_form
        self.normalize = normalize

    @classmethod
    def load(cls, cursor, normalize):
        cursor.execute(WRITTEN_REPRESENTATIONS_QUERY)
        lemma_ids_by_form = defaultdict(set)
        for id_lemma, written_representation in cursor.fetchall():
            lemma_ids_by_form[normalize(written_representation)].add(id_lemma)
        return cls(dict(lemma_ids_by_form), normalize)

    def link(self, lemma_form):
        candidates = self.lemma_ids_by_form.get(self.normalize(lemma_form), set())
        return link_for_candidates(tuple(sorted(candidates)))
