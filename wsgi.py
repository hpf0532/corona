# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/4/2 下午2:52
# File: wsgi.py
# IDE: PyCharm

from backend import create_app

# from backend.extensions import celery_ext

app = create_app('production')
