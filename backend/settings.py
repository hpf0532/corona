# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/1 上午9:28
# File: settings.py
# IDE: PyCharm

import os
import secrets

import redis
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
playbook_dir = os.path.join(basedir, 'playbooks')

REDIS_ADDR = '127.0.0.1'
REDIS_PORT = 6379
REDIS_PD = ''
ansible_result_redis_db = 10
# 连接远程服务器使用的用户名
# ansible_remote_user = 'shiyanlou'
broker_db = 3
result_db = 4

# 指定服务器与组关系的文件
inventory = 'scripts/inventory'
# broker 地址
BROKER = "redis://:%s@%s:%s/%s" % (REDIS_PD, REDIS_ADDR, REDIS_PORT, broker_db)
# 结果保存地址
BACKEND = "redis://:%s@%s:%s/%s" % (REDIS_PD, REDIS_ADDR, REDIS_PORT, result_db)

# 连接池
POOL = redis.ConnectionPool(host=REDIS_ADDR, port=REDIS_PORT, password=REDIS_PD, db=ansible_result_redis_db)


class BaseConfig:
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    BACK_LOCALES = ['en_US', 'zh_Hans_CN']
    BACK_ITEM_PER_PAGE = 2
    secret = secrets.token_urlsafe(nbytes=15)
    '''
    # 旧版本
    import random
    import string
    ''.join(random.choices(string.ascii_letters + string.digits, k=15))
    # py3.6+
    import secrets
    secrets.token_urlsafe(nbytes=15)
    '''
    SECRET_KEY = os.getenv('SECRET_KEY', secret)
    AUTH_EXPIRE = 5


class MySQLConfig:
    MYSQL_USERNAME = os.getenv('MYSQL_USER')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
    MYSQL_HOST = os.getenv('MYSQL_HOST')
    MYSQL_DATABASE = 'ansible'
    MYSQL_CHARSET = 'utf8'


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    # CELERY_TASK_ALWAYS_EAGER = True
    # CELERY_TASK_EAGER_PROPAGATES = True
    # CELERY_BROKER_URL = "redis://127.0.0.1:6379/3"
    CELERY_BROKER_URL = BROKER
    # CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/4"
    CELERY_RESULT_BACKEND = BACKEND
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MySQLConfig.MYSQL_USERNAME}:{MySQLConfig.MYSQL_PASSWORD}' \
                              f'@{MySQLConfig.MYSQL_HOST}/{MySQLConfig.MYSQL_DATABASE}?charset={MySQLConfig.MYSQL_CHARSET}'


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MySQLConfig.MYSQL_USERNAME}:{MySQLConfig.MYSQL_PASSWORD}' \
                              f'@{MySQLConfig.MYSQL_HOST}/{MySQLConfig.MYSQL_DATABASE}?charset={MySQLConfig.MYSQL_CHARSET}'

class ProductionConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MySQLConfig.MYSQL_USERNAME}:{MySQLConfig.MYSQL_PASSWORD}' \
                              f'@{MySQLConfig.MYSQL_HOST}/{MySQLConfig.MYSQL_DATABASE}?charset={MySQLConfig.MYSQL_CHARSET}'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}