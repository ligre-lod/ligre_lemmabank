CREATE TABLE gender (
  gen varchar(1) NOT NULL,
  descr text DEFAULT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (gen)
);

CREATE TABLE universal_pos_tag (
  upostag varchar(10) NOT NULL,
  descr text DEFAULT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (upostag)
);

CREATE TABLE lemma (
  id_lemma SERIAL NOT NULL,
  gen varchar(1) DEFAULT NULL,
  label varchar(64) NOT NULL,
  upostag varchar(10) NOT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_lemma)
);

CREATE TABLE lemma_wr (
  id_lemma int NOT NULL,
  wr varchar(64) NOT NULL,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_lemma, wr)
);

CREATE TABLE variant_group (
  id_lemma int NOT NULL,
  id_variant varchar(22) NOT NULL DEFAULT '',
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_lemma)
);

CREATE TABLE lemma_replaced (
  id_lemma int NOT NULL,
  replaced_by int DEFAULT NULL,
  label varchar(64) DEFAULT NULL,
  PRIMARY KEY (id_lemma)
);

CREATE INDEX ix_lemma_label ON lemma (label);
CREATE INDEX ix_lemma_gen ON lemma (gen);
CREATE INDEX ix_lemma_upostag ON lemma (upostag);

CREATE INDEX ix_lemma_wr_wr ON lemma_wr (wr);
CREATE INDEX ix_lemma_wr_id_lemma ON lemma_wr (id_lemma);

CREATE INDEX ix_variant_group_id_variant ON variant_group (id_variant);

ALTER TABLE lemma
  ADD CONSTRAINT lemma_fk_gen FOREIGN KEY (gen) REFERENCES gender (gen),
  ADD CONSTRAINT lemma_fk_upostag FOREIGN KEY (upostag) REFERENCES universal_pos_tag (upostag);

ALTER TABLE lemma_wr
  ADD CONSTRAINT lemma_wr_fk_lemma FOREIGN KEY (id_lemma) REFERENCES lemma (id_lemma) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE variant_group
  ADD CONSTRAINT variant_group_fk_lemma FOREIGN KEY (id_lemma) REFERENCES lemma (id_lemma) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE lemma_replaced
  ADD CONSTRAINT lemma_replaced_fk_replaced_by FOREIGN KEY (replaced_by) REFERENCES lemma (id_lemma) ON DELETE CASCADE ON UPDATE CASCADE;
