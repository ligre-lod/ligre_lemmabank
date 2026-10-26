CREATE TABLE papygreek_corpus (
  title text NOT NULL,
  license text NOT NULL,
  source text NOT NULL,
  see_also text NOT NULL,
  PRIMARY KEY (title)
);

CREATE TABLE papygreek_document (
  id_document varchar(64) NOT NULL,
  PRIMARY KEY (id_document)
);

CREATE TABLE papygreek_document_tm (
  id_document varchar(64) NOT NULL,
  tm_id varchar(32) NOT NULL,
  PRIMARY KEY (id_document, tm_id)
);

CREATE TABLE papygreek_document_hgv (
  id_document varchar(64) NOT NULL,
  hgv_id varchar(32) NOT NULL,
  PRIMARY KEY (id_document, hgv_id)
);

CREATE TABLE papygreek_part (
  id_document varchar(64) NOT NULL,
  part_number int NOT NULL,
  PRIMARY KEY (id_document, part_number)
);

CREATE TABLE papygreek_line (
  id_document varchar(64) NOT NULL,
  part_number int NOT NULL,
  line varchar(32) NOT NULL,
  position int NOT NULL,
  PRIMARY KEY (id_document, part_number, line),
  UNIQUE (id_document, part_number, position)
);

CREATE TABLE papygreek_sentence (
  id_document varchar(64) NOT NULL,
  id_sentence int NOT NULL,
  position int NOT NULL,
  PRIMARY KEY (id_document, id_sentence),
  UNIQUE (id_document, position)
);

CREATE TABLE papygreek_token (
  id_document varchar(64) NOT NULL,
  token_index int NOT NULL,
  token_number varchar(7) GENERATED ALWAYS AS (lpad(token_index::text, 7, '0')) STORED,
  form text NOT NULL,
  source_lemma text NOT NULL,
  postag varchar(16) NOT NULL,
  link_status varchar(16) NOT NULL,
  id_lemma int DEFAULT NULL,
  id_sentence int NOT NULL,
  part_number int NOT NULL,
  line varchar(32) DEFAULT NULL,
  PRIMARY KEY (id_document, token_index),
  CHECK (link_status IN ('linked', 'ambiguous', 'unmatched', 'not_linkable')),
  CHECK ((link_status = 'linked') = (id_lemma IS NOT NULL))
);

CREATE TABLE papygreek_token_candidate (
  id_document varchar(64) NOT NULL,
  token_index int NOT NULL,
  id_lemma int NOT NULL,
  PRIMARY KEY (id_document, token_index, id_lemma)
);

CREATE INDEX ix_papygreek_token_id_lemma ON papygreek_token (id_lemma);
CREATE INDEX ix_papygreek_token_sentence ON papygreek_token (id_document, id_sentence);
CREATE INDEX ix_papygreek_token_line ON papygreek_token (id_document, part_number, line);
CREATE INDEX ix_papygreek_token_link_status ON papygreek_token (link_status);
CREATE INDEX ix_papygreek_token_candidate_id_lemma ON papygreek_token_candidate (id_lemma);

ALTER TABLE papygreek_document_tm
  ADD CONSTRAINT papygreek_document_tm_fk_document FOREIGN KEY (id_document) REFERENCES papygreek_document (id_document) ON DELETE CASCADE;

ALTER TABLE papygreek_document_hgv
  ADD CONSTRAINT papygreek_document_hgv_fk_document FOREIGN KEY (id_document) REFERENCES papygreek_document (id_document) ON DELETE CASCADE;

ALTER TABLE papygreek_part
  ADD CONSTRAINT papygreek_part_fk_document FOREIGN KEY (id_document) REFERENCES papygreek_document (id_document) ON DELETE CASCADE;

ALTER TABLE papygreek_line
  ADD CONSTRAINT papygreek_line_fk_part FOREIGN KEY (id_document, part_number) REFERENCES papygreek_part (id_document, part_number) ON DELETE CASCADE;

ALTER TABLE papygreek_sentence
  ADD CONSTRAINT papygreek_sentence_fk_document FOREIGN KEY (id_document) REFERENCES papygreek_document (id_document) ON DELETE CASCADE;

ALTER TABLE papygreek_token
  ADD CONSTRAINT papygreek_token_fk_sentence FOREIGN KEY (id_document, id_sentence) REFERENCES papygreek_sentence (id_document, id_sentence) ON DELETE CASCADE,
  ADD CONSTRAINT papygreek_token_fk_line FOREIGN KEY (id_document, part_number, line) REFERENCES papygreek_line (id_document, part_number, line) ON DELETE CASCADE,
  ADD CONSTRAINT papygreek_token_fk_lemma FOREIGN KEY (id_lemma) REFERENCES lemma (id_lemma) ON DELETE CASCADE;

ALTER TABLE papygreek_token_candidate
  ADD CONSTRAINT papygreek_token_candidate_fk_token FOREIGN KEY (id_document, token_index) REFERENCES papygreek_token (id_document, token_index) ON DELETE CASCADE,
  ADD CONSTRAINT papygreek_token_candidate_fk_lemma FOREIGN KEY (id_lemma) REFERENCES lemma (id_lemma) ON DELETE CASCADE;

CREATE VIEW papygreek_document_start AS
SELECT d.id_document,
       (SELECT min(p.part_number) FROM papygreek_part p WHERE p.id_document = d.id_document) AS first_part_number,
       (SELECT s.id_sentence FROM papygreek_sentence s WHERE s.id_document = d.id_document AND s.position = 1) AS first_sentence
FROM papygreek_document d;

CREATE VIEW papygreek_part_span AS
SELECT DISTINCT id_document,
       part_number,
       first_value(line) OVER part_lines AS first_line,
       last_value(line) OVER part_lines AS last_line
FROM papygreek_line
WINDOW part_lines AS (
  PARTITION BY id_document, part_number
  ORDER BY position
  ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
);

CREATE VIEW papygreek_line_span AS
SELECT id_document,
       part_number,
       line,
       lpad(min(token_index)::text, 7, '0') AS first_token_number,
       lpad(max(token_index)::text, 7, '0') AS last_token_number
FROM papygreek_token
WHERE line IS NOT NULL
GROUP BY id_document, part_number, line;

CREATE VIEW papygreek_sentence_span AS
SELECT id_document,
       id_sentence,
       lpad(min(token_index)::text, 7, '0') AS first_token_number,
       lpad(max(token_index)::text, 7, '0') AS last_token_number
FROM papygreek_token
GROUP BY id_document, id_sentence;

CREATE VIEW papygreek_part_sequence AS
SELECT *
FROM (
  SELECT id_document,
         part_number,
         lead(part_number) OVER (PARTITION BY id_document ORDER BY part_number) AS next_part_number
  FROM papygreek_part
) parts
WHERE next_part_number IS NOT NULL;

CREATE VIEW papygreek_line_sequence AS
SELECT *
FROM (
  SELECT id_document,
         part_number,
         line,
         lead(line) OVER (PARTITION BY id_document, part_number ORDER BY position) AS next_line
  FROM papygreek_line
) lines
WHERE next_line IS NOT NULL;

CREATE VIEW papygreek_sentence_sequence AS
SELECT *
FROM (
  SELECT id_document,
         id_sentence,
         lead(id_sentence) OVER (PARTITION BY id_document ORDER BY position) AS next_sentence
  FROM papygreek_sentence
) sentences
WHERE next_sentence IS NOT NULL;

CREATE VIEW papygreek_token_sequence AS
SELECT *
FROM (
  SELECT t.id_document,
         t.token_number,
         lead(t.token_number) OVER (PARTITION BY t.id_document, t.part_number ORDER BY t.token_index) AS next_token_number
  FROM papygreek_token t
  JOIN papygreek_part p ON p.id_document = t.id_document AND p.part_number = t.part_number
) tokens
WHERE next_token_number IS NOT NULL;

CREATE VIEW papygreek_unlinked_lemma AS
SELECT source_lemma,
       link_status,
       candidate_lemmas,
       count(*) AS frequency
FROM (
  SELECT t.source_lemma,
         t.link_status,
         array(
           SELECT c.id_lemma
           FROM papygreek_token_candidate c
           WHERE c.id_document = t.id_document AND c.token_index = t.token_index
           ORDER BY c.id_lemma
         ) AS candidate_lemmas
  FROM papygreek_token t
  WHERE t.link_status IN ('ambiguous', 'unmatched')
) unlinked_tokens
GROUP BY source_lemma, link_status, candidate_lemmas;
