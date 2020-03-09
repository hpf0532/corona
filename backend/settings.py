# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/1 上午9:28
# File: settings.py
# IDE: PyCharm

import os
import secrets
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
playbook_dir = os.path.join(basedir, 'playbooks')


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
    AUTH_EXPIRE = 8 * 60 * 60


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
    CELERY_BROKER_URL = "redis://127.0.0.1:6379/3"
    CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/4"
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