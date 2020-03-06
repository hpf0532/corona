# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/1 上午10:31
# File: utils.py
# IDE: PyCharm

from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES


def api_abort(code, message=None, **kwargs):
    if message is None:
        message = HTTP_STATUS_CODES.get(code, '')
    response = jsonify(code=code, message=message, **kwargs)
    response.status_code = code
    return response
