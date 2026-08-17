CREATE DATABASE IF NOT EXISTS `ligre_db` /*!40100 DEFAULT CHARACTER SET utf8 COLLATE utf8_bin */;

USE `ligre_db`;
SET FOREIGN_KEY_CHECKS=0;

CREATE TABLE `base` (
  `id_base` int(11) NOT NULL AUTO_INCREMENT,
  `label` varchar(64) NOT NULL,
  `updatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_base`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `gender` (
  `gen` char(1) NOT NULL,
  `descr` text DEFAULT NULL,
  `updatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`gen`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `grade` (
  `grad` char(4) NOT NULL,
  `descr` text DEFAULT NULL,
  `updatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`grad`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `hypolemma` (
  `id_hypolemma` int(11) NOT NULL AUTO_INCREMENT,
  `label` varchar(64) NOT NULL,
  `type` varchar(60) NOT NULL,
  `updatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_hypolemma`),
  KEY `label` (`label`),
  KEY `type` (`type`),
  CONSTRAINT `hypolemma_type` FOREIGN KEY (`type`) REFERENCES `hypolemmaType` (`type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `hypolemmaCompSup` (
  `id_hypolemma` int(11) NOT NULL,
  `updatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_hypolemma`),
  CONSTRAINT `hypolemmaCompSup_fk_hypolemma` FOREIGN KEY (`id_hypolemma`) REFERENCES `hypolemma` (`id_hypolemma`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `hypolemmaType` (
  `type` varchar(60) NOT NULL,
  `infl_cat` char(5) NOT NULL,
  `gen` char(1) DEFAULT NULL,
  `p` char(2) DEFAULT NULL,
  `grad` char(4) DEFAULT NULL,
  `upostag` char(10) NOT NULL,
  `updatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`type`),
  KEY `infl_cat` (`infl_cat`),
  KEY `gen` (`gen`),
  KEY `p` (`p`),
  KEY `grad` (`grad`),
  KEY `upostag` (`upostag`),
  CONSTRAINT `hypolemmaType_fk_fl_cat` FOREIGN KEY (`infl_cat`) REFERENCES `inflectional_category` (`infl_cat`),
  CONSTRAINT `hypolemmaType_fk_gen` FOREIGN KEY (`gen`) REFERENCES `gender` (`gen`),
  CONSTRAINT `hypolemmaType_fk_grad` FOREIGN KEY (`grad`) REFERENCES `grade` (`grad`),
  CONSTRAINT `hypolemmaType_fk_p` FOREIGN KEY (`p`) REFERENCES `plurality` (`p`),
  CONSTRAINT `hypolemmaType_fk_upostag` FOREIGN KEY (`upostag`) REFERENCES `universal_pos_tag` (`upostag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `hypolemma_hypolemma` (
  `hyper_id_hypolemma` int(11) NOT NULL,
  `hypo_id_hypolemma` int(11) NOT NULL,
  `updatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`hyper_id_hypolemma`,`hypo_id_hypolemma`),
  KEY `hypolemma_hypolemma_fk_hypolemma_ipo` (`hypo_id_hypolemma`),
  CONSTRAINT `hypolemma_hypolemma_fk_hypolemma_iper` FOREIGN KEY (`hyper_id_hypolemma`) REFERENCES `hypolemma` (`id_hypolemma`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `hypolemma_hypolemma_fk_hypolemma_ipo` FOREIGN KEY (`hypo_id_hypolemma`) REFERENCES `hypolemma` (`id_hypolemma`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `hypolemma_suffix` (
  `id_hypolemma` int(11) NOT NULL,
  `id_suffix` int(11) NOT NULL,
  `updatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_hypolemma`,`id_suffix`),
  KEY `id_suffix` (`id_suffix`),
  KEY `id_hypolemma` (`id_hypolemma`),
  CONSTRAINT `hypolemma_suffix_ibfk_1` FOREIGN KEY (`id_suffix`) REFERENCES `suffix` (`id_suffix`),
  CONSTRAINT `hypolemma_suffix_ibfk_3` FOREIGN KEY (`id_hypolemma`) REFERENCES `hypolemma` (`id_hypolemma`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `hypolemma_wr` (
  `id_hypolemma` int(11) NOT NULL,
  `wr` varchar(64) NOT NULL,
  `updatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_hypolemma`,`wr`),
  KEY `id_hypolemma` (`id_hypolemma`),
  KEY `wr` (`wr`),
  CONSTRAINT `hypolemma_wr_ibfk_2` FOREIGN KEY (`id_hypolemma`) REFERENCES `hypolemma` (`id_hypolemma`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `inflectional_category` (
  `infl_cat` char(5) NOT NULL,
  `descr` text DEFAULT NULL,
  `updatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`infl_cat`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `lemma` (
  `id_lemma` int(11) NOT NULL AUTO_INCREMENT,
  `infl_cat` char(5) DEFAULT NULL,
  `gen` char(1) DEFAULT NULL,
  `p` char(2) DEFAULT NULL,
  `grad` char(4) DEFAULT NULL,
  `label` varchar(64) NOT NULL,
  `upostag` char(10) NOT NULL,
  `updatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_lemma`),
  KEY `label` (`label`),
  KEY `infl_cat` (`infl_cat`),
  KEY `gen` (`gen`),
  KEY `p` (`p`),
  KEY `grad` (`grad`),
  KEY `upostag` (`upostag`),
  CONSTRAINT `lemma_ibfk_1` FOREIGN KEY (`infl_cat`) REFERENCES `inflectional_category` (`infl_cat`),
  CONSTRAINT `lemma_ibfk_2` FOREIGN KEY (`gen`) REFERENCES `gender` (`gen`),
  CONSTRAINT `lemma_ibfk_3` FOREIGN KEY (`p`) REFERENCES `plurality` (`p`),
  CONSTRAINT `lemma_ibfk_4` FOREIGN KEY (`grad`) REFERENCES `grade` (`grad`),
  CONSTRAINT `lemma_ibfk_5` FOREIGN KEY (`upostag`) REFERENCES `universal_pos_tag` (`upostag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `lemma_base` (
  `id_lemma` int(11) NOT NULL,
  `id_base` int(11) NOT NULL,
  `updatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_lemma`,`id_base`),
  KEY `id_base` (`id_base`),
  KEY `id_lemma` (`id_lemma`),
  CONSTRAINT `lemma_base_fk_base` FOREIGN KEY (`id_base`) REFERENCES `base` (`id_base`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `lemma_base_fk_lemma` FOREIGN KEY (`id_lemma`) REFERENCES `lemma` (`id_lemma`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `lemma_hypolemma` (
  `id_lemma` int(11) NOT NULL,
  `id_hypolemma` int(11) NOT NULL,
  `updatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_lemma`,`id_hypolemma`),
  KEY `lemma_hypolemma_fk_hypolemma` (`id_hypolemma`),
  CONSTRAINT `lemma_hypolemma_fk_hypolemma` FOREIGN KEY (`id_hypolemma`) REFERENCES `hypolemma` (`id_hypolemma`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `lemma_hypolemma_fk_lemma` FOREIGN KEY (`id_lemma`) REFERENCES `lemma` (`id_lemma`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `lemma_prefix` (
  `id_lemma` int(11) NOT NULL,
  `id_prefix` int(11) NOT NULL,
  `updatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_lemma`,`id_prefix`),
  KEY `id_prefix` (`id_prefix`),
  KEY `id_lemma` (`id_lemma`),
  CONSTRAINT `lemma_prefix_fk_lemma` FOREIGN KEY (`id_lemma`) REFERENCES `lemma` (`id_lemma`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `lemma_prefix_ibfk_1` FOREIGN KEY (`id_prefix`) REFERENCES `prefix` (`id_prefix`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `lemma_suffix` (
  `id_lemma` int(11) NOT NULL,
  `id_suffix` int(11) NOT NULL,
  `updatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_lemma`,`id_suffix`),
  KEY `id_suffix` (`id_suffix`),
  KEY `id_lemma` (`id_lemma`),
  CONSTRAINT `lemma_suffix_fk_lemma` FOREIGN KEY (`id_lemma`) REFERENCES `lemma` (`id_lemma`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `lemma_suffix_ibfk_1` FOREIGN KEY (`id_suffix`) REFERENCES `suffix` (`id_suffix`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `lemma_wr` (
  `id_lemma` int(11) NOT NULL,
  `wr` varchar(64) NOT NULL,
  `updatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_lemma`,`wr`),
  KEY `wr` (`wr`),
  KEY `id_lemma` (`id_lemma`),
  CONSTRAINT `lemma_wr_fk_lemma` FOREIGN KEY (`id_lemma`) REFERENCES `lemma` (`id_lemma`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `ligreLU` (
  `id_lemma` int(11) NOT NULL,
  `id_hypolemma0` int(11) DEFAULT NULL,
  `id_hypolemma1` int(11) DEFAULT NULL,
  `class` tinyint(1) NOT NULL,
  `type` varchar(60) DEFAULT NULL,
  `label` varchar(64) NOT NULL,
  `upostag` char(10) NOT NULL,
  `infl_cat` char(5) DEFAULT NULL,
  `gen` char(1) DEFAULT NULL,
  `p` char(2) DEFAULT NULL,
  `grad` char(4) DEFAULT NULL,
  `wrList` mediumtext NOT NULL,
  `src` char(1) DEFAULT NULL,
  `updatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  UNIQUE KEY `id_lemma` (`id_lemma`,`id_hypolemma0`,`id_hypolemma1`),
  KEY `id_lemma_2` (`id_lemma`),
  KEY `id_hypolemma0` (`id_hypolemma0`),
  KEY `id_hypolemma1` (`id_hypolemma1`),
  FULLTEXT KEY `wrList` (`wrList`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `phonetic_rep` (
  `id_lemma` int(11) NOT NULL,
  `phr` varchar(64) NOT NULL,
  `updatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_lemma`,`phr`),
  KEY `phr` (`phr`),
  KEY `id_lemma` (`id_lemma`),
  CONSTRAINT `phonetic_rep_fk_lemma` FOREIGN KEY (`id_lemma`) REFERENCES `lemma` (`id_lemma`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `plurality` (
  `p` char(2) NOT NULL,
  `descr` text DEFAULT NULL,
  `updatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`p`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `prefix` (
  `id_prefix` int(11) NOT NULL AUTO_INCREMENT,
  `value` varchar(16) NOT NULL,
  `descr` text DEFAULT NULL,
  `updatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_prefix`),
  UNIQUE KEY `value` (`value`)
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `prefix_stage` (
  `value` varchar(16) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `suffix` (
  `id_suffix` int(11) NOT NULL AUTO_INCREMENT,
  `value` varchar(16) NOT NULL,
  `descr` text DEFAULT NULL,
  `updatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_suffix`),
  UNIQUE KEY `value` (`value`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `universal_pos_tag` (
  `upostag` char(10) NOT NULL,
  `descr` text DEFAULT NULL,
  `updatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`upostag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;

CREATE TABLE `variant_group` (
  `id_lemma` int(11) NOT NULL,
  `id_variant` varchar(22) NOT NULL DEFAULT '',
  `updatedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id_lemma`),
  KEY `id_variant` (`id_variant`),
  CONSTRAINT `variant_group_fk_lemma` FOREIGN KEY (`id_lemma`) REFERENCES `lemma` (`id_lemma`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
SET FOREIGN_KEY_CHECKS=1;