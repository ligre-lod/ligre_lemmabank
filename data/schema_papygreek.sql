-- The PapyGreek–LiGre corpus, mapped to RDF by ontop/input/mapping.ttl.template.
-- Loaded from a PapyGreek–LiGre release by data/load_papygreek.py.
-- Unit names (pars, linea, sentence) are the citation values as written (e.g. 'Linea_16/17');
-- the mapping percent-encodes them in the IRIs, as the release does.

CREATE SCHEMA IF NOT EXISTS papygreek;

CREATE TABLE IF NOT EXISTS papygreek.document (
  doc_id text NOT NULL,
  title text NOT NULL,
  PRIMARY KEY (doc_id)
);

CREATE TABLE IF NOT EXISTS papygreek.document_identifier (
  doc_id text NOT NULL REFERENCES papygreek.document (doc_id) ON DELETE CASCADE,
  identifier text NOT NULL,
  PRIMARY KEY (doc_id, identifier)
);

CREATE TABLE IF NOT EXISTS papygreek.document_see_also (
  doc_id text NOT NULL REFERENCES papygreek.document (doc_id) ON DELETE CASCADE,
  url text NOT NULL,
  PRIMARY KEY (doc_id, url)
);

-- layer is 'CiteStructure' (parts and lines) or 'SentenceLayer' (sentences)
CREATE TABLE IF NOT EXISTS papygreek.citation_structure (
  doc_id text NOT NULL REFERENCES papygreek.document (doc_id) ON DELETE CASCADE,
  layer text NOT NULL CHECK (layer IN ('CiteStructure', 'SentenceLayer')),
  title text NOT NULL,
  description text NOT NULL,
  first_unit text NOT NULL,
  PRIMARY KEY (doc_id, layer)
);

CREATE TABLE IF NOT EXISTS papygreek.pars (
  doc_id text NOT NULL REFERENCES papygreek.document (doc_id) ON DELETE CASCADE,
  pars text NOT NULL,
  label text NOT NULL,
  first_linea text NOT NULL,
  last_linea text NOT NULL,
  next_pars text,
  PRIMARY KEY (doc_id, pars)
);

CREATE TABLE IF NOT EXISTS papygreek.linea (
  doc_id text NOT NULL,
  pars text NOT NULL,
  linea text NOT NULL,
  label text NOT NULL,
  first_position int NOT NULL,
  last_position int NOT NULL,
  next_linea text,
  PRIMARY KEY (doc_id, pars, linea),
  FOREIGN KEY (doc_id, pars) REFERENCES papygreek.pars (doc_id, pars) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS papygreek.sentence (
  doc_id text NOT NULL REFERENCES papygreek.document (doc_id) ON DELETE CASCADE,
  sentence text NOT NULL,
  label text NOT NULL,
  first_position int NOT NULL,
  last_position int NOT NULL,
  next_sentence text,
  PRIMARY KEY (doc_id, sentence)
);

-- position is the token number in the document (the IRI pads it to 7 digits);
-- id_lemma is the LiGre lemma (no foreign key, so that reloading the lemma bank
-- does not empty the corpus; the loader checks that the lemmas exist)
CREATE TABLE IF NOT EXISTS papygreek.token (
  doc_id text NOT NULL REFERENCES papygreek.document (doc_id) ON DELETE CASCADE,
  position int NOT NULL,
  string_value text NOT NULL,
  label text NOT NULL,
  id_lemma int,
  next_position int,
  pars text,
  linea text,
  sentence text NOT NULL,
  PRIMARY KEY (doc_id, position)
);

CREATE INDEX IF NOT EXISTS ix_token_lemma ON papygreek.token (id_lemma);
CREATE INDEX IF NOT EXISTS ix_token_linea ON papygreek.token (doc_id, pars, linea);
CREATE INDEX IF NOT EXISTS ix_token_sentence ON papygreek.token (doc_id, sentence);
CREATE INDEX IF NOT EXISTS ix_token_next ON papygreek.token (doc_id, next_position);
