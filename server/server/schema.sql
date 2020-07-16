-- Initialize the database.
-- Drop any existing data and create empty tables.


DROP TABLE IF EXISTS user_info;
DROP TABLE IF EXISTS hndf_static_info;
DROP TABLE IF EXISTS hndf_dynamic_info;
DROP TABLE IF EXISTS hndf_subscriber_info;
DROP TABLE IF EXISTS cdfbj_static_info;
DROP TABLE IF EXISTS cdfbj_dynamic_info;
DROP TABLE IF EXISTS cdfbj_subscriber_info;

CREATE TABLE `user_info` (
  `id` bigint(64) NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL,
  `email` varchar(128) NOT NULL,
  `password` varchar(64) NOT NULL,
  `user_status` int(8) NOT NULL DEFAULT '0',
  `email_status` int(8) NOT NULL DEFAULT '0',
  `register_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `email` (`email`),
  KEY `register_time` (`register_time`),
  KEY `email_status` (`email_status`) USING BTREE,
  KEY `user_status` (`user_status`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `hndf_static_info` (
  `goods_id` varchar(64) NOT NULL,
  `goods_name` varchar(256) NOT NULL,
  `goods_url` varchar(1024) NOT NULL,
  `subscriber_num` int(32) NOT NULL,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`goods_id`),
  KEY `subscriber_num` (`subscriber_num`),
  KEY `update_time` (`update_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `hndf_dynamic_info` (
  `id` bigint(64) NOT NULL AUTO_INCREMENT,
  `goods_id` varchar(64) NOT NULL,
  `goods_status` varchar(64) NOT NULL,
  `goods_num` int(32) DEFAULT NULL,
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `goods_status` (`goods_status`),
  KEY `goods_num` (`goods_num`),
  KEY `update_time` (`goods_id`,`update_time`) USING BTREE,
  CONSTRAINT `goods_id` FOREIGN KEY (`goods_id`) REFERENCES `hndf_static_info` (`goods_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `hndf_subscriber_info` (
  `id` bigint(64) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(64) NOT NULL,
  `goods_id` varchar(64) NOT NULL,
  `subscribe_status` int(8) NOT NULL DEFAULT '0',
  `subscribe_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `goods_user` (`goods_id`,`user_id`),
  KEY `subscribe_status` (`subscribe_status`),
  KEY `subscribe_time` (`subscribe_time`),
  KEY `user_id` (`user_id`),
  KEY `goods_id` (`goods_id`) USING BTREE,
  CONSTRAINT `user_id` FOREIGN KEY (`user_id`) REFERENCES `user_info` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `cdfbj_static_info` (
  `goods_id` varchar(64) NOT NULL,
  `goods_name` varchar(256) NOT NULL,
  `goods_url` varchar(512) NOT NULL,
  `subscriber_num` int(32) NOT NULL,
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`goods_id`),
  KEY `subscriber_num` (`subscriber_num`),
  KEY `update_time` (`update_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `cdfbj_dynamic_info` (
  `id` bigint(64) NOT NULL AUTO_INCREMENT,
  `goods_id` varchar(64) NOT NULL,
  `goods_status` varchar(64) NOT NULL,
  `goods_num` int(32) DEFAULT NULL,
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `goods_status` (`goods_status`),
  KEY `goods_num` (`goods_num`),
  KEY `update_time` (`goods_id`,`update_time`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `cdfbj_subscriber_info` (
  `id` bigint(64) NOT NULL AUTO_INCREMENT,
  `user_id` bigint(64) NOT NULL,
  `goods_id` varchar(64) NOT NULL,
  `subscribe_status` int(8) NOT NULL DEFAULT '0',
  `subscribe_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `goods_user` (`goods_id`,`user_id`),
  KEY `subscribe_status` (`subscribe_status`),
  KEY `subscribe_time` (`subscribe_time`),
  KEY `user_id` (`user_id`),
  KEY `goods_id` (`goods_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
