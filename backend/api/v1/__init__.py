# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/1 下午12:11
# File: __init__.py.py
# IDE: PyCharm

from flask import Blueprint
from flask_cors import CORS

api_v1 = Blueprint('api_v1', __name__)

CORS(api_v1)

from backend.api.v1 import views
from backend.api.v1 import errors
