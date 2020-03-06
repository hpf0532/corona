# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/1 上午9:25
# File: __init__.py.py
# IDE: PyCharm

import os
import logging
import click
from flask import Flask
from celery import Celery
from logging.handlers import TimedRotatingFileHandler
from backend.settings import config
from backend.utils import api_abort
from backend.extensions import db, migrate
from backend.settings import basedir


# celery注册工厂函数
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


# flask app工厂函数
def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", 'development')

    app = Flask("backend")
    app.config.from_object(config[config_name])

    register_extensions(app)  # 注册扩展
    register_blueprints(app)  # 注册蓝图
    register_errors(app)  # 错误信息注册
    register_commands(app)  # 注册自定义命令

    return app


def register_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)


def register_blueprints(app):
    from backend.api.v1 import api_v1
    app.register_blueprint(api_v1, url_prefix='/api/v1')


def register_logging(app):
    app.logger.setLevel(logging.INFO)

    formatter = logging.Formatter('[%(asctime)s]-[%(pathname)s]-[%(funcName)s]-[%(lineno)s]-[%(levelname)s] - %(message)s')

    file_handler = TimedRotatingFileHandler(
        os.path.join(basedir, 'logs/flask.log'), when="D", interval=1, backupCount=15,
        encoding="UTF-8", delay=False, utc=True)

    # file_handler = RotatingFileHandler(os.path.join(basedir, 'logs/catchatlog.log'),
    #                                    maxBytes=10 * 1024 * 1024, backupCount=10)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    if not app.debug:
        app.logger.addHandler(file_handler)


def register_errors(app):
    @app.errorhandler(400)
    def bad_request(e):
        return api_abort(400, "Bad Request")

    @app.errorhandler(403)
    def forbidden(e):
        return api_abort(403, "Forbidden")

    @app.errorhandler(404)
    def page_not_found(e):
        return api_abort(404, 'The requested URL was not found on the server.')

    @app.errorhandler(405)
    def method_not_allowed(e):
        return api_abort(405, 'The method is not allowed for the requested URL.')

    @app.errorhandler(500)
    def internal_server_error(e):
        return api_abort(500, 'An internal server error occurred.')


def register_commands(app):
    @app.cli.command()
    @click.option('--drop', is_flag=True, help='Create after drop.')
    def initdb(drop):
        """Initialize the database."""
        if drop:
            click.confirm('This operation will delete the database, do you want to continue?', abort=True)
            db.drop_all()
            click.echo('Drop tables.')
        db.create_all()
        click.echo('Initialized database.')


