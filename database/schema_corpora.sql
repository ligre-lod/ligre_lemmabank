CREATE SCHEMA IF NOT EXISTS corpus;

CREATE TABLE IF NOT EXISTS corpus.corpus (
  corpus_id text NOT NULL,
  iri text NOT NULL,
  release text NOT NULL,
  source_url text NOT NULL,
  dump_sha256 text NOT NULL,
  PRIMARY KEY (corpus_id)
);

CREATE TABLE IF NOT EXISTS corpus.document (
  iri text NOT NULL,
  corpus_id text NOT NULL REFERENCES corpus.corpus (corpus_id) ON DELETE CASCADE,
  title text,
  PRIMARY KEY (iri)
);

CREATE TABLE IF NOT EXISTS corpus.document_identifier (
  iri text NOT NULL REFERENCES corpus.document (iri) ON DELETE CASCADE,
  identifier text NOT NULL,
  PRIMARY KEY (iri, identifier)
);

CREATE TABLE IF NOT EXISTS corpus.document_see_also (
  iri text NOT NULL REFERENCES corpus.document (iri) ON DELETE CASCADE,
  url text NOT NULL,
  PRIMARY KEY (iri, url)
);

CREATE TABLE IF NOT EXISTS corpus.citation_structure (
  iri text NOT NULL,
  corpus_id text NOT NULL REFERENCES corpus.corpus (corpus_id) ON DELETE CASCADE,
  document_iri text NOT NULL REFERENCES corpus.document (iri) ON DELETE CASCADE,
  title text,
  description text,
  first_iri text,
  PRIMARY KEY (iri)
);

CREATE TABLE IF NOT EXISTS corpus.citation_unit (
  iri text NOT NULL,
  corpus_id text NOT NULL REFERENCES corpus.corpus (corpus_id) ON DELETE CASCADE,
  structure_iri text NOT NULL REFERENCES corpus.citation_structure (iri) ON DELETE CASCADE,
  parent_iri text,
  label text,
  ref_type text,
  cit_level int,
  ref_value text,
  first_iri text,
  last_iri text,
  next_iri text,
  PRIMARY KEY (iri)
);

CREATE TABLE IF NOT EXISTS corpus.token (
  iri text NOT NULL,
  corpus_id text NOT NULL REFERENCES corpus.corpus (corpus_id) ON DELETE CASCADE,
  string_value text,
  label text,
  id_lemma int,
  next_iri text,
  PRIMARY KEY (iri)
);

CREATE TABLE IF NOT EXISTS corpus.unit_token (
  unit_iri text NOT NULL REFERENCES corpus.citation_unit (iri) ON DELETE CASCADE,
  token_iri text NOT NULL REFERENCES corpus.token (iri) ON DELETE CASCADE,
  PRIMARY KEY (unit_iri, token_iri)
);

CREATE TABLE IF NOT EXISTS corpus.token_structure (
  token_iri text NOT NULL REFERENCES corpus.token (iri) ON DELETE CASCADE,
  structure_iri text NOT NULL REFERENCES corpus.citation_structure (iri) ON DELETE CASCADE,
  PRIMARY KEY (token_iri, structure_iri)
);

CREATE INDEX IF NOT EXISTS ix_document_corpus ON corpus.document (corpus_id);
CREATE INDEX IF NOT EXISTS ix_citation_structure_corpus ON corpus.citation_structure (corpus_id);
CREATE INDEX IF NOT EXISTS ix_citation_unit_corpus ON corpus.citation_unit (corpus_id);
CREATE INDEX IF NOT EXISTS ix_citation_unit_structure ON corpus.citation_unit (structure_iri);
CREATE INDEX IF NOT EXISTS ix_citation_unit_parent ON corpus.citation_unit (parent_iri);
CREATE INDEX IF NOT EXISTS ix_citation_unit_next ON corpus.citation_unit (next_iri);
CREATE INDEX IF NOT EXISTS ix_token_corpus ON corpus.token (corpus_id);
CREATE INDEX IF NOT EXISTS ix_token_lemma ON corpus.token (id_lemma);
CREATE INDEX IF NOT EXISTS ix_token_next ON corpus.token (next_iri);
CREATE INDEX IF NOT EXISTS ix_unit_token_token ON corpus.unit_token (token_iri);
CREATE INDEX IF NOT EXISTS ix_token_structure_structure ON corpus.token_structure (structure_iri);
