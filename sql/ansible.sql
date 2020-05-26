/*
Navicat MySQL Data Transfer

Source Server         : ubuntu
Source Server Version : 50729
Source Host           : 192.168.3.23:3306
Source Database       : ansible

Target Server Type    : MYSQL
Target Server Version : 50729
File Encoding         : 65001

Date: 2020-04-08 15:13:43
*/

SET FOREIGN_KEY_CHECKS=0;

CREATE DATABASE IF NOT EXISTS `ansible` default charset utf8mb4;

use `ansible`
-- ----------------------------
-- Table structure for alembic_version
-- ----------------------------
DROP TABLE IF EXISTS `alembic_version`;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for ansibletask
-- ----------------------------
DROP TABLE IF EXISTS `ansibletask`;
CREATE TABLE `ansibletask` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ansible_id` varchar(80) DEFAULT NULL,
  `celery_id` varchar(80) DEFAULT NULL,
  `group_name` varchar(80) DEFAULT NULL,
  `playbook` varchar(80) DEFAULT NULL,
  `extra_vars` text,
  `ansible_result` longtext,
  `celery_result` text,
  `create_time` datetime DEFAULT NULL,
  `state` tinyint(1) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `option_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ansible_id` (`ansible_id`),
  UNIQUE KEY `celery_id` (`celery_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `ansibletask_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
  CONSTRAINT `ansibletask_ibfk_2` FOREIGN KEY (`option_id`) REFERENCES `options` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for environment
-- ----------------------------
DROP TABLE IF EXISTS `environment`;
CREATE TABLE `environment` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(20) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;


INSERT INTO `ansible`.`environment` (`id`, `name`) VALUES ('1', 'test');
INSERT INTO `ansible`.`environment` (`id`, `name`) VALUES ('2', 'prod');


-- ----------------------------
-- Table structure for host
-- ----------------------------
DROP TABLE IF EXISTS `host`;
CREATE TABLE `host` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `hostname` varchar(60) NOT NULL,
  `ip` varchar(20) NOT NULL,
  `port` int(11) NOT NULL,
  `group_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `hostname` (`hostname`),
  UNIQUE KEY `ip` (`ip`),
  KEY `group_id` (`group_id`),
  CONSTRAINT `host_ibfk_1` FOREIGN KEY (`group_id`) REFERENCES `host_group` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;

INSERT INTO `ansible`.`host` (`id`, `hostname`, `ip`, `port`, `group_id`) VALUES ('1', 'localhost', '127.0.0.1', '22', NULL);


-- ----------------------------
-- Table structure for host_group
-- ----------------------------
DROP TABLE IF EXISTS `host_group`;
CREATE TABLE `host_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(48) NOT NULL,
  `description` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for options
-- ----------------------------
DROP TABLE IF EXISTS `options`;
CREATE TABLE `options` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(48) NOT NULL,
  `content` text,
  `playbook_id` int(11) NOT NULL,
  `env_id` int(11) DEFAULT NULL,
  `url` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `env_id` (`env_id`),
  KEY `playbook_id` (`playbook_id`),
  CONSTRAINT `options_ibfk_1` FOREIGN KEY (`env_id`) REFERENCES `environment` (`id`),
  CONSTRAINT `options_ibfk_2` FOREIGN KEY (`playbook_id`) REFERENCES `playbook` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for playbook
-- ----------------------------
DROP TABLE IF EXISTS `playbook`;
CREATE TABLE `playbook` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(48) NOT NULL,
  `author` varchar(20) NOT NULL,
  `information` varchar(48) NOT NULL,
  `is_env` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `information` (`information`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for playbook_detail
-- ----------------------------
DROP TABLE IF EXISTS `playbook_detail`;
CREATE TABLE `playbook_detail` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `playbook_id` int(11) NOT NULL,
  `content` text,
  PRIMARY KEY (`id`),
  KEY `playbook_id` (`playbook_id`),
  CONSTRAINT `playbook_detail_ibfk_1` FOREIGN KEY (`playbook_id`) REFERENCES `playbook` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for user
-- ----------------------------
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(48) NOT NULL,
  `email` varchar(64) NOT NULL,
  `password` varchar(128) NOT NULL,
  `avatar_l` varchar(64) DEFAULT NULL,
  `avatar_m` varchar(64) DEFAULT NULL,
  `avatar_s` varchar(64) DEFAULT NULL,
  `confirmed` tinyint(1) DEFAULT NULL,
  `bucket` varchar(64) DEFAULT NULL COMMENT '用户桶名称',
  `use_space` int(11) DEFAULT NULL COMMENT '用户已使用空间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS `file_repository`;
CREATE TABLE `file_repository` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `file_type` int(11) DEFAULT NULL COMMENT '文件类型',
  `file_path` varchar(255) DEFAULT NULL COMMENT '文件路径',
  `file_size` int(11) DEFAULT NULL COMMENT '文件大小/字节',
  `key` varchar(128) DEFAULT NULL COMMENT '文件存储在OSS中的KEY',
  `name` varchar(64) NOT NULL COMMENT '文件/文件夹名称',
  `parent_id` int(11) DEFAULT NULL COMMENT '父级目录id',
  `update_datetime` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `user_id` (`user_id`),
  KEY `parent_id` (`parent_id`),
  CONSTRAINT `file_repository_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
  CONSTRAINT `file_repository_ibfk_2` FOREIGN KEY (`parent_id`) REFERENCES `file_repository` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS `category`;
CREATE TABLE `category` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(32) DEFAULT NULL COMMENT '分类名称',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


DROP TABLE IF EXISTS `post`;
CREATE TABLE `post` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(60) NOT NULL COMMENT '文章标题',
  `desc` varchar(180) DEFAULT NULL COMMENT '文章摘要',
  `body` text,
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  `category_id` int(11) DEFAULT NULL,
  `author_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `category_id` (`category_id`),
  KEY `author_id` (`author_id`),
  CONSTRAINT `post_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `category` (`id`),
  CONSTRAINT `post_ibfk_2` FOREIGN KEY (`author_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;