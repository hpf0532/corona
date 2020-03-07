# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/6 下午5:14
# File: errors.py
# IDE: PyCharm

from flask import jsonify
from backend.api.v1 import api_v1


# 定义webargs错误处理函数
@api_v1.errorhandler(422)
def handle_error(err):
    headers = err.data.get("headers", None)
    messages = err.data.get("messages", ["Invalid request."])
    if headers:
        return jsonify({"errors": messages}), err.code, headers
    else:
        return jsonify({"errors": messages}), err.code


class SqlOperationError(ValueError):
    pass


