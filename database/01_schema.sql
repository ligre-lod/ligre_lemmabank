-- Tables (no inline foreign keys; those are added below once every table exists).

CREATE TABLE base (
  id_base SERIAL NOT NULL,
  label varchar(64) NOT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_base)
);

CREATE TABLE gender (
  gen varchar(1) NOT NULL,
  descr text DEFAULT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (gen)
);

CREATE TABLE grade (
  grad varchar(4) NOT NULL,
  descr text DEFAULT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (grad)
);

CREATE TABLE hypolemma (
  id_hypolemma SERIAL NOT NULL,
  label varchar(64) NOT NULL,
  type varchar(60) NOT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_hypolemma)
);

CREATE TABLE hypolemma_comp_sup (
  id_hypolemma int NOT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_hypolemma)
);

CREATE TABLE hypolemma_type (
  type varchar(60) NOT NULL,
  infl_cat varchar(5) NOT NULL,
  gen varchar(1) DEFAULT NULL,
  p varchar(2) DEFAULT NULL,
  grad varchar(4) DEFAULT NULL,
  upostag varchar(10) NOT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (type)
);

CREATE TABLE hypolemma_hypolemma (
  hyper_id_hypolemma int NOT NULL,
  hypo_id_hypolemma int NOT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (hyper_id_hypolemma, hypo_id_hypolemma)
);

CREATE TABLE hypolemma_suffix (
  id_hypolemma int NOT NULL,
  id_suffix int NOT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_hypolemma, id_suffix)
);

CREATE TABLE hypolemma_wr (
  id_hypolemma int NOT NULL,
  wr varchar(64) NOT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_hypolemma, wr)
);

CREATE TABLE inflectional_category (
  infl_cat varchar(5) NOT NULL,
  descr text DEFAULT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (infl_cat)
);

CREATE TABLE lemma (
  id_lemma SERIAL NOT NULL,
  infl_cat varchar(5) DEFAULT NULL,
  gen varchar(1) DEFAULT NULL,
  p varchar(2) DEFAULT NULL,
  grad varchar(4) DEFAULT NULL,
  label varchar(64) NOT NULL,
  upostag varchar(10) NOT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_lemma)
);

CREATE TABLE lemma_base (
  id_lemma int NOT NULL,
  id_base int NOT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_lemma, id_base)
);

CREATE TABLE lemma_hypolemma (
  id_lemma int NOT NULL,
  id_hypolemma int NOT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_lemma, id_hypolemma)
);

CREATE TABLE lemma_prefix (
  id_lemma int NOT NULL,
  id_prefix int NOT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_lemma, id_prefix)
);

CREATE TABLE lemma_suffix (
  id_lemma int NOT NULL,
  id_suffix int NOT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_lemma, id_suffix)
);

CREATE TABLE lemma_wr (
  id_lemma int NOT NULL,
  wr varchar(64) NOT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_lemma, wr)
);

-- Full-text search on wr_list is not ported (MySQL FULLTEXT has no direct
-- Postgres equivalent); wr_list gets a plain btree index below instead.
CREATE TABLE ligre_lu (
  id_lemma int NOT NULL,
  id_hypolemma0 int DEFAULT NULL,
  id_hypolemma1 int DEFAULT NULL,
  class smallint NOT NULL,
  type varchar(60) DEFAULT NULL,
  label varchar(64) NOT NULL,
  upostag varchar(10) NOT NULL,
  infl_cat varchar(5) DEFAULT NULL,
  gen varchar(1) DEFAULT NULL,
  p varchar(2) DEFAULT NULL,
  grad varchar(4) DEFAULT NULL,
  wr_list text NOT NULL,
  src varchar(1) DEFAULT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (id_lemma, id_hypolemma0, id_hypolemma1)
);

CREATE TABLE phonetic_rep (
  id_lemma int NOT NULL,
  phr varchar(64) NOT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_lemma, phr)
);

CREATE TABLE plurality (
  p varchar(2) NOT NULL,
  descr text DEFAULT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (p)
);

CREATE TABLE prefix (
  id_prefix SERIAL NOT NULL,
  value varchar(16) NOT NULL,
  descr text DEFAULT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_prefix),
  UNIQUE (value)
);

CREATE TABLE prefix_stage (
  value varchar(16) NOT NULL
);

CREATE TABLE suffix (
  id_suffix SERIAL NOT NULL,
  value varchar(16) NOT NULL,
  descr text DEFAULT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_suffix),
  UNIQUE (value)
);

CREATE TABLE universal_pos_tag (
  upostag varchar(10) NOT NULL,
  descr text DEFAULT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (upostag)
);

CREATE TABLE variant_group (
  id_lemma int NOT NULL,
  id_variant varchar(22) NOT NULL DEFAULT '',
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_lemma)
);

-- Indexes (mirrors the non-unique KEY entries from the MySQL schema).

CREATE INDEX ix_hypolemma_label ON hypolemma (label);
CREATE INDEX ix_hypolemma_type ON hypolemma (type);

CREATE INDEX ix_hypolemma_type_infl_cat ON hypolemma_type (infl_cat);
CREATE INDEX ix_hypolemma_type_gen ON hypolemma_type (gen);
CREATE INDEX ix_hypolemma_type_p ON hypolemma_type (p);
CREATE INDEX ix_hypolemma_type_grad ON hypolemma_type (grad);
CREATE INDEX ix_hypolemma_type_upostag ON hypolemma_type (upostag);

CREATE INDEX ix_hypolemma_hypolemma_hypo ON hypolemma_hypolemma (hypo_id_hypolemma);

CREATE INDEX ix_hypolemma_suffix_id_suffix ON hypolemma_suffix (id_suffix);
CREATE INDEX ix_hypolemma_suffix_id_hypolemma ON hypolemma_suffix (id_hypolemma);

CREATE INDEX ix_hypolemma_wr_id_hypolemma ON hypolemma_wr (id_hypolemma);
CREATE INDEX ix_hypolemma_wr_wr ON hypolemma_wr (wr);

CREATE INDEX ix_lemma_label ON lemma (label);
CREATE INDEX ix_lemma_infl_cat ON lemma (infl_cat);
CREATE INDEX ix_lemma_gen ON lemma (gen);
CREATE INDEX ix_lemma_p ON lemma (p);
CREATE INDEX ix_lemma_grad ON lemma (grad);
CREATE INDEX ix_lemma_upostag ON lemma (upostag);

CREATE INDEX ix_lemma_base_id_base ON lemma_base (id_base);
CREATE INDEX ix_lemma_base_id_lemma ON lemma_base (id_lemma);

CREATE INDEX ix_lemma_hypolemma_id_hypolemma ON lemma_hypolemma (id_hypolemma);

CREATE INDEX ix_lemma_prefix_id_prefix ON lemma_prefix (id_prefix);
CREATE INDEX ix_lemma_prefix_id_lemma ON lemma_prefix (id_lemma);

CREATE INDEX ix_lemma_suffix_id_suffix ON lemma_suffix (id_suffix);
CREATE INDEX ix_lemma_suffix_id_lemma ON lemma_suffix (id_lemma);

CREATE INDEX ix_lemma_wr_wr ON lemma_wr (wr);
CREATE INDEX ix_lemma_wr_id_lemma ON lemma_wr (id_lemma);

CREATE INDEX ix_ligre_lu_id_lemma ON ligre_lu (id_lemma);
CREATE INDEX ix_ligre_lu_id_hypolemma0 ON ligre_lu (id_hypolemma0);
CREATE INDEX ix_ligre_lu_id_hypolemma1 ON ligre_lu (id_hypolemma1);
CREATE INDEX ix_ligre_lu_wr_list ON ligre_lu (wr_list);

CREATE INDEX ix_phonetic_rep_phr ON phonetic_rep (phr);
CREATE INDEX ix_phonetic_rep_id_lemma ON phonetic_rep (id_lemma);

CREATE INDEX ix_variant_group_id_variant ON variant_group (id_variant);

-- Foreign keys (added last so table creation order above doesn't matter).

ALTER TABLE hypolemma
  ADD CONSTRAINT hypolemma_fk_type FOREIGN KEY (type) REFERENCES hypolemma_type (type);

ALTER TABLE hypolemma_comp_sup
  ADD CONSTRAINT hypolemma_comp_sup_fk_hypolemma FOREIGN KEY (id_hypolemma) REFERENCES hypolemma (id_hypolemma) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE hypolemma_type
  ADD CONSTRAINT hypolemma_type_fk_infl_cat FOREIGN KEY (infl_cat) REFERENCES inflectional_category (infl_cat),
  ADD CONSTRAINT hypolemma_type_fk_gen FOREIGN KEY (gen) REFERENCES gender (gen),
  ADD CONSTRAINT hypolemma_type_fk_grad FOREIGN KEY (grad) REFERENCES grade (grad),
  ADD CONSTRAINT hypolemma_type_fk_p FOREIGN KEY (p) REFERENCES plurality (p),
  ADD CONSTRAINT hypolemma_type_fk_upostag FOREIGN KEY (upostag) REFERENCES universal_pos_tag (upostag);

ALTER TABLE hypolemma_hypolemma
  ADD CONSTRAINT hypolemma_hypolemma_fk_hyper FOREIGN KEY (hyper_id_hypolemma) REFERENCES hypolemma (id_hypolemma) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT hypolemma_hypolemma_fk_hypo FOREIGN KEY (hypo_id_hypolemma) REFERENCES hypolemma (id_hypolemma) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE hypolemma_suffix
  ADD CONSTRAINT hypolemma_suffix_fk_suffix FOREIGN KEY (id_suffix) REFERENCES suffix (id_suffix),
  ADD CONSTRAINT hypolemma_suffix_fk_hypolemma FOREIGN KEY (id_hypolemma) REFERENCES hypolemma (id_hypolemma) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE hypolemma_wr
  ADD CONSTRAINT hypolemma_wr_fk_hypolemma FOREIGN KEY (id_hypolemma) REFERENCES hypolemma (id_hypolemma) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE lemma
  ADD CONSTRAINT lemma_fk_infl_cat FOREIGN KEY (infl_cat) REFERENCES inflectional_category (infl_cat),
  ADD CONSTRAINT lemma_fk_gen FOREIGN KEY (gen) REFERENCES gender (gen),
  ADD CONSTRAINT lemma_fk_p FOREIGN KEY (p) REFERENCES plurality (p),
  ADD CONSTRAINT lemma_fk_grad FOREIGN KEY (grad) REFERENCES grade (grad),
  ADD CONSTRAINT lemma_fk_upostag FOREIGN KEY (upostag) REFERENCES universal_pos_tag (upostag);

ALTER TABLE lemma_base
  ADD CONSTRAINT lemma_base_fk_base FOREIGN KEY (id_base) REFERENCES base (id_base) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT lemma_base_fk_lemma FOREIGN KEY (id_lemma) REFERENCES lemma (id_lemma) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE lemma_hypolemma
  ADD CONSTRAINT lemma_hypolemma_fk_hypolemma FOREIGN KEY (id_hypolemma) REFERENCES hypolemma (id_hypolemma) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT lemma_hypolemma_fk_lemma FOREIGN KEY (id_lemma) REFERENCES lemma (id_lemma) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE lemma_prefix
  ADD CONSTRAINT lemma_prefix_fk_lemma FOREIGN KEY (id_lemma) REFERENCES lemma (id_lemma) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT lemma_prefix_fk_prefix FOREIGN KEY (id_prefix) REFERENCES prefix (id_prefix);

ALTER TABLE lemma_suffix
  ADD CONSTRAINT lemma_suffix_fk_lemma FOREIGN KEY (id_lemma) REFERENCES lemma (id_lemma) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT lemma_suffix_fk_suffix FOREIGN KEY (id_suffix) REFERENCES suffix (id_suffix);

ALTER TABLE lemma_wr
  ADD CONSTRAINT lemma_wr_fk_lemma FOREIGN KEY (id_lemma) REFERENCES lemma (id_lemma) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE phonetic_rep
  ADD CONSTRAINT phonetic_rep_fk_lemma FOREIGN KEY (id_lemma) REFERENCES lemma (id_lemma) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE variant_group
  ADD CONSTRAINT variant_group_fk_lemma FOREIGN KEY (id_lemma) REFERENCES lemma (id_lemma) ON DELETE CASCADE ON UPDATE CASCADE;
