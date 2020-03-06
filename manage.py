# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/2 下午8:02
# File: manage.py
# IDE: PyCharm

from backend import create_app, make_celery
# from backend.extensions import celery_ext

app = create_app()
celery = make_celery(app)
# celery = celery_ext.celery

if __name__ == '__main__':
    app.run()
